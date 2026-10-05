# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Freeze entry point for the standalone DeepPlant Editor.

PyInstaller needs a script file to analyze. This script deliberately does nothing
except call the exact same console-script function that the installed
``deepplant-editor`` entry point uses
(:func:`deepplant.editor.desktop.main`), so the packaged application and the
installed entry point can never diverge.

Since Issue #93 that entry point is the native desktop host (a Qt window with an
embedded webview), not the browser-opening launcher it was for the distribution
foundation.
"""

from __future__ import annotations

from deepplant.editor.desktop import main

if __name__ == "__main__":
    main()
