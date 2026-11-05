"""What every flow's views share: the tile a stage starts from, the lazy context its tile function reads, the stale
rule over a flow's tiles, and the render view a flow without its own measures serves.

A flow's view module (views/tiles_loop.py for the loop, views/pair.py, views/director.py) holds a table
{stage name: tile function}; views/job.stage_views builds each stage's base tile, then calls the function of its
name, if the table has one. A tile function fills the tile in place: state, detail, thumb and its own keys.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.fs import Json, inside, read_json
from reveal_studio.jobs.candidates import candidate, candidates, requests_of, rounds
from reveal_studio.jobs.grades import owner_frames
from reveal_studio.jobs.plans import plans_of
from reveal_studio.jobs.records import progress_of, records
from reveal_studio.jobs.store import job_root
from reveal_studio.media.pictures import frames_dir
from reveal_studio.registry.schema import VERDICTS


@dataclass
class TileContext:
    """What the tile functions of one stage_views call read, each read from disk once and only when asked for."""

    settings: Settings
    d: Path
    job: Json
    by: dict[str, list[Json]] = field(default_factory=dict)
    """The job's records by stage name, in start order, reconciled."""
    memo: dict[str, Any] = field(default_factory=dict)
    """A flow's own reads (the loop's prep summary), kept by `once`."""

    def once(self, key: str, read: Callable[[], Any]) -> Any:
        """The value `read` returns, read on the first call for `key` only."""
        if key not in self.memo:
            self.memo[key] = read()
        return self.memo[key]

    @cached_property
    def root(self) -> Path:
        return job_root(self.settings, self.job)

    @cached_property
    def cands(self) -> list[Json]:
        return candidates(self.settings, self.d, self.job)

    @cached_property
    def full(self) -> list[Json]:
        return [c for c in self.cands if c["kind"] == "full"]

    @cached_property
    def drafts(self) -> list[Json]:
        return [c for c in self.cands if c["kind"] == "draft"]

    @cached_property
    def reqs(self) -> list[Json]:
        return requests_of(self.settings, self.d)

    @cached_property
    def rounds(self) -> list[Json]:
        return rounds(self.d)

    @cached_property
    def plans(self) -> list[Json]:
        return plans_of(self.settings, self.d)


TileFn = Callable[[TileContext, Json, Json | None], None]
"""A stage's tile function: the context, the tile (filled in place) and the stage's latest record or None."""
ExtrasFn = Callable[[Settings, Path, Json], Json]
"""A flow's extra keys on the job view (a pair's relation, a director's resolve), from the settings, folder, job."""


def base_tile(d: Path, s: Json, hist: list[Json]) -> Json:
    """The tile every stage starts from: its registry fields, and the latest record's state, wall time and reason."""
    latest = hist[-1] if hist else None
    v: Json = {
        "name": s["name"],
        "title": s["title"],
        "kind": s["kind"],
        "optional": s["optional"],
        "parent": s.get("parent"),
        "branch": bool(s.get("branch")),
        "what": s["what"],
        "backend": s.get("backend"),
        "knobs": s["knobs"],
        "state": "none",
        "detail": "",
        "wall_s": None,
        "thumb": None,
        "latest": latest["id"] if latest else None,
        "history": [
            {
                "id": r["id"],
                "state": r["state"],
                "started": r["started"],
                "wall_s": r.get("wall_s"),
                "reason": r.get("reason"),
            }
            for r in hist
        ],
        "stale": False,
        "generated": False,
        "progress": None,
        "reason": None,
    }
    if latest:
        v["state"] = latest["state"]
        v["wall_s"] = latest.get("wall_s")
        v["reason"] = latest.get("reason")
        v["unchanged_from"] = latest.get("unchanged_from")
        v["latest_knobs"] = latest.get("knobs") or {}
        if latest["state"] == "running":
            v["progress"] = progress_of(d / "stages" / latest["id"])
    return v


def skeptic_state(settings: Settings, req: Json) -> tuple[str, str]:
    """The skeptic tile's state and detail for a two-photo flow's latest request: waiting, answered, or answered with
    no verdict in the answer, which leaves every render unjudged and the page gated (critique B, minor 12: the tile
    read a green "answered" over three unjudged renders). The parenthesis keeps the chip's hint chip.answered."""
    if not req["answered"]:
        return "waiting", f"{req['name']} · {req['age_s']} s old"
    ans = read_json(settings.root / req["answer"]) if req.get("answer") else None
    n = sum(
        1
        for v in ((ans or {}).get("candidates") or {}).values()
        if isinstance(v, dict) and v.get("verdict") in VERDICTS
    )
    if n:
        return "answered", f"{req['name']} answered"
    return "answered (0 verdicts)", f"{req['name']} answered with no verdict"


def attempt_note(rec: Json) -> str:
    """The panel head's muted line when a tile says what the stage holds while its latest record did not finish: the
    attempt's state and reason, so the head never shows "done" beside a bare "cancelled by you" (critique A2, P2 4)."""
    state, reason = rec["state"], rec.get("reason") or ""
    if not reason:
        return f"last attempt {state}"
    return f"last attempt: {reason}" if reason.startswith(state) else f"last attempt {state}: {reason}"


def is_draft(rec: Json) -> bool:
    """A render record of a draft (knob draft above 0): its output goes under drafts/, never onto a page."""
    try:
        return int((rec.get("knobs") or {}).get("draft") or 0) > 0
    except (TypeError, ValueError):
        return False


def mark_stale(views: list[Json], stages: list[Json], by: dict[str, list[Json]]) -> None:
    """The stale rule: an earlier stage's latest record started after this stage's latest record. A branch (probe,
    measure, a verdict) writes into its own folder that no stage reads, so it makes no stage stale, and it goes stale
    only after the stages its `stale_after` names (the probe after a registration; a measure of a finished mp4 never).
    The page lists full renders only, so its upstream render is the latest full render's record, never a draft's
    (T98; the `draft` knob convention every flow's render follows)."""
    defs = {s["name"]: s for s in stages}
    latest_started = {name: hist[-1]["started"] for name, hist in by.items() if hist}
    full_renders = [r for r in by.get("render", []) if not is_draft(r)]
    for i, v in enumerate(views):
        if v["state"] not in ("done",) or not v["latest"]:
            continue
        mine = latest_started.get(v["name"])
        after = defs[v["name"]].get("stale_after")
        ups = (
            [u for u in views if u["name"] in after]
            if after is not None
            else [u for u in views[:i] if not defs[u["name"]].get("branch")]
        )
        for u in ups:
            up = by.get(u["name"], [{}])[-1]
            if v["name"] == "page" and u["name"] == "render":
                up = full_renders[-1] if full_renders else {}
            if u["kind"] == "script" and up.get("started", "") > (mine or "") and up.get("state") == "done":
                v["stale"] = True
                v["stale_after"] = u["name"]


def render_fps(d: Path, c: Json, records_of: list[Json], default: float) -> Any:
    """The clip's playback rate: the `fps` knob of the record that wrote the candidate, else `default` (an adopted or
    shell-made render has no record)."""
    rec = next((r for r in reversed(records_of) if r.get("out_final") == c["path"] and r.get("state") == "done"), None)
    fps = ((rec or {}).get("knobs") or {}).get("fps")
    return fps if isinstance(fps, int | float) and not isinstance(fps, bool) and fps > 0 else default


def file_url(settings: Settings, d: Path, job: Json, path: str) -> str:
    """The file route's URL of a repo-relative path inside the job's run folder or its job folder (the route tries
    the run folder first, then the job folder: a director's drafts sit in the job folder, outside run/)."""
    full = settings.root / path
    for base in (job_root(settings, job), d):
        if inside(full, base):
            return f"/api/jobs/{job['id']}/file/{full.resolve().relative_to(base.resolve())}"
    return f"/api/jobs/{job['id']}/file/{path}"


def base_render_view(settings: Settings, d: Path, job: Json, kind: str, name: str, default_fps: float) -> Json:
    """A render as the viewer reads it without a flow's own measures: the candidate, its decoded frames, the mp4 and
    frame URLs, the playback rate (the terminal file's fps, else the record's fps knob, else `default_fps`) and the
    marked frames. A flow's render view adds its series to this."""
    c = candidate(settings, d, job, kind, name)
    fps = c.get("fps") or render_fps(d, c, records(d), default_fps)
    fd = frames_dir(d, c) if (c["dir"] / c["mp4"]).exists() else None
    own = {k: v for k, v in c.items() if k != "dir"}
    own["frames_tags"] = []
    own["frames_available"] = len(list(fd.glob("f*.jpg"))) if fd else 0
    own["frame_url"] = f"/api/jobs/{job['id']}/render/{kind}/{name}/frame/"
    own["mp4_url"] = file_url(settings, d, job, f"{c['path']}/{c['mp4']}")
    own["fps"] = fps
    own["owner_frames"] = [o for o in owner_frames(d) if o and o.get("name") == name and o.get("kind") == kind]
    return own
