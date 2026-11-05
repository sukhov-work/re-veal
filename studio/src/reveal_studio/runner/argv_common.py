"""The argv of the stages more than one flow shares (registry/common.py): Reveal's verdict.

`reveal.py align A B --out <job>/verdict.part`, the strict reshot profile as the workbench ran it
(scripts/research/director_ui.py:430-446): A and B are the job's two linked photos, the inputs their sha256s. The
verdict folder sits in the job folder, beside the pair's relation and outside a director's run/ folder.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, rel
from reveal_studio.runner.argv import Argv, ScriptFlags, script_rel


def argv_verdict(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    by = {i.get("role"): i for i in job.get("inputs") or []}
    if "A" not in by or "B" not in by:
        raise StudioError("Reveal's verdict needs the job's two photos, A and B", 409)
    a, b = by["A"], by["B"]
    out_final, out_part = d / "verdict", d / "verdict.part"
    argv = [
        str(settings.python),
        script_rel(settings, stage["script"]),
        "align",
        a.get("link") or a["path"],
        b.get("link") or b["path"],
        "--out",
        rel(out_part, settings.root),
    ]
    inputs = [{"path": a["path"], "sha256": a["sha256"]}, {"path": b["path"], "sha256": b["sha256"]}]
    return argv, out_final, out_part, inputs


ARGV: dict[str, Callable[[Settings, ScriptFlags, Json, Path, Json, Json, Path], Argv]] = {"verdict": argv_verdict}
"""A shared stage's argv by its name: runner.argv.argv_for looks here before the flow's own module."""
