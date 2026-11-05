"""The registration's named windows under each fit, as the registration panel's table draws them.

`loop_seq.py prep --windows` (SCHEMA.md, the section of 2026-11-05) writes the boxes at the top level of prep.json,
`windows` {name: [x0, y0, x1, y1]} in frame-0 px before the crop, and per frame i >= 1 that is not a cut
`frames[i].windows` {name: {box, box_canvas, fits: {fit: {dx, dy, corr, edge}}}}. The fits come in the order all,
far, chain, ecc, final; a fit the prep did not make has no entry, and the table has no column for it.
"""

from __future__ import annotations

import math
from typing import Any

from reveal_studio.fs import Json

FIT_ORDER = ("all", "far", "chain", "ecc", "final")
"""The prep's fits in the order the table shows them; an unknown fit name follows them in name order."""


def _ordered(names: set[str]) -> list[str]:
    return [f for f in FIT_ORDER if f in names] + sorted(names - set(FIT_ORDER))


def _cell(fit: Any) -> Json | None:
    """One window under one fit: dx, dy and corr as the prep wrote them, edge, and the offset's length in px."""
    if (
        not isinstance(fit, dict)
        or not isinstance(fit.get("dx"), (int, float))
        or not isinstance(fit.get("dy"), (int, float))
    ):
        return None
    dx, dy = float(fit["dx"]), float(fit["dy"])
    return {
        "dx": dx,
        "dy": dy,
        "corr": fit.get("corr"),
        "edge": bool(fit.get("edge")),
        "px": round(math.hypot(dx, dy), 2),
    }


def fits_summary(prep_json: Any) -> Json | None:
    """The fits table per registered frame, or None when the prep measured no windows.

    Returns {"windows": {name: box}, "names": [...], "fits": [every fit present, in FIT_ORDER],
    "frames": [{"i", "method", "lock_shift": [dx, dy] | None, "fits": [this frame's fits],
    "rows": [{"name", "box", "box_canvas", "cells": {fit: {"dx", "dy", "corr", "edge", "px"} | None}}],
    "largest": {fit: {"name", "dx", "dy", "px", "edge"}}}], "unmeasured": [i, ...]}. `largest` is, per fit, the
    window whose offset is longest (the first one on a tie); an edge cell takes part with its bound.
    """
    if not isinstance(prep_json, dict) or not isinstance(prep_json.get("windows"), dict):
        return None
    boxes: dict[str, Any] = prep_json["windows"]
    names = list(boxes)
    frames_out: list[Json] = []
    unmeasured: list[int] = []
    present: set[str] = set()
    for i, fr in enumerate(prep_json.get("frames") or []):
        if i == 0:
            continue  # frame 0 holds the windows: nothing to measure against
        wins = fr.get("windows") if isinstance(fr, dict) else None
        if not isinstance(wins, dict) or not wins:
            unmeasured.append(i)  # a declared cut, or a frame the prep left alone
            continue
        mine: set[str] = set()
        for w in wins.values():
            if isinstance(w, dict) and isinstance(w.get("fits"), dict):
                mine |= set(w["fits"])
        fits = _ordered(mine)
        present |= mine
        rows: list[Json] = []
        largest: dict[str, Json] = {}
        for name in names + [n for n in wins if n not in boxes]:
            w = wins.get(name)
            if not isinstance(w, dict):
                continue
            cells = {f: _cell((w.get("fits") or {}).get(f)) for f in fits}
            rows.append({"name": name, "box": w.get("box"), "box_canvas": w.get("box_canvas"), "cells": cells})
            for f, c in cells.items():
                if c is not None and (f not in largest or c["px"] > largest[f]["px"]):
                    largest[f] = {"name": name, "dx": c["dx"], "dy": c["dy"], "px": c["px"], "edge": c["edge"]}
        lock = fr.get("lock") if isinstance(fr.get("lock"), dict) else None
        frames_out.append(
            {
                "i": i,
                "method": fr.get("method"),
                "lock_shift": lock.get("shift_px") if lock else None,
                "fits": fits,
                "rows": rows,
                "largest": largest,
            }
        )
    return {
        "windows": boxes,
        "names": names,
        "fits": _ordered(present),
        "frames": frames_out,
        "unmeasured": unmeasured,
    }
