"""The pair flow's decode of a transition.mp4: the step series on the decoded frames and the decode's observables.

The step series is the measure transitions.py's quality.flicker takes before encoding (transitions.py:1156-1164):
per pair of adjacent frames, the mean absolute difference of grey on 0..1, over a proxy of long edge 480 made with
INTER_AREA (TCFG quality_long; proxy_of). Here it runs on the decoded mp4, after the libx264 yuv420p encode: the clip
as a player shows it (on mismatch_3's 1920 morph of 2026-11-05 the largest step read 0.0580 here and 0.0583 in the
report). The observables are those of transitions_harness.py section H: the decoded frame count, size and rate
(check 28) and the darkest frame's mean over every channel, 0..255 (check 30: above 5). Cached under the job's
cache/steps/ by the mp4's md5 (derived; safe to delete). cv2 is imported inside the function, as media/pictures.py
does.
"""

from __future__ import annotations

from pathlib import Path

from reveal_studio.fs import Json, read_json, write_json

PROXY_LONG = 480
"""The proxy's long edge: transitions.py's TCFG quality_long."""


def step_series(d: Path, c: Json) -> Json:
    """{steps, frames, size, fps, darkest_mean, proxy_long} of the candidate's mp4 (c: dir, mp4, kind, name, md5_mp4);
    {} when the mp4 is missing."""
    mp4 = Path(c["dir"]) / c["mp4"]
    if not mp4.is_file():
        return {}
    cache = d / "cache" / "steps" / f"{c['kind']}_{c['name']}_{(c.get('md5_mp4') or 'x')[:8]}.json"
    hit = read_json(cache)
    if isinstance(hit, dict) and "steps" in hit:
        return hit
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(str(mp4))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    steps: list[float] = []
    prev = None
    n = 0
    size: list[int] = []
    darkest: float | None = None
    while True:
        ok, f = cap.read()
        if not ok:
            break
        h, w = f.shape[:2]
        size = [int(w), int(h)]
        mean = float(f.mean())
        darkest = mean if darkest is None else min(darkest, mean)
        s = min(1.0, PROXY_LONG / max(h, w))
        p = f if s >= 1.0 else cv2.resize(f, (max(2, round(w * s)), max(2, round(h * s))), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        if prev is not None:
            steps.append(round(float(np.abs(g - prev).mean()), 5))
        prev = g
        n += 1
    cap.release()
    out: Json = {
        "steps": steps,
        "frames": n,
        "size": size,
        "fps": round(fps, 3),
        "darkest_mean": None if darkest is None else round(darkest, 2),
        "proxy_long": PROXY_LONG,
    }
    write_json(cache, out)
    return out
