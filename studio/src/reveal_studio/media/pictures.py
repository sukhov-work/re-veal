"""Thumbnails and JPEG frames for the page, cached under the job's cache/ folder (derived; safe to delete).

cv2 is imported inside the functions, so `reveal-studio check` and the unit tests that never decode run without it.
"""

from __future__ import annotations

import threading
from pathlib import Path

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, log, rel
from reveal_studio.jobs.candidates import candidate
from reveal_studio.jobs.store import prep_dir

DECODE_LOCKS: dict[str, threading.Lock] = {}
"""One lock per decode cache folder, so two requests for one render's frames decode it once."""


def jpeg_thumb(settings: Settings, src: Path, dest: Path, long: int = 160) -> Path:
    """A JPEG of `src` with its long edge at most `long` px (downscale only, INTER_AREA), quality 85."""
    import cv2

    im = cv2.imread(str(src))
    if im is None:
        raise StudioError(f"cannot read {rel(src, settings.root)}", 500)
    h, w = im.shape[:2]
    s = long / max(h, w)
    if s < 1:
        im = cv2.resize(im, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dest), im, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return dest


def frames_dir(d: Path, c: Json) -> Path:
    """The render's JPEG frames: its own frames/ when the script wrote it, else a decode of loop.mp4 cached by the
    mp4's md5 (one decode per render, under a lock per cache folder)."""
    own: Path = c["dir"] / "frames"
    if (own / "f0000.jpg").exists():
        return own
    cache = d / "cache" / "frames" / f"{c['kind']}_{c['name']}_{(c['md5_mp4'] or 'x')[:8]}"
    if (cache / "done").exists():
        return cache
    lock = DECODE_LOCKS.setdefault(str(cache), threading.Lock())
    with lock:
        if (cache / "done").exists():
            return cache
        import cv2

        cache.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(c["dir"] / "loop.mp4"))
        i = 0
        while True:
            ok, f = cap.read()
            if not ok:
                break
            cv2.imwrite(str(cache / f"f{i:04d}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 90])
            i += 1
        (cache / "done").write_text(str(i))
        log(f"{d.name}: decoded {i} frames of {c['kind']}/{c['name']} into the cache")
    return cache


def thumb_path(settings: Settings, d: Path, job: Json, what: str, a: str, b: str | None = None) -> Path:
    """The cached thumbnail of a registered still (still/<i>), an original (raw/<i>) or a render's frame 0."""
    cache = d / "cache" / "thumbs"
    if what == "still":
        i = int(a)
        src = prep_dir(settings, job) / f"k{i}.png"
        if not src.exists():
            raise StudioError(f"no k{i}.png", 404)
        dest = cache / f"still_{i}_{int(src.stat().st_mtime)}.jpg"
    elif what == "raw":
        i = int(a)
        if i < 0 or i >= len(job["inputs"]):
            raise StudioError("no such still", 404)
        link = job["inputs"][i].get("link")
        src = Path((link and settings.root / link) or job["inputs"][i]["path"])
        if not src.exists():
            raise StudioError("the original is not reachable", 404)
        dest = cache / f"raw_{i}_{job['inputs'][i]['sha256'][:8]}.jpg"
    elif what == "render":
        c = candidate(settings, d, job, a, b or "")
        fd = frames_dir(d, c)
        src = fd / "f0000.jpg"
        if not src.exists():
            raise StudioError("no frame 0", 404)
        dest = cache / f"render_{c['kind']}_{c['name']}_{(c['md5_mp4'] or 'x')[:8]}.jpg"
    else:
        raise StudioError("a thumb is still/<i>, raw/<i> or render/<kind>/<name>", 404)
    if not dest.exists():
        jpeg_thumb(settings, src, dest, 192)
    return dest
