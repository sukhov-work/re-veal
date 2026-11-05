"""The plan schema as data (scripts/research/plans/loops/SCHEMA.md, read 2026-11-05), the id rules and validate_plan.

One entry per key a plan can hold, in the order the plan editor's forms show them:
- `path`: the key's place as a pattern: `crf`, `matte.thr`, `timeline[*].n` (every transition), `timeline[method=rife].margin`
  (a rife step only), `timeline[method=sheets].sheets[*].carry` (each sheet of a sheets step), `effects[kind=glow].gain`.
  The rulings table (registry/rulings.py) names its plan knobs in the same grammar.
- `group`: the form the key belongs to: plan, matte, hold, transition, chain, a method's name, a list item's group
  (rife.local, sheets.sheet, sheets.object) or an effect kind (effect.breath).
- `type`: int, float, str, bool, list (`item` names the element: a scalar type, or the group of an object's keys),
  box (x0, y0, x1, y1), point (x, y) or object (a JSON object edited as text).
- `default`: the value an absent key takes. `default_from` says where it was read: "SCHEMA.md" where SCHEMA.md states
  it (its "the code's default is X" included), "loop_seq.py" where only the code's literal default exists (SCHEMA.md
  does not document the slide, rise and snap keys at all), null when an absent key has no single value (a required
  key, or a key whose absence switches a branch off).
- `range`: null unless SCHEMA.md states one; it states one, the slices' `shadow` (0–1).
- `choices`, `units`, `roles` (the names of a box's or a point's numbers), `required`, `hint` (its sentence's key in
  registry/hints.py).

The keys loop_seq.py reads but SCHEMA.md does not list (the teleport's rest, flash, flash_gain, box_mode, box_open) are
not entries: the editor shows them under "other keys" with their JSON values.
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

from reveal_studio.errors import StudioError

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,59}$")
"""A render, plan or sequence name: 60 characters since phase B, so a director folder <stem>_<concept>-<tag> fits."""
SCHEMA_DATE = "2026-11-05"
METHODS = (
    "rife",
    "dissolve",
    "morph",
    "teleport",
    "cut",
    "rewind",
    "slices",
    "sheets",
    "snap",
    "slide",
    "rise",
    "repaint",
)
EASES = ("linear", "smooth", "snap", "accel", "accel3", "decel", "sine")
EFFECTS = ("breath", "parallax", "glow")
PLAN_KEYS = ("seq", "in", "title", "gag", "timeline", "effects", "matte", "crf", "gif_long", "crop", "provenance")
VERDICTS = ("READY", "READY WITH A NOTE", "NOT READY")
TYPES = ("int", "float", "str", "bool", "list", "box", "point", "object")
CHAIN_METHODS = ("rife", "dissolve")
"""The methods a `through` chain renders (loop_seq.py's frames_chain: dissolve blends, every other method is RIFE)."""
MORPH_PRESETS = ("morph", "dissolve", "flow-dissolve", "snap-morph", "iris", "wipe", "luma")
"""transitions.py's PRESETS, which the morph's `preset` names."""
WAVES = ("sin", "pulse")
FRACTIONS = "canvas fractions"
PX = "prep-canvas px"


class Entry(TypedDict):
    path: str
    group: str
    key: str
    type: str
    item: str | None
    default: Any
    default_from: str | None
    range: list[float] | None
    choices: list[Any] | None
    units: str | None
    roles: list[str] | None
    required: bool
    hint: str


# The path prefix and the hint prefix of each group, in the order the editor shows the groups.
GROUPS: dict[str, tuple[str, str, str]] = {
    "plan": ("", "plan.", "the plan"),
    "matte": ("matte.", "plan.matte.", "the change matte"),
    "hold": ("timeline[*].", "plan.timeline.", "a hold"),
    "transition": ("timeline[*].", "plan.timeline.", "a transition"),
    "chain": ("timeline[*].", "plan.timeline.", "a chain through several stills"),
    "rife": ("timeline[method=rife].", "plan.timeline.", "rife"),
    "rife.local": ("timeline[method=rife].local[*].", "plan.timeline.local.", "a local box"),
    "morph": ("timeline[method=morph].", "plan.timeline.morph.", "morph"),
    "teleport": ("timeline[method=teleport].", "plan.timeline.teleport.", "teleport"),
    "rewind": ("timeline[method=rewind].", "plan.timeline.rewind.", "rewind"),
    "snap": ("timeline[method=snap].", "plan.timeline.snap.", "snap"),
    "slide": ("timeline[method=slide].", "plan.timeline.slide.", "slide"),
    "rise": ("timeline[method=rise].", "plan.timeline.rise.", "rise"),
    "slices": ("timeline[method=slices].", "plan.timeline.slices.", "slices"),
    "sheets": ("timeline[method=sheets].", "plan.timeline.sheets.", "sheets"),
    "sheets.sheet": ("timeline[method=sheets].sheets[*].", "plan.timeline.sheets.sheet.", "a sheet"),
    "sheets.object": ("timeline[method=sheets].objects[*].", "plan.timeline.sheets.object.", "an object plate"),
    "repaint": ("timeline[method=repaint].", "plan.timeline.repaint.", "repaint"),
    "effect": ("effects[*].", "plan.effects.", "an effect"),
    "effect.breath": ("effects[kind=breath].", "plan.effects.breath.", "breath"),
    "effect.parallax": ("effects[kind=parallax].", "plan.effects.parallax.", "parallax"),
    "effect.glow": ("effects[kind=glow].", "plan.effects.glow.", "glow"),
}
ROLES = {"box": ["x0", "y0", "x1", "y1"], "point": ["x", "y"]}


def _e(
    group: str,
    key: str,
    typ: str,
    default: Any = None,
    src: str | None = None,
    *,
    req: bool = False,
    choices: tuple[Any, ...] | list[Any] | None = None,
    units: str | None = None,
    item: str | None = None,
    roles: list[str] | None = None,
    rng: list[float] | None = None,
) -> Entry:
    """One schema entry; the path and the hint key follow from the group (GROUPS)."""
    path_prefix, hint_prefix, _title = GROUPS[group]
    return {
        "path": path_prefix + key,
        "group": group,
        "key": key,
        "type": typ,
        "item": item,
        "default": default,
        "default_from": src if default is not None else None,
        "range": rng,
        "choices": list(choices) if choices is not None else None,
        "units": units,
        "roles": roles or ROLES.get(typ),
        "required": req,
        "hint": hint_prefix + key,
    }


S, C = "SCHEMA.md", "loop_seq.py"
DEFAULT_MATTE = {"thr": 14, "grow": 0.015, "feather": 0.01, "min_share": 0.0005}
MATTE_SPEC = ("kind", "thr", "open", "exclude", "erode", "iters")

PLAN_SCHEMA: list[Entry] = [
    # the plan level
    _e("plan", "seq", "str"),
    _e("plan", "in", "str"),
    _e("plan", "title", "str"),
    _e("plan", "gag", "str"),
    _e("plan", "crf", "int", 14, C),
    _e("plan", "gif_long", "int", 540, C, units="px"),
    _e("plan", "crop", "float", 1.0, C, units="share of the canvas"),
    _e("plan", "matte", "object", DEFAULT_MATTE, C, item="matte"),
    _e("matte", "thr", "float", 14, C, units="Lab levels"),
    _e("matte", "grow", "float", 0.015, C, units="share of the width"),
    _e("matte", "feather", "float", 0.01, C, units="share of the width"),
    _e("matte", "min_share", "float", 0.0005, C, units="share of the frame"),
    _e("matte", "all", "bool", False, C),
    # a hold
    _e("hold", "key", "int", req=True, units="still"),
    _e("hold", "hold", "int", 1, C, units="frames"),
    # every transition
    _e("transition", "to", "int", req=True, units="still"),
    _e("transition", "n", "int", 0, C, units="frames"),
    _e("transition", "method", "str", "rife", C, choices=METHODS),
    _e("transition", "ease", "str", "smooth", C, choices=EASES),
    # a chain (rife or dissolve with `through`)
    _e("chain", "through", "list", item="int", units="stills"),
    _e("chain", "weights", "list", item="float"),
    _e("chain", "soft", "float", 0.0, C),
    _e("chain", "knot_margin", "float", 0.0, C, units="share of a leg"),
    # rife
    _e("rife", "margin", "float", 0, S, units="share of t"),
    _e("rife", "local", "list", [], C, item="rife.local"),
    _e("rife.local", "box", "box", req=True, units=FRACTIONS),
    _e("rife.local", "ease", "str", "snap", C, choices=EASES),
    _e("rife.local", "feather", "float", 0.01, C, units="share of the width"),
    # morph (transitions.py's)
    _e("morph", "preset", "str", "morph", C, choices=MORPH_PRESETS),
    _e("morph", "anchors", "str", units="canvas px"),
    _e("morph", "falloff", "float", 0.25, C),
    _e("morph", "warp", "float", 1.0, C),
    _e("morph", "color", "float", 0.7, C),
    # teleport
    _e("teleport", "out_box", "box", units=FRACTIONS),
    _e("teleport", "in_box", "box", units=FRACTIONS),
    _e("teleport", "mode", "str", "squeeze", C, choices=("squeeze", "fade")),
    _e("teleport", "span", "float", 0.6, C, units="share of the segment"),
    _e("teleport", "glow", "float", 0.6, C),
    _e("teleport", "box_thr", "float", 30.0, C, units="Lab levels"),
    # rewind
    _e("rewind", "from", "int", 0, C, units="frame"),
    _e("rewind", "stride", "int", 3, C, units="frames"),
    # snap
    _e("snap", "blur_frac", "float", 0.015, C, units="share of the height"),
    _e("snap", "direction", "str", "vertical", C, choices=("vertical", "horizontal")),
    # slide
    _e("slide", "box_a", "box", req=True, units=FRACTIONS),
    _e("slide", "box_b", "box", req=True, units=FRACTIONS),
    _e("slide", "matte_a", "object", {"kind": "box", "thr": 24}, C),
    _e("slide", "matte_b", "object", {"kind": "grabcut"}, C),
    _e("slide", "mode", "str", "fly", C, choices=("fly", "dissolve")),
    _e("slide", "window", "list", [0.2, 0.8], C, item="float", units="share of the segment"),
    _e("slide", "window_out", "list", [0.0, 0.55], C, item="float", units="share of the segment"),
    _e("slide", "window_in", "list", [0.45, 1.0], C, item="float", units="share of the segment"),
    _e("slide", "slide_ease", "str", "sine", C, choices=EASES),
    _e("slide", "blur", "bool", True, C),
    _e("slide", "blur_k", "float", 0.5, C),
    _e("slide", "fill", "str", "donor+vertical", C),
    _e("slide", "floor_y", "float", units="share of the height"),
    _e("slide", "donor_box_b", "box", units=FRACTIONS),
    # rise
    _e("rise", "ghoul_box", "box", req=True, units=FRACTIONS),
    _e("rise", "man_box", "box", req=True, units=FRACTIONS),
    _e("rise", "matte_ghoul", "object", {"kind": "grabcut"}, C),
    _e("rise", "matte_man", "object", {"kind": "grabcut"}, C),
    _e("rise", "direction", "str", "up", C, choices=("up", "down")),
    _e("rise", "start_offset", "point", [0, 0.1], C, units="share of W and H", roles=["dx", "dy"]),
    _e("rise", "window", "list", [0.35, 1.0], C, item="float", units="share of the segment"),
    _e("rise", "rise_ease", "str", "smooth", C, choices=EASES),
    _e("rise", "fill", "str", "vertical", C),
    _e("rise", "floor_y", "float", units="share of the height"),
    _e("rise", "man_box_other", "box", units=FRACTIONS),
    # slices
    _e("slices", "through", "list", item="int", units="stills"),
    _e("slices", "angle", "float", 62.0, C, units="degrees"),
    _e("slices", "bands", "int", 12, C),
    _e("slices", "widths", "list", item="float"),
    _e("slices", "families", "int", 1, C, choices=(1, 2)),
    _e("slices", "width2", "float", 0, C, units="px"),
    _e("slices", "mirror", "bool", False, C),
    _e("slices", "slide", "str", "across", C, choices=("across", "along")),
    _e("slices", "travel", "float", 0.4, C, units="× the canvas diagonal"),
    _e("slices", "wrap", "bool", False, C),
    _e("slices", "ramp", "int", 3, C, units="frames"),
    _e("slices", "dir", "int", 1, C, choices=(1, -1)),
    _e("slices", "alternate", "bool", False, C),
    _e("slices", "lattice_axis", "str", "alt", C, choices=("alt", "1", "2")),
    _e("slices", "order", "str", "up", C, choices=("up", "down", "centre", "edges", "random", "diag", "antidiag")),
    _e("slices", "seed", "int", 1, C),
    _e("slices", "stagger", "int", 2, C, units="frames"),
    _e("slices", "dur", "int", 12, C, units="frames"),
    _e("slices", "period", "int", units="frames"),
    _e("slices", "flip_each", "bool", True, S),
    _e("slices", "reverse_each", "bool", False, C),
    _e("slices", "samples", "int", 6, C),
    _e("slices", "samples_max", "int", 48, S),
    _e("slices", "shutter", "float", 0.8, C),
    _e("slices", "shadow", "float", 0.0, S, rng=[0, 1]),
    _e("slices", "shadow_px", "float", 24, C, units="px"),
    # sheets
    _e("sheets", "ease", "str", "linear", S, choices=EASES),
    _e("sheets", "sheets", "list", req=True, item="sheets.sheet"),
    _e("sheets", "angle", "float", 62, S, units="degrees"),
    _e("sheets", "motion", "str", "normal", C, choices=("normal", "lateral")),
    _e("sheets", "feather", "float", 1.5, S, units=PX),
    _e("sheets", "valid_feather", "float", 1, S, units=PX),
    _e("sheets", "overlap_alpha", "float", 1.0, C),
    _e("sheets", "shadow", "float", 0.0, C),
    _e("sheets", "shadow_px", "float", 40, C, units=PX),
    _e("sheets", "shadow_from", "str", "front", C, choices=("front", "all")),
    _e("sheets", "parallax", "float", 0.0, C),
    _e("sheets", "edge_depth", "float", 0.0, C, units=PX),
    _e("sheets", "layer_soft", "float", 0.06, S),
    _e("sheets", "shutter", "float", 0.0, C),
    _e("sheets", "samples_max", "int", 24, C),
    _e("sheets", "objects", "list", item="sheets.object"),
    _e("sheets", "object_feather", "float", 6.0, C, units=PX),
    _e("sheets.sheet", "key", "int", req=True, units="still"),
    _e("sheets.sheet", "name", "str"),
    _e("sheets.sheet", "side", "str", "+", C, choices=("+", "-")),
    _e("sheets.sheet", "width", "float", 0.8, C, units="× the canvas extent"),
    _e("sheets.sheet", "carry", "float", 1.0, C),
    _e("sheets.sheet", "lag", "int", 0, C, units="frames"),
    _e("sheets.sheet", "dur", "int", units="frames"),
    _e("sheets.sheet", "scale", "float", 0.0, C),
    _e("sheets.sheet", "layer", "list", item="float", units="depth, 0 far .. 1 near"),
    _e("sheets.sheet", "layer_y", "list", item="float", units="prep-canvas rows"),
    _e("sheets.sheet", "shadow", "float"),
    _e("sheets.object", "name", "str"),
    _e("sheets.object", "box", "box", req=True, units=PX),
    _e("sheets.object", "lead", "int", 6, S, units="frames"),
    _e("sheets.object", "linger", "int", 10, S, units="frames"),
    _e("sheets.object", "seasons", "list", item="int", units="stills"),
    # repaint (SCHEMA.md, 2026-11-05): `through` as the slices group has its own, since the leg reads no chain key
    _e("repaint", "through", "list", item="int", units="stills"),
    _e("repaint", "front", "float", 0.35, S, units="order units"),
    _e("repaint", "overlap", "float", 0.35, S, units="share of a step"),
    _e("repaint", "zone_erode", "int", 15, S, units=PX),
    # effects
    _e("effect", "kind", "str", req=True, choices=EFFECTS),
    _e("effect.breath", "z", "float", req=True, units="share of the frame"),
    _e("effect.breath", "cx", "float", 0.5, C, units="share of the width"),
    _e("effect.breath", "cy", "float", 0.5, C, units="share of the height"),
    _e("effect.breath", "depth_k", "float", 0.0, C),
    _e("effect.breath", "depth_clip", "float", 0.6, C, units="depth"),
    _e("effect.breath", "ref", "float", 0.0, C, units="depth, 0 far .. 1 near"),
    _e("effect.breath", "ref_at", "point", units=FRACTIONS, roles=["fx", "fy"]),
    _e("effect.breath", "sigma", "float", 3.0, C, units=PX),
    _e("effect.parallax", "amp", "float", req=True, units="share of the width"),
    _e("effect.parallax", "ref", "float", 0.0, C, units="depth, 0 far .. 1 near"),
    _e("effect.parallax", "ref_at", "point", units=FRACTIONS, roles=["fx", "fy"]),
    _e("effect.parallax", "dir", "point", [1, 0], C),
    _e("effect.parallax", "shape", "str", "sin", C, choices=WAVES),
    _e("effect.parallax", "dir2", "point"),
    _e("effect.parallax", "shape2", "str", "pulse", C, choices=WAVES),
    _e("effect.parallax", "amp2", "float", 0.5, C, units="share of amp"),
    _e("effect.parallax", "sigma", "float", 3.0, C, units=PX),
    _e("effect.glow", "box", "box", [0, 0, 1, 1], C, units=FRACTIONS),
    _e("effect.glow", "thr", "float", 235, C, units="grey levels"),
    _e("effect.glow", "sigma", "list", [0.012, 0.05], C, item="float", units="share of the width"),
    _e("effect.glow", "mix", "list", [0.6, 0.4], C, item="float"),
    _e("effect.glow", "gain", "float", 0.15, C),
    _e("effect.glow", "shape", "str", "pulse", C, choices=WAVES),
]
BY_PATH: dict[str, Entry] = {e["path"]: e for e in PLAN_SCHEMA}
BY_GROUP_KEY: dict[tuple[str, str], Entry] = {(e["group"], e["key"]): e for e in PLAN_SCHEMA}


def choices_of(path: str) -> list[Any]:
    """The choices of one entry (validate_plan reads the methods, the eases and the effect kinds here)."""
    return BY_PATH[path]["choices"] or []


def schema_view() -> dict[str, Any]:
    """GET /api/registry's `plan_schema`: the entries, the groups' order and titles, the lists and the date read."""
    return {
        "date": SCHEMA_DATE,
        "source": "scripts/research/plans/loops/SCHEMA.md",
        "entries": PLAN_SCHEMA,
        "groups": [{"group": g, "path": p, "hint": h, "title": t} for g, (p, h, t) in GROUPS.items()],
        "chain_methods": list(CHAIN_METHODS),
    }


# ------------------------------------------------------------------ resolving a path pattern on a plan


def element_groups(list_key: str, element: Any, parent_groups: list[str]) -> list[str]:
    """The groups whose entries describe one element of a list: a hold or a transition of the timeline (its method's
    group first, so an override such as the sheets' ease wins), an effect by its kind, an item by its list's entry."""
    if not isinstance(element, dict):
        return []
    if list_key == "timeline" and "plan" in parent_groups:
        if "to" not in element:
            return ["hold"]
        m = str(element.get("method", "rife"))
        return [m, "transition"] + (["chain"] if m in CHAIN_METHODS else [])
    if list_key == "effects" and "plan" in parent_groups:
        return [f"effect.{element.get('kind')}", "effect"]
    for g in parent_groups:
        e = BY_GROUP_KEY.get((g, list_key))
        if e and e["item"] in GROUPS:
            return [str(e["item"])]
    return []


def entry_for(groups: list[str], key: str) -> Entry | None:
    """The first entry of `key` among `groups` (the order of element_groups)."""
    for g in groups:
        e = BY_GROUP_KEY.get((g, key))
        if e:
            return e
    return None


def _segments(pattern: str) -> list[tuple[str, str | None]]:
    out: list[tuple[str, str | None]] = []
    for seg in pattern.split("."):
        m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?", seg)
        if not m:
            raise ValueError(f"bad path segment {seg!r} in {pattern!r}")
        out.append((m.group(1), m.group(2)))
    return out


def _selected(sel: str, element: dict[str, Any], groups: list[str]) -> bool:
    if sel == "*":
        return True
    k, _, v = sel.partition("=")
    if k in element:
        return str(element[k]) == v
    e = entry_for(groups, k)
    return e is not None and e["default"] is not None and str(e["default"]) == v


def resolve(plan: Any, pattern: str) -> list[tuple[str, Any, bool]]:
    """Every place `pattern` names in `plan` as (JSON pointer, effective value, explicit): an absent key takes its
    entry's default (explicit False); an absent key without a default is not listed."""
    segs = _segments(pattern)
    nodes: list[tuple[str, Any, list[str]]] = [("", plan, ["plan"])]
    out: list[tuple[str, Any, bool]] = []
    for depth, (name, sel) in enumerate(segs):
        last = depth == len(segs) - 1
        nxt: list[tuple[str, Any, list[str]]] = []
        for ptr, obj, groups in nodes:
            if not isinstance(obj, dict):
                continue
            if last and sel is None:
                if name in obj:
                    out.append((f"{ptr}/{name}", obj[name], True))
                else:
                    e = entry_for(groups, name)
                    if e is not None and e["default"] is not None:
                        out.append((f"{ptr}/{name}", e["default"], False))
                continue
            child = obj.get(name)
            if sel is None:
                parent = entry_for(groups, name)
                item = parent["item"] if parent else None
                if isinstance(child, dict) and item:
                    nxt.append((f"{ptr}/{name}", child, [item]))
                continue
            if not isinstance(child, list):
                continue
            for i, el in enumerate(child):
                eg = element_groups(name, el, groups)
                if isinstance(el, dict) and eg and _selected(sel, el, eg):
                    nxt.append((f"{ptr}/{name}/{i}", el, eg))
        nodes = nxt
    return out


# ------------------------------------------------------------------ the checks before a plan is saved


def validate_plan(plan: Any) -> None:
    """Refuses (400) unknown top-level keys, an empty timeline, unknown methods, eases and effect kinds; the three
    lists are the choices of the schema's `timeline[*].method`, `timeline[*].ease` and `effects[*].kind`."""
    if not isinstance(plan, dict):
        raise StudioError("a plan is a JSON object", 400)
    unknown = sorted(k for k in plan if k not in PLAN_KEYS)
    if unknown:
        raise StudioError(f"unknown plan keys {unknown}; the keys are {list(PLAN_KEYS)} (plans/loops/SCHEMA.md)", 400)
    tl = plan.get("timeline")
    if not isinstance(tl, list) or not tl:
        raise StudioError("the plan needs a non-empty timeline", 400)
    methods, eases = choices_of("timeline[*].method"), choices_of("timeline[*].ease")
    for i, st in enumerate(tl):
        if not isinstance(st, dict) or not ("key" in st or "to" in st):
            raise StudioError(f"timeline[{i}] is a hold {{key, hold}} or a transition {{to, n, method, ease}}", 400)
        if "to" in st:
            m = st.get("method", "rife")
            if m not in methods:
                raise StudioError(f"timeline[{i}]: method {m!r} is not one of {methods}", 400)
            e = st.get("ease", "smooth")
            if e not in eases:
                raise StudioError(f"timeline[{i}]: ease {e!r} is not one of {eases}", 400)
    kinds = choices_of("effects[*].kind")
    for i, e in enumerate(plan.get("effects") or []):
        if not isinstance(e, dict) or e.get("kind") not in kinds:
            raise StudioError(f"effects[{i}]: kind is one of {kinds}", 400)
    if "matte" in plan and not isinstance(plan["matte"], dict):
        raise StudioError("matte is an object", 400)
