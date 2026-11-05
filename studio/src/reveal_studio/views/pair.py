"""The pair flow's views (builder P's module from wave 2 on): its stage tiles, its keys on the job view and its
render view. The slice of 2026-11-05 left them empty: a stage of this flow shows its base tile (its latest record's
state), the job view carries the shared keys only, and a render opens in the base view.
"""

from __future__ import annotations

from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.fs import Json
from reveal_studio.views.base import TileFn, base_render_view

TILES: dict[str, TileFn] = {}
"""The pair flow's tile function per stage name (see views/tiles_loop.py for the shape)."""
DEFAULT_FPS = 30
"""The playback rate when neither the terminal file nor the record names one: a pair's report.json keeps the
clip's fps under spec (transitions.py's default, 30)."""


def extras(settings: Settings, d: Path, job: Json) -> Json:
    """The pair flow's own keys on the job view (none yet)."""
    return {}


def render_view(settings: Settings, d: Path, job: Json, kind: str, name: str) -> Json:
    """GET /api/jobs/<id>/render/<kind>/<name> for a pair job: the base view until the flow adds its measures."""
    return base_render_view(settings, d, job, kind, name, DEFAULT_FPS)
