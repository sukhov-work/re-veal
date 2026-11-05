"""The rulings table: a knob value the owner ruled out, with its date and source, so the page warns before a run.

STUDIO.md §4: "a rulings table in the registry (a knob, the value ruled out, the DECISIONS date) warns before a run that
sets one". A warning, never a refusal: the plan editor shows a chip beside the field, the inspector beside the stage
knob, and the run endpoint's 202 body and the record carry `warnings`.

One row per ruling: {"knob", "value", "since", "why", "source"}.
- `knob`: a plan path in registry/schema.py's grammar (`timeline[method=slide].mode`, `timeline[*].method`) or a stage
  knob (`registration.ecc_refine`, a stage name then the knob's key).
- `value`: the ruled-out value, or a range: {"min": v} rules out v and above, {"above": v} everything above v.
- The value is compared with the effective value: an absent key takes its schema default, because three of the ruled
  values are loop_seq.py's own defaults (the slide's fly, the teleport's squeeze, a sheet's carry of 1.0).
- `since`: the date of the ruling; `source`: the DECISIONS line and the playbook section (`loops.md` is
  `.claude/skills/reveal/references/loops.md`); `why`: one sentence with his words or the measure.

Filled on 2026-11-05 from loops.md §2, §3 and §5 and the DECISIONS lines of 2026-10-30, 2026-11-01 and 2026-11-04.
A row without a cited source is not added.
"""

from __future__ import annotations

from typing import Any, TypedDict

from reveal_studio.registry.flows import STAGE_NAMES
from reveal_studio.registry.schema import resolve


class Ruling(TypedDict):
    knob: str
    value: Any
    since: str
    why: str
    source: str


class Hit(TypedDict):
    """One warning: the ruling's fields, where it was found (a JSON pointer or the stage knob) and the value found;
    `absent` is true when the plan does not set the key and the code's default is the ruled value."""

    knob: str
    value: Any
    since: str
    why: str
    source: str
    path: str
    absent: bool


RULINGS: list[Ruling] = [
    {
        "knob": "timeline[*].method",
        "value": "slices",
        "since": "2026-11-01",
        "why": 'His grade on the first seasons round, eight candidates of diagonal cells: "simple 2d pattern transtions, boring, tasteless and junky".',
        "source": "DECISIONS 2026-11-01; loops.md §3",
    },
    {
        "knob": "timeline[*].method",
        "value": "rise",
        "since": "2026-10-30",
        "why": 'His grade on the rise from behind the man (zeke-back c2, round 3): "ugly and has lots of artifacts"; he asked for "a more immediat snap" instead.',
        "source": "DECISIONS 2026-10-30 (fourth; archived 2026-11-05, the digest in DECISIONS.md); loops.md §5",
    },
    {
        "knob": "timeline[method=slide].mode",
        "value": "fly",
        "since": "2026-10-30",
        "why": 'His grade on the slide\'s flight (group-teleport c2, round 3): "very dirty"; he asked to "just dissolbe morph person into background and do inverse in destination", the mode dissolve.',
        "source": "DECISIONS 2026-10-30 (fourth; archived 2026-11-05, the digest in DECISIONS.md); loops.md §3, §5",
    },
    {
        "knob": "timeline[method=teleport].mode",
        "value": "squeeze",
        "since": "2026-10-30",
        "why": 'His grade on the teleport\'s squeeze to a bright line (group-teleport, round 2): "do not beam, this looks like cardbard cut out very cheap and photoshop-style".',
        "source": "DECISIONS 2026-10-30 (third; archived 2026-11-05, the digest in DECISIONS.md); loops.md §3, §5",
    },
    {
        "knob": "timeline[method=teleport].flash",
        "value": {"min": 1},
        "since": "2026-10-30",
        "why": 'His rule on round 2: "no flashes, no double pokes, nothing jerky"; the playbook lists the teleport\'s flash cut among what failed.',
        "source": "DECISIONS 2026-10-30 (third; archived 2026-11-05, the digest in DECISIONS.md); loops.md §5",
    },
    {
        "knob": "timeline[method=sheets].sheets[*].carry",
        "value": {"above": 0},
        "since": "2026-11-01",
        "why": 'His grade on the seasons round 2, where the carried and drifting pictures were rejected: "all other example are horribly misaligned"; the carry knob stays, never above 0 for him.',
        "source": "DECISIONS 2026-11-01 (third); loops.md §3",
    },
    {
        "knob": "registration.ecc_refine",
        "value": True,
        "since": "2026-11-04",
        "why": "Measured on the angel pair: the masked ECC on the far field left the far field 2–9 px worse.",
        "source": "DECISIONS 2026-11-04; loops.md §2",
    },
]


def is_stage_knob(knob: str) -> bool:
    """A stage knob names a stage of the registry first (`registration.ecc_refine`): a stage of any flow, as the page's
    isStageKnob reads the registry view's stage_order; anything else is a plan path."""
    return knob.split(".", 1)[0].split("[", 1)[0] in STAGE_NAMES


def _number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def ruled(rule: Any, v: Any) -> bool:
    """Whether the value `v` is the ruled-out value or falls in the ruled-out range (a bool never equals a number)."""
    if isinstance(rule, dict):
        if not _number(v):
            return False
        if "min" in rule:
            return bool(v >= rule["min"])
        if "above" in rule:
            return bool(v > rule["above"])
        return False
    if isinstance(rule, bool) or isinstance(v, bool):
        return rule is v
    return bool(rule == v)


def _hit(r: Ruling, path: str, value: Any, absent: bool) -> Hit:
    return {
        "knob": r["knob"],
        "value": value,
        "since": r["since"],
        "why": r["why"],
        "source": r["source"],
        "path": path,
        "absent": absent,
    }


def plan_hits(plan: Any) -> list[Hit]:
    """The ruled values a plan holds, an absent key at its schema default included."""
    out: list[Hit] = []
    for r in RULINGS:
        if is_stage_knob(r["knob"]):
            continue
        for ptr, v, explicit in resolve(plan, r["knob"]):
            if ruled(r["value"], v):
                out.append(_hit(r, ptr, v, not explicit))
    return out


def knob_hits(stage: str, knobs: dict[str, Any]) -> list[Hit]:
    """The ruled values among one stage's knobs (the knobs as the runner coerced them)."""
    out: list[Hit] = []
    for r in RULINGS:
        name, _, key = r["knob"].partition(".")
        if name == stage and key in knobs and ruled(r["value"], knobs[key]):
            out.append(_hit(r, r["knob"], knobs[key], False))
    return out


def stage_warnings(stage: str, knobs: dict[str, Any], plan: Any = None) -> list[Hit]:
    """What a run of `stage` with `knobs` warns about: its own knobs, and the plan it renders when it renders one."""
    return knob_hits(stage, knobs) + (plan_hits(plan) if plan is not None else [])
