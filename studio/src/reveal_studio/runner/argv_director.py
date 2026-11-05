"""The director flow's argv (builder D's module from wave 2 on): not built in the slice of 2026-11-05.

The flow's script stages get their argv here, one function per stage, in the shape of runner/argv_loop.py. The
shared stages (Reveal's verdict) never reach this module: runner.argv.argv_for routes them to argv_common.py first.
"""

from __future__ import annotations

from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json
from reveal_studio.runner.argv import Argv, ScriptFlags


def argv_for(
    settings: Settings, flags: ScriptFlags, stage: Json, d: Path, job: Json, knobs: Json, rec_dir: Path
) -> Argv:
    raise StudioError(f"the director flow's {stage['name']} stage is not built yet", 501)
