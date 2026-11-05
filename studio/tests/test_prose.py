"""Every sentence the page shows from the registry passes the no-slop checker without a BLOCK finding."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from reveal_studio.registry.hints import HINTS
from reveal_studio.registry.loop import FLOWS, LOOP_STAGES

from .conftest import REPO

CHECKER = REPO / ".claude/skills/no-slop/scripts/slop-check.py"


def sentences() -> list[str]:
    """Every hint, every stage and flow sentence, and every knob sentence: one paragraph each."""
    out = [h["what"] for h in HINTS.values()]
    out += [s["what"] for s in LOOP_STAGES]
    out += [f["what"] for f in FLOWS.values()]
    out += [k["what"] for s in LOOP_STAGES for k in s["knobs"]]
    return out


@pytest.mark.skipif(not CHECKER.is_file(), reason=f"the no-slop checker is absent at {CHECKER}")
def test_no_registry_sentence_blocks_the_prose_checker(tmp_path: Path) -> None:
    text = tmp_path / "registry_sentences.md"
    text.write_text("\n\n".join(sentences()) + "\n")
    p = subprocess.run(
        [sys.executable, "-I", str(CHECKER), "--json", "--profile", "file", str(text)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    findings = json.loads(p.stdout or "[]")
    for f in findings:
        if f["severity"] != "BLOCK":
            print(f"advisory {f['check']} line {f['line']}: {f['excerpt']}")
    blocks = [f for f in findings if f["severity"] == "BLOCK"]
    assert not blocks, blocks
    assert p.returncode == 0, p.stderr
