"""Every flow of the studio, the enabled ones, and the lookups by flow: a stage, the stage order, identity patterns.

ALL_FLOWS holds the loop, the pair and the director flows; FLOWS the enabled ones, which the page offers and
POST /api/jobs accepts. A job of a disabled flow still opens: every lookup here reads ALL_FLOWS. A flow entry is
{title, what, enabled, stages} and, for a flow whose renders the spec reader lists, `candidates` (registry/pair.py).
STAGE_NAMES is the union of the stage names in flow order, the loop's ten first: the registry view's `stage_order`,
which the page reads with .includes, and the first segment that marks a ruling's knob as a stage knob.
"""

from __future__ import annotations

from typing import Any

from reveal_studio.errors import StudioError
from reveal_studio.registry import director, loop, pair
from reveal_studio.registry.common import COMMON_STAGES

ALL_FLOWS: dict[str, dict[str, Any]] = {"loop": loop.FLOW, "pair": pair.FLOW, "director": director.FLOW}
FLOWS: dict[str, dict[str, Any]] = {k: f for k, f in ALL_FLOWS.items() if f["enabled"]}
STAGE_NAMES: list[str] = list(dict.fromkeys(s["name"] for f in ALL_FLOWS.values() for s in f["stages"]))


def flow_def(flow: str) -> dict[str, Any]:
    f = ALL_FLOWS.get(flow)
    if f is None:
        raise StudioError(f"no flow {flow!r}; the flows are {list(ALL_FLOWS)}", 404)
    return f


def stage_order(flow: str) -> list[str]:
    return [s["name"] for s in flow_def(flow)["stages"]]


def stage_def(flow: str, name: str) -> dict[str, Any]:
    stages: list[dict[str, Any]] = flow_def(flow)["stages"]
    for s in stages:
        if s["name"] == name:
            return s
    raise StudioError(f"no stage {name!r} in the {flow} flow", 404)


def identity_of(flow: str | None, name: str) -> list[str]:
    """The file-name patterns (fnmatch) whose md5s name a run's result, for the "unchanged" rule: the flow's own
    stage, else the shared stage of that name (a shared stage may sit in no flow's list yet), else none."""
    stages: list[dict[str, Any]] = ALL_FLOWS[flow]["stages"] if flow in ALL_FLOWS else []
    s = next((s for s in stages if s["name"] == name), None) or COMMON_STAGES.get(name) or {}
    return list(s.get("identity") or [])
