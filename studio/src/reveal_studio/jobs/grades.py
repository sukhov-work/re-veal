"""What the owner and the session write into a job: request files, his grade per round (his text, or the picks of a
two-photo flow with his text), the frames he marks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, now_iso, read_json, rel, stamp, write_json
from reveal_studio.jobs.candidates import candidate, candidates, rounds

REQUEST_KINDS = ("skeptic", "plan", "reading", "director", "keyframe")
# The picks shape of the director rounds (benchmarks/runs/2026-10-17/director_r11/director_picks_11.json), checked as
# the workbench checked it (scripts/research/director_ui.py:688-707); the pair and director flows grade in it.
PICK_TOP = frozenset({"date", "page", "best", "clips"})
PICK_CLIP = frozenset({"acceptable", "note", "props"})
PICK_CLIP_OPT = frozenset({"frames", "render", "draft"})
PICK_PROPS = frozenset({"one_picture", "transforms", "not_invented"})


def owner_frames(d: Path) -> list[Any]:
    """The frames he marked, as saved under owner_frames/ (an unreadable file reads as None)."""
    return [read_json(f) for f in sorted((d / "owner_frames").glob("*.json"))]


def write_request(settings: Settings, d: Path, job: Json, kind: str, body: Json) -> Json:
    """requests/<kind>_<stamp>.json with the candidates' md5s, his brief and marks, and the answer's expected shape."""
    if kind not in REQUEST_KINDS:
        raise StudioError("a request kind is skeptic, plan, reading, director or keyframe", 400)
    names = body.get("candidates") or [c["name"] for c in candidates(settings, d, job) if c["kind"] == "full"]
    cands = candidates(settings, d, job)
    chosen = []
    for n in names:
        c = next((c for c in cands if c["name"] == n and c["kind"] == "full"), None)
        if not c:
            raise StudioError(f"no full render {n}", 404)
        chosen.append(
            {
                "name": n,
                "path": c["path"],
                "md5_mp4": c["md5_mp4"],
                "frames": c["frames"],
                "canvas": c["canvas"],
                "plan_sha256": c.get("plan_sha256"),
            }
        )
    (d / "requests").mkdir(exist_ok=True)
    fname = f"{kind}_{stamp()}.json"
    req = {
        "kind": kind,
        "at": now_iso(),
        "job": job["id"],
        "job_dir": rel(d, settings.root),
        "root": job["root"],
        "seq": job["seq"],
        "brief": str(body.get("brief", "")),
        "candidates": chosen,
        "crops": body.get("crops") or [],
        "owner_frames": owner_frames(d),
        "answer": {
            "file": f"answers/{fname}",
            "shape": {
                "at": "<iso>",
                "candidates": {
                    "<name>": {
                        "verdict": "READY | READY WITH A NOTE | NOT READY",
                        "judged_md5": "<the md5_mp4 judged>",
                        "note": "<one line>",
                    }
                },
                "report": f"answers/{fname[:-5]}.md (the crops beside it)",
            },
        },
    }
    write_json(d / "requests" / fname, req)
    log(f"{d.name}: request {fname} ({len(chosen)} candidates)")
    return {"file": rel(d / "requests" / fname, settings.root), "name": fname}


def check_picks(obj: Any) -> None:
    """The picks object as the workbench took it: exactly date, page, best and clips; best and clips objects; per clip
    acceptable, note and props, with frames, render and draft allowed; props exactly the three boxes. 400 otherwise."""
    if not isinstance(obj, dict) or set(obj) != PICK_TOP:
        keys = sorted(obj) if isinstance(obj, dict) else type(obj).__name__
        raise StudioError(f"picks keys must be exactly {sorted(PICK_TOP)}, not {keys}", 400)
    if not isinstance(obj["best"], dict) or not isinstance(obj["clips"], dict):
        raise StudioError("picks: best and clips must be objects", 400)
    for tag, c in obj["clips"].items():
        if not isinstance(c, dict) or not (PICK_CLIP <= set(c) <= PICK_CLIP | PICK_CLIP_OPT):
            raise StudioError(f"picks: clip {tag}: keys {sorted(c) if isinstance(c, dict) else c!r}", 400)
        if not isinstance(c["props"], dict) or set(c["props"]) != PICK_PROPS:
            raise StudioError(f"picks: clip {tag}: props must be exactly {sorted(PICK_PROPS)}", 400)


def save_picks(d: Path, picks: Any) -> Path:
    """picks/director_picks_<stamp>.json after the shape check; a second save in the same second gets _2, _3."""
    check_picks(picks)
    base = d / "picks" / f"director_picks_{stamp()}"
    p, k = base.with_suffix(".json"), 1
    while p.exists():
        k += 1
        p = base.with_name(f"{base.name}_{k}.json")
    write_json(p, picks)
    return p


def save_grade(d: Path, body: Json) -> Json:
    """His words verbatim for a round (the latest by default) with the page md5, or 'ungraded by his word'. With
    `picks` (a two-photo flow's grade) the picks file is written first and the round's grade is {at, page_md5, picks,
    text}: the file's path in the job folder and his words, which may be empty since the picks carry his notes."""
    rs = rounds(d)
    if not rs:
        raise StudioError("no round yet: build the page first", 409)
    try:
        n = int(body.get("round") or rs[-1]["n"])
    except (TypeError, ValueError):
        raise StudioError("round is a number", 400) from None
    r = next((r for r in rs if r["n"] == n), None)
    if not r:
        raise StudioError(f"no round {n}", 404)
    if body.get("ungraded_by_his_word"):
        r["ungraded_by_his_word"] = {"at": now_iso(), "words": str(body.get("words", ""))}
    elif "picks" in body:
        p = save_picks(d, body["picks"])
        text = str(body.get("text") or "").strip()
        r["grade"] = {"at": now_iso(), "page_md5": r["page_md5"], "picks": str(p.relative_to(d)), "text": text}
    else:
        text = str(body.get("text", "")).strip()
        if not text:
            raise StudioError("the grade text is empty: his words, verbatim", 400)
        r["grade"] = {"text": text, "at": now_iso(), "page_md5": r["page_md5"]}
    write_json(d / "rounds" / str(n) / "round.json", r)
    log(f"{d.name}: round {n} {'graded' if r.get('grade') else 'marked ungraded by his word'}")
    return r


def mark_frame(settings: Settings, d: Path, job: Json, body: Json) -> Json:
    """owner_frames/<kind>_<name>_f<i>.json: the frame index, the render's md5 and his note."""
    kind: Any = body.get("kind", "full")
    name: Any = body.get("name")
    i: Any = body.get("frame")
    c = candidate(settings, d, job, kind, name)
    try:
        i = int(i)
    except (TypeError, ValueError):
        raise StudioError("frame is a number", 400) from None
    if i < 0 or (c.get("frames") and i >= int(c["frames"])):
        raise StudioError(f"frame {i} is outside 0..{int(c['frames']) - 1}", 400)
    (d / "owner_frames").mkdir(exist_ok=True)
    f = d / "owner_frames" / f"{kind}_{name}_f{i:04d}.json"
    obj = {
        "kind": kind,
        "name": name,
        "frame": i,
        "md5_mp4": c["md5_mp4"],
        "note": str(body.get("note", "")),
        "at": now_iso(),
    }
    write_json(f, obj)
    return obj
