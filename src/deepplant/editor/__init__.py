# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Local Engineering Editor application boundary (read-only Process/PFD slice).

This package separates framework-independent editor application code
(``application``) from the local-only FastAPI/Uvicorn transport (``api``). Both
depend on the DeepPlant-owned Process/PFD projection (``projection``); neither
belongs in the semantic model (ADR-0002), and neither contains domain rules.
"""
