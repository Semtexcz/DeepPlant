# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Local Engineering Editor application boundary (read-only Process/PFD slice).

This package holds the DeepPlant-owned consumer/application code for the
Engineering Editor: the Process/PFD projection (``projection``) and the
local-only transport that serves it to the browser (``app``). It never lives in
the semantic model (ADR-0002) and contains no domain rules.
"""
