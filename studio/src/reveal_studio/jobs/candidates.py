"""What a job holds, read from disk on every call: its renders (candidates), the verdicts, rounds and requests."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, read_json, rel
from reveal_studio.jobs.store import job_root
from reveal_studio.registry.schema import NAME_RE, VERDICTS


def candidates(settings: Settings, d: Path, job: Json) -> list[Json]:
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
