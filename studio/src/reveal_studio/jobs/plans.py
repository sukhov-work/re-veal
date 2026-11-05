"""Plans: the job's saved plans (each with a provenance block) and the frozen ones, which are never written."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, now_iso, read_json, rel, sha256_file, write_json
from reveal_studio.registry.rulings import plan_hits, stage_warnings
from reveal_studio.registry.schema import NAME_RE, validate_plan


def resolve_plan(settings: Settings, d: Path | None, ref: Any) -> Path:
    """`job:<name>` (a plan saved in the job `d`) or `frozen:<name>` (scripts/research/plans/loops/<name>.json)."""
    if not isinstance(ref, str) or ":" not in ref:
        raise StudioError(
            "the plan is job:<name> (a plan saved in this job) or frozen:<name> "
            "(scripts/research/plans/loops/<name>.json)",
            400,
        )
    kind, name = ref.split(":", 1)
    if not NAME_RE.match(name):
        raise StudioError("a plan name is letters, digits, dash and underscore", 400)
    if kind == "job" and d is not None:
        p = d / "plans" / f"{name}.json"
    elif kind == "frozen":
        p = settings.frozen_plans / f"{name}.json"
    else:
        raise StudioError("the plan is job:<name> or frozen:<name>", 400)
    if not p.exists():
        raise StudioError(f"no plan {rel(p, settings.root)}", 404)
    return p


def plans_of(settings: Settings, d: Path) -> list[Json]:
    out = []
    for pj in sorted((d / "plans").glob("*.json")):
        p = read_json(pj) or {}
        prov = p.get("provenance") or {}
        out.append(
            {
                "name": pj.stem,
                "ref": f"job:{pj.stem}",
                "path": rel(pj, settings.root),
                "sha256": sha256_file(pj),
                "title": p.get("title", ""),
                "from": prov.get("from"),
                "author": prov.get("author"),
                "at": prov.get("at"),
                "changes": len(prov.get("changes") or []),
                "words": prov.get("words", ""),
                "warnings": [dict(h) for h in plan_hits(p)],
            }
        )
    return out


def frozen_plans(settings: Settings) -> list[Json]:
    out = []
    for pj in sorted(settings.frozen_plans.glob("*.json")):
        p = read_json(pj) or {}
        out.append(
            {
                "name": pj.stem,
                "ref": f"frozen:{pj.stem}",
                "path": rel(pj, settings.root),
                "seq": p.get("seq"),
                "title": p.get("title", "")[:160],
                "in": p.get("in"),
                "warnings": [dict(h) for h in plan_hits(p)],
            }
        )
    return out


def run_warnings(settings: Settings, d: Path, stage: str, knobs: Json) -> list[Json]:
    """The rulings a run warns about (STUDIO.md §4): the stage's own knobs, and for a render the plan it reads."""
    plan = read_json(resolve_plan(settings, d, knobs.get("plan"))) if stage == "render" else None
    return [dict(h) for h in stage_warnings(stage, knobs, plan)]


def plan_diff(old: Any, new: Any, path: str = "", out: list[Json] | None = None, cap: int = 300) -> list[Json]:
    """The changed leaves as [{path: "/timeline/1/n", old, new}], the provenance block skipped, at most `cap`."""
    out = [] if out is None else out
    if len(out) >= cap:
        return out
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            if k == "provenance":
                continue
            if k not in old:
                out.append({"path": f"{path}/{k}", "old": None, "new": new[k]})
            elif k not in new:
                out.append({"path": f"{path}/{k}", "old": old[k], "new": None})
            else:
                plan_diff(old[k], new[k], f"{path}/{k}", out, cap)
    elif isinstance(old, list) and isinstance(new, list):
        for i in range(max(len(old), len(new))):
            if i >= len(old):
                out.append({"path": f"{path}/{i}", "old": None, "new": new[i]})
            elif i >= len(new):
                out.append({"path": f"{path}/{i}", "old": old[i], "new": None})
            else:
                plan_diff(old[i], new[i], f"{path}/{i}", out, cap)
    elif old != new:
        out.append({"path": path or "/", "old": old, "new": new})
    return out


def save_plan(
    settings: Settings,
    d: Path,
    job: Json,
    name: Any,
    plan: Any,
    from_ref: Any = None,
    words: Any = "",
) -> Json:
    """Writes plans/<name>.json with a provenance block; refuses a name that exists (a saved plan stays as saved)."""
    if not NAME_RE.match(name or ""):
        raise StudioError("a plan name is letters, digits, dash and underscore", 400)
    validate_plan(plan)
    dest = d / "plans" / f"{name}.json"
    if dest.exists():
        raise StudioError(f"plans/{name}.json exists: a saved plan is never overwritten; choose another name", 409)
    prov: Json = {"author": "owner", "at": now_iso(), "ui_version": settings.ui_version, "words": str(words or "")}
    if from_ref:
        src = resolve_plan(settings, d, from_ref)
        old = read_json(src) or {}
        prov["from"] = rel(src, settings.root)
        prov["from_sha256"] = sha256_file(src)
        prov["changes"] = plan_diff(old, plan)
    else:
        prov["from"] = None
        prov["changes"] = []
    plan = dict(plan)
    plan["provenance"] = prov
    write_json(dest, plan)
    log(f"{d.name}: plan {name} saved ({len(prov['changes'])} changes from {prov['from']})")
    return {
        "name": name,
        "ref": f"job:{name}",
        "path": rel(dest, settings.root),
        "sha256": sha256_file(dest),
        "changes": prov["changes"],
    }
