"""The real loop_seq.py, run by the main venv, carries every flag the registry's knobs and the runner's argv use."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from reveal_studio.config import resolve_settings
from reveal_studio.registry.loop import LOOP_STAGES
from reveal_studio.runner.argv import ScriptFlags, probe_script_flags

from ..conftest import REPO, free_port

pytestmark = pytest.mark.integration

MAIN_PY = REPO / ".venv/bin/python"
SCRIPT = "scripts/research/loop_seq.py"
# The flags argv_for writes beside the knobs' own, per subcommand (runner/argv.py, 2026-11-05).
ARGV_FLAGS = {
    "prep": ["--out"],
    "readers": ["--out"],
    "probe": ["--out"],  # agent E, A2 (2026-11-05): the probe and measure branches of argv_for
    "measure": ["--out", "--frames-json"],
    "render": ["--out", "--fps", "--draft", "--set", "--progress", "--frames"],
    "page": ["--root", "--out", "--order", "--title", "--intro", "--footer", "--notes"],
}

if not MAIN_PY.exists() or not (REPO / SCRIPT).is_file():
    pytest.skip(f"the main venv ({MAIN_PY}) or {SCRIPT} is absent", allow_module_level=True)


def help_of(*sub: str) -> str:
    p = subprocess.run(
        [str(MAIN_PY), SCRIPT, *sub, "--help"], cwd=str(REPO), capture_output=True, text=True, timeout=120
    )
    assert p.returncode == 0, p.stderr
    return p.stdout


@pytest.mark.parametrize("stage", [s for s in LOOP_STAGES if s["kind"] == "script"], ids=lambda s: s["name"])
def test_every_flag_of_a_stage_is_in_its_subcommands_help(stage: dict[str, object]) -> None:
    sub = str(stage["backend"]).split()[1]
    h = help_of(sub)
    knob_flags = [k["flag"] for k in stage["knobs"] if k["flag"]]
    for flag in [*knob_flags, *ARGV_FLAGS[sub]]:
        # 2026-11-05 (the Fable review's F8): a whole-word match, so `--window` no longer passes against a help that
        # lists only `--windows`; the mutation that turns it red is a flag renamed by a suffix in the registry.
        assert re.search(rf"(^|\s){re.escape(flag)}(\s|$|,)", h, re.M), f"loop_seq.py {sub} --help lacks {flag}"


def test_the_three_script_flags_are_there(tmp_path: Path) -> None:
    assert "--progress" in help_of("render") and "--frames" in help_of("render")
    assert "readers" in help_of()
    settings = resolve_settings(root=REPO, port=free_port(), lock=tmp_path / "lock", open_browser=False, env={})
    assert probe_script_flags(settings) == ScriptFlags(progress=True, frames=True, readers=True)
