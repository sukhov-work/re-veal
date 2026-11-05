"""The director flow's hints (builder D). Merged into registry.hints.HINTS; a key here must be in no other flow's
table (the merge raises on a duplicate). A flow control takes the prefix `control.director_`."""

from __future__ import annotations

from typing import Any

HINTS: dict[str, dict[str, Any]] = {}
