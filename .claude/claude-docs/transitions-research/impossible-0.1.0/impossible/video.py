"""Video I/O on PyAV (bundled FFmpeg libs: libx264/libx265 in the wheel).

Rules learned from the research (RESEARCH-PLAN.md section 6):
  * Never trust timestamp seeking for the cut frame: seek to the keyframe
    BEFORE the target, then decode forward and pick by PTS. iPhone footage
    is often variable-frame-rate; count PTS, not frame indexes.
  * Frame-accurate joins require re-encoding the touched neighborhood.
    v0.1 re-encodes the whole output (correct first); E12 adds stream-copy
    of untouched outer segments.
  * HDR/HLG 10-bit: v0.1 decodes to 8-bit sRGB-ish frames via swscale and
    encodes yuv420p. E13 covers keeping the transition in the clip's color
    space. Tag HEVC as hvc1 for Apple players.
"""
import fractions
import logging
from pathlib import Path

import av
import numpy as np

log = logging.getLogger("impossible.video")


def probe(path):
    with av.open(str(path)) as c:
        v = c.streams.video[0]
        fps = float(v.average_rate or v.guessed_rate or 30)
        dur = float(c.duration / av.time_base) if c.duration else None
        cc = v.codec_context
        return {"path": str(path), "width": v.width, "height": v.height,
                "fps": fps, "duration": dur, "frames": v.frames or None,
                "codec": cc.name, "pix_fmt": cc.pix_fmt,
                "bit_depth": (cc.format.bits_per_pixel if cc.format else None),
                "color_primaries": getattr(cc, "color_primaries", None),
                "color_trc": getattr(cc, "color_trc", None),
                "time_base": str(v.time_base)}


def _to_rgb(frame):
    return frame.to_ndarray(format="rgb24")


def frames_between(path, t0, t1):
    """Yield (t_seconds, rgb) for all frames with t0 <= pts < t1, exact by
    PTS. Seeks to the keyframe before t0 and discards until t0."""
    with av.open(str(path)) as c:
        v = c.streams.video[0]
        v.thread_type = "AUTO"
        if t0 > 0:
            c.seek(int(t0 / v.time_base), stream=v, backward=True, any_frame=False)
        for fr in c.decode(v):
            if fr.pts is None:
                continue
            t = float(fr.pts * v.time_base)
            if t < t0 - 1e-6:
                continue
            if t1 is not None and t >= t1 - 1e-6:
                break
            yield t, _to_rgb(fr)


def frame_at(path, t, tolerance=None):
    """The frame whose PTS is closest to t (never earlier by more than half
    a frame). Returns (t_actual, rgb)."""
    info = probe(path)
    half = 0.5 / info["fps"] if tolerance is None else tolerance
    best = None
    for tt, rgb in frames_between(path, max(0.0, t - 2.0 / info["fps"]), t + 3.0 / info["fps"]):
        if best is None or abs(tt - t) < abs(best[0] - t):
            best = (tt, rgb)
        if tt > t + half:
            break
    if best is None:
        raise ValueError(f"no frame near t={t}s in {path}")
    return best


def context(path, t, n_before=4, n_after=4):
    """Frames around a cut for motion carry-over (E7). Returns (before,
    after) lists of (t, rgb) with `before` ending at the frame AT t."""
    info = probe(path)
    dt = 1.0 / info["fps"]
    all_ = list(frames_between(path, max(0.0, t - (n_before + 1) * dt), t + (n_after + 1) * dt))
    if not all_:
        return [], []
    idx = int(np.argmin([abs(tt - t) for tt, _ in all_]))
    return all_[max(0, idx - n_before):idx + 1], all_[idx + 1:idx + 1 + n_after]


class Writer:
    """Constant-fps H.264/HEVC writer. crf 18 is visually lossless for
    social use; the operator's 4K a6700 material may want crf 16."""

    def __init__(self, path, w, h, fps, codec="libx264", crf=18,
                 pix_fmt="yuv420p", tag_hvc1=True):
        self.c = av.open(str(path), mode="w")
        fr = fractions.Fraction(fps).limit_denominator(1001 * 60)
        self.s = self.c.add_stream(codec, rate=fr)
        self.s.width, self.s.height = int(w) & ~1, int(h) & ~1
        self.s.pix_fmt = pix_fmt
        self.s.options = {"crf": str(crf), "preset": "medium"}
        if codec == "libx265" and tag_hvc1:
            self.s.codec_context.codec_tag = "hvc1"
        self.n = 0

    def write(self, rgb):
        if rgb.shape[1] != self.s.width or rgb.shape[0] != self.s.height:
            import cv2
            rgb = cv2.resize(rgb, (self.s.width, self.s.height), interpolation=cv2.INTER_AREA)
        fr = av.VideoFrame.from_ndarray(np.ascontiguousarray(rgb), format="rgb24")
        for pkt in self.s.encode(fr):
            self.c.mux(pkt)
        self.n += 1

    def close(self):
        for pkt in self.s.encode():
            self.c.mux(pkt)
        self.c.close()
        return self.n


def count_frames(path):
    with av.open(str(path)) as c:
        return sum(1 for _ in c.decode(c.streams.video[0]))
