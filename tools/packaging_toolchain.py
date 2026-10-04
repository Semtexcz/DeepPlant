# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Read the external native packaging-toolchain contract (Issue #85 review fix).

Python build dependencies are locked in ``uv.lock``. The native tools that turn
the frozen application into a user-facing artifact are not Python packages, so
they cannot live in that lock. Their exact version, immutable upstream URL, and
expected SHA-256 live in one reviewed file, ``packaging/toolchain.toml``; this
module is the only code that reads it, so no workflow repeats a version or
digest literal.

Commands::

    export   append the pinned values to ``$GITHUB_ENV`` and echo them
    show     print the pinned toolchain for humans

The ``version`` recorded for each downloaded artifact must equal the release tag
segment of its ``url``, and that tag may not be a mutable locator
(``continuous``, ``latest``, ``master``, ``main``); both rules fail closed before
any download.

Practice, ownership, and the ``uv.lock`` boundary are documented in
``docs/dev/workflow/packaging.md``.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN_FILE = REPO_ROOT / "packaging" / "toolchain.toml"

#: Environment variable names CI consumes. They are declared here, next to the
#: loader, so the workflow and the contract cannot drift apart silently.
ENV_APPIMAGETOOL_VERSION = "APPIMAGETOOL_VERSION"
ENV_APPIMAGETOOL_URL = "APPIMAGETOOL_URL"
ENV_APPIMAGETOOL_SHA256 = "APPIMAGETOOL_SHA256"
ENV_APPIMAGE_RUNTIME_VERSION = "APPIMAGE_RUNTIME_VERSION"
ENV_APPIMAGE_RUNTIME_URL = "APPIMAGE_RUNTIME_URL"
ENV_APPIMAGE_RUNTIME_SHA256 = "APPIMAGE_RUNTIME_SHA256"
ENV_INNO_SETUP_VERSION = "INNO_SETUP_VERSION"

_RELEASE_URL = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/releases/download/(?P<tag>[^/]+)/[^/]+$"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

#: Release locators that upstream can republish at any time, so they can never
#: anchor a reproducible packaging input (the toolchain fix this module exists for).
_MUTABLE_LOCATORS = frozenset({"continuous", "latest", "master", "main", "head", "trunk"})


class ToolchainError(RuntimeError):
    """Raised when the toolchain contract is missing, malformed, or mutable."""


@dataclass(frozen=True)
class Download:
    """One pinned, integrity-checked upstream artifact."""

    version: str
    architecture: str
    url: str
    sha256: str
    licence: str


@dataclass(frozen=True)
class InnoSetup:
    """The pinned Windows installer compiler."""

    chocolatey_package: str
    version: str
    licence: str


@dataclass(frozen=True)
class Toolchain:
    """The reviewed external native packaging toolchain."""

    appimagetool: Download
    appimage_runtime: Download
    inno_setup: InnoSetup


def _require_table(document: Mapping[str, object], name: str) -> Mapping[str, object]:
    """Return ``[name]`` from the parsed contract, or fail closed."""
    table = document.get(name)
    if not isinstance(table, Mapping):
        raise ToolchainError(f"packaging/toolchain.toml has no [{name}] table")
    return cast("Mapping[str, object]", table)


def _require_text(table: Mapping[str, object], section: str, key: str) -> str:
    """Return a required non-empty string field, or fail closed."""
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise ToolchainError(f"[{section}] is missing a non-empty {key!r}")
    return value


def _require_download(document: Mapping[str, object], section: str) -> Download:
    """Validate one immutable, checksummed download artifact."""
    table = _require_table(document, section)
    version = _require_text(table, section, "version")
    url = _require_text(table, section, "url")
    sha256 = _require_text(table, section, "sha256")
    match = _RELEASE_URL.match(url)
    if match is None:
        raise ToolchainError(
            f"[{section}] url must be an immutable GitHub release asset url, got {url!r}"
        )
    tag = match.group("tag")
    if tag.lower() in _MUTABLE_LOCATORS:
        raise ToolchainError(
            f"[{section}] release tag {tag!r} is a mutable locator, which cannot pin a build input"
        )
    if tag != version:
        raise ToolchainError(f"[{section}] url release tag {tag!r} must equal version {version!r}")
    if _SHA256.match(sha256) is None:
        raise ToolchainError(f"[{section}] sha256 must be 64 lowercase hex characters")
    return Download(
        version=version,
        architecture=_require_text(table, section, "architecture"),
        url=url,
        sha256=sha256,
        licence=_require_text(table, section, "licence"),
    )


def load_toolchain(path: Path | None = None) -> Toolchain:
    """Load and validate ``packaging/toolchain.toml``."""
    source = TOOLCHAIN_FILE if path is None else path
    if not source.is_file():
        raise ToolchainError(f"missing toolchain contract at {source}")
    document: dict[str, object] = tomllib.loads(source.read_text(encoding="utf-8"))
    inno = _require_table(document, "inno_setup")
    return Toolchain(
        appimagetool=_require_download(document, "appimagetool"),
        appimage_runtime=_require_download(document, "appimage_runtime"),
        inno_setup=InnoSetup(
            chocolatey_package=_require_text(inno, "inno_setup", "chocolatey_package"),
            version=_require_text(inno, "inno_setup", "version"),
            licence=_require_text(inno, "inno_setup", "licence"),
        ),
    )


def environment(toolchain: Toolchain) -> dict[str, str]:
    """Return the CI-facing environment variables for ``toolchain``."""
    return {
        ENV_APPIMAGETOOL_VERSION: toolchain.appimagetool.version,
        ENV_APPIMAGETOOL_URL: toolchain.appimagetool.url,
        ENV_APPIMAGETOOL_SHA256: toolchain.appimagetool.sha256,
        ENV_APPIMAGE_RUNTIME_VERSION: toolchain.appimage_runtime.version,
        ENV_APPIMAGE_RUNTIME_URL: toolchain.appimage_runtime.url,
        ENV_APPIMAGE_RUNTIME_SHA256: toolchain.appimage_runtime.sha256,
        ENV_INNO_SETUP_VERSION: toolchain.inno_setup.version,
    }


def write_github_env(values: Mapping[str, str]) -> Path | None:
    """Append ``values`` to ``$GITHUB_ENV`` when running in GitHub Actions.

    Writing the file directly (instead of shell redirection) keeps the Windows
    and Linux jobs identical and avoids PowerShell's UTF-16 redirection.
    """
    target = os.environ.get("GITHUB_ENV")
    if not target:
        return None
    path = Path(target)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")
    return path


def _print_download(label: str, download: Download) -> None:
    print(f"{label}: {download.version} ({download.architecture}, {download.licence})")
    print(f"  url:    {download.url}")
    print(f"  sha256: {download.sha256}")


def _print_toolchain(toolchain: Toolchain) -> None:
    _print_download("appimagetool", toolchain.appimagetool)
    _print_download("AppImage runtime", toolchain.appimage_runtime)
    inno = toolchain.inno_setup
    print(f"Inno Setup: {inno.version} (Chocolatey package {inno.chocolatey_package})")


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``export`` and ``show`` commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["export", "show"])
    parser.add_argument(
        "--file",
        type=Path,
        default=TOOLCHAIN_FILE,
        help="toolchain contract to read (default: packaging/toolchain.toml)",
    )
    args = parser.parse_args(argv)
    try:
        toolchain = load_toolchain(args.file)
    except ToolchainError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.command == "show":
        _print_toolchain(toolchain)
        return 0
    values = environment(toolchain)
    target = write_github_env(values)
    for key, value in values.items():
        print(f"{key}={value}")
    if target is None:
        print("no $GITHUB_ENV set; values printed only", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
