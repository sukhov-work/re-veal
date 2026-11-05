"""The registry: stage and knob shapes, the hints table and the page's hint rule, the plan schema as data and its lists,
the resolver the rulings use, and the rulings table's shape."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from reveal_studio.errors import StudioError
from reveal_studio.registry import loop
from reveal_studio.registry.entries import merge_hints
from reveal_studio.registry.flows import ALL_FLOWS, FLOWS, STAGE_NAMES, stage_def, stage_order
from reveal_studio.registry.hints import HINTS, LOOP_HINTS
from reveal_studio.registry.hints_director import HINTS as DIRECTOR_HINTS
from reveal_studio.registry.hints_pair import HINTS as PAIR_HINTS
from reveal_studio.registry.loop import LOOP_STAGES, STAGE_ORDER
from reveal_studio.registry.rulings import RULINGS, Ruling, is_stage_knob
from reveal_studio.registry.schema import (
    BY_PATH,
    EASES,
    EFFECTS,
    GROUPS,
    METHODS,
    PLAN_KEYS,
    PLAN_SCHEMA,
    TYPES,
    VERDICTS,
    element_groups,
    resolve,
    schema_view,
)

from .conftest import REPO

WEB = Path(__file__).resolve().parents[1] / "src" / "reveal_studio" / "web"

# The lists as scripts/research/plans/loops/SCHEMA.md and loop_seq.py's EASES and method branches name them on
# 2026-11-05 (SCHEMA.md lists rife..rewind, slices, sheets; loop_seq.py's render also dispatches snap, slide, rise;
# its EASES dict holds accel3 and sine beside the five SCHEMA.md names). Phase B added repaint, a leg with its own
# SCHEMA.md section. Mutation: repaint dropped from METHODS turns this red, and validate_plan refuses a repaint step.
SCHEMA_METHODS_2026_11_05 = [
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
]
SCHEMA_EASES_2026_11_05 = ["linear", "smooth", "snap", "accel", "accel3", "decel", "sine"]
SCHEMA_EFFECTS_2026_11_05 = ["breath", "parallax", "glow"]

# 85 keys: the A1 build shipped 86; the Fable review's low finding removed `chip.queued` (a state never written).
A1_HINT_COUNT = 85
HINT_PREFIXES = ("plan.", "measure.", "prep.", "readers.", "chip.", "region.", "control.")

# The keys loop_seq.py reads that SCHEMA.md does not list (the editor shows them under "other keys"); read from the
# frozen plans and loop_seq.py's frames_teleport on 2026-11-05.
UNDOCUMENTED_2026_11_05 = {"teleport": {"rest", "flash", "flash_gain"}}


LOOP_ORDER_2026_11_05 = [
    "import",
    "registration",
    "readers",
    "probe",
    "plan",
    "render",
    "measure",
    "skeptic",
    "page",
    "grades",
]
# 290 rows on 2026-11-05 (85 at the port, 145 for the plan keys and the editor, 37 for the views, 23 for the fix
# round), the two still-count chips of phase B's slice (chip.above_6, chip.above_10) and the four keys of its repaint
# leg (plan.timeline.repaint.through, front, overlap, zone_erode).
LOOP_HINT_COUNT = 296


def test_the_loop_flow_has_its_stages_in_order() -> None:
    # A1's eight stages; agent E's A2 build added probe after readers and measure after render (2026-11-05). The slice
    # of phase B moved the flow table to registry/flows.py: the loop is the first flow and enabled. Mutation: a loop
    # stage reordered, or the loop entry dropped from the enabled flows, turns this red.
    assert STAGE_ORDER == stage_order("loop") == LOOP_ORDER_2026_11_05
    assert ALL_FLOWS["loop"] is loop.FLOW and next(iter(ALL_FLOWS)) == "loop" and "loop" in FLOWS
    assert loop.FLOW["stages"] is LOOP_STAGES and loop.FLOW["enabled"] is True
    assert loop.FLOW["what"].strip()
    assert STAGE_NAMES[: len(STAGE_ORDER)] == STAGE_ORDER  # the union the page reads starts with the loop's ten


def test_every_loop_script_stage_names_its_script_and_identity() -> None:
    """The Runner hashes the stage's own script and reads the "unchanged" files from the stage. Mutation: dropping
    `identity` from the render stage (or naming loop.gif there) turns this red, and test_runner's unchanged test too."""
    ident = {s["name"]: s["identity"] for s in LOOP_STAGES if s["kind"] == "script"}
    assert ident == {
        "registration": ["*.png", "*.npy"],
        "readers": ["readers.json"],
        "probe": [],
        "render": ["loop.mp4"],
        "measure": [],
        "page": [],
    }
    assert {s["script"] for s in LOOP_STAGES if s["kind"] == "script"} == {"loop_seq"}
    assert all("script" not in s and "identity" not in s for s in LOOP_STAGES if s["kind"] != "script")


@pytest.mark.parametrize("stage", LOOP_STAGES, ids=lambda s: s["name"])
def test_every_stage_has_its_fields(stage: dict[str, object]) -> None:
    for key in ("name", "title", "kind", "optional", "terminal", "knobs", "what"):
        assert key in stage, key
    assert stage["kind"] in ("builtin", "script", "request")
    assert isinstance(stage["what"], str) and len(stage["what"]) > 20
    if stage["kind"] == "script":
        assert str(stage["backend"]).startswith("loop_seq.py ")
        assert isinstance(stage["terminal"], str) and "." in stage["terminal"]
    else:
        assert stage["terminal"] is None


@pytest.mark.parametrize("knob", [k for s in LOOP_STAGES for k in s["knobs"]], ids=lambda k: k["key"])
def test_every_knob_carries_what_its_popover_shows(knob: dict[str, object]) -> None:
    # The page builds a knob's popover from the knob itself (data-knob), not from HINTS: key, flag, what, default,
    # range, type. So every knob needs a sentence, and no loop knob states a range (none is stated by the script).
    assert set(knob) == {"key", "type", "default", "what", "flag", "choices", "range"}
    assert knob["type"] in ("int", "float", "bool", "str", "plan", "list")
    assert isinstance(knob["what"], str) and len(knob["what"]) > 10
    assert knob["range"] is None
    assert knob["flag"] is None or str(knob["flag"]).startswith("--")


def test_knob_flags_are_unique_per_stage() -> None:
    for s in LOOP_STAGES:
        flags = [k["flag"] for k in s["knobs"] if k["flag"]]
        assert len(flags) == len(set(flags)), s["name"]


def test_the_page_stage_has_the_variants_knob() -> None:
    # backlog T76: a list of full render names, empty by default (every full render in name order, no flag).
    k = {k["key"]: k for k in stage_def("loop", "page")["knobs"]}["variants"]
    assert (k["type"], k["default"], k["flag"]) == ("list", [], "--variants")


def test_the_hints_table_holds_the_a1_keys_each_with_a_sentence() -> None:
    # The prefixes are the loop's; another flow's table may add its own (a pair's `report.`, a director's `info.`).
    assert len(HINTS) >= A1_HINT_COUNT
    assert all(key.startswith(HINT_PREFIXES) for key in LOOP_HINTS), [
        k for k in LOOP_HINTS if not k.startswith(HINT_PREFIXES)
    ]
    for key, h in HINTS.items():
        assert isinstance(h["what"], str) and h["what"].strip(), key
        assert set(h) <= {"what", "default", "range", "stage", "source"}, key
        if "stage" in h:
            assert h["stage"] in STAGE_NAMES, key


def test_the_hint_tables_are_disjoint_and_merged_into_one() -> None:
    """HINTS is the loop's rows and each flow's, every key once. Mutation: a key added to hints_pair.py that the loop
    already holds fails the import (merge_hints raises); a merge that dropped a table turns the count red."""
    assert len(LOOP_HINTS) == LOOP_HINT_COUNT
    assert len(HINTS) == len(LOOP_HINTS) + len(PAIR_HINTS) + len(DIRECTOR_HINTS)
    assert set(HINTS) == set(LOOP_HINTS) | set(PAIR_HINTS) | set(DIRECTOR_HINTS)
    assert all(HINTS[k] is LOOP_HINTS[k] for k in LOOP_HINTS)
    with pytest.raises(ValueError, match=r"hint keys in two flows' tables: \['chip.done'\]"):
        merge_hints({"chip.done": {"what": "a"}}, {"chip.done": {"what": "b"}})


def _page_hint_keys() -> set[str]:
    """Every literal hint key in the page's files: data-hint attributes and quoted keys passed to hintBtn or tables."""
    keys: set[str] = set()
    texts = [(WEB / "index.html").read_text(), *(p.read_text() for p in sorted((WEB / "js").glob("*.js")))]
    for t in texts:
        keys |= set(re.findall(r'data-hint="([^"+]+)"', t))
        keys |= set(re.findall(r"'((?:plan|measure|prep|readers|chip|region|control)\.[^']+)'", t))
    return keys


def test_every_literal_hint_key_of_the_page_is_in_the_table() -> None:
    keys = _page_hint_keys()
    assert len(keys) >= 60  # the scan finds the page's keys (62 on 2026-11-05), so an empty result cannot pass
    missing = sorted(k for k in keys if k not in HINTS)
    assert not missing, f"the page asks for hints the table lacks: {missing}"


def _chip_key(text: str, words: list[str]) -> str:
    """core.js chipKey: a parenthesis and a progress fraction dropped; a leading state word kept alone."""
    t = re.sub(r" \d+/\d+.*$", "", re.sub(r" \(.*$", "", text)).strip()
    return "chip." + (t.split(" ")[0] if t.split(" ")[0] in words else t)


def test_every_chip_text_of_the_page_resolves_to_a_hint_row() -> None:
    """A chip with no row shows no hint and nothing says so (Fable review F2). Each literal chip text without an
    explicit key, each state word chipKey keeps alone and each state stateClass colours has a row. Mutation: deleting
    the row chip.adopted, or a new chip('<text>') without its row, turns this red."""
    core = (WEB / "js" / "core.js").read_text()
    m = re.search(r"const CHIP_WORDS=\[([^\]]*)\]", core)
    assert m, "core.js defines CHIP_WORDS"
    words = re.findall(r"'([^']+)'", m.group(1))
    s = re.search(r"function stateClass\(st\)\{return \(\{(.*?)\}\)", core)
    assert s, "core.js defines stateClass"
    states = re.findall(r"'?([a-z][a-z ]*)'?:'(?:ok|run|bad|info)'", s.group(1))
    literals: set[str] = set()
    for p in sorted((WEB / "js").glob("*.js")):
        literals |= set(re.findall(r"chip\('([^'+]+)'(?:,'[^']*')?\)", p.read_text()))
    # the scans find something (2026-11-05: 6 words, 14 states, 14 literal texts), so an empty result cannot pass
    assert len(words) >= 5 and len(states) >= 12 and len(literals) >= 12
    keys = {f"chip.{w}" for w in words} | {f"chip.{x}" for x in states} | {_chip_key(x, words) for x in literals}
    missing = sorted(k for k in keys if k not in HINTS)
    assert not missing, f"chips whose hint key has no row: {missing}"


def test_stage_hints_come_from_the_stage_sentence() -> None:
    core = (WEB / "js" / "strip.js").read_text()
    # stageHint() writes hints['stage.<name>'] from the stage view's `what`; hintBtn('stage.'+s.name) reads it.
    assert "S.reg.hints['stage.'+name]={what:s.what" in core
    panels = (WEB / "js" / "inspector.js").read_text()
    assert "data-hint=\"knob.'+esc(s.name)+'.'+esc(k.key)+'\" data-knob=" in panels


def test_the_schema_lists_match_schema_md() -> None:
    assert list(METHODS) == SCHEMA_METHODS_2026_11_05
    assert list(EASES) == SCHEMA_EASES_2026_11_05
    assert list(EFFECTS) == SCHEMA_EFFECTS_2026_11_05
    assert list(PLAN_KEYS) == [
        "seq",
        "in",
        "title",
        "gag",
        "timeline",
        "effects",
        "matte",
        "crf",
        "gif_long",
        "crop",
        "provenance",
    ]
    assert VERDICTS == ("READY", "READY WITH A NOTE", "NOT READY")


def test_the_schema_entries_carry_the_lists_validate_plan_reads() -> None:
    # The method, ease and effect-kind choices of the schema are the dated lists (validate_plan reads them there).
    assert BY_PATH["timeline[*].method"]["choices"] == SCHEMA_METHODS_2026_11_05
    assert BY_PATH["timeline[*].ease"]["choices"] == SCHEMA_EASES_2026_11_05
    assert BY_PATH["effects[*].kind"]["choices"] == SCHEMA_EFFECTS_2026_11_05


@pytest.mark.parametrize("entry", PLAN_SCHEMA, ids=lambda e: e["path"])
def test_every_schema_entry_is_complete(entry: dict[str, Any]) -> None:
    assert entry["type"] in TYPES
    assert "default" in entry  # a value or None (null: no single value for an absent key)
    assert entry["hint"] in HINTS, f"{entry['hint']} has no sentence in registry/hints.py"
    assert entry["group"] in GROUPS and entry["path"] == GROUPS[entry["group"]][0] + entry["key"]
    assert (entry["default"] is None) == (entry["default_from"] is None)
    assert entry["default_from"] in (None, "SCHEMA.md", "loop_seq.py")
    assert not (entry["required"] and entry["default"] is not None), "a required key has no default"
    if entry["type"] == "list":
        assert entry["item"] in ("int", "float", "str") or entry["item"] in GROUPS, entry["item"]
    if entry["type"] in ("box", "point"):
        assert len(entry["roles"] or []) == (4 if entry["type"] == "box" else 2)
    if entry["choices"] is not None and entry["default"] is not None:
        assert entry["default"] in entry["choices"]
    h = HINTS[entry["hint"]]
    if "default" in h:  # a sentence that states a default states the schema's
        assert h["default"] == entry["default"], entry["hint"]
    if entry["range"] is not None:  # SCHEMA.md states one range only: the slices' shadow, 0–1
        assert (entry["path"], entry["range"]) == ("timeline[method=slices].shadow", [0, 1])


def test_the_schema_paths_are_unique_and_the_view_serves_them() -> None:
    assert len(BY_PATH) == len(PLAN_SCHEMA) == 155  # 151 on 2026-11-05 and the repaint leg's 4 of phase B
    v = schema_view()
    assert (v["date"], v["source"]) == ("2026-11-05", "scripts/research/plans/loops/SCHEMA.md")
    assert v["entries"] is PLAN_SCHEMA and [g["group"] for g in v["groups"]] == list(GROUPS)


def test_the_resolver_fills_an_absent_key_from_its_default() -> None:
    plan = {
        "timeline": [
            {"key": 0, "hold": 4},
            {"to": 1, "n": 3, "method": "slide", "box_a": [0, 0, 1, 1], "box_b": [0, 0, 1, 1]},
            {"to": 0, "n": 90, "method": "sheets", "sheets": [{"key": 1}, {"key": 2, "carry": 0}]},
            {"to": 1, "n": 2},
        ],
        "effects": [{"kind": "breath", "z": 0.02}],
    }
    assert resolve(plan, "timeline[method=slide].mode") == [("/timeline/1/mode", "fly", False)]
    assert resolve(plan, "timeline[*].method") == [
        ("/timeline/1/method", "slide", True),
        ("/timeline/2/method", "sheets", True),
        ("/timeline/3/method", "rife", False),  # a transition without a method is rife; a hold has no method
    ]
    assert resolve(plan, "timeline[method=sheets].sheets[*].carry") == [
        ("/timeline/2/sheets/0/carry", 1.0, False),
        ("/timeline/2/sheets/1/carry", 0, True),
    ]
    assert resolve(plan, "timeline[method=sheets].ease") == [("/timeline/2/ease", "linear", False)]  # the override
    assert resolve(plan, "timeline[method=rife].ease") == [("/timeline/3/ease", "smooth", False)]
    assert resolve(plan, "effects[kind=breath].cx") == [("/effects/0/cx", 0.5, False)]
    assert resolve(plan, "matte.thr") == []  # no matte object in the plan: nothing to name
    assert resolve({**plan, "matte": {}}, "matte.thr") == [("/matte/thr", 14, False)]
    assert element_groups("timeline", {"to": 1, "method": "dissolve"}, ["plan"]) == ["dissolve", "transition", "chain"]


CODE_ONLY_KNOBS = {"timeline[method=teleport].flash": "loop_seq.py frames_teleport, read but not in SCHEMA.md"}
"""Ruled plan keys that loop_seq.py reads and SCHEMA.md does not list, so the schema has no entry for them (moved here
from registry/rulings.py on 2026-11-05: this test was its only reader)."""


def test_the_rulings_table_has_its_shape_and_every_knob_names_something() -> None:
    assert set(Ruling.__annotations__) == {"knob", "value", "since", "why", "source"}
    assert len(RULINGS) == 7
    knobs = {f"{s['name']}.{k['key']}" for s in LOOP_STAGES for k in s["knobs"]}
    for r in RULINGS:
        assert set(r) == set(Ruling.__annotations__), r
        assert re.fullmatch(r"2026-1[01]-\d\d", r["since"]), r
        assert r["source"].startswith("DECISIONS 2026-") and "loops.md §" in r["source"], r
        assert r["why"].strip().endswith("."), r
        if is_stage_knob(r["knob"]):
            assert r["knob"] in knobs, r["knob"]
        else:  # a schema path, or a key loop_seq.py reads that SCHEMA.md does not list
            assert r["knob"] in BY_PATH or r["knob"] in CODE_ONLY_KNOBS, r["knob"]


def test_every_plan_key_has_a_hint() -> None:
    for key in PLAN_KEYS:
        assert f"plan.{key}" in HINTS, key


def test_stage_def_finds_a_stage_and_refuses_an_unknown_one() -> None:
    assert stage_def("loop", "render")["terminal"] == "measure.json"
    with pytest.raises(StudioError) as e:
        stage_def("loop", "warp")
    assert e.value.code == 404
    with pytest.raises(StudioError, match="no flow 'align'") as e2:
        stage_def("align", "render")
    assert e2.value.code == 404


@pytest.mark.integration
def test_the_schema_covers_every_key_of_the_frozen_plans() -> None:
    """Every key of the 49 frozen plans of the real tree is a schema entry or one of the listed undocumented keys."""
    plans = sorted((REPO / "scripts/research/plans/loops").glob("*.json"))
    if not plans:
        pytest.skip("the real tree's frozen plans are absent")
    pairs = {(e["group"], e["key"]) for e in PLAN_SCHEMA}
    gaps: set[str] = set()
    for p in plans:
        plan = json.loads(p.read_text())
        gaps |= {f"plan.{k}" for k in plan if k not in BY_PATH and k not in ("timeline", "effects")}
        gaps |= {f"matte.{k}" for k in plan.get("matte", {}) if f"matte.{k}" not in BY_PATH}
        for st in plan["timeline"]:
            groups = element_groups("timeline", st, ["plan"])
            undocumented = UNDOCUMENTED_2026_11_05.get(str(st.get("method")), set())
            for k, v in st.items():
                if not any((g, k) in pairs for g in groups) and k not in undocumented:
                    gaps.add(f"{groups[0]}.{k}")
                if isinstance(v, list) and v and isinstance(v[0], dict):  # local, sheets, objects: their items' keys
                    item_group = (element_groups(k, v[0], groups) or [k])[0]
                    gaps |= {f"{item_group}.{ik}" for item in v for ik in item if (item_group, ik) not in pairs}
        for e in plan.get("effects", []):
            groups = element_groups("effects", e, ["plan"])
            gaps |= {f"{groups[0]}.{k}" for k in e if not any((g, k) in pairs for g in groups)}
    assert not gaps, f"keys of the frozen plans the schema lacks: {sorted(gaps)}"


def test_the_loop_registers_a_panel_for_each_of_its_stages_in_flow_ui() -> None:
    """The page picks a stage's panel from FLOW_UI[flow].panels (core.js); each loop script registers its own at
    load. Mutation: a dropped registration (the stage then shows the plain panel: its sentence only) or a loop panel
    registered under another flow turns this red."""
    js = {p.stem: p.read_text() for p in (WEB / "js").glob("*.js")}
    assert "const FLOW_UI={};" in js["core"]
    names: list[str] = []
    for text in js.values():
        for block in re.findall(r"Object\.assign\(flowEntry\('loop'\)\.panels,\{([^}]*)\}\)", text):
            names += re.findall(r"([a-z]+):panel[A-Z]", block)
        names += re.findall(r"flowEntry\('loop'\)\.panels\.([a-z]+)=panel[A-Z]", text)
    assert sorted(names) == sorted(STAGE_ORDER)
    for key in ("wire:wireLoop", "candRow:candRow", "sources:loopSources", "plots:drawPlots", "newJob:openLoopForm"):
        assert any(key in text for text in js.values()), key
    assert "flowEntry('loop').measures=loopMeasures" in js["inspector"] and "flowEntry('loop').graph=" in js["graph"]
    assert "flowEntry('pair')" in js["pair"] and "flowEntry('director')" in js["director"]


def _digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


# The loop's registry rows on 2026-11-05, pinned by the slice of phase B before its first edit (in
# tests/test_loop_snapshot.py then, moved here so a loop builder updates them with the loop counts): the stages without
# the two keys the slice added, the hints without its two chips, the plan schema and the rulings. Phase B's repaint leg
# moved two digests on purpose: the hints (290 to 294: its four keys, and repaint named in plan.timeline.method's
# sentence; then the main thread's five flow-neutral rewordings of 2026-11-05: region.viewer, chip.tag, control.render,
# control.candidate, chip.above_6, digest 164bc46d1a2b4bb2; then the phase B fix round's copy pass, ten rows split
# or cleaned with their facts kept: region.inspector, region.viewer, region.axis, control.page, control.render and
# prep.windows_jpg under 40 words a sentence, plan.timeline.slide.mode and .fill split at their semicolons, chip.within
# and chip.past bar without the inline "(loops.md §6)"; digest 9af43c6c9d8c8c39)
# sentence) and the schema (151 to 155 entries, digest d9bdc86dd439f099 before); the stages and the rulings held.
LOOP_REGISTRY_2026_11_05 = {
    "stages": "83b7f497d40f9380",
    "hints": "9af43c6c9d8c8c39",
    "hint_count": 294,
    "schema": "28130182bcbb2232",
    "schema_rows": 155,
    "rulings": "b533b58ecedcb25e",
    "rulings_rows": 7,
}


def test_the_loop_registry_rows_keep_their_digests() -> None:
    """Mutation: one character of a loop knob's sentence, a hint, a schema default or a ruling turns this red; a loop
    builder who changes a row on purpose updates the digest here with the loop counts."""
    stages = [{k: v for k, v in s.items() if k not in ("script", "identity")} for s in LOOP_STAGES]
    hints = {k: v for k, v in LOOP_HINTS.items() if k not in ("chip.above_6", "chip.above_10")}
    assert {
        "stages": _digest(stages),
        "hints": _digest(hints),
        "hint_count": len(hints),
        "schema": _digest(PLAN_SCHEMA),
        "schema_rows": len(PLAN_SCHEMA),
        "rulings": _digest(RULINGS),
        "rulings_rows": len(RULINGS),
    } == LOOP_REGISTRY_2026_11_05
