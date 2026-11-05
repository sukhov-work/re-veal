"""The review gate: the page is refused while a listed full render is unjudged or NOT READY, unless he overrides; the
override is printed in the page's footer and kept in the round.

`variants` (backlog T76, STUDIO.md §12's last paragraph) lists the full renders the page shows, in its order; empty
lists every full render in name order and passes no flag. The gate checks the listed candidates only, so an excluded
unjudged render does not block. A name that is not a full render, or a name given twice, is refused here (400) before
the script's own `FAILED:` line would be.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, now_iso
from reveal_studio.jobs.candidates import candidates
from reveal_studio.registry.loop import stage_def
from reveal_studio.runner.argv import as_list
from reveal_studio.runner.process import Runner


def _why(c: Json) -> str:
    if c["verdict"] and c["verdict"]["verdict"] == "NOT READY":
        return "NOT READY" + (f": {c['verdict'].get('note')}" if c["verdict"].get("note") else "")
    return "unjudged: " + (c.get("unjudged_reason") or "")


def page_variants(raw: Any, full: list[Json]) -> list[str]:
    """The names the page lists, checked against the full renders: [] (every one), or each name once and existing."""
    if raw in (None, "", []):
        return []
    try:
        names = as_list(raw)
    except TypeError:
        raise StudioError("variants is a list of full render names, e.g. ['a2', 'a3']", 400) from None
    have = [c["name"] for c in full]
    for n in names:
        if names.count(n) > 1:
            raise StudioError(f"variants: {n} is named twice", 400)
        if n not in have:
            raise StudioError(
                f"variants: {n} is not a full render of this job (the full renders are {have})", 400, {"unknown": n}
            )
    return names


def build_page(runner: Runner, d: Path, job: Json, body: Json) -> Json:
    """POST /api/jobs/<id>/page: the variants check, the gate, then the page stage's record (`loop_seq.py page`)."""
    full = [c for c in candidates(runner.settings, d, job) if c["kind"] == "full"]
    if not full:
        raise StudioError("no full render to put on a page", 409)
    variants = page_variants(body.get("variants"), full)
    by_name = {c["name"]: c for c in full}
    listed = [by_name[n] for n in variants] if variants else full
    bad = [c for c in listed if c["unjudged"] or (c["verdict"] and c["verdict"]["verdict"] == "NOT READY")]
    override = bool(body.get("override"))
    knobs: Json = {k: str(body.get(k) or "") for k in ("title", "intro", "footer")}
    knobs["notes"] = body.get("notes") or {}
    knobs["variants"] = variants
    if bad and not override:
        raise StudioError(
            "the page is refused: "
            + "; ".join(f"{c['name']} ({_why(c)})" for c in bad)
            + ". Request the skeptic, or override (the page prints the override).",
            409,
            {"refused": [c["name"] for c in bad]},
        )
    if bad:
        text = (
            "Override: built on his word with "
            + ", ".join(f"{c['name']} ({_why(c)})" for c in bad)
            + f" ({now_iso()})."
        )
        knobs["footer"] = (knobs["footer"] + " " + text).strip()
        knobs["override"] = text
    return runner.start_stage(d, job, stage_def(job["flow"], "page"), knobs)
