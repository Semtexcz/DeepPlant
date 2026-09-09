"""Verify that a built DeepPlant wheel contains runtime process-symbol resources.

The headless renderer resolves the built-in ``basic`` symbol pack through
``importlib.resources`` at runtime, so a missing asset only shows up after
installation. CI builds the wheel and runs this stdlib ``zipfile`` check so the
packaged runtime resources are protected without extracting or installing the
wheel or adding a dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile

REQUIRED_MEMBERS = {
    "deepplant/assets/symbols/process/basic/README.md",
    "deepplant/assets/symbols/process/basic/source.svg",
    "deepplant/assets/symbols/process/basic/mixing.svg",
    "deepplant/assets/symbols/process/basic/pump.svg",
    "deepplant/assets/symbols/process/basic/heat_exchanger.svg",
    "deepplant/assets/symbols/process/basic/splitting.svg",
    "deepplant/assets/symbols/process/basic/vessel.svg",
    "deepplant/assets/symbols/process/basic/sink.svg",
}


def main() -> None:
    wheels = [Path(argument) for argument in sys.argv[1:]]
    if len(wheels) != 1:
        raise SystemExit("usage: python tools/verify_wheel_contents.py dist/deepplant-*.whl")
    with ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    missing = sorted(REQUIRED_MEMBERS - names)
    if missing:
        raise SystemExit(
            "wheel is missing required process-symbol resources: " + ", ".join(missing)
        )
    print(f"verified {wheels[0]} contains {len(REQUIRED_MEMBERS)} process-symbol resources")


if __name__ == "__main__":
    main()
