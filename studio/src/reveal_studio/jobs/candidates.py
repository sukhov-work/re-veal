"""What a job holds, read from disk on every call: its renders (candidates), the verdicts, rounds and requests.

The loop's renders are read by loop_candidates (measure.json); another flow's by spec_candidates, from the spec its
registry entry holds (registry/pair.py). Every candidate carries `dir` (dropped before it reaches the page), `mp4`
(the clip's file name in the folder) and `md5_mp4`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, md5_file, read_json, rel
from reveal_studio.jobs.records import records
from reveal_studio.jobs.store import job_root
from reveal_studio.registry.flows import ALL_FLOWS
from reveal_studio.registry.schema import NAME_RE, VERDICTS


def candidates(settings: Settings, d: Path, job: Json) -> list[Json]:
    """Every render of the job: the loop's by its own reader, another flow's by its registry entry's spec."""
    spec = (ALL_FLOWS.get(job.get("flow") or "") or {}).get("candidates")
    if spec is None:
        return loop_candidates(settings, d, job)
    return spec_candidates(settings, d, job, spec)


def loop_candidates(settings: Settings, d: Path, job: Json) -> list[Json]:
    """Every render of the sequence: the full ones under <root>/<seq>/, the drafts under <root>/drafts/<seq>/ or
    <root>/drafts/. A `.part` folder is a render still running and is skipped. Each candidate carries `dir`."""
    root, seq = job_root(settings, job), job["seq"]
    verd = verdicts(d)
    out = []
    pairs = [(root / seq, "full"), (root / "drafts" / seq, "draft"), (root / "drafts", "draft")]
    seen = set()
    for base, kind in pairs:
        if not base.is_dir():
            continue
        for v in sorted(base.iterdir()):
            if not v.is_dir() or v.name.endswith(".part") or v in seen:  # a .part folder is a render still running
                continue
            m = read_json(v / "measure.json")
            if not m:
                continue
            seen.add(v)
            plan = read_json(v / "plan.json", {}) or {}
            vd = verd.get(v.name) if kind == "full" else None
            c: Json = {
                "name": v.name,
                "kind": kind,
                "dir": v,
                "path": rel(v, settings.root),
                "mp4": "loop.mp4",
                "title": plan.get("title", ""),
                "gag": plan.get("gag", ""),
                "md5_mp4": m.get("md5_mp4"),
                "frames": m.get("frames"),
                "seconds": m.get("seconds"),
                "canvas": m.get("canvas"),
                "draft": m.get("draft", 0),
                "step_mean": m.get("step_mean"),
                "step_max": m.get("step_max"),
                "step_max_at": m.get("step_max_at"),
                "seam_step": m.get("seam_step"),
                "generated_frames": m.get("generated_frames"),
                "generated_share": m.get("generated_share"),
                "dexp_max": m.get("dexp_max"),
                "render_s": m.get("render_s"),
                "faces_keyframes": m.get("faces_keyframes"),
                "plan_sha256": m.get("plan_sha256"),
                "script_md5": m.get("script_md5"),
                "rife_version": m.get("rife_version"),
                "has_frames": (v / "frames").is_dir(),
                "mtime": dt.datetime.fromtimestamp((v / "measure.json").stat().st_mtime).isoformat(timespec="seconds"),
                "verdict": vd,
                "unjudged": kind == "full" and (not vd or vd.get("judged_md5") != m.get("md5_mp4")),
            }
            if vd and vd.get("judged_md5") != m.get("md5_mp4"):
                c["unjudged_reason"] = "the render changed after the verdict (judged md5 differs)"
            elif not vd and kind == "full":
                c["unjudged_reason"] = "no skeptic verdict for this candidate"
                before = sorted(q.name for q in (root / "agents").glob("skeptic*.md")) if job.get("adopted") else []
                if before:
                    c["judged_before_studio"] = before
                    c["unjudged_reason"] += f" in the studio (judged before it: {', '.join(before)})"
            out.append(c)
    return out


def cached_md5(d: Path, f: Path) -> str | None:
    """The md5 of `f`, hashed once per size and mtime and kept under the job's cache/md5/ (derived; safe to delete)."""
    if not f.is_file():
        return None
    st = f.stat()
    key = hashlib.sha256(str(f.resolve()).encode()).hexdigest()[:16]
    memo = d / "cache" / "md5" / f"{key}_{st.st_size}_{st.st_mtime_ns}"
    if memo.is_file():
        return memo.read_text().strip()
    v = md5_file(f)
    memo.parent.mkdir(parents=True, exist_ok=True)
    tmp = memo.with_name(memo.name + f".{os.getpid()}.tmp")
    tmp.write_text(v)
    os.replace(tmp, memo)
    return v


def _num(t: Json, key: str, alt: str | None = None) -> Any:
    """The terminal file's value: its own key, else the key under `spec` (transitions.py's report keeps seconds and
    fps there), else `alt` (the report's n_frames for frames)."""
    if key in t:
        return t[key]
    spec = t.get("spec")
    if isinstance(spec, dict) and key in spec:
        return spec[key]
    return t.get(alt) if alt else None


def spec_candidates(settings: Settings, d: Path, job: Json, spec: Json) -> list[Json]:
    """Every render of a flow read by its spec: the children of the `full` and `draft` folders ({root} the run
    folder, {job} the job folder, {seq} the job's seq) that hold the `terminal` file; a `.part` folder is skipped. The
    mp4's md5 is the done record's output (the record whose out_final is the folder), else hashed and cached; the
    record's `record_knobs` and the terminal file's `fields` ride on the candidate."""
    root, seq = job_root(settings, job), job["seq"]
    verd = verdicts(d)
    made = {r["out_final"]: r for r in records(d) if r.get("state") == "done" and r.get("out_final")}
    out: list[Json] = []
    seen: set[Path] = set()
    groups = [(f, "full") for f in spec["full"]] + [(f, "draft") for f in spec["draft"]]
    for fmt, kind in groups:
        base = Path(fmt.format(root=root, job=d, seq=seq))
        if not base.is_dir():
            continue
        for v in sorted(base.iterdir()):
            t = read_json(v / spec["terminal"]) if v.is_dir() and not v.name.endswith(".part") else None
            if not isinstance(t, dict) or v in seen:
                continue
            seen.add(v)
            out.append(_spec_candidate(settings, d, spec, v, kind, t, made.get(rel(v, settings.root)), verd))
    return out


def _mp4_md5(d: Path, spec: Json, v: Path, rec: Json | None) -> str | None:
    """The md5 the record that wrote the folder lists for its mp4, else the file's, hashed and cached."""
    mine = [o for o in (rec or {}).get("outputs") or [] if Path(o.get("path", "")).name == spec["mp4"]]
    return str(mine[0]["md5"]) if mine else cached_md5(d, v / spec["mp4"])


def _draft_of(kind: str, knobs: Json, canvas: Any) -> int:
    """A draft's long edge: the record's `draft` knob, else the canvas's long side; 0 for a full render."""
    if kind != "draft":
        return 0
    return int(knobs.get("draft") or 0) or (max(canvas) if isinstance(canvas, list) and canvas else 0)


def _spec_candidate(
    settings: Settings, d: Path, spec: Json, v: Path, kind: str, t: Json, rec: Json | None, verd: dict[str, Json]
) -> Json:
    knobs: Json = (rec or {}).get("knobs") or {}
    md5 = _mp4_md5(d, spec, v, rec)
    canvas = t.get("canvas")
    draft = _draft_of(kind, knobs, canvas)
    vd = verd.get(v.name) if kind == "full" else None
    c: Json = {
        "name": v.name,
        "kind": kind,
        "dir": v,
        "path": rel(v, settings.root),
        "mp4": spec["mp4"],
        "md5_mp4": md5,
        "frames": _num(t, "frames", "n_frames"),
        "seconds": _num(t, "seconds"),
        "fps": _num(t, "fps"),
        "canvas": canvas,
        "draft": draft,
        "has_frames": (v / "frames").is_dir(),
        "mtime": dt.datetime.fromtimestamp((v / spec["terminal"]).stat().st_mtime).isoformat(timespec="seconds"),
        "record": (rec or {}).get("id"),
        "verdict": vd,
        "unjudged": kind == "full" and (not vd or vd.get("judged_md5") != md5),
    }
    c.update({k: t.get(k) for k in spec.get("fields") or []})
    c.update({k: knobs.get(k) for k in spec.get("record_knobs") or []})
    if vd and vd.get("judged_md5") != md5:
        c["unjudged_reason"] = "the render changed after the verdict (judged md5 differs)"
    elif not vd and kind == "full":
        c["unjudged_reason"] = "no skeptic verdict for this candidate"
    return c


def candidate(settings: Settings, d: Path, job: Json, kind: str, name: str) -> Json:
    if kind not in ("full", "draft") or not NAME_RE.match(name or ""):
        raise StudioError("a render is full|draft/<name>", 400)
    for c in candidates(settings, d, job):
        if c["kind"] == kind and c["name"] == name:
            return c
    raise StudioError(f"no {kind} render {name}", 404)


def verdicts(d: Path) -> dict[str, Json]:
    """The latest skeptic verdict per candidate, merged over answers/skeptic_*.json in time order."""
    out: dict[str, Json] = {}
    for a in sorted((d / "answers").glob("skeptic_*.json")):
        ans = read_json(a) or {}
        for name, v in (ans.get("candidates") or {}).items():
            if isinstance(v, dict) and v.get("verdict") in VERDICTS:
                out[name] = {
                    "verdict": v["verdict"],
                    "judged_md5": v.get("judged_md5"),
                    "note": v.get("note", ""),
                    "from": a.name,
                    "at": ans.get("at"),
                }
    return out


def rounds(d: Path) -> list[Json]:
    out = []
    for rj in (d / "rounds").glob("*/round.json"):
        r = read_json(rj)
        if r:
            out.append(r)
    return sorted(out, key=lambda r: r["n"])


def requests_of(settings: Settings, d: Path) -> list[Json]:
    """The job's request files with their age in seconds and whether answers/ holds the reply."""
    out = []
    for rq in sorted((d / "requests").glob("*.json")):
        r = read_json(rq) or {}
        ans = d / "answers" / rq.name
        age = round((dt.datetime.now() - dt.datetime.fromtimestamp(rq.stat().st_mtime)).total_seconds())
        out.append(
            {
                "file": rel(rq, settings.root),
                "name": rq.name,
                "kind": r.get("kind"),
                "at": r.get("at"),
                "brief": r.get("brief", ""),
                "candidates": [c.get("name") for c in r.get("candidates", [])],
                "answered": ans.exists(),
                "answer": rel(ans, settings.root) if ans.exists() else None,
                "age_s": age,
            }
        )
    return out
