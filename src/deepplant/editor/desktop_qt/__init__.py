# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Native Qt/WebEngine host for the shared Engineering Editor SPA (Issue #93).

The only DeepPlant package that imports a GUI toolkit. It exposes the same
public entry point the former single `deepplant.editor.desktop_qt` module
provided (`run_host`); the implementation is organized by capability:

- `window`: the native window, the embedded webview, and the page policy;
- `runtime`: the desktop host lifecycle and `run_host`;
- `session`: the shared self-check run state and low-level primitives;
- `self_check`: the packaged self-check harness and the empty/loaded scenarios;
- `transition`: the project-replacement (session) scenario.

It is imported lazily by `deepplant.editor.desktop`, only after
`deepplant.editor.require_desktop_dependencies` has succeeded, so the semantic
Core, the ordinary CLI, and the developer/browser host never depend on it.
"""

from __future__ import annotations

from deepplant.editor.desktop_qt.runtime import run_host

__all__ = ["run_host"]
