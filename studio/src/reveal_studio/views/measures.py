"""The measures the viewer and the inspector read beside a render's measure.json: stalls and jumps on the step series
(the bars of the loops playbook, loops.md §6), the frame kinds those rules read, a render's measure runs with the
latest stability series (`loop_seq.py measure`), and the probe's table (`loop_seq.py probe`)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.fs import Json, read_json, rel
from reveal_studio.jobs.records import records
from reveal_studio.jobs.store import job_root, prep_dir

STALL_BAR = 0.3
"""Grey levels: a run of steps below this while motion is open is a stall (loops.md §6)."""
JUMP_RATIO = 3.0
"""A step above this many times the mean of its neighbours is a jump unless a cut or a snap is declared there."""
CLOSED = frozenset({"hold", "cut"})
"""The kinds that close motion: a still's hold, and the first frame after a cut (a still in every plan of the
playbook)."""
PROBE_METHODS = ("rife", "morph", "dissolve")


def _kind(generated: Any) -> str:
    g = str(generated or "")
    if g == "none (photo)":
        return "hold"
    if g.startswith("none (blend + motion blur)"):
        return "snap"
    if g == "none (repaint)":  # the repaint leg (2026-11-05): a per-pixel blend of the stills, nothing generated
        return "blend"
    if g.startswith("none ("):
        return g[6:].split(")")[0].split()[0] if g[6:].strip(" )") else "none"
    if g.startswith("none"):
        return "none"
    return "generated"


def _ends(row: Json) -> tuple[Any, Any]:
    """The still a frame's step starts from and ends on: a hold's key, a transition's from and to."""
    if "key" in row:
        return row["key"], row["key"]
    return row.get("from"), row.get("to")


def frame_kinds(rows: list[Json]) -> list[str]:
    """Per row of frames.json, the kind the step rules read.

    hold: a still (`none (photo)`); snap: a short blurred jump (`none (blend + motion blur)`); generated: a model
    drew the frame (`rife`, `rife (the base)`, ...); blend for a repaint leg's frame (`none (repaint)`); otherwise the
    word frames.json gives (blend, morph, rewind, slices, sheets). cut: the first frame after a declared cut, found
    where two neighbouring frames belong to different plan steps and the still the first step ends on differs from the
    one the next step starts from (a cut writes no frames, so it shows only at that boundary).
    """
    kinds = [_kind(r.get("generated")) for r in rows]
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        if a.get("step") is None or b.get("step") is None or a.get("step") == b.get("step"):
            continue
        end, start = _ends(a)[1], _ends(b)[0]
        if end is not None and start is not None and end != start:
            kinds[i] = "cut"
    return kinds


def stalls_and_jumps(steps: list[float], tags: list[str]) -> Json:
    """Stalls and jumps on the step series, as loops.md §6 states the bars.

    steps[i] is the mean absolute difference between frames i and i + 1; tags[i] is frame i's kind (frame_kinds;
    a missing tag counts as an in-between). A stall is a run of two or more consecutive steps below STALL_BAR while
    motion is open: both frames of every step in the run are in-betweens, neither a hold nor a cut's first frame. A
    jump is a step above JUMP_RATIO times the mean of its two neighbours; the first and the last step have one
    neighbour and are judged against it alone. A step below STALL_BAR reads as a stop and is never a jump: without
    that floor the encoder's noise inside a hold (0.01 grey levels against 0.0, step 0 of 2026-10-30's Halloween
    renders) is listed. A step into a cut's first frame, or with a snap frame at either end, is a declared jump and
    never listed.

    Returns {"stalls": [[first, last], ...], "jumps": [index, ...]}, step indices.
    """

    def kind(i: int) -> str:
        return tags[i] if 0 <= i < len(tags) else ""

    stalls: list[list[int]] = []
    run: list[int] | None = None
    for i, v in enumerate(steps):
        if v < STALL_BAR and kind(i) not in CLOSED and kind(i + 1) not in CLOSED:
            run = [run[0], i] if run else [i, i]
            continue
        if run and run[1] > run[0]:
            stalls.append(run)
        run = None
    if run and run[1] > run[0]:
        stalls.append(run)
    jumps: list[int] = []
    for i, v in enumerate(steps):
        near = [steps[j] for j in (i - 1, i + 1) if 0 <= j < len(steps)]
        if not near or kind(i + 1) == "cut" or "snap" in (kind(i), kind(i + 1)):
            continue
        if v >= STALL_BAR and v > JUMP_RATIO * sum(near) / len(near):
            jumps.append(i)
    return {"stalls": stalls, "jumps": jumps}


def measure_runs(settings: Settings, d: Path, c: Json) -> list[Json]:
    """The candidate's measure runs, oldest first: every <render>/measures/<stamp>/measure.json (a `.part` folder is
    a run still going), each with the record that made it (None for a run made from the shell)."""
    base: Path = c["dir"] / "measures"
    if not base.is_dir():
        return []
    made = {r.get("out_final"): r for r in records(d) if r.get("stage") == "measure"}
    found: list[tuple[float, str, Path, Json]] = []
    for f in base.iterdir():
        m = read_json(f / "measure.json") if f.is_dir() and not f.name.endswith(".part") else None
        if isinstance(m, dict):
            found.append(((f / "measure.json").stat().st_mtime, f.name, f, m))
    out: list[Json] = []
    for mtime, _name, f, m in sorted(found, key=lambda x: (x[0], x[1])):
        rec = made.get(rel(f, settings.root))
        peaks: Json = m["stability_max"] if isinstance(m.get("stability_max"), dict) else {}
        out.append(
            {
                "record": rec["id"] if rec else None,
                "at": (rec or {}).get("ended") or dt.datetime.fromtimestamp(mtime).isoformat(timespec="seconds"),
                "folder": rel(f, settings.root),
                "windows": {n: p.get("box") for n, p in peaks.items() if isinstance(p, dict)},
                "ref": m.get("stability_ref"),
                "stability_max": peaks,
                "measure": m,
            }
        )
    return out


def latest_stability(runs: list[Json]) -> Json | None:
    """The stability series of the latest run that measured windows: {record, at, ref, margin, series, max}."""
    for r in reversed(runs):
        m = r["measure"]
        if isinstance(m.get("stability"), dict) and m["stability"]:
            return {
                "record": r["record"],
                "at": r["at"],
                "folder": r["folder"],
                "ref": m.get("stability_ref"),
                "margin": m.get("stability_margin"),
                "series": m["stability"],
                "max": r["stability_max"],
            }
    return None


def probe_view(settings: Settings, job: Json) -> Json | None:
    """probe.json as the probe panel draws it, or None before a probe ran: per pair the strips, the double-exposure
    share per method and t (inside the change matte and over the frame), the step to each still, and the face crops
    as one row per face and method (still a, the three t, still b)."""
    folder = prep_dir(settings, job) / "probe"
    p = read_json(folder / "probe.json")
    if not isinstance(p, dict):
        return None
    root = job_root(settings, job)
    url = f"/api/jobs/{job['id']}/file/{rel(folder, root)}/"
    pairs: list[Json] = []
    for pr in p.get("pairs") or []:
        a, b = pr.get("a"), pr.get("b")
        meths = pr.get("methods") or {}
        methods: list[Json] = []
        for name in [m for m in PROBE_METHODS if m in meths] + sorted(set(meths) - set(PROBE_METHODS)):
            m = meths[name] or {}
            frames = [
                {k: f.get(k) for k in ("t", "dexp", "dexp_frame", "step_a", "step_b", "seconds")}
                for f in m.get("frames") or []
            ]
            methods.append(
                {
                    "method": name,
                    "strip": url + m["strip"] if m.get("strip") else None,
                    "flow": m.get("flow"),
                    "frames": frames,
                    "crops": [[url + c for c in (f.get("crops") or [])] for f in m.get("frames") or []],
                }
            )
        faces = pr.get("faces") or []
        crops: list[Json] = []
        for k in range(len(faces)):
            ends = [f"crops/{a}_{b}_k{s}_face{k}.jpg" for s in (a, b)]
            for m in methods:
                mid = [row[k] for row in m["crops"] if k < len(row)]
                crops.append(
                    {
                        "face": k,
                        "method": m["method"],
                        "a": url + ends[0] if (folder / ends[0]).exists() else None,
                        "mid": mid,
                        "b": url + ends[1] if (folder / ends[1]).exists() else None,
                    }
                )
        pairs.append(
            {
                "a": a,
                "b": b,
                "matte_share": pr.get("matte_share"),
                "faces": len(faces),
                "methods": methods,
                "crops": crops,
            }
        )
    return {
        "folder": rel(folder, settings.root),
        "long": p.get("long"),
        "size": p.get("size"),
        "t": p.get("t"),
        "rife_version": p.get("rife_version"),
        "rife_skipped": p.get("rife_skipped"),
        "seconds": p.get("seconds"),
        "script_md5": p.get("script_md5"),
        "pairs": pairs,
    }
