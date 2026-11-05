"""The route table: the studio's URL grammar as one list of (method, compiled regex, function, name) rows.

The first row whose method and regex match the path answers. Every job route loads the job first, so a bad id is
refused (400) or unknown (404) before the route's own checks; the two fallback rows load the job and then answer
404 "no such route", as the research script did. `GET /static/<path>` serves the page's assets from `web/`.

CORE holds the 26 rows every flow shares, the two fallbacks among them. ROUTES is what `match` walks: the shared rows,
then each flow's list (server/routes_pair.py, server/routes_director.py), then the two fallbacks, so a flow's row
answers before a fallback. `match` filters by method first, so the GET fallback's place among the POST rows is moot.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, inside, read_json
from reveal_studio.jobs.candidates import candidate
from reveal_studio.jobs.grades import mark_frame, save_grade, write_request
from reveal_studio.jobs.plans import resolve_plan, save_plan
from reveal_studio.jobs.records import record_dir
from reveal_studio.jobs.store import create_job, job_dirs, load_job
from reveal_studio.media.pictures import frames_dir, thumb_path
from reveal_studio.registry.flows import stage_def
from reveal_studio.server import routes_director, routes_pair
from reveal_studio.server.route import JOB, Route, RouteFn, _r
from reveal_studio.views.job import job_row, job_view, record_view
from reveal_studio.views.models import models_view, open_requests, registry_view
from reveal_studio.views.page import build_page
from reveal_studio.views.render import render_view

if TYPE_CHECKING:
    from reveal_studio.server.handler import Handler

__all__ = ["CORE", "FALLBACKS", "ROUTES", "WEB_DIR", "Route", "RouteFn", "dispatch", "match"]

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
"""The page's assets: index.html, css/, js/ (package data, served under /static/)."""
HTML = "text/html; charset=utf-8"


# ------------------------------------------------------------------ GET


def get_page(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(200, (WEB_DIR / "index.html").read_text(), HTML)


def get_favicon(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(204, b"", "image/x-icon")


def get_static(h: Handler, m: re.Match[str], body: Json) -> None:
    p = WEB_DIR / m.group(1)
    if not inside(p, WEB_DIR) or not p.is_file():
        raise StudioError("no such file", 404)
    h._file(p, static=True)


def get_registry(h: Handler, m: re.Match[str], body: Json) -> None:
    app = h.app
    h._send(200, registry_view(app.settings, app.flags, app.flows))


def get_jobs(h: Handler, m: re.Match[str], body: Json) -> None:
    s = h.app.settings
    h._send(200, [r for r in (job_row(s, d, h.app.runner) for d in job_dirs(s)) if r])


def get_requests(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(200, open_requests(h.app.settings))


def get_models(h: Handler, m: re.Match[str], body: Json) -> None:
    h._send(200, models_view(h.app.settings))


def get_frozen_plan(h: Handler, m: re.Match[str], body: Json) -> None:
    p = resolve_plan(h.app.settings, None, f"frozen:{m.group(1)}")
    h._send(200, read_json(p))


def get_job(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._send(200, job_view(h.app.runner, d, job))


def get_record(h: Handler, m: re.Match[str], body: Json) -> None:
    d, _job = load_job(h.app.settings, m.group(1))
    rd = record_dir(d, m.group(2))
    h._send(200, record_view(h.app.runner, d, read_json(rd / "stage.json")))


def get_file(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._file(h._safe_file(d, job, m.group(2)))


def get_thumb(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._file(thumb_path(h.app.settings, d, job, m.group(2), m.group(3)), cacheable=True)


def get_thumb_render(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._file(thumb_path(h.app.settings, d, job, "render", m.group(2), m.group(3)), cacheable=True)


def get_render(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._send(200, render_view(h.app.settings, d, job, m.group(2), m.group(3)))


def get_frame(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    c = candidate(h.app.settings, d, job, m.group(2), m.group(3))
    fd = frames_dir(d, c)
    h._file(fd / f"f{int(m.group(4)):04d}.jpg", cacheable=True)


def get_job_plan(h: Handler, m: re.Match[str], body: Json) -> None:
    d, _job = load_job(h.app.settings, m.group(1))
    h._send(200, read_json(resolve_plan(h.app.settings, d, f"job:{m.group(2)}")))


def job_route_unknown(h: Handler, m: re.Match[str], body: Json) -> None:
    load_job(h.app.settings, m.group(1))
    h._err(404, "no such route")


# ------------------------------------------------------------------ POST


def post_job(h: Handler, m: re.Match[str], body: Json) -> None:
    job = create_job(
        h.app.settings,
        body.get("flow", "loop"),
        folder=body.get("folder"),
        adopt=body.get("adopt"),
        seq=body.get("seq"),
        fixture=body.get("fixture"),
        a=body.get("a"),
        b=body.get("b"),
        pair=body.get("pair"),
    )
    h._send(201, {"id": job["id"], "job": job})


def post_run(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    stage = stage_def(job["flow"], m.group(2))
    if stage["name"] == "page":
        raise StudioError(
            "the page runs through POST /api/jobs/<id>/page (the review gate), not through the stage runner", 409
        )
    rec = h.app.runner.start_stage(d, job, stage, body.get("knobs") or {})
    h._send(202, {"record": rec["id"], "state": rec["state"], "argv": rec["argv"], "warnings": rec.get("warnings", [])})


def post_cancel(h: Handler, m: re.Match[str], body: Json) -> None:
    d, _job = load_job(h.app.settings, m.group(1))
    h._send(200, h.app.runner.cancel(d, m.group(2)))


def post_plan(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._send(
        201,
        save_plan(h.app.settings, d, job, body.get("name"), body.get("plan"), body.get("from"), body.get("words", "")),
    )


def post_request(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._send(201, write_request(h.app.settings, d, job, m.group(2), body))


def post_page(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    rec = build_page(h.app.runner, d, job, body)
    h._send(202, {"record": rec["id"], "state": rec["state"], "override": rec["knobs"].get("override")})


def post_picks(h: Handler, m: re.Match[str], body: Json) -> None:
    d, _job = load_job(h.app.settings, m.group(1))
    h._send(200, save_grade(d, body))


def post_mark(h: Handler, m: re.Match[str], body: Json) -> None:
    d, job = load_job(h.app.settings, m.group(1))
    h._send(201, mark_frame(h.app.settings, d, job, body))


CORE: list[Route] = [
    _r("GET", r"^/$", get_page),
    _r("GET", r"^/favicon\.ico$", get_favicon),
    _r("GET", r"^/static/(.+)$", get_static),
    _r("GET", r"^/api/registry$", get_registry),
    _r("GET", r"^/api/jobs$", get_jobs),
    _r("GET", r"^/api/requests$", get_requests),
    _r("GET", r"^/api/models$", get_models),
    _r("GET", r"^/api/plans/frozen/([^/]+)$", get_frozen_plan),
    _r("GET", JOB + r"$", get_job),
    _r("GET", JOB + r"/stages/([^/]+)$", get_record),
    _r("GET", JOB + r"/file/(.+)$", get_file),
    _r("GET", JOB + r"/thumb/(still|raw)/(\d+)$", get_thumb),
    _r("GET", JOB + r"/thumb/render/(full|draft)/([^/]+)$", get_thumb_render),
    _r("GET", JOB + r"/render/(full|draft)/([^/]+)$", get_render),
    _r("GET", JOB + r"/render/(full|draft)/([^/]+)/frame/(\d+)$", get_frame),
    _r("GET", JOB + r"/plans/([^/]+)$", get_job_plan),
    _r("GET", JOB + r"(/.*)?$", job_route_unknown),
    _r("POST", r"^/api/jobs$", post_job),
    _r("POST", JOB + r"/stages/([^/]+)/run$", post_run),
    _r("POST", JOB + r"/stages/([^/]+)/cancel$", post_cancel),
    _r("POST", JOB + r"/plans$", post_plan),
    _r("POST", JOB + r"/requests/([a-z]+)$", post_request),
    _r("POST", JOB + r"/page$", post_page),
    _r("POST", JOB + r"/picks$", post_picks),
    _r("POST", JOB + r"/frames/mark$", post_mark),
    _r("POST", JOB + r"(/.*)$", job_route_unknown),
]
FALLBACKS: list[Route] = [r for r in CORE if r.fn is job_route_unknown]
"""The GET and the POST fallback of a job's routes: a 404 after the job is loaded."""
ROUTES: list[Route] = [r for r in CORE if r not in FALLBACKS] + routes_pair.ROUTES + routes_director.ROUTES + FALLBACKS


def match(method: str, path: str) -> tuple[Route, re.Match[str]] | None:
    """The first route of `method` whose regex matches `path` (HEAD is served as GET)."""
    for r in ROUTES:
        if r.method == method:
            m = r.pattern.match(path)
            if m:
                return r, m
    return None


def dispatch(h: Handler, method: str, path: str, body: Json) -> None:
    found = match(method, path)
    if found is None:
        h._err(404, "no such route")
        return
    route, m = found
    route.fn(h, m, body)
