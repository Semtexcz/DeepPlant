# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Cross-platform packaging driver for the standalone DeepPlant Editor.

This is the single canonical application-packaging entry point (Issue #85). It is
plain Python on purpose: Windows is a first-class target, so the canonical
packaging logic must not depend on bash, GNU Make, or Linux-only shell syntax.
The Makefile wraps it for developer convenience only.

Phases stay explicit and separately runnable so a failure is diagnosable:

    frontend   build the production Vue SPA
    stage      collect the built SPA as application-owned resources
    freeze     assemble the standalone application (PyInstaller, native OS)
    package    create the platform user artifact (installer / AppImage)
    verify     smoke-test the produced artifact from outside the checkout
    extract    install/extract an artifact and print its launcher path
    all        frontend -> stage -> freeze -> package -> verify

Layout (all under git-ignored paths):

    build/editor-package/spa      staged SPA mapped into the bundle
    build/editor-package/work     freeze scratch space
    build/editor-package/frozen   frozen application tree
    build/editor-package/verify   packaged-artifact smoke scratch space
    dist/editor/                  user-consumable artifacts

The selected architecture and the measured alternatives are recorded in
``docs/dev/research/standalone-editor-distribution.md``; the reasoning is
summarized in ``docs/dev/workflow/packaging.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[1]

APP_NAME = "deepplant-editor"
APP_DISPLAY_NAME = "DeepPlant Editor"
ENTRY_SCRIPT = REPO_ROOT / "tools" / "editor_entry.py"
SPA_BUILD_DIR = REPO_ROOT / "apps" / "editor" / "dist"
FRONTEND_DIR = REPO_ROOT / "apps" / "editor"
INNO_SCRIPT = REPO_ROOT / "packaging" / "windows" / "deepplant-editor.iss"
APP_ICON_SVG = REPO_ROOT / "assets" / "brand" / "logo" / "deepplant-master-icon.svg"

DEFAULT_BUILD_DIR = REPO_ROOT / "build" / "editor-package"
DEFAULT_DIST_DIR = REPO_ROOT / "dist" / "editor"

#: Where the staged SPA is mapped inside the frozen application. This is the
#: location ``deepplant.editor.application`` looks for first, and it matches the
#: package-relative path the base wheel deliberately excludes.
BUNDLE_SPA_DESTINATION = "deepplant/editor/dist"

SUPPORTED_PLATFORMS = ("windows", "linux")


class PackagingError(RuntimeError):
    """Raised when a packaging phase cannot proceed; the message is user-facing."""


def log(message: str) -> None:
    """Print one packaging diagnostic line, unbuffered enough for CI logs."""
    print(f"[package-editor] {message}", flush=True)


def run(
    command: Sequence[str], *, cwd: Path | None = None, env: Mapping[str, str] | None = None
) -> None:
    """Run one build command, echoing it so CI logs stay diagnosable."""
    log("run: " + " ".join(command))
    merged_env = dict(os.environ)
    if env is not None:
        merged_env.update(env)
    completed = subprocess.run(
        list(command),
        cwd=None if cwd is None else str(cwd),
        env=merged_env,
        check=False,
    )
    if completed.returncode != 0:
        raise PackagingError(
            f"command failed with exit code {completed.returncode}: {' '.join(command)}"
        )


def project_version() -> str:
    """Return the canonical application version from ``pyproject.toml``.

    The project file is the single source of truth, so the packaging driver
    never introduces a second, manually maintained version string.
    """
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        document = tomllib.load(handle)
    project = document.get("project")
    if not isinstance(project, dict):
        raise PackagingError("pyproject.toml has no [project] table")
    version = cast("dict[str, object]", project).get("version")
    if not isinstance(version, str) or not version:
        raise PackagingError("pyproject.toml [project] version is missing")
    return version


def platform_slug() -> str:
    """Return the distribution platform slug, refusing unsupported hosts."""
    if os.name == "nt":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    raise PackagingError(
        f"standalone Editor packaging supports {', '.join(SUPPORTED_PLATFORMS)}; "
        f"this host is {sys.platform!r}"
    )


def architecture_slug() -> str:
    """Return a normalized CPU architecture slug for artifact naming."""
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64", "x64"}:
        return "x86_64"
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    return machine or "unknown"


def artifact_name(version: str) -> str:
    """Return the deterministic artifact filename for this platform."""
    slug = platform_slug()
    arch = architecture_slug()
    if slug == "windows":
        return f"{APP_NAME}-{version}-windows-{arch}-setup.exe"
    return f"{APP_NAME}-{version}-linux-{arch}.AppImage"


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_frontend() -> None:
    """Phase 1: build the production Vue SPA from the frozen lockfile.

    ``pnpm`` is invoked directly (not through Make) so this phase works
    unchanged on a Windows CI runner.
    """
    log("phase: frontend - production SPA build")
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        raise PackagingError(
            "pnpm was not found on PATH; the frontend build needs Node.js 22 and "
            "pnpm (a build-time requirement only - end users never need them)"
        )
    run([pnpm, "install", "--frozen-lockfile"], cwd=FRONTEND_DIR)
    run([pnpm, "run", "build"], cwd=FRONTEND_DIR)
    if not (SPA_BUILD_DIR / "index.html").is_file():
        raise PackagingError(f"frontend build produced no SPA at {SPA_BUILD_DIR}")


def stage_spa(build_dir: Path) -> Path:
    """Phase 2: collect the built SPA as the application's own resource."""
    log("phase: stage - collect built SPA into the packaging tree")
    if not (SPA_BUILD_DIR / "index.html").is_file():
        raise PackagingError(f"no built SPA at {SPA_BUILD_DIR}; run the frontend phase first")
    staged = build_dir / "spa"
    if staged.exists():
        shutil.rmtree(staged)
    shutil.copytree(SPA_BUILD_DIR, staged)
    log(f"staged SPA: {staged} ({_directory_size(staged)} bytes)")
    return staged


def _directory_size(path: Path) -> int:
    """Return the total size in bytes of every file under ``path``."""
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def freeze(build_dir: Path, staged_spa: Path) -> Path:
    """Phase 3: assemble the standalone application for this native OS.

    PyInstaller collects the interpreter, DeepPlant, its runtime dependencies and
    the canonical symbol resources, and maps the staged SPA into the bundle at
    the location the editor application resolves. The result is OS- and
    architecture-specific, which is why every platform builds on its own runner.
    """
    log("phase: freeze - assemble standalone application")
    frozen_root = build_dir / "frozen"
    if frozen_root.exists():
        shutil.rmtree(frozen_root)
    # PyInstaller uses the platform path separator in --add-data on purpose.
    separator = ";" if os.name == "nt" else ":"
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--name",
            APP_NAME,
            "--collect-data",
            "deepplant",
            "--add-data",
            f"{staged_spa}{separator}{BUNDLE_SPA_DESTINATION}",
            "--distpath",
            str(frozen_root),
            "--workpath",
            str(build_dir / "work"),
            "--specpath",
            str(build_dir / "work"),
            str(ENTRY_SCRIPT),
        ],
        cwd=REPO_ROOT,
    )
    frozen_app = frozen_root / APP_NAME
    launcher = frozen_launcher(frozen_app)
    if not launcher.is_file():
        raise PackagingError(f"frozen application has no launcher at {launcher}")
    log(f"frozen application: {frozen_app} ({_directory_size(frozen_app)} bytes)")
    return frozen_app


def frozen_launcher(frozen_app: Path) -> Path:
    """Return the launcher executable inside a frozen application directory."""
    suffix = ".exe" if os.name == "nt" else ""
    return frozen_app / f"{APP_NAME}{suffix}"


def create_package(build_dir: Path, frozen_app: Path, dist_dir: Path, version: str) -> Path:
    """Phase 4: turn the frozen application into a user-consumable artifact."""
    slug = platform_slug()
    dist_dir.mkdir(parents=True, exist_ok=True)
    artifact = dist_dir / artifact_name(version)
    if artifact.exists():
        artifact.unlink()
    if slug == "windows":
        _package_windows(build_dir, frozen_app, artifact, version)
    else:
        _package_linux(build_dir, frozen_app, artifact)
    if not artifact.is_file():
        raise PackagingError(f"packaging produced no artifact at {artifact}")
    log(f"artifact: {artifact} ({artifact.stat().st_size} bytes)")
    log(f"sha256:   {sha256_of(artifact)}")
    return artifact


def _package_windows(build_dir: Path, frozen_app: Path, artifact: Path, version: str) -> None:
    """Build a real Windows installer with Inno Setup.

    Issue #85 asks for a normal installer, not a raw build directory or a ZIP
    around one. Inno Setup produces a standard wizard installer with Start Menu
    entries and a working uninstaller. It is a build-time tool only: it is never
    redistributed inside the artifact, so the end user downloads one ``.exe``.
    """
    log("phase: package - Windows installer (Inno Setup)")
    compiler = _find_inno_setup()
    if not INNO_SCRIPT.is_file():
        raise PackagingError(f"missing Inno Setup script at {INNO_SCRIPT}")
    run(
        [
            str(compiler),
            f"/DAppVersion={version}",
            f"/DSourceDir={frozen_app}",
            f"/DOutputDir={artifact.parent}",
            f"/DOutputBaseFilename={artifact.name[: -len('.exe')]}",
            f"/DLicenseFile={REPO_ROOT / 'LICENSE'}",
            str(INNO_SCRIPT),
        ]
    )


def _find_inno_setup() -> Path:
    """Locate the Inno Setup command-line compiler (``ISCC``)."""
    override = os.environ.get("ISCC")
    if override:
        return Path(override)
    found = shutil.which("ISCC") or shutil.which("iscc")
    if found:
        return Path(found)
    for candidate in (
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ):
        if candidate.is_file():
            return candidate
    raise PackagingError(
        "Inno Setup (ISCC.exe) was not found; install it on the build machine "
        "(for example `choco install innosetup -y`) or set the ISCC environment "
        "variable. This is a build-time requirement only."
    )


def _package_linux(build_dir: Path, frozen_app: Path, artifact: Path) -> None:
    """Build a directly runnable AppImage (Issue #85's preferred Linux format)."""
    log("phase: package - Linux AppImage")
    appdir = _assemble_appdir(build_dir, frozen_app)
    appimagetool = _find_appimagetool()
    run(
        [str(appimagetool), "--no-appstream", str(appdir), str(artifact)],
        env={"ARCH": architecture_slug()},
    )


def _assemble_appdir(build_dir: Path, frozen_app: Path) -> Path:
    """Assemble an AppDir around the frozen application.

    The AppDir is a plain directory layout, so it needs no packaging framework:
    a launcher script, a desktop entry, an icon, and the frozen payload. The
    AppImage runtime itself is added by ``appimagetool``.
    """
    appdir = build_dir / f"{APP_NAME}.AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)
    payload = appdir / "usr" / "bin" / APP_NAME
    payload.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(frozen_app, payload)

    launcher = appdir / "AppRun"
    launcher.write_text(
        "#!/bin/sh\n"
        'HERE="$(dirname "$(readlink -f "$0")")"\n'
        f'exec "$HERE/usr/bin/{APP_NAME}/{APP_NAME}" "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)

    (appdir / f"{APP_NAME}.desktop").write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_DISPLAY_NAME}\n"
        "Comment=Read-only Process/PFD editor over the DeepPlant semantic model\n"
        f"Exec={APP_NAME}\n"
        f"Icon={APP_NAME}\n"
        # The editor prints the loopback URL and keeps running, so it uses a
        # terminal window instead of pretending to be a silent background app.
        "Terminal=true\n"
        "Categories=Science;Engineering;\n",
        encoding="utf-8",
    )

    icon = appdir / f"{APP_NAME}.svg"
    if not APP_ICON_SVG.is_file():
        raise PackagingError(f"missing application icon at {APP_ICON_SVG}")
    shutil.copy2(APP_ICON_SVG, icon)
    shutil.copy2(APP_ICON_SVG, appdir / ".DirIcon")
    log(f"AppDir: {appdir}")
    return appdir


def _find_appimagetool() -> Path:
    """Locate ``appimagetool`` (MIT licensed, build-time only)."""
    override = os.environ.get("APPIMAGETOOL")
    if override:
        return Path(override)
    found = shutil.which("appimagetool")
    if found:
        return Path(found)
    raise PackagingError(
        "appimagetool was not found; download the official upstream release "
        "(https://github.com/AppImage/appimagetool/releases) onto the build "
        "machine, put it on PATH, or set the APPIMAGETOOL environment variable. "
        "This is a build-time requirement only."
    )


def install_or_extract(artifact: Path, destination: Path) -> Path:
    """Install or extract ``artifact`` under ``destination``; return the launcher.

    The two supported artifacts are deliberately handled differently, because
    they are different things to a user:

    - a Windows installer is *installed* (silently, into a temporary directory)
      and later uninstalled, exactly like an end user would;
    - a Linux AppImage is *extracted* into a temporary AppDir, which is the
      supported way to inspect or run one without FUSE.

    No Unix-only process-group or negative-PID assumption is used anywhere here.
    """
    if not artifact.is_file():
        raise PackagingError(f"no artifact at {artifact}")
    destination.mkdir(parents=True, exist_ok=True)

    if platform_slug() == "windows":
        install_dir = destination / "installed"
        run(
            [
                str(artifact),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
                f"/DIR={install_dir}",
            ]
        )
        launcher = install_dir / f"{APP_NAME}.exe"
        if not launcher.is_file():
            raise PackagingError(f"installer placed no launcher at {launcher}")
        return launcher

    run([str(artifact), "--appimage-extract"], cwd=destination)
    appdir = destination / "squashfs-root"
    launcher = appdir / "AppRun"
    if not launcher.is_file():
        raise PackagingError(f"AppImage contains no AppRun launcher at {launcher}")
    return launcher


def uninstall(artifact: Path, destination: Path) -> None:
    """Remove an installed/extracted artifact, using the artifact's own uninstaller."""
    if platform_slug() == "windows":
        uninstaller = destination / "installed" / "unins000.exe"
        if uninstaller.is_file():
            # The uninstaller returns immediately; wait for the files to vanish.
            run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])
            for _ in range(100):
                if not uninstaller.exists():
                    break
                time.sleep(0.1)
    if destination.exists():
        shutil.rmtree(destination, ignore_errors=True)


def sanitized_environment() -> dict[str, str]:
    """Return an environment that proves no separate Python/Node toolchain is used.

    Only operating-system facilities are kept on ``PATH``. Virtual environments,
    Python homes, Node/npm/pnpm entries, and PyInstaller's own variables are
    removed, so a packaged application that still needed any of them would fail
    here. Required OS facilities are deliberately **not** broken.
    """
    if platform_slug() == "windows":
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        path = os.pathsep.join([f"{system_root}\\system32", system_root])
    else:
        path = os.pathsep.join(
            ["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"]
        )
    return {
        "PATH": path,
        "HOME": os.environ.get("HOME", ""),
        "TMPDIR": os.environ.get("TMPDIR", ""),
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
        "SystemRoot": os.environ.get("SystemRoot", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        # PyInstaller reads this to relocate its extraction directory; leaving it
        # unset proves the artifact does not depend on the build environment.
        "PYTHONNOUSERSITE": "1",
    }


_ANNOUNCED_URL = re.compile(r"^\s*open:\s+(http://127\.0\.0\.1:(\d+)/)\s*$", re.MULTILINE)
_STARTUP_TIMEOUT_S = 120.0
_READY_TIMEOUT_S = 60.0
_POLL_INTERVAL_S = 0.2
_HTTP_TIMEOUT_S = 20.0
EXPECTED_STEPS = 7
EXPECTED_STREAMS = 7


def _http_get(port: int, path: str) -> tuple[int, str, bytes]:
    """Return ``(status, content_type, body)`` for one loopback GET."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=_HTTP_TIMEOUT_S)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.getheader("content-type") or "", response.read()
    finally:
        connection.close()


def _wait_for_port(port: int, process: subprocess.Popen[str]) -> None:
    """Block until the loopback port accepts connections, or fail with the log."""
    deadline = time.monotonic() + _READY_TIMEOUT_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise PackagingError("the packaged application exited during startup")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=_POLL_INTERVAL_S):
                return
        except OSError:
            time.sleep(_POLL_INTERVAL_S)
    raise PackagingError(f"the packaged application never accepted connections on port {port}")


def _read_announced_port(process: subprocess.Popen[str]) -> int:
    """Read the launcher's own announcement of its loopback URL.

    Readiness is the application's real output, not a fixed sleep, and the port
    is never hard-coded: the launcher is asked for port ``0``.
    """
    assert process.stdout is not None
    deadline = time.monotonic() + _STARTUP_TIMEOUT_S
    captured: list[str] = []
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise PackagingError(
                "the packaged application exited before announcing a URL:\n" + "".join(captured)
            )
        line = process.stdout.readline()
        if not line:
            time.sleep(_POLL_INTERVAL_S)
            continue
        captured.append(line)
        log("  app: " + line.rstrip())
        match = _ANNOUNCED_URL.search(line)
        if match:
            return int(match.group(2))
    raise PackagingError("the packaged application never announced a URL:\n" + "".join(captured))


def _stop_process(process: subprocess.Popen[str]) -> None:
    """Stop the packaged application and prove nothing is left listening.

    Windows and POSIX are handled with the same API on purpose: the packaged
    application is a single direct child (the browser is disabled for
    automation), so ``terminate``/``kill`` is correct on both and no Unix-only
    process-group signal is used.
    """
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)
    if process.stdout is not None:
        process.stdout.close()


def smoke_test_artifact(artifact: Path, *, work_dir: Path, model_path: Path) -> dict[str, object]:
    """Run the full packaged-artifact verification and return the evidence.

    The sequence intentionally mirrors what an end user does, and additionally
    hides the checkout's built SPA first, so a packaged application that secretly
    depended on ``apps/editor/dist`` fails here instead of passing.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, object] = {"artifact": str(artifact)}

    # The model is copied outside the repository: the packaged application must
    # open a plant model that has nothing to do with the source checkout.
    model_copy = work_dir / "model" / "plant.yaml"
    model_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, model_copy)
    evidence["model"] = str(model_copy)

    launcher = install_or_extract(artifact, work_dir / "install")
    evidence["launcher"] = str(launcher)

    # The checkout's built SPA is moved out of the way so a packaged application
    # that secretly read `apps/editor/dist` would fail here. It is moved into the
    # git-ignored build tree rather than a sibling directory, so no stray copy can
    # be picked up by the frontend lint/type gates.
    hidden_spa = work_dir / "checkout-spa-hidden"
    spa_was_present = SPA_BUILD_DIR.is_dir()
    process: subprocess.Popen[str] | None = None
    try:
        if spa_was_present:
            if hidden_spa.exists():
                shutil.rmtree(hidden_spa)
            SPA_BUILD_DIR.rename(hidden_spa)
        evidence["checkout_spa_removed"] = spa_was_present

        process = _start_packaged_app(launcher, model_copy)
        port = _read_announced_port(process)
        evidence["port"] = port
        _wait_for_port(port, process)
        evidence["checks"] = _verify_served_application(port)
    finally:
        if process is not None:
            _stop_process(process)
        if spa_was_present and hidden_spa.exists() and not SPA_BUILD_DIR.exists():
            hidden_spa.rename(SPA_BUILD_DIR)
        uninstall(artifact, work_dir / "install")

    return evidence


def _start_packaged_app(launcher: Path, model_copy: Path) -> subprocess.Popen[str]:
    """Start the packaged application like an end user, with a sanitized env."""
    command = [
        str(launcher),
        str(model_copy),
        "--port",
        "0",
        "--no-browser",
        "--symbol-role",
        "PS-vessel=vessel",
    ]
    log("smoke: " + " ".join(command))
    return subprocess.Popen(
        command,
        cwd=str(model_copy.parent),
        env=sanitized_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _verify_served_application(port: int) -> dict[str, object]:
    """Probe the running packaged application over loopback only."""
    checks: dict[str, object] = {}

    status, content_type, body = _http_get(port, "/")
    if status != 200 or "text/html" not in content_type:
        raise PackagingError(f"GET / returned {status} ({content_type})")
    if b"/src/main.ts" in body:
        raise PackagingError("the served document is a dev entry point, not the built SPA")
    if b"assets/" not in body:
        raise PackagingError("the served document does not reference built SPA assets")
    checks["GET /"] = status

    status, _, body = _http_get(port, "/api/projection")
    if status != 200:
        raise PackagingError(f"GET /api/projection returned {status}")
    payload = json.loads(body.decode("utf-8"))
    projection = payload["projection"]
    if projection is None:
        raise PackagingError(f"no projection for the realistic fragment: {payload}")
    if payload["validation"]["valid"] is not True:
        raise PackagingError("the packaged application reported the model as invalid")
    checks["steps"] = len(projection["steps"])
    checks["streams"] = len(projection["streams"])
    if checks["steps"] != EXPECTED_STEPS or checks["streams"] != EXPECTED_STREAMS:
        raise PackagingError(f"unexpected projection size: {checks}")

    for role in ("pump", "vessel", "heat_exchanger"):
        status, content_type, body = _http_get(port, f"/api/symbols/{role}.svg")
        if status != 200 or "image/svg+xml" not in content_type or not body.startswith(b"<"):
            raise PackagingError(
                f"canonical symbol {role!r} did not load: {status} ({content_type})"
            )
    checks["symbols"] = "pump,vessel,heat_exchanger"
    return checks


def main(argv: Sequence[str] | None = None) -> int:
    """Run one packaging phase (or all of them) and report the outcome."""
    parser = argparse.ArgumentParser(
        prog="package_editor",
        description="Package the standalone DeepPlant Editor for this platform.",
    )
    parser.add_argument(
        "phase",
        choices=("frontend", "stage", "freeze", "package", "verify", "extract", "all"),
        help="packaging phase to run",
    )
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--dist-dir", type=Path, default=DEFAULT_DIST_DIR)
    parser.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help="artifact to verify/extract (default: the artifact this platform builds)",
    )
    parser.add_argument(
        "--extract-to",
        type=Path,
        default=None,
        help="for the extract phase: install/extract the artifact into this directory",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=REPO_ROOT / "examples" / "realistic-process-fragment" / "plant.yaml",
        help="plant model used by the packaged-artifact smoke test",
    )
    args = parser.parse_args(argv)

    version = project_version()
    build_dir: Path = args.build_dir
    dist_dir: Path = args.dist_dir
    phase: str = args.phase

    try:
        if phase in {"frontend", "all"}:
            build_frontend()
        if phase in {"stage", "all"}:
            stage_spa(build_dir)
        if phase in {"freeze", "all"}:
            freeze(build_dir, staged_spa_dir(build_dir))
        if phase in {"package", "all"}:
            create_package(build_dir, frozen_app_dir(build_dir), dist_dir, version)
        if phase in {"verify", "all"}:
            artifact = (
                args.artifact if args.artifact is not None else dist_dir / artifact_name(version)
            )
            evidence = smoke_test_artifact(
                artifact, work_dir=build_dir / "verify", model_path=args.model
            )
            log("packaged smoke: " + json.dumps(evidence, sort_keys=True, default=str))
            log("VERIFIED: the packaged application served the real editor outside the checkout")
        elif phase == "extract":
            artifact = (
                args.artifact if args.artifact is not None else dist_dir / artifact_name(version)
            )
            destination = (
                args.extract_to
                if args.extract_to is not None
                else Path(tempfile.mkdtemp(prefix="deepplant-editor-extract-"))
            )
            destination.mkdir(parents=True, exist_ok=True)
            launcher = install_or_extract(artifact, destination)
            log(f"extracted: {artifact} -> {launcher}")
            print(str(launcher))
    except PackagingError as error:
        log(f"FAILED: {error}")
        return 1
    return 0


def staged_spa_dir(build_dir: Path) -> Path:
    """Return the staged SPA directory, failing with a clear phase hint."""
    staged = build_dir / "spa"
    if not (staged / "index.html").is_file():
        raise PackagingError(f"no staged SPA at {staged}; run the stage phase first")
    return staged


def frozen_app_dir(build_dir: Path) -> Path:
    """Return the frozen application directory, failing with a phase hint."""
    frozen = build_dir / "frozen" / APP_NAME
    if not frozen.is_dir():
        raise PackagingError(f"no frozen application at {frozen}; run the freeze phase first")
    return frozen


if __name__ == "__main__":
    sys.exit(main())
