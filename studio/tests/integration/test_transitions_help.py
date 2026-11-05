"""The real transitions.py, run by the main venv, carries every flag the pair flow's knobs and argv use, with the
registry's choices; the registry copies its help sentences verbatim; the defaults and the ranges are the CLI's and
TransitionSpec.clamp's (read from the module's TCFG and PRESETS in a child of the main venv: the package never imports
the tool)."""

from __future__ import annotations

import json
import re
import subprocess

import pytest

from reveal_studio.registry import pair
from reveal_studio.registry.flows import stage_def

from ..conftest import REPO
from ..test_pair_flow import help_flags

pytestmark = pytest.mark.integration

MAIN_PY = REPO / ".venv/bin/python"
SCRIPT = "transitions.py"
ARGV_FLAGS = ["--out", "--max-long", "--seconds"]
"""The flags runner/argv_pair.py writes beside the knobs' own: --out for both stages, --max-long from draft or
max_long, --seconds for the relation."""

if not MAIN_PY.exists() or not (REPO / SCRIPT).is_file():
    pytest.skip(f"the main venv ({MAIN_PY}) or {SCRIPT} is absent", allow_module_level=True)


def help_text() -> str:
    p = subprocess.run(
        [str(MAIN_PY), SCRIPT, "pair", "--help"], cwd=str(REPO), capture_output=True, text=True, timeout=120
    )
    assert p.returncode == 0, p.stderr
    return p.stdout


def knobs() -> dict[str, dict[str, object]]:
    return {str(k["key"]): k for k in stage_def("pair", "render")["knobs"]}


def test_every_flag_of_the_render_and_the_relation_is_in_pair_help() -> None:
    """Mutation: a knob's flag renamed in the registry (--anchor_falloff for --anchor-falloff) turns this red."""
    flags = help_flags(help_text())
    want = [str(k["flag"]) for k in knobs().values() if k["flag"]] + ARGV_FLAGS
    assert [f for f in want if f not in flags] == []
    assert set(flags) - {"--help"} == set(want)  # every flag of the CLI has a knob or an argv rule


def test_the_choices_are_the_clis() -> None:
    """Mutation: a preset the CLI lacks, or the empty class choice dropped, turns this red."""
    usage = " ".join(help_text().split("positional arguments")[0].split())
    for flag, key in (
        ("--preset", "preset"),
        ("--canvas", "canvas"),
        ("--class", "force_class"),
        ("--camera", "camera"),
    ):
        m = re.search(rf"\[{re.escape(flag)} \{{([^}}]*)\}}", usage)
        assert m, flag
        assert m.group(1).split(",") == knobs()[key]["choices"], flag


def test_the_registry_copies_the_help_sentences() -> None:
    """A knob's sentence starts with the CLI's own where the help has one. Mutation: a sentence reworded away from the
    help (the hint then says something the script does not) turns this red."""
    flags = help_flags(help_text())
    for key, k in knobs().items():
        said = flags.get(str(k["flag"])) if k["flag"] else None
        if said:
            assert " ".join(str(k["what"]).split()).startswith(said), key
    assert " ".join(str(knobs()["max_long"]["what"]).split()).startswith(flags["--max-long"])


def test_the_defaults_and_the_ranges_are_the_tools() -> None:
    """Mutation: a range not stated by clamp, a default that differs from the CLI's (fps 25), or a preset added to the
    registry turns this red."""
    keys = {
        "fps": "c['fps']",
        "seconds": "[c['min_seconds'], c['max_seconds']]",
        "zoom": "list(c['zoom_range'])",
        "classb_zoom": "c['classb_zoom']",
        "falloff": "c['anchor_falloff']",
        "falloff_max": "c['anchor_falloff_max']",
        "presets": "list(t.PRESETS)",
    }
    code = (
        "import json, transitions as t; c = t.TCFG; print(json.dumps({"
        + ", ".join(f"'{k}': {v}" for k, v in keys.items())
        + "}))"
    )
    p = subprocess.run([str(MAIN_PY), "-c", code], cwd=str(REPO), capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    t = json.loads(p.stdout.strip().splitlines()[-1])
    k = knobs()
    assert (k["fps"]["default"], k["seconds"]["range"], k["zoom"]["range"]) == (t["fps"], t["seconds"], t["zoom"])
    assert (k["zoom"]["default"], k["anchor_falloff"]["default"]) == (t["classb_zoom"], t["falloff"])
    assert k["anchor_falloff"]["range"] == [0.0, t["falloff_max"]]
    assert (k["color"]["range"], k["warp"]["range"]) == ([0.0, 1.0], [0.0, 1.0])  # clamp: min(1, max(0, x))
    assert t["presets"] == pair.PRESETS and k["seconds"]["default"] == 1.0 and k["color"]["default"] == 0.7
