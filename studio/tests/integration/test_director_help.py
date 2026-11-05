"""The real director_render.py and director_page.py, run by the main venv, carry every flag the director flow's knobs
and argv use; the fakes of tests/fakes/ print the same --help, so the unit layer's argv is the real one's."""

from __future__ import annotations

import re
import subprocess
import sys

import pytest

from reveal_studio.registry.flows import stage_def

from ..conftest import FAKES, REPO

pytestmark = pytest.mark.integration

MAIN_PY = REPO / ".venv/bin/python"
RENDER, PAGE = "scripts/research/director_render.py", "scripts/research/director_page.py"
ARGV_FLAGS = {
    "resolve": ["--resolve-only", "--max-long", "--layers-dir", "--mattes-dir"],
    "render": ["--max-long", "--progress", "--layers-dir", "--mattes-dir"],
    "page": ["--notes"],
}
"""The flags runner/argv_director.py writes beside the knobs' own (2026-11-05)."""

if not MAIN_PY.exists() or not (REPO / RENDER).is_file() or not (REPO / PAGE).is_file():
    pytest.skip(f"the main venv ({MAIN_PY}) or the director scripts are absent", allow_module_level=True)


def help_of(python: str, script: str, cwd: str) -> str:
    p = subprocess.run([python, script, "--help"], cwd=cwd, capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    return p.stdout


def flags(h: str) -> set[str]:
    return set(re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", h))


@pytest.mark.parametrize("stage", ["resolve", "render", "page"])
def test_every_flag_of_a_stage_is_in_its_scripts_help(stage: str) -> None:
    """Mutation: a knob's flag renamed in the registry (--max_long), or an argv flag the script lacks, turns this
    red."""
    s = stage_def("director", stage)
    h = help_of(str(MAIN_PY), RENDER if s["script"] == "director_render" else PAGE, str(REPO))
    want = [str(k["flag"]) for k in s["knobs"] if k["flag"]] + ARGV_FLAGS[stage]
    assert [f for f in want if f not in flags(h)] == []


def test_the_render_and_resolve_use_every_flag_of_the_renderer() -> None:
    """Every flag of director_render.py has a knob or an argv rule. Mutation: a renderer flag the studio never passes
    (a new --frames) turns this red until the registry names it."""
    h = help_of(str(MAIN_PY), RENDER, str(REPO))
    used = {str(k["flag"]) for st in ("resolve", "render") for k in stage_def("director", st)["knobs"] if k["flag"]}
    used |= set(ARGV_FLAGS["resolve"]) | set(ARGV_FLAGS["render"])
    assert flags(h) - {"--help"} == used


@pytest.mark.parametrize(("script", "fake"), [(RENDER, "director_render.py"), (PAGE, "director_page.py")])
def test_the_fakes_print_the_real_help(script: str, fake: str) -> None:
    """The unit layer's fakes parse the real flags. Mutation: a flag added to the real script and not to its fake
    (the unit tests then pass an argv the real script refuses) turns this red."""
    real = help_of(str(MAIN_PY), script, str(REPO))
    mine = help_of(sys.executable, str(FAKES / fake), str(FAKES))
    assert mine == real
