"""A director job's pictures drawn from the layer tables and the mattes, and a render's step series decoded from its
mp4: numpy and cv2 here only (the import contract keeps both inside media/), every result cached under the job's
cache/ (derived; safe to delete) and written to a tmp twin first, so a reader never sees half a file.

The four overlays of b_director_research.md §5, as scripts/research/director_ui.py:512-579 drew them on the layer
table's canvas at a long side of 960 px:
- base: the photo scaled to cover the table's canvas and cropped at the centre;
- elements: each element filled with its group's colour, scaled by 0.7 + 0.6 * frac(id * 0.618), at alpha 150, and the
  element borders (a 3×3 morphological gradient of the id map) white at alpha 230;
- disparity: the table's disparity clipped to 0-1 in the TURBO colour map at alpha 200;
- matte_<id>: the element's el_<id>.png, or its hard mask when the file is missing, in magenta at 0.75 of its alpha,
  outlined in yellow where the alpha is above 127.
The group colours cover the 22 groups of the layer tables under benchmarks/runs/2026-09-28/layers_v3 (2026-11-05); the
workbench's table named 12 groups, one of them (plant) in no table, and drew the other 11 grey.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from pathlib import Path
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, read_json, rel, sha256_file
from reveal_studio.media.pictures import DECODE_LOCKS

OVERLAY_LONG = 960
KIND_RE = re.compile(r"^(base|elements|disparity|matte_(\d+))$")
GROUP_COLOURS: dict[str, tuple[int, int, int]] = {
    "person": (230, 60, 60),
    "sky": (90, 160, 240),
    "building": (200, 160, 90),
    "wall": (170, 170, 120),
    "water": (40, 120, 200),
    "furniture": (180, 100, 200),
    "ceiling": (140, 140, 200),
    "object": (240, 180, 40),
    "ground": (150, 110, 70),
    "vehicle": (240, 120, 20),
    "light": (255, 240, 120),
    "animal": (220, 120, 160),
    "appliance": (120, 200, 200),
    "cloud": (200, 210, 230),
    "floor": (130, 90, 60),
    "luminary": (255, 210, 60),
    "opening": (60, 200, 180),
    "picture": (200, 80, 140),
    "star": (250, 250, 210),
    "structure": (160, 130, 110),
    "tree": (40, 150, 60),
    "vegetation": (110, 200, 80),
}
"""RGB per group: the workbench's 11 that occur in a table (director_ui.py:513-515) and 11 more."""
GREY = (200, 200, 200)


def _root_of(settings: Settings, given: Any, default: Path) -> Path:
    if not isinstance(given, str) or not given:
        return default
    p = Path(given)
    return p if p.is_absolute() else settings.root / p


def photo_of(job: Json, side: str) -> Json:
    """The job's input of role A or B (A is the pair's _S photo, B its _F photo)."""
    if side not in ("A", "B"):
        raise StudioError("a photo is A or B", 404)
    i: Json | None = next((i for i in job.get("inputs") or [] if i.get("role") == side), None)
    if i is None:
        raise StudioError(f"this job has no photo {side}", 404)
    return i


def table_dir(settings: Settings, job: Json, side: str) -> Path:
    """<layers root>/<photo> of the job's photo A or B, the root the job recorded at its import."""
    return _root_of(settings, job.get("layers_dir"), settings.layers_dir) / Path(photo_of(job, side)["path"]).stem


def matte_dir(settings: Settings, job: Json, side: str) -> Path:
    return _root_of(settings, job.get("mattes_dir"), settings.mattes_dir) / Path(photo_of(job, side)["path"]).stem


def _write_png(dest: Path, img: Any) -> Path:
    import cv2

    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise StudioError(f"cannot encode {dest.name}", 500)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(buf.tobytes())
    os.replace(tmp, dest)
    return dest


def _cover(img: Any, w: int, h: int) -> Any:
    """The picture scaled to cover w × h and cropped at the centre (director_ui.py:518-523)."""
    import cv2

    hh, ww = img.shape[:2]
    s = max(w / ww, h / hh)
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    r = cv2.resize(img, (max(w, round(ww * s)), max(h, round(hh * s))), interpolation=interp)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y : y + h, x : x + w]


def overlay_png(settings: Settings, d: Path, job: Json, side: str, kind: str) -> Path:
    """GET /api/jobs/<id>/overlay/<A|B>/<kind>.png: the cached PNG of one overlay of photo A or B."""
    m = KIND_RE.match(kind or "")
    if not m:
        raise StudioError("an overlay is base, elements, disparity or matte_<id>", 404)
    tdir = table_dir(settings, job, side)
    table = read_json(tdir / "layers.json")
    if not isinstance(table, dict) or not table.get("canvas"):
        raise StudioError(f"no layer table for {tdir.name} under {rel(tdir.parent, settings.root)}", 404)
    w, h = (int(v) for v in table["canvas"][:2])
    sig = sha256_file(tdir / "layers.json")[:8]
    mfile = matte_dir(settings, job, side) / f"el_{m.group(2)}.png" if m.group(2) else None
    if mfile is not None and mfile.is_file():
        sig += f"_{mfile.stat().st_size}_{mfile.stat().st_mtime_ns}"
    dest = d / "cache" / "overlays" / f"{side}_{kind}_{sig}.png"
    if dest.is_file():
        return dest
    import cv2
    import numpy as np

    s = min(1.0, OVERLAY_LONG / max(w, h))
    ow, oh = round(w * s), round(h * s)
    if kind == "base":
        src = Path(photo_of(job, side)["path"])
        img = cv2.imread(str(src), cv2.IMREAD_COLOR)
        if img is None:
            raise StudioError(
                f"cv2 cannot read {src.name}; the resolve's canvas_{side}.png shows the crop instead", 409
            )
        return _write_png(dest, cv2.resize(_cover(img, w, h), (ow, oh), interpolation=cv2.INTER_AREA))
    npz = tdir / "layers.npz"
    if not npz.is_file():
        raise StudioError(f"no layers.npz for {tdir.name}: the {kind} overlay needs the table's maps", 404)
    with np.load(npz) as z:
        el = z["element"]
        disparity = z["disparity"] if kind == "disparity" else el
    if kind == "elements":
        col = np.zeros((h, w, 4), np.uint8)
        for e in table.get("elements") or []:
            c = np.array(GROUP_COLOURS.get(str(e.get("group")), GREY), np.float32)
            c = np.clip(c * (0.7 + 0.6 * ((int(e["id"]) * 0.618) % 1.0)), 0, 255)
            col[el == int(e["id"])] = (int(c[2]), int(c[1]), int(c[0]), 150)
        kernel = np.ones((3, 3), np.uint8)
        edge = cv2.morphologyEx(el.astype(np.float32), cv2.MORPH_GRADIENT, kernel) > 0
        col[edge] = (255, 255, 255, 230)
        return _write_png(dest, cv2.resize(col, (ow, oh), interpolation=cv2.INTER_NEAREST))
    if kind == "disparity":
        dsp = np.clip(disparity, 0, 1)
        cm = cv2.applyColorMap((dsp * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
        rgba = np.dstack([cm, np.full((h, w), 200, np.uint8)])
        return _write_png(dest, cv2.resize(rgba, (ow, oh), interpolation=cv2.INTER_AREA))
    eid = int(m.group(2))
    if eid not in {int(e["id"]) for e in table.get("elements") or [] if "id" in e}:
        raise StudioError(f"{tdir.name} has no element {eid}", 404)
    a = cv2.imread(str(mfile), cv2.IMREAD_GRAYSCALE) if mfile is not None and mfile.is_file() else None
    if a is None:
        a = (el == eid).astype(np.uint8) * 255  # no matte file: the hard element mask, as the renderer falls back
    if a.shape != (h, w):
        a = cv2.resize(a, (w, h), interpolation=cv2.INTER_LINEAR)
    col = np.zeros((h, w, 4), np.uint8)
    col[..., 0], col[..., 2] = 255, 255
    col[..., 3] = (a.astype(np.float32) * 0.75).astype(np.uint8)
    cnt, _ = cv2.findContours((a > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(col, cnt, -1, (0, 255, 255, 255), max(2, int(3 / s)))
    return _write_png(dest, cv2.resize(col, (ow, oh), interpolation=cv2.INTER_AREA))


def step_series(d: Path, c: Json) -> list[float]:
    """The render's whole step series: the mean absolute difference over the three channels between consecutive frames
    of its decoded mp4, the rule of director_render.py:2014 (info.json keeps its first, second, last and largest
    values). Cached under cache/steps/ by the mp4's md5; one decode per render, under a lock per cache file."""
    mp4 = c["dir"] / c["mp4"]
    if not mp4.is_file():
        return []
    key = c.get("md5_mp4") or hashlib.sha256(str(mp4.stat().st_mtime_ns).encode()).hexdigest()
    cache = d / "cache" / "steps" / f"{c['kind']}_{c['name']}_{str(key)[:8]}.json"
    got = read_json(cache)
    if isinstance(got, list):
        return [float(x) for x in got]
    with DECODE_LOCKS.setdefault(str(cache), threading.Lock()):
        got = read_json(cache)
        if isinstance(got, list):
            return [float(x) for x in got]
        import cv2
        import numpy as np

        cap = cv2.VideoCapture(str(mp4))
        prev, steps = None, []
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if prev is not None:
                steps.append(float(np.abs(fr.astype(np.float32) - prev).mean()))
            prev = fr
        cap.release()
        cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_name(cache.name + f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps([round(x, 4) for x in steps]))
        os.replace(tmp, cache)
        log(f"{d.name}: decoded the step series of {c['kind']}/{c['name']} ({len(steps)} steps)")
        return [round(x, 4) for x in steps]
