"""The pair transition flow (phase B): two photos animated from one into the other by transitions.py.

Registered and disabled: no stage yet, so the page offers no new pair job and POST /api/jobs refuses one, while the
job creator (jobs/store.py) and the shared verdict stage already work. Builder P fills PAIR_STAGES (the entries of
.claude/claude-docs/research/2026-11-05/b_pair_research.md, Part 1) and sets `enabled`.

`candidates` is the spec jobs/candidates.py reads a pair job's renders by: the folders of the full renders and the
drafts ({root} the job's run folder, {job} the job folder, {seq} the pair's name), the file that marks a finished
render, its mp4, the knobs copied from the record that wrote it, and the terminal file's fields copied onto the
candidate.
"""

from __future__ import annotations

from typing import Any

PAIR_STAGES: list[dict[str, Any]] = []

FLOW: dict[str, Any] = {
    "title": "pair transition",
    "what": "Two photos, related or not, animated from one into the other by transitions.py: the relation first, then the renders, then the review.",
    "enabled": False,
    "stages": PAIR_STAGES,
    "candidates": {
        "full": ["{root}/{seq}"],
        "draft": ["{root}/drafts/{seq}"],
        "terminal": "report.json",
        "mp4": "transition.mp4",
        "record_knobs": ["preset"],
        "fields": ["class", "method", "sparse_inliers", "median_disp_px", "mean_certainty", "n_frames", "quality"],
    },
}
