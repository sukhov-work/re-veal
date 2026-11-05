"""The director flow's routes (builder D), spliced into server/routes.ROUTES after the shared rows and before the two
fallback rows, so a row here answers before the fallbacks' 404.

- GET /api/pairs: the fixture pairs a director plan names, with their plans and each photo's layer and matte status.
- GET /api/plans/director/<stem>: a frozen director plan as the plan panel reads it (views/director.plan_view).
- GET /api/jobs/<id>/director/plans/<name>: a plan saved in a director job, in the same shape.
- GET /api/jobs/<id>/overlay/<A|B>/<kind>.png: an overlay of the layer table, kinds base, elements, disparity and
  matte_<id>, cached under the job's cache/overlays/ (media/overlays.py).
- GET /api/jobs/<id>/thumb/canvas/<A|B>: the latest resolve's canvas as a thumbnail, for the import tile.

A job route loads its job first and refuses (400) a job of another flow.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from reveal_studio.errors import StudioError
from reveal_studio.fs import Json
from reveal_studio.jobs.store import load_job
from reveal_studio.media.overlays import overlay_png
from reveal_studio.media.pictures import thumb_path
from reveal_studio.server.route import JOB, Route, _r
from reveal_studio.views.director import pairs_view, plan_view

if TYPE_CHECKING:
    from reveal_studio.server.handler import Handler


def _director_job(h: Handler, jid: str) -> tuple[Path, Json]:
    d, job = load_job(h.app.settings, jid)
    if job.get("flow") != "director":
        raise StudioError(f"{jid} is a {job.get('flow')} job; this route serves director jobs", 400)
    return d, job


def get_pairs(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(200, pairs_view(h.app.settings))


def get_director_plan(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(200, plan_view(h.app.settings, None, f"frozen:{m.group(1)}"))


def get_job_director_plan(h: Handler, m: re.Match[str], body: Json) -> None:
    d, _job = _director_job(h, m.group(1))
    h._send(200, plan_view(h.app.settings, d, f"job:{m.group(2)}"))


def get_overlay(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = _director_job(h, m.group(1))
    h._file(overlay_png(h.app.settings, d, job, m.group(2), m.group(3)), cacheable=True)


def get_canvas_thumb(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = _director_job(h, m.group(1))
    h._file(thumb_path(h.app.settings, d, job, "canvas", m.group(2)), cacheable=True)


ROUTES: list[Route] = [
    _r("GET", r"^/api/pairs$", get_pairs),
    _r("GET", r"^/api/plans/director/([^/]+)$", get_director_plan),
    _r("GET", JOB + r"/director/plans/([^/]+)$", get_job_director_plan),
    _r("GET", JOB + r"/overlay/(A|B)/([^/]+)\.png$", get_overlay),
    _r("GET", JOB + r"/thumb/canvas/(A|B)$", get_canvas_thumb),
]
