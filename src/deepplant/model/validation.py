# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Shared, genuinely reusable field and validation primitives.

These are the only validation mechanics every semantic model layer shares:
the non-empty semantic string constraint and the duplicate-id detector. Each
model keeps its own uniqueness rule, namespace, and message, so duplicate
detection stays a local domain statement rather than a generic framework.
"""

from collections.abc import Iterable
from typing import Annotated

from pydantic import StringConstraints

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def find_duplicate_ids(ids: Iterable[str]) -> list[str]:
    """Return every id that occurs more than once, once each and sorted.

    Private helper only: each model keeps its own uniqueness rule, message, and
    namespace, so duplicate-id validation stays a local domain statement.
    """
    seen: set[str] = set()
    duplicates: set[str] = set()

    for id_ in ids:
        if id_ in seen:
            duplicates.add(id_)
        else:
            seen.add(id_)

    return sorted(duplicates)
