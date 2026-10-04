# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Local Engineering Editor application boundary (read-only Process/PFD slice).

This package separates framework-independent editor application code
(``application``) from the local-only FastAPI/Uvicorn transport (``api``). Both
depend on the DeepPlant-owned Process/PFD projection (``projection``); neither
belongs in the semantic model (ADR-0002), and neither contains domain rules.

The module also owns the editor's runtime dependency boundary (Issue #85). The
HTTP transport is the only DeepPlant code that needs FastAPI and Uvicorn, so
those two are an explicit installation extra (``deepplant[editor]``) rather than
base dependencies of the semantic Core. Importing this package stays cheap:
``require_editor_dependencies()`` is the single probe callers use before they
import :mod:`deepplant.editor.api`, and the loopback defaults live here so the
application entry point can describe the server without importing the transport.
"""

from __future__ import annotations

import importlib

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "EDITOR_EXTRA",
    "MissingEditorDependenciesError",
    "require_editor_dependencies",
]

# Loopback defaults. The editor is a single-user local application: the bind
# address is fixed to loopback and there is no supported way to expose it on
# 0.0.0.0 (Issue #79).
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765

#: Installation extra carrying the editor HTTP transport dependencies.
EDITOR_EXTRA: str = "editor"

_TRANSPORT_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
)


class MissingEditorDependenciesError(Exception):
    """Raised when the editor HTTP transport dependencies are not installed."""


def require_editor_dependencies() -> None:
    """Fail with an actionable message when FastAPI/Uvicorn are unavailable.

    Callers probe here *before* importing :mod:`deepplant.editor.api`, so an
    installation without the ``editor`` extra reports which supported
    installation provides it instead of surfacing an ``ImportError`` traceback.
    """
    missing = [
        distribution
        for module, distribution in _TRANSPORT_DEPENDENCIES
        if not _module_available(module)
    ]
    if not missing:
        return
    raise MissingEditorDependenciesError(
        f"the DeepPlant Editor needs {', '.join(missing)}, which this installation "
        f"does not include. Install the editor extra "
        f'(`pip install "deepplant[{EDITOR_EXTRA}]"`), or use the standalone '
        "DeepPlant Editor application, which already contains them."
    )


def _module_available(module: str) -> bool:
    """Return whether ``module`` can be imported in this interpreter."""
    try:
        importlib.import_module(module)
    except ImportError:
        return False
    return True
