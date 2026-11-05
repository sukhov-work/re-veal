"""The pair flow's routes, spliced into server/routes.ROUTES after the shared rows and before the two fallback rows, so
a row here answers before the fallbacks' 404.

  GET /api/fixtures                         the fixture pairs the new pair job form offers (views/pair.fixture_pairs)
  GET /api/jobs/<id>/relation               the relation: the report's numbers, the bars, the strip, the frame URLs
  GET /api/jobs/<id>/relation/frame/<i>     frame i of the relation's decoded mp4 (decoded once into cache/frames/)
  GET /api/jobs/<id>/verdict                Reveal's verdict: the record's state and reason, the metrics, the stills

The verdict is the shared branch stage, so its route answers for a job of any flow. A job route loads its job first
(load_job), as the shared rows do. The page of a pair job goes through the shared POST /api/jobs/<id>/page: its gate
(views/page.py) calls views/pair.build_pair_page.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from reveal_studio.errors import StudioError
from reveal_studio.fs import Json
from reveal_studio.jobs.store import load_job
from reveal_studio.server.route import JOB, Route, _r
from reveal_studio.views.pair import fixture_pairs, relation_frames, relation_view, verdict_view

if TYPE_CHECKING:
    from reveal_studio.server.handler import Handler


def _require_pair(job: Json) -> None:
    if job.get("flow") != "pair":
        raise StudioError(f"the relation is the pair flow's stage; {job.get('id')} is a {job.get('flow')} job", 404)


def get_fixtures(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(200, fixture_pairs(h.app.settings))


def get_relation(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    _require_pair(job)
    h._send(200, relation_view(h.app.settings, d, job))


def get_relation_frame(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    _require_pair(job)
    fd = relation_frames(h.app.settings, d, job)
    if fd is None:
        raise StudioError("no relation yet: run the relation first", 404)
    h._file(fd / f"f{int(m.group(2)):04d}.jpg", cacheable=True)


def get_verdict(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._send(200, verdict_view(h.app.settings, d, job))


ROUTES: list[Route] = [
    _r("GET", r"^/api/fixtures$", get_fixtures),
    _r("GET", JOB + r"/relation$", get_relation),
    _r("GET", JOB + r"/relation/frame/(\d+)$", get_relation_frame),
    _r("GET", JOB + r"/verdict$", get_verdict),
]
