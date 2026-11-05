"""One render as the viewer reads it: the measures, every frame's tag (photo, blend, generated with its t, snap)."""

from __future__ import annotations

from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.fs import Json, read_json
from reveal_studio.jobs.candidates import candidate
from reveal_studio.jobs.grades import owner_frames
from reveal_studio.media.pictures import frames_dir
from reveal_studio.views.measures import frame_kinds, latest_stability, measure_runs, stalls_and_jumps


def frame_tag(generated: str) -> str:
    """The strip's word for a frame from frames.json's `generated` string."""
    if generated.startswith("none (photo)"):
        return "photo"
    if generated.startswith("none (blend + motion blur)"):
        return "snap"
    if generated.startswith("none (blend"):
        return "blend"
    if generated.startswith("none (rewind"):
        return "rewind"
    if generated.startswith("none"):
        return generated[6:-1] if generated.endswith(")") else generated[5:]
    return "generated"


def render_view(settings: Settings, d: Path, job: Json, kind: str, name: str) -> Json:
    """GET /api/jobs/<id>/render/<kind>/<name>: the candidate, its measure.json, frame tags, plan and the marks."""
    c = candidate(settings, d, job, kind, name)
    m = read_json(c["dir"] / "measure.json") or {}
    rows = read_json(c["dir"] / "frames.json") or []
    plan = read_json(c["dir"] / "plan.json") or {}
    tags = []
    for i, r in enumerate(rows):
        g = r.get("generated", "")
        tags.append(
            {
                "i": i,
                "tag": frame_tag(g),
                "t": r.get("t"),
                "key": r.get("key"),
                "step": r.get("step"),
                "from": r.get("from"),
                "to": r.get("to"),
                "method": r.get("method"),
                "dexp": r.get("dexp", r.get("dexp_rest")),
                "generated": not g.startswith("none"),
            }
        )
    fd = frames_dir(d, c) if (c["dir"] / "loop.mp4").exists() else None
    nf = len(list(fd.glob("f*.jpg"))) if fd else 0
    own = {k: v for k, v in c.items() if k != "dir"}
    own["measure"] = m
    own["frames_tags"] = tags
    own["frames_available"] = nf
    own["plan"] = plan
    own["frame_url"] = f"/api/jobs/{job['id']}/render/{kind}/{name}/frame/"
    sub = Path(c["path"]).relative_to(job["root"]) if c["path"].startswith(job["root"]) else c["path"]
    own["mp4_url"] = f"/api/jobs/{job['id']}/file/{sub}/loop.mp4"
    own["owner_frames"] = [o for o in owner_frames(d) if o and o.get("name") == name and o.get("kind") == kind]
    kinds = frame_kinds(rows)
    own["frame_kinds"] = kinds
    own["stalls_and_jumps"] = stalls_and_jumps(list(m.get("steps") or []), kinds)
    runs = measure_runs(settings, d, c)
    own["measures"] = [{k: v for k, v in r.items() if k != "measure"} for r in runs]
    own["stability"] = latest_stability(runs)
    return own
