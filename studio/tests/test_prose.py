"""Every sentence the page shows from the registry passes the no-slop checker without a BLOCK finding: at the checker's
60 words for every sentence, and at 40 words (the phase B critique's copy pass) for the hints and the phase B flows'
stage, knob and `--set` sentences. The loop's stage and knob sentences keep the 60-word bar: the loop's snapshot test
pins their digest, and that test is never regenerated."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from reveal_studio.registry.common import COMMON_STAGES
from reveal_studio.registry.director import SET_KEYS
from reveal_studio.registry.flows import ALL_FLOWS
from reveal_studio.registry.hints import HINTS

from .conftest import REPO

CHECKER = REPO / ".claude/skills/no-slop/scripts/slop-check.py"


def set_texts() -> list[str]:
    """The `--set` table's own texts the director's plan panel prints beside each key: the condition the renderer reads
    it under, the reason a key is read-only, and where its default comes from (Fable review F6)."""
    return [r[k] for r in SET_KEYS for k in ("when", "readonly", "default_from") if r[k]]


def sentences() -> list[str]:
    """Every hint, every stage and flow sentence of every flow (the disabled ones and the shared stages included),
    every knob sentence and the `--set` table's texts: one paragraph each."""
    stages = [s for f in ALL_FLOWS.values() for s in f["stages"]] + list(COMMON_STAGES.values())
    out = [h["what"] for h in HINTS.values()]
    out += [s["what"] for s in stages]
    out += [f["what"] for f in ALL_FLOWS.values()]
    out += [k["what"] for s in stages for k in s["knobs"]]
    return out + set_texts()


def short_sentences() -> list[str]:
    """The sentences held to 40 words: every hint, every flow sentence, the stage and knob sentences of the flows
    other than the loop and of the shared stages, and the `--set` table's texts."""
    stages = [s for n, f in ALL_FLOWS.items() if n != "loop" for s in f["stages"]] + list(COMMON_STAGES.values())
    out = [h["what"] for h in HINTS.values()] + [f["what"] for f in ALL_FLOWS.values()]
    out += [s["what"] for s in stages] + [k["what"] for s in stages for k in s["knobs"]]
    return out + set_texts()


def blocks(tmp_path: Path, texts: list[str], max_sentence: int) -> list[dict[str, object]]:
    text = tmp_path / f"registry_sentences_{max_sentence}.md"
    text.write_text("\n\n".join(texts) + "\n")
    p = subprocess.run(
        [
            sys.executable,
            "-I",
            str(CHECKER),
            "--json",
            "--profile",
            "file",
            "--max-sentence",
            str(max_sentence),
            str(text),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    findings = json.loads(p.stdout or "[]")
    for f in findings:
        if f["severity"] != "BLOCK":
            print(f"advisory {f['check']} line {f['line']}: {f['excerpt']}")
    out = [f for f in findings if f["severity"] == "BLOCK"]
    assert out or p.returncode == 0, p.stderr
    return out


@pytest.mark.skipif(not CHECKER.is_file(), reason=f"the no-slop checker is absent at {CHECKER}")
def test_no_registry_sentence_blocks_the_prose_checker(tmp_path: Path) -> None:
    """Mutation: a `--set` row's condition with a hedge ("should work") or over 60 words turns this red (the `when`,
    `readonly` and `default_from` texts passed no check before, Fable review F6)."""
    found = blocks(tmp_path, sentences(), 60)
    assert not found, found


@pytest.mark.skipif(not CHECKER.is_file(), reason=f"the no-slop checker is absent at {CHECKER}")
def test_no_hint_or_phase_b_sentence_runs_over_40_words(tmp_path: Path) -> None:
    """The phase B critique's copy pass read five sentences over 40 words on the page (region.viewer 54, region.axis
    48, region.inspector 45, the director skeptic stage 44, control.render 43). Mutation: one of them put back turns
    this red."""
    found = blocks(tmp_path, short_sentences(), 40)
    assert not found, found
