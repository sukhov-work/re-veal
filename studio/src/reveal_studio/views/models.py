"""The rail's models panel, the open requests across jobs (the session's inbox), and the registry for the page."""

from __future__ import annotations

from typing import Any

from reveal_studio.config import Settings
from reveal_studio.fs import Json, read_json, rel
from reveal_studio.jobs.candidates import requests_of
from reveal_studio.jobs.plans import frozen_plans
from reveal_studio.jobs.store import job_dirs
from reveal_studio.registry.flows import STAGE_NAMES
from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.rulings import RULINGS
from reveal_studio.registry.schema import EASES, EFFECTS, METHODS, PLAN_KEYS, VERDICTS, schema_view
from reveal_studio.runner.argv import ScriptFlags

MODEL_MANIFESTS = (
    ("reveal matcher", "models/MANIFEST.json", "matcher"),
    ("depth model", "models/DEPTH_MANIFEST.json", "model"),
    ("RIFE", "benchmarks/runs/2026-10-21/rife/RIFE_MANIFEST.json", "model"),
    ("faces (YuNet)", "benchmarks/runs/2026-10-18/face/FACE_MANIFEST.json", "model"),
)


def models_view(settings: Settings) -> list[Json]:
    """Readiness per model: a manifest that reads is a model the scripts load offline."""
    out = []
    for name, p, key in MODEL_MANIFESTS:
        m = read_json(settings.root / p)
        out.append(
            {
                "name": name,
                "manifest": p,
                "ready": m is not None,
                "version": (m or {}).get(key) or (m or {}).get("model") or None,
                "verified": (m or {}).get("verified") or (m or {}).get("date"),
            }
        )
    return out + director_inputs(settings)


def director_inputs(settings: Settings) -> list[Json]:
    """The director flow's two derived inputs beside the models (phase B, builder D): the layer tables under the
    layers root (<photo>/layers.json) and the mattes under the mattes root (<photo>/el_<id>.png), with their counts in
    the row's name, since the rail prints the name and the readiness."""
    tables = sorted(p.parent.name for p in settings.layers_dir.glob("*/layers.json"))
    mattes = {p.parent.name for p in settings.mattes_dir.glob("*/el_*.png")}
    files = sum(1 for _ in settings.mattes_dir.glob("*/el_*.png"))
    return [
        {
            "name": f"layer tables ({len(tables)} photos)" if tables else "layer tables",
            "manifest": rel(settings.layers_dir, settings.root),
            "ready": bool(tables),
            "version": None,
            "verified": None,
            "count": len(tables),
        },
        {
            "name": f"mattes ({len(mattes)} photos, {files} files)" if mattes else "mattes",
            "manifest": rel(settings.mattes_dir, settings.root),
            "ready": bool(mattes),
            "version": None,
            "verified": None,
            "count": files,
        },
    ]


def open_requests(settings: Settings) -> list[Json]:
    """Every unanswered request of every job, the oldest first."""
    rows = []
    for d in job_dirs(settings):
        job = read_json(d / "job.json") or {}
        for r in requests_of(settings, d):
            if not r["answered"]:
                rows.append({"job": job.get("id"), "job_dir": rel(d, settings.root), **r})
    return sorted(rows, key=lambda r: -r["age_s"])


def registry_view(settings: Settings, flags: ScriptFlags, flows: dict[str, Any]) -> Json:
    """GET /api/registry: the flows and their stages, the hints, the schema's lists and the server's identity."""
    return {
        "flows": flows,
        "stage_order": STAGE_NAMES,
        "hints": HINTS,
        "methods": METHODS,
        "eases": EASES,
        "effects": EFFECTS,
        "plan_keys": PLAN_KEYS,
        "plan_schema": schema_view(),
        "rulings": RULINGS,
        "verdicts": VERDICTS,
        "ui_version": settings.ui_version,
        "script_flags": flags.as_dict(),
        "frozen_plans": frozen_plans(settings),
        "runs_date": settings.runs_date,
        "port": settings.port,
    }
