"""Image decode and framing helpers. Self-contained (no reveal import)."""
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:  # optional
    pillow_heif = None
try:
    import rawpy
except Exception:  # optional
    rawpy = None

RAW = {".dng", ".arw"}
VIDEO = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".webm"}


class MediaError(Exception):
    pass


def is_video(path):
    return Path(path).suffix.lower() in VIDEO


def load_rgb(path):
    """sRGB uint8 HxWx3 with EXIF orientation applied."""
    p = Path(path)
    if not p.exists():
        raise MediaError(f"not found: {p}")
    if p.suffix.lower() in RAW:
        if rawpy is None:
            raise MediaError("RAW needs rawpy (pip install rawpy)")
        with rawpy.imread(str(p)) as r:
            return np.ascontiguousarray(
                r.postprocess(use_camera_wb=True, output_bps=8))
    with Image.open(p) as im:
        im = ImageOps.exif_transpose(im)
        icc = im.info.get("icc_profile")
        if icc:
            try:
                im = ImageCms.profileToProfile(
                    im, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                    ImageCms.createProfile("sRGB"), outputMode="RGB")
            except Exception:
                im = im.convert("RGB")
        else:
            im = im.convert("RGB")
        return np.asarray(im, dtype=np.uint8).copy()


def cover(img, w, h):
    """Scale-to-fill and center-crop to exactly (w, h)."""
    H, W = img.shape[:2]
    s = max(w / W, h / H)
    r = cv2.resize(img, (max(w, round(W * s)), max(h, round(H * s))),
                   interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return np.ascontiguousarray(r[y:y + h, x:x + w])


def even(n):
    return int(n) & ~1


def common_canvas(a, b, max_long=None):
    """Pick a shared canvas for two images: the smaller frame's size (never
    upscale the smaller source), optionally capped, even dimensions."""
    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])
    if max_long and max(h, w) > max_long:
        s = max_long / max(h, w)
        h, w = round(h * s), round(w * s)
    return even(w), even(h)


def gray(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
