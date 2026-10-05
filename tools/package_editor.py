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
    licenses   assemble the redistribution compliance payload (Issue #93 review)
    freeze     assemble the standalone application (PyInstaller, native OS)
    package    create the platform user artifact (installer / AppImage)
    verify     smoke-test the produced artifact from outside the checkout
    extract    install/extract an artifact and print its launcher path
    all        frontend -> stage -> licenses -> freeze -> package -> verify

Layout (all under git-ignored paths):

    build/editor-package/spa      staged SPA mapped into the bundle
    build/editor-package/work     freeze scratch space
    build/editor-package/frozen   frozen application tree
    build/editor-package/verify   packaged-artifact smoke scratch space
    dist/editor/                  user-consumable artifacts

The selected architecture and the measured alternatives are recorded in
``docs/dev/research/standalone-editor-distribution.md``; the reasoning is
summarized in ``docs/dev/workflow/packaging.md``.

The external native toolchain is not a Python dependency, so it is not in
``uv.lock``. ``appimagetool``, the AppImage runtime it embeds, and Inno Setup are
pinned and integrity-checked by CI as declared in ``packaging/toolchain.toml``.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[1]

# The packaging driver runs both as ``python tools/package_editor.py`` (CI, where
# only ``tools/`` is on ``sys.path``) and as the imported ``tools.package_editor``
# module (tests). Adding the repository root keeps the shared Chromium notice
# tooling importable in both cases without a second copy of its logic.
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - import bridge
    sys.path.append(str(REPO_ROOT))

from tools.chromium_notices import (  # noqa: E402 - needs the path bridge above
    REQUIRED_PROVENANCE_MARKERS,
    bundle_component_names,
    bundle_components_without_text,
    check_bundle,
)

APP_NAME = "deepplant-editor"
APP_DISPLAY_NAME = "DeepPlant Editor"
ENTRY_SCRIPT = REPO_ROOT / "tools" / "editor_entry.py"
SPA_BUILD_DIR = REPO_ROOT / "apps" / "editor" / "dist"
FRONTEND_DIR = REPO_ROOT / "apps" / "editor"
INNO_SCRIPT = REPO_ROOT / "packaging" / "windows" / "deepplant-editor.iss"
APP_ICON_SVG = REPO_ROOT / "assets" / "brand" / "logo" / "deepplant-master-icon.svg"
LICENSES_MANIFEST = REPO_ROOT / "packaging" / "licenses.toml"
LICENSES_STATIC_DIR = REPO_ROOT / "packaging" / "licenses"

#: Repository-owned, reviewable Linux host-runtime baseline (Issue #93 review).
#: The audit fails when the packaged application resolves a host library that is
#: not declared here, so a new system dependency cannot appear silently.
LINUX_RUNTIME_BASELINE = REPO_ROOT / "packaging" / "linux-runtime-baseline.toml"

#: A pinned content digest, as stored in the packaging manifests.
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

DEFAULT_BUILD_DIR = REPO_ROOT / "build" / "editor-package"
DEFAULT_DIST_DIR = REPO_ROOT / "dist" / "editor"

#: Where the staged SPA is mapped inside the frozen application. This is the
#: location ``deepplant.editor.application`` looks for first, and it matches the
#: package-relative path the base wheel deliberately excludes.
BUNDLE_SPA_DESTINATION = "deepplant/editor/dist"

SUPPORTED_PLATFORMS = ("windows", "linux")

#: Qt modules the desktop host imports *lazily*, so that the semantic Core, the
#: CLI, and the developer/browser host never depend on PySide6. PyInstaller's
#: static analysis cannot follow a lazy import, so each module is declared
#: explicitly. Naming them makes the PyInstaller Qt hooks bundle the Qt WebEngine
#: helper process, resource packs, ICU data, and locales into the frozen
#: application (Issue #93).
QT_HIDDEN_IMPORTS: tuple[str, ...] = (
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtNetwork",
    "PySide6.QtWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
)

#: Resources a packaged desktop application must contain. The check is a search
#: by name, not a hard-coded layout, because PyInstaller's per-OS placement
#: differs (see `verify_bundle_contents`).
REQUIRED_SPA_ENTRY: str = "deepplant/editor/dist/index.html"
REQUIRED_SYMBOL: str = "deepplant/assets/symbols/process/basic/pump.svg"

#: Directory, inside the installed application, holding the redistribution
#: compliance payload (Issue #93 review). It sits next to the executable so a user
#: can find it, and it is copied into both the Windows install tree and the Linux
#: AppDir by the ordinary packaging flow.
BUNDLE_LICENSES_DESTINATION: str = "licenses"

#: The complete expected compliance payload, relative to
#: ``BUNDLE_LICENSES_DESTINATION``. The project-owned files are always present;
#: the Qt/Qt WebEngine texts come from ``packaging/licenses.toml``. Verification
#: fails if any of these is absent from the built artifact.
REQUIRED_LICENSE_FILES: tuple[str, ...] = (
    "README.md",
    "CORRESPONDING-SOURCE.md",
    "DEEPLANT-AGPL-3.0.txt",
    "THIRD_PARTY_NOTICES.md",
    "Qt/LGPL-3.0-only.txt",
    "Qt/LGPL-2.1-or-later.txt",
    "Qt/GPL-2.0-only.txt",
    "Qt/GPL-3.0-only.txt",
    "Qt/Qt-GPL-exception-1.0.txt",
    "Qt-WebEngine/LGPL-3.0-only.txt",
    "Qt-WebEngine/LGPL-2.0-or-later.txt",
    "Qt-WebEngine/GPL-2.0-only.txt",
    "Qt-WebEngine/GPL-3.0-only.txt",
    "Qt-WebEngine/Qt-GPL-exception-1.0.txt",
    "Qt-WebEngine/Chromium-VERSION.txt",
    "Qt-WebEngine/Chromium-LICENSE-BSD.txt",
    "Qt-WebEngine/Chromium-THIRD-PARTY-NOTICES.txt",
    "Qt-WebEngine/Chromium-NOTICES.md",
)

#: Name of the executable that must never leak after the application exits.
_QT_WEBENGINE_HELPER: str = "QtWebEngineProcess"

#: Dynamic dependencies that must resolve from inside the frozen payload on Linux.
#: A Qt library resolving anywhere else means the bundle mixes in the build host's
#: Qt, which is the mixed-Qt bug the freeze environment guards against.
_LINUX_QT_LIBRARY_PREFIX: str = "libQt6"

#: The Linux binaries the dynamic-dependency audit inspects (Issue #93 review).
#: ``deepplant-editor`` itself is included: it is the launcher the user runs, so
#: its own host dependencies are part of the runtime contract. The ``prefix``
#: form matches the versioned shared objects (``libQt6WebEngineCore.so.6``,
#: ``libqxcb.so``). Each entry is required: a missing target fails the audit.
LINUX_AUDIT_TARGETS: tuple[tuple[str, str], ...] = (
    ("deepplant-editor", "exact"),
    ("QtWebEngineProcess", "exact"),
    ("libQt6WebEngineCore.so", "prefix"),
    ("libqxcb.so", "prefix"),
)


class PackagingError(RuntimeError):
    """Raised when a packaging phase cannot proceed; the message is user-facing."""


def log(message: str) -> None:
    """Print one packaging diagnostic line, unbuffered enough for CI logs.

    Diagnostics go to **stderr** so that a phase whose machine-readable result is
    printed to stdout (``extract`` prints the launcher path) can be consumed by a
    shell substitution. CI captures both streams, so nothing is lost.
    """
    print(f"[package-editor] {message}", file=sys.stderr, flush=True)


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


def load_licenses_manifest() -> dict[str, object]:
    """Load and validate ``packaging/licenses.toml`` (Issue #93 review).

    Raises:
        PackagingError: If the manifest is missing, malformed, or pins a mutable
            locator, so a build can never silently ship stale or unpinned notices.
    """
    if not LICENSES_MANIFEST.is_file():
        raise PackagingError(f"no licence manifest at {LICENSES_MANIFEST}")
    with LICENSES_MANIFEST.open("rb") as handle:
        document: dict[str, object] = tomllib.load(handle)
    version = document.get("pyside6_version")
    if not isinstance(version, str) or not version:
        raise PackagingError("packaging/licenses.toml must declare pyside6_version")
    files_raw = document.get("file")
    if not isinstance(files_raw, list) or not files_raw:
        raise PackagingError("packaging/licenses.toml declares no [[file]] entries")
    for entry in cast("list[object]", files_raw):
        if not isinstance(entry, dict):
            raise PackagingError("packaging/licenses.toml [[file]] entries must be tables")
        table = cast("dict[str, object]", entry)
        for key in ("destination", "url", "sha256"):
            value = table.get(key)
            if not isinstance(value, str) or not value:
                raise PackagingError(f"packaging/licenses.toml entry is missing {key}: {table}")
        url = cast("str", table["url"])
        if any(segment in url for segment in ("/latest", "/continuous", "/master", "/main")):
            raise PackagingError(f"packaging/licenses.toml must not pin a mutable locator: {url}")
    chromium = document.get("chromium")
    if not isinstance(chromium, dict):
        raise PackagingError("packaging/licenses.toml must declare a [chromium] table")
    for key in (
        "version",
        "source_tag",
        "generator",
        "publication",
        "publication_sha256",
        "bundle",
    ):
        value = cast("dict[str, object]", chromium).get(key)
        if not isinstance(value, str) or not value:
            raise PackagingError(f"packaging/licenses.toml [chromium] is missing {key}")
    publication_hash = cast("dict[str, object]", chromium)["publication_sha256"]
    if not isinstance(publication_hash, str) or not _SHA256.match(publication_hash):
        raise PackagingError(
            "packaging/licenses.toml [chromium] publication_sha256 is not a digest"
        )
    components = cast("dict[str, object]", chromium).get("components")
    if not isinstance(components, int) or components <= 0:
        raise PackagingError("packaging/licenses.toml [chromium] must declare a component count")
    return document


def _verify_digest(url: str, data: bytes, expected_sha256: str) -> None:
    """Raise unless ``data`` matches the pinned digest for ``url``."""
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise PackagingError(
            f"licence digest mismatch for {url}: expected {expected_sha256}, got {actual}"
        )


def _fetch_pinned_bytes(url: str, expected_sha256: str) -> bytes:
    """Return the digest-verified bytes at ``url`` (cached when a cache is set).

    The URL is an immutable, version-matched upstream location and the content is
    verified against a pinned SHA-256, so a build never stages mutable "latest"
    licence text. ``DEEPLANT_LICENSE_CACHE`` (optional) points at a directory of
    digest-named blobs so CI can avoid re-downloading.
    """
    cache = os.environ.get("DEEPLANT_LICENSE_CACHE")
    if cache:
        cached = Path(cache) / expected_sha256
        if cached.is_file():
            data = cached.read_bytes()
            _verify_digest(url, data, expected_sha256)
            return data
    log(f"licenses: fetching {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - pinned https
            data = response.read()
    except urllib.error.URLError as exc:
        raise PackagingError(f"could not fetch pinned licence material {url}: {exc}") from exc
    _verify_digest(url, data, expected_sha256)
    if cache:
        cache_dir = Path(cache)
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / expected_sha256).write_bytes(data)
    return data


def verify_chromium_notices(manifest: Mapping[str, object], payload: Path) -> dict[str, object]:
    """Prove the shipped Chromium notice bundle matches the pinned upstream set.

    ``stage_licenses`` calls this with the staged payload, so a build fails when
    the bundle is missing, empty, partial, or built from a different upstream
    publication than ``packaging/licenses.toml`` pins (Issue #93 review fix). The
    upstream publication is fetched from the pinned URL and digest-verified, which
    is what ties the shipped notice text to the exact engine version.
    """
    chromium = manifest.get("chromium")
    if not isinstance(chromium, dict):
        raise PackagingError("packaging/licenses.toml declares no [chromium] table")
    table = cast("Mapping[str, object]", chromium)
    bundle = payload / cast("str", table["bundle"])
    if not bundle.is_file():
        raise PackagingError(
            f"the compliance payload carries no Chromium notice bundle at {bundle}"
        )
    bundle_text = bundle.read_text(encoding="utf-8")
    list_html = _fetch_pinned_bytes(
        cast("str", table["publication"]), cast("str", table["publication_sha256"])
    ).decode("utf-8")
    problems = check_bundle(bundle_text, list_html)
    if problems:
        raise PackagingError(
            "the Chromium notice bundle is not complete:\n  " + "\n  ".join(problems)
        )
    components = len(set(bundle_component_names(bundle_text)))
    declared = cast("int", table["components"])
    if components != declared:
        raise PackagingError(
            f"the Chromium notice bundle covers {components} components but "
            f"packaging/licenses.toml declares {declared}"
        )
    log(
        f"chromium notices: {components} components verified against "
        f"{cast('str', table['publication'])}"
    )
    return {
        "chromium_version": cast("str", table["version"]),
        "chromium_components": components,
        "chromium_publication": cast("str", table["publication"]),
        "chromium_publication_sha256": cast("str", table["publication_sha256"]),
        "chromium_bundle_bytes": len(bundle_text.encode("utf-8")),
    }


def verify_chromium_notices_presence(app_dir: Path) -> dict[str, object]:
    """Assert the installed artifact carries real Chromium notice content.

    Offline companion to :func:`verify_chromium_notices` for artifact
    verification: it proves the shipped bundle is present, carries the generated
    provenance markers, enumerates the declared number of components, and has
    non-empty notice text for each of them, so a placeholder file listing URLs
    cannot satisfy the artifact gate (Issue #93 review fix).
    """
    chromium = load_licenses_manifest().get("chromium")
    if not isinstance(chromium, dict):
        raise PackagingError("packaging/licenses.toml declares no [chromium] table")
    table = cast("Mapping[str, object]", chromium)
    bundle = app_dir / BUNDLE_LICENSES_DESTINATION / cast("str", table["bundle"])
    if not bundle.is_file():
        raise PackagingError(
            f"the packaged application carries no Chromium notice bundle at {bundle}"
        )
    bundle_text = bundle.read_text(encoding="utf-8")
    for marker in REQUIRED_PROVENANCE_MARKERS:
        if marker not in bundle_text:
            raise PackagingError(f"the packaged Chromium notice bundle is missing {marker!r}")
    components = sorted(set(bundle_component_names(bundle_text)))
    declared = cast("int", table["components"])
    if len(components) != declared:
        raise PackagingError(
            f"the packaged Chromium notice bundle covers {len(components)} components, "
            f"expected {declared}"
        )
    empty = bundle_components_without_text(bundle_text)
    if empty:
        raise PackagingError(
            "the packaged Chromium notice bundle has entries without notice text: "
            + ", ".join(sorted(empty)[:10])
        )
    return {
        "chromium_components": len(components),
        "chromium_bundle_bytes": len(bundle_text.encode("utf-8")),
    }


def stage_licenses(build_dir: Path) -> Path:
    """Phase: assemble the redistribution compliance payload (Issue #93 review).

    The payload combines the project's own licence and notice index, the
    project-authored compliance mechanism documents under ``packaging/licenses/``
    (including the generated, version-matched Chromium third-party notice bundle),
    and the version-matched Qt / Qt WebEngine licence texts pinned in
    ``packaging/licenses.toml`` (fetched from immutable URLs and SHA-256 verified).
    The result is a ``licenses/`` tree that the packaging flow copies next to the
    installed executable.
    """
    log("phase: licenses - assemble the redistribution compliance payload")
    manifest = load_licenses_manifest()
    staged = build_dir / BUNDLE_LICENSES_DESTINATION
    if staged.exists():
        shutil.rmtree(staged)
    staged.mkdir(parents=True)

    license_file = REPO_ROOT / "LICENSE"
    if not license_file.is_file():
        raise PackagingError(f"no project licence at {license_file}")
    shutil.copy2(license_file, staged / "DEEPLANT-AGPL-3.0.txt")
    shutil.copy2(REPO_ROOT / "THIRD_PARTY_NOTICES.md", staged / "THIRD_PARTY_NOTICES.md")
    if not LICENSES_STATIC_DIR.is_dir():
        raise PackagingError(f"no project compliance documents at {LICENSES_STATIC_DIR}")
    shutil.copytree(LICENSES_STATIC_DIR, staged, dirs_exist_ok=True)

    entries = cast("list[dict[str, object]]", manifest.get("file"))
    verified = 0
    for table in entries:
        destination = cast("str", table["destination"])
        url = cast("str", table["url"])
        digest = cast("str", table["sha256"])
        target = staged / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_fetch_pinned_bytes(url, digest))
        verified += 1

    verify_chromium_notices(manifest, staged)

    missing = [name for name in REQUIRED_LICENSE_FILES if not (staged / name).is_file()]
    if missing:
        raise PackagingError("staged compliance payload is incomplete: " + ", ".join(missing))
    log(
        f"licenses: {staged} ({_directory_size(staged)} bytes, "
        f"{verified} pinned files digest-verified)"
    )
    return staged


def _install_licenses(frozen_app: Path, build_dir: Path) -> None:
    """Copy the staged compliance payload next to the installed executable."""
    staged = build_dir / BUNDLE_LICENSES_DESTINATION
    if not (staged / "README.md").is_file():
        raise PackagingError(
            f"no staged compliance payload at {staged}; run the licenses phase first"
        )
    destination = frozen_app / BUNDLE_LICENSES_DESTINATION
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(staged, destination)
    log(f"licenses: installed {destination}")


def verify_license_payload(app_dir: Path) -> dict[str, object]:
    """Assert the installed application really carries its compliance payload.

    Repository documentation is not artifact evidence, so this inspects the built
    Windows install tree / extracted Linux AppImage and fails if any required
    licence or notice file is missing or empty (Issue #93 review).
    """
    root = app_dir / BUNDLE_LICENSES_DESTINATION
    if not root.is_dir():
        raise PackagingError(f"the packaged application carries no licenses/ directory at {root}")
    missing: list[str] = []
    empty: list[str] = []
    for name in REQUIRED_LICENSE_FILES:
        path = root / name
        if not path.is_file():
            missing.append(name)
        elif path.stat().st_size == 0:
            empty.append(name)
    if missing:
        raise PackagingError(
            "the packaged application is missing licence material: " + ", ".join(missing)
        )
    if empty:
        raise PackagingError(
            "the packaged application has empty licence material: " + ", ".join(empty)
        )
    return {
        "licenses_dir": str(root),
        "license_files": len(REQUIRED_LICENSE_FILES),
        "license_bytes": _directory_size(root),
    }


def select_audited_artifacts(app_dir: Path) -> dict[str, list[Path]]:
    """Return the required Linux audit targets and the files that satisfy them.

    Every target in ``_LINUX_AUDIT_TARGETS`` must be present in the packaged
    application; a missing one is a packaging failure, not a warning, because the
    audit can only prove what it actually inspected (Issue #93 review).
    """
    found: dict[str, list[Path]] = {}
    for label, form in LINUX_AUDIT_TARGETS:
        if form == "exact":
            matches = [path for path in app_dir.rglob("*") if path.is_file() and path.name == label]
        else:
            matches = [
                path
                for path in app_dir.rglob("*")
                if path.is_file() and path.name.startswith(label)
            ]
        if not matches:
            raise PackagingError(f"the packaged application carries no {label} to audit")
        found[label] = sorted(matches)
    return found


def parse_ldd_output(output: str) -> list[tuple[str, str | None]]:
    """Parse ``ldd`` output into (library name, resolved path or None) pairs.

    ``None`` means the loader reported ``not found``. The dynamic-loader line
    (``/lib64/ld-linux-x86-64.so.2``) and ``linux-vdso.so.1`` carry no ``=>``
    mapping and are skipped: they are not reviewable library dependencies.
    """
    entries: list[tuple[str, str | None]] = []
    for line in output.splitlines():
        match = re.match(r"\s*(?P<name>\S+)\s+=>\s+(?P<resolved>.+)$", line)
        if match is None:
            continue
        resolved = re.sub(r"\s*\(0x[0-9a-fA-F]+\)\s*$", "", match.group("resolved")).strip()
        entries.append((match.group("name"), None if resolved == "not found" else resolved))
    return entries


def classify_linux_dependency(
    resolved: Path,
    app_dir: Path,
    *,
    repo_root: Path | None = None,
    python_prefix: Path | None = None,
) -> str:
    """Classify a resolved dependency path as bundled / host / checkout / uv-env."""
    try:
        target = resolved.resolve()
    except OSError:  # pragma: no cover - unreadable path
        target = resolved
    app = app_dir.resolve()
    if target == app or app in target.parents:
        return "bundled"
    # The uv environment is checked before the checkout as a whole, because its own
    # path normally lives inside the repository and a developer-environment leak is
    # the more specific diagnosis.
    prefix = (python_prefix or Path(sys.prefix)).resolve()
    if target == prefix or prefix in target.parents:
        return "uv-env"
    repo = (repo_root or REPO_ROOT).resolve()
    if target == repo or repo in target.parents:
        return "checkout"
    return "host"


def load_linux_runtime_baseline(path: Path | None = None) -> dict[str, str]:
    """Load the repository-owned Linux host-runtime baseline (Issue #93 review).

    The baseline names the host libraries the packaged application is allowed to
    resolve, by SONAME (stable library identity) rather than by machine-specific
    path, so the contract is reviewable and portable. A new host library must be
    reviewed and added deliberately; CI never auto-updates this file.
    """
    baseline_path = path or LINUX_RUNTIME_BASELINE
    if not baseline_path.is_file():
        raise PackagingError(f"no Linux runtime baseline at {baseline_path}")
    with baseline_path.open("rb") as handle:
        document: dict[str, object] = tomllib.load(handle)
    if document.get("schema_version") != 1:
        raise PackagingError(f"{baseline_path} must declare schema_version = 1")
    host = document.get("host")
    if not isinstance(host, dict) or not host:
        raise PackagingError(f"{baseline_path} declares no [host] dependencies")
    baseline: dict[str, str] = {}
    for name, reason in cast("dict[str, object]", host).items():
        if not isinstance(reason, str) or not reason:
            raise PackagingError(f"{baseline_path} must give a reason for {name!r}")
        baseline[name] = reason
    return baseline


def check_host_baseline(actual: set[str], declared: set[str]) -> tuple[list[str], list[str]]:
    """Return (unexpected, stale) host dependencies relative to the baseline."""
    return sorted(actual - declared), sorted(declared - actual)


def audit_linux_dependencies(app_dir: Path) -> dict[str, object]:
    """Audit the packaged Linux application's dynamic dependencies (Issue #93 review).

    ``ldd`` runs on the launcher the user actually executes (``deepplant-editor``)
    and on the toolchain-critical Qt binaries: the ``QtWebEngineProcess`` helper,
    the Qt WebEngine Core library, and the Qt platform plugin. Every resolved
    dependency is classified as bundled (inside the application tree), host (an
    ordinary Linux system library), checkout, or uv-environment.

    The audit fails on all of the following, so it is fail-closed rather than
    merely descriptive:

    - a required audited target is missing from the artifact;
    - a dependency is ``not found``;
    - a dependency resolves into the repository checkout or the uv environment;
    - a Qt library resolves from the host instead of the bundle;
    - a host library is resolved that the repository-owned baseline
      (``packaging/linux-runtime-baseline.toml``) does not declare.

    Declared-but-unused baseline entries are reported as evidence, not treated as
    a failure: they are how platform variation shows up for a maintainer to review.
    """
    if platform_slug() != "linux":
        return {"platform": platform_slug(), "audited": False}
    ldd = shutil.which("ldd")
    if ldd is None:
        raise PackagingError("ldd is required for the Linux dynamic-dependency audit")
    targets = select_audited_artifacts(app_dir)
    baseline = load_linux_runtime_baseline()

    inventory: dict[str, dict[str, list[str]]] = {}
    resolved_host: dict[str, str] = {}
    actual_host: set[str] = set()
    bundled_total: set[str] = set()
    problems: list[str] = []
    for label, paths in targets.items():
        bundled: set[str] = set()
        host: set[str] = set()
        for path in paths:
            completed = subprocess.run(
                [ldd, str(path)], capture_output=True, text=True, check=False
            )
            for name, resolved in parse_ldd_output(completed.stdout):
                if resolved is None:
                    problems.append(f"{label}: {name} is not found")
                    continue
                kind = classify_linux_dependency(Path(resolved), app_dir)
                if kind == "bundled":
                    bundled.add(name)
                    bundled_total.add(name)
                elif kind == "host":
                    if name.startswith(_LINUX_QT_LIBRARY_PREFIX):
                        problems.append(
                            f"{label}: Qt library {name} resolves to the host ({resolved})"
                        )
                    host.add(name)
                    actual_host.add(name)
                    resolved_host[name] = resolved
                else:
                    problems.append(f"{label}: {name} resolves into the {kind} ({resolved})")
        inventory[label] = {"bundled": sorted(bundled), "host": sorted(host)}

    unexpected, stale = check_host_baseline(actual_host, set(baseline))
    for name in unexpected:
        problems.append(
            f"undeclared host dependency {name} resolved from {resolved_host.get(name)}; "
            "review it and add it to packaging/linux-runtime-baseline.toml"
        )
    if problems:
        raise PackagingError("Linux dependency audit failed:\n  " + "\n  ".join(problems))

    log(
        f"dependency audit: {len(targets)} binaries, {len(bundled_total)} bundled / "
        f"{len(actual_host)} host libraries ({len(baseline)} declared in the baseline)"
    )
    if stale:
        log(f"dependency audit: declared but unused baseline entries: {stale}")
    return {
        "audited_targets": sorted(targets),
        "targets": inventory,
        "bundled_dependencies": len(bundled_total),
        "host_dependencies": len(actual_host),
        "host_baseline": {
            "source": "packaging/linux-runtime-baseline.toml",
            "declared": sorted(baseline),
            "unexpected": unexpected,
            "stale": stale,
        },
        "resolved_host_paths": dict(sorted(resolved_host.items())),
    }


def _qtwebengine_helper_pids() -> set[int]:
    """Return the PIDs of currently running Qt WebEngine helper processes.

    Deliberately narrow: the packaged self-check compares the before/after
    snapshots of this set, so it proves the application did not leak the helpers it
    started - not that the operating system contains zero unrelated ones.
    """
    pids: set[int] = set()
    if os.name == "nt":
        completed = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {_QT_WEBENGINE_HELPER}.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in completed.stdout.splitlines():
            match = re.match(r'\s*"[^"]+","(\d+)"', line)
            if match is not None:
                pids.add(int(match.group(1)))
        return pids
    proc = Path("/proc")
    if not proc.is_dir():
        return pids
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if _QT_WEBENGINE_HELPER.encode() in cmdline:
            pids.add(int(entry.name))
    return pids


def qt_build_environment() -> dict[str, str]:
    """Return build-environment overrides that keep the frozen Qt consistent.

    PyInstaller resolves each collected library's own dependencies through the
    *build host*. If that host happens to have a Qt 6 runtime installed - a common
    developer machine, and some CI images - a Qt library that PySide6 ships can be
    collected from the host instead, producing a bundle that mixes two Qt versions
    and fails at import with an unresolved Qt *private* symbol rather than a clear
    error.

    Preferring PySide6's own Qt library directory during dependency analysis makes
    the collected Qt come from one place on any build host. This is a build-time
    concern only: nothing about the end-user runtime changes, and the base
    Python/Core installation is unaffected.
    """
    if os.name == "nt":
        return {}
    module = importlib.import_module("PySide6")
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        return {}
    qt_lib = Path(module_file).parent / "Qt" / "lib"
    if not qt_lib.is_dir():
        return {}
    existing = os.environ.get("LD_LIBRARY_PATH", "")
    value = f"{qt_lib}{os.pathsep}{existing}" if existing else str(qt_lib)
    return {"LD_LIBRARY_PATH": value}


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
    command = [
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
    ]
    # The desktop host imports Qt lazily, so its hidden imports are declared here
    # (see QT_HIDDEN_IMPORTS).
    for module in QT_HIDDEN_IMPORTS:
        command += ["--hidden-import", module]
    if platform_slug() == "windows":
        # A graphical application must not open a console window when the user
        # launches it from the Start Menu.
        command.append("--windowed")
    command.append(str(ENTRY_SCRIPT))
    run(command, cwd=REPO_ROOT, env=qt_build_environment())
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
    """Phase 4: turn the frozen application into a user-consumable artifact.

    The staged redistribution compliance payload is installed into the frozen tree
    first, so both the Windows installer and the Linux AppImage carry it (Issue #93
    review).
    """
    slug = platform_slug()
    _install_licenses(frozen_app, build_dir)
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
        "Inno Setup (ISCC.exe) was not found; CI installs the pinned version "
        "recorded in packaging/toolchain.toml (see docs/dev/workflow/packaging.md). "
        "For a local build, install Inno Setup 6 or set the ISCC environment "
        "variable. This is a build-time requirement only."
    )


def _package_linux(build_dir: Path, frozen_app: Path, artifact: Path) -> None:
    """Build a directly runnable AppImage (Issue #85's preferred Linux format).

    CI pins the AppImage type-2 runtime and passes it through ``APPIMAGE_RUNTIME``
    with ``--runtime-file``, so the runtime embedded into the artifact is a
    reviewed, checksum-verified input instead of whatever the upstream mutable
    ``continuous`` release happens to serve at build time. Without the variable,
    ``appimagetool`` selects the runtime itself, which is fine for a local build.
    """
    log("phase: package - Linux AppImage")
    appdir = _assemble_appdir(build_dir, frozen_app)
    appimagetool = _find_appimagetool()
    command = [str(appimagetool), "--no-appstream"]
    runtime = os.environ.get("APPIMAGE_RUNTIME")
    if runtime:
        log(f"AppImage runtime: {runtime}")
        command += ["--runtime-file", runtime]
    command += [str(appdir), str(artifact)]
    run(command, env={"ARCH": architecture_slug()})


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
        "Comment=Graphical editor for the DeepPlant semantic model\n"
        f"Exec={APP_NAME}\n"
        f"Icon={APP_NAME}\n"
        # The standalone application is a native desktop window with an embedded
        # webview (Issue #93), so it must not ask for a terminal.
        "Terminal=false\n"
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
        "appimagetool was not found; CI downloads the pinned, checksum-verified "
        "release recorded in packaging/toolchain.toml (see "
        "docs/dev/workflow/packaging.md). For a local build, put appimagetool on "
        "PATH or set the APPIMAGETOOL environment variable. This is a build-time "
        "requirement only."
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

    Only operating-system facilities are kept. Virtual environments, Python
    homes, Node/npm/pnpm entries, and PyInstaller's own variables are removed, so
    a packaged application that still needed any of them would fail here.
    Required OS facilities are deliberately **not** broken - and that includes the
    graphical session: the desktop application (Issue #93) needs the display it
    would have in a normal user session, so ``DISPLAY`` and the other platform
    session variables are preserved and are *not* considered a toolchain.
    """
    if platform_slug() == "windows":
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        path = os.pathsep.join([f"{system_root}\\system32", system_root])
    else:
        path = os.pathsep.join(
            ["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"]
        )
    environment = {
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
    # The graphical session and platform identity a normal desktop provides.
    # These are OS/platform facilities, not a Python/Node toolchain: without the
    # display variables a GUI application cannot start on Linux at all, and
    # without the Windows session variables the platform cannot resolve a home or
    # application-data directory.
    for name in (
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_RUNTIME_DIR",
        "XAUTHORITY",
        "DBUS_SESSION_BUS_ADDRESS",
        "XDG_SESSION_TYPE",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "USERNAME",
        "USERDOMAIN",
        "COMPUTERNAME",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE",
    ):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


#: The packaged desktop application is a graphical product, so its verification
#: drives the real window rather than an HTTP endpoint (Issue #93). The bound sits
#: comfortably above the application's own self-check watchdog, so a stalled run
#: reports why instead of being killed by the caller.
_DESKTOP_SELF_CHECK_TIMEOUT_S = 150.0

#: How long the Qt WebEngine helper processes may take to disappear after the main
#: process has exited. Qt reaps them as the page/profile are destroyed; a helper
#: still present after this grace period means the application leaked it.
_HELPER_EXIT_GRACE_S = 10.0


def frozen_app_dir_of(launcher: Path) -> Path:
    """Return the directory that contains the frozen executable.

    The two artifacts expose a different launcher path:

    - the Windows installer installs the onedir tree directly, so the launcher is
      ``<dir>/deepplant-editor.exe``;
    - the AppImage exposes ``AppRun`` at the AppDir root, with the frozen tree at
      ``usr/bin/deepplant-editor/``.
    """
    if launcher.name == "AppRun":
        payload = launcher.parent / "usr" / "bin" / APP_NAME
        if payload.is_dir():
            return payload
    return launcher.parent


def bundle_dir(launcher: Path) -> Path:
    """Return the directory that holds the frozen application's bundled data.

    PyInstaller 6 *onedir* places the collected modules, resources, and data
    under ``_internal/`` beside the executable (older layouts put them in the
    same directory), so that directory is preferred when it exists.
    """
    app_dir = frozen_app_dir_of(launcher)
    internal = app_dir / "_internal"
    return internal if internal.is_dir() else app_dir


def verify_bundle_contents(bundle: Path) -> dict[str, object]:
    """Assert the packaged application really carries what it must.

    Static artifact evidence for Issue #93: the built shared SPA, the canonical
    DeepPlant symbols, and the Qt WebEngine runtime (helper process, resource
    packs, locales) that make the embedded webview work without a system browser
    and without the end user installing anything.
    """
    evidence: dict[str, object] = {}
    for required in (REQUIRED_SPA_ENTRY, REQUIRED_SYMBOL):
        path = bundle / required
        if not path.is_file():
            raise PackagingError(f"the packaged application is missing {required}")
        evidence[required] = path.stat().st_size

    entries = list(bundle.rglob("*"))
    names = [entry.name for entry in entries]
    helper = sorted(name for name in names if name.startswith("QtWebEngineProcess"))
    if not helper:
        raise PackagingError("the packaged application carries no QtWebEngineProcess helper")
    packs = sorted(name for name in names if name.endswith(".pak"))
    if not packs:
        raise PackagingError("the packaged application carries no Qt WebEngine resource pack")
    if "icudtl.dat" not in names:
        raise PackagingError(
            "the packaged application carries no Qt WebEngine ICU data (icudtl.dat)"
        )

    # The locale packs live in a platform- and PyInstaller-version-dependent
    # directory name (``locales`` or ``qtwebengine_locales``), and an empty
    # ``resources/locales`` directory can also exist. The search therefore looks
    # for a directory that actually *contains* locale packs, in any order, rather
    # than trusting the first name match.
    locale_dirs = [entry for entry in entries if entry.is_dir() and "locale" in entry.name.lower()]
    locale_dir = next(
        (
            directory
            for directory in locale_dirs
            if any(item.suffix == ".pak" for item in directory.glob("*"))
        ),
        None,
    )
    if locale_dir is None:
        raise PackagingError("the packaged application carries no Qt WebEngine locale packs")

    evidence["qtwebengine_helper"] = helper[0]
    evidence["qt_webengine_resource_packs"] = len(packs)
    evidence["qt_webengine_locales"] = locale_dir.name
    return evidence


def _read_text_file(path: Path) -> str:
    """Return a file's text, or an empty string when it is absent or unreadable."""
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _self_check_diagnostics(report: Path) -> str:
    """Return the self-check report and its stage log, for failure messages.

    A packaged Windows Editor has no console, so this is the only place its
    diagnostics can be read from.
    """
    parts: list[str] = []
    log_path = report.with_name(report.name + ".log")
    if log_path.is_file():
        parts.append(f"--- {log_path.name} ---")
        parts.append(log_path.read_text(encoding="utf-8", errors="replace").rstrip())
    if report.is_file():
        parts.append(f"--- {report.name} ---")
        parts.append(report.read_text(encoding="utf-8", errors="replace").rstrip())
    return "\n".join(parts)


def run_desktop_self_check(
    launcher: Path,
    *,
    report: Path,
    model: Path | None,
    cwd: Path,
    timeout: float = _DESKTOP_SELF_CHECK_TIMEOUT_S,
) -> dict[str, object]:
    """Run the packaged desktop application's own verification and check it.

    The application is launched exactly as an end user launches it - from outside
    the checkout, with a sanitized environment (no virtualenv, and no Python/Node
    entries on ``PATH``) - and shows the real native window with the real embedded
    SPA. It then writes a JSON report and exits; both the exit code and the report
    must agree that the desktop product works.

    ``model`` is optional. Without it the bootstrap window is verified (the
    no-argument launch), with it the full packaged editor workflow is verified.
    """
    command = [str(launcher)]
    if model is not None:
        command += [str(model), "--symbol-role", "PS-vessel=vessel"]
    # Absolute: the application runs with the model's directory as its working
    # directory, so a relative report path would be written somewhere else.
    report = report.resolve()
    command += ["--self-check", "--self-check-report", str(report), "--port", "0"]
    log("desktop self-check: " + " ".join(command))

    if report.exists():
        report.unlink()
    for suffix in (".log", ".console.log"):
        stale = report.with_name(report.name + suffix)
        if stale.exists():
            stale.unlink()

    environment = sanitized_environment()
    # The verification runs on a headless/virtual display in CI, which has no GPU
    # it can use. This is an automation-only Chromium flag and is not part of the
    # user's runtime environment; the sandbox is untouched.
    environment["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"

    # The child's output is redirected to a *file*, never a pipe. A GUI process
    # can own helper processes (Qt WebEngine's renderer), and an inherited pipe
    # write handle would keep the pipe open: the caller would then wait for a
    # channel that nothing can close, which is a well-known way to hang an
    # automated GUI check. A file handle has no such coupling.
    console_log = report.with_name(report.name + ".console.log")
    # Snapshot the Qt WebEngine helpers that already exist before this run, so the
    # post-exit check can prove *this* application did not leak the helpers *it*
    # started (never "the OS has zero QtWebEngineProcess processes").
    helpers_before = _qtwebengine_helper_pids()
    timed_out = False
    return_code: int | None = None
    try:
        with console_log.open("wb") as sink:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        return_code = completed.returncode
    except subprocess.TimeoutExpired:
        timed_out = True

    for line in _read_text_file(console_log).splitlines():
        log("  app: " + line)

    diagnostics = _self_check_diagnostics(report)
    for line in diagnostics.splitlines():
        log("  stage: " + line)

    if timed_out:
        raise PackagingError(
            f"the packaged desktop application did not exit within {timeout:.0f} s "
            f"(self-check report written: {report.is_file()})\n{diagnostics}"
        )
    if not report.is_file():
        raise PackagingError(
            "the packaged desktop application wrote no self-check report "
            f"(exit code {return_code})\n{diagnostics}"
        )
    payload = json.loads(report.read_text(encoding="utf-8"))
    if return_code != 0 or payload.get("verdict") != "pass":
        raise PackagingError(f"the packaged desktop self-check failed: {payload}\n{diagnostics}")
    checks_raw = payload.get("checks")
    if not isinstance(checks_raw, dict):
        raise PackagingError(f"the packaged desktop self-check reported no checks: {payload}")
    checks = cast("dict[str, object]", checks_raw)
    if not checks:
        raise PackagingError(f"the packaged desktop self-check reported no checks: {payload}")
    required_lifecycle = (
        "windowVisible",
        "windowClosed",
        "serverStopRequested",
        "serverStopped",
        "serverThreadTerminated",
        "portReleased",
        "eventLoopReturned",
    )
    missing_lifecycle = [name for name in required_lifecycle if name not in checks]
    if missing_lifecycle:
        raise PackagingError(
            "the packaged desktop self-check did not report required lifecycle facts: "
            + ", ".join(missing_lifecycle)
            + f" -> {payload}"
        )
    failed = sorted(name for name, value in checks.items() if value is not True)
    if failed:
        raise PackagingError(f"the packaged desktop self-check failed: {failed} -> {payload}")

    # The application exited and the event loop returned; Qt now reaps its own
    # helper processes. Give it a bounded moment, then require that no helper this
    # run started is still alive.
    deadline = time.monotonic() + _HELPER_EXIT_GRACE_S
    leaked = sorted(_qtwebengine_helper_pids() - helpers_before)
    while leaked and time.monotonic() < deadline:
        time.sleep(0.25)
        leaked = sorted(_qtwebengine_helper_pids() - helpers_before)
    if leaked:
        raise PackagingError(
            f"the packaged desktop application leaked Qt WebEngine helper processes: {leaked}\n"
            f"{diagnostics}"
        )
    payload["qtwebengineHelpersLeaked"] = leaked
    return payload


def _write_dependency_inventory(work_dir: Path, inventory: Mapping[str, object]) -> Path:
    """Persist the full Linux dependency inventory as CI evidence (Issue #93 review).

    Counts alone are not reviewable, so the exact per-target bundled/host library
    inventory is written as deterministic JSON and uploaded with the desktop
    evidence artifact, letting a reviewer inspect what the AppImage requires.
    """
    path = work_dir / "dependency-inventory.json"
    path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(f"dependency inventory: {path}")
    return path


def smoke_test_artifact(artifact: Path, *, work_dir: Path, model_path: Path) -> dict[str, object]:
    """Verify the packaged **desktop** application outside the checkout.

    The sequence mirrors what an end user does, and additionally hides the
    checkout's built SPA first, so a packaged application that secretly depended
    on ``apps/editor/dist`` fails here instead of passing.

    Since Issue #93 the product is a graphical desktop application, so the
    evidence is the real native window and the real embedded SPA - not an HTTP
    endpoint. Two launches are checked:

    1. no model argument -> the bootstrap window appears and closes cleanly;
    2. the realistic fragment -> the packaged editor workflow renders Valid, seven
       ProcessSteps, seven ProcessStreams, selects ``PS-pump``, and shows its
       semantic data in the Inspector.

    Both report whether the owned server stopped and the loopback socket was
    released when the window closed.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, object] = {"artifact": str(artifact), "sha256": sha256_of(artifact)}

    # The model is copied outside the repository: the packaged application must
    # open a plant model that has nothing to do with the source checkout.
    model_copy = work_dir / "model" / "plant.yaml"
    model_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, model_copy)
    evidence["model"] = str(model_copy)

    launcher = install_or_extract(artifact, work_dir / "install")
    evidence["launcher"] = str(launcher)
    evidence["bundle"] = verify_bundle_contents(bundle_dir(launcher))
    app_dir = frozen_app_dir_of(launcher)
    # Redistribution compliance payload and (on Linux) the dynamic-dependency
    # audit are asserted against the *installed/extracted artifact*, not the source
    # checkout (Issue #93 review).
    licenses_evidence = verify_license_payload(app_dir)
    licenses_evidence.update(verify_chromium_notices_presence(app_dir))
    evidence["licenses"] = licenses_evidence
    inventory = audit_linux_dependencies(app_dir)
    evidence["dependencies"] = inventory
    _write_dependency_inventory(work_dir, inventory)

    # The checkout's built SPA is moved out of the way so a packaged application
    # that secretly read `apps/editor/dist` would fail here. It is moved into the
    # git-ignored build tree rather than a sibling directory, so no stray copy can
    # be picked up by the frontend lint/type gates.
    hidden_spa = work_dir / "checkout-spa-hidden"
    spa_was_present = SPA_BUILD_DIR.is_dir()
    reports = work_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    try:
        if spa_was_present:
            if hidden_spa.exists():
                shutil.rmtree(hidden_spa)
            SPA_BUILD_DIR.rename(hidden_spa)
        evidence["checkout_spa_removed"] = spa_was_present

        evidence["window_lifecycle"] = run_desktop_self_check(
            launcher,
            report=reports / "no-model.json",
            model=None,
            cwd=model_copy.parent,
        )
        evidence["desktop_workflow"] = run_desktop_self_check(
            launcher,
            report=reports / "desktop-workflow.json",
            model=model_copy,
            cwd=model_copy.parent,
        )
    finally:
        if spa_was_present and hidden_spa.exists() and not SPA_BUILD_DIR.exists():
            hidden_spa.rename(SPA_BUILD_DIR)
        uninstall(artifact, work_dir / "install")

    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    """Run one packaging phase (or all of them) and report the outcome."""
    parser = argparse.ArgumentParser(
        prog="package_editor",
        description="Package the standalone DeepPlant Editor for this platform.",
    )
    parser.add_argument(
        "phase",
        choices=("frontend", "stage", "licenses", "freeze", "package", "verify", "extract", "all"),
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
        if phase in {"licenses", "all"}:
            stage_licenses(build_dir)
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
            log(
                "VERIFIED: the packaged desktop application opened a native window with the "
                "real shared Vue editor outside the checkout, and closed cleanly"
            )
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
