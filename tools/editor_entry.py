# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Freeze entry point for the standalone DeepPlant Editor.

PyInstaller needs a script file to analyze. This script deliberately does nothing
except call the exact same console-script function that the installed
``deepplant-editor`` entry point uses
(:func:`deepplant.editor.launcher.main`), so the packaged application and the
installed entry point can never diverge.
"""

from __future__ import annotations

from deepplant.editor.launcher import main

if __name__ == "__main__":
    main()
