"""The stages more than one flow shares, defined once: Reveal's verdict, the optional branch under the import of the
pair and director flows (phase B design, decision 3, 2026-11-05).

A shared stage's name is reserved in every flow. runner/argv.py routes it to runner/argv_common.py before the flow's
own argv module, and registry/flows.py finds its identity patterns even where no flow's stage list holds it yet.
"""

from __future__ import annotations

from typing import Any

VERDICT_STAGE: dict[str, Any] = {
    "name": "verdict",
    "title": "Reveal's verdict",
    "kind": "script",
    "optional": True,
    "parent": "import",
    "branch": True,
    "stale_after": [],
    "backend": "reveal.py align",
    "script": "reveal",
    "terminal": "metrics.json",
    "identity": ["metrics.json"],
    "what": "Reveal's strict alignment of B onto A, run on demand. Exit 2 with a FAILED: line is a refusal: the photos share too little detail to align. On success it writes metrics.json and two full-resolution aligned stills, the align flow's outputs.",
    "knobs": [],
}

COMMON_STAGES: dict[str, dict[str, Any]] = {"verdict": VERDICT_STAGE}
