"""The director plan flow (phase B): a fixture pair and a frozen plan from scripts/research/plans/, rendered by
director_render.py and reviewed on director_page.py's page.

Registered and disabled: no stage yet, so the page offers no new director job and POST /api/jobs refuses one, while
the job creator (jobs/store.py) and the shared verdict stage already work. Builder D fills DIRECTOR_STAGES (the
entries of .claude/claude-docs/research/2026-11-05/b_director_research.md, section 1) and sets `enabled`.

`candidates`: the full renders are the run folder's own children (director_page.py lists every child of run/ that
holds an info.json), the drafts sit in the job folder's drafts/, outside run/; see registry/pair.py for the keys.
"""

from __future__ import annotations

from typing import Any

DIRECTOR_STAGES: list[dict[str, Any]] = []

FLOW: dict[str, Any] = {
    "title": "director plan",
    "what": "A fixture pair and a frozen plan from scripts/research/plans/: director_render.py resolves the plan's names into pixels and renders one concept, then the review.",
    "enabled": False,
    "stages": DIRECTOR_STAGES,
    "candidates": {
        "full": ["{root}"],
        "draft": ["{job}/drafts"],
        "terminal": "info.json",
        "mp4": "transition.mp4",
        "record_knobs": [],
        "fields": [
            "motion_median_px",
            "motion_pauses",
            "motion_jumps",
            "b_inside_first",
            "residual_edge_max",
            "halo_step_max",
            "halo_ring_max",
            "step_first",
            "step_max",
            "wall_s",
            "renderer_md5",
            "transitions_md5",
            "plan_sha256",
        ],
    },
}
