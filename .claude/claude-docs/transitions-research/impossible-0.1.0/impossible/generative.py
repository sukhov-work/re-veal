"""The generative tier: contracts, steering primitives, and the budget
policy. Nothing here downloads anything; adapters that need weights are
explicit TODOs with the experiment ID that validates them locally.

The deterministic transition always exists first. Enrichment operates on
a bounded frame window and optional mask, conditioned on those frames,
with a wall-clock budget and a seed. Dreaminess (0..100) maps to
SDEdit-style denoise strength.
"""
import logging
import time
from dataclasses import dataclass

import cv2
import numpy as np

log = logging.getLogger("impossible.generative")


@dataclass
class EnrichRequest:
    frames: list            # deterministic uint8 RGB frames (the skeleton)
    disp_fields: list       # per-frame displacement A-frame -> next, for steering
    window: tuple           # (i0, i1) frame indexes enrichment may touch
    mask: np.ndarray        # HxW float32 0..1, 1 = may be dreamed
    strength: float         # 0..1 denoise / dreaminess
    seed: int
    budget_s: float
    prompt: str = ""        # optional; the skeleton is the primary condition


class Enricher:
    """Contract. Implementations must (a) be deterministic for a fixed seed
    on CPU (MPS is best-effort), (b) never exceed budget_s, (c) return the
    same number of frames at the same size, (d) leave frames outside the
    window byte-identical."""
    name = "null"

    def available(self):
        return True

    def estimate_seconds(self, req):
        return 0.0

    def enrich(self, req):
        return req.frames


class NullEnricher(Enricher):
    pass


# ---------------------------------------------------------------------------
# steering primitives that work with ANY diffusion backend
# ---------------------------------------------------------------------------

def warp_noise_along_flow(shape, disp_fields, seed, fresh_mix=0.15):
    """Correlated noise that follows the deterministic flow (simplified
    Go-with-the-Flow, Burgert et al. CVPR 2025). Frame 0 is i.i.d. Gaussian;
    each next frame is the previous noise forward-splatted along the
    displacement, holes refilled with fresh noise, then re-standardized so
    every frame stays unit-variance. The paper's particle-based scheme
    preserves Gaussianity more carefully; E14 measures whether this
    simplification is enough to steer Wan/LTX.

    Returns list of (h, w, c) float32 noise frames."""
    h, w, c = shape
    rng = np.random.default_rng(seed)
    cur = rng.standard_normal((h, w, c)).astype(np.float32)
    out = [cur]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    for d in disp_fields:
        tx = np.rint(gx + d[..., 0]).astype(int).ravel()
        ty = np.rint(gy + d[..., 1]).astype(int).ravel()
        ok = (tx >= 0) & (tx < w) & (ty >= 0) & (ty < h)
        acc = np.zeros((h, w, c), np.float32)
        cnt = np.zeros((h, w), np.float32)
        np.add.at(acc, (ty[ok], tx[ok]), cur.reshape(-1, c)[ok])
        np.add.at(cnt, (ty[ok], tx[ok]), 1.0)
        nxt = acc / np.maximum(cnt, 1)[..., None]
        fresh = rng.standard_normal((h, w, c)).astype(np.float32)
        hole = (cnt == 0)[..., None]
        nxt = np.where(hole, fresh, nxt * (1 - fresh_mix) + fresh * fresh_mix)
        nxt = (nxt - nxt.mean()) / (nxt.std() + 1e-6)
        out.append(nxt.astype(np.float32))
        cur = nxt
    return out


def frequency_split_blend(det_hi, gen_lo, sigma=3.0, amount=1.0):
    """Take the LOW frequencies from a (possibly upscaled) generated frame
    and the HIGH frequencies from the deterministic full-resolution frame.
    This is how a 480-720p generative pass lifts a 1080p/4K transition
    without smearing detail: the generator supplies mood, light and
    structure changes; the skeleton keeps texture. amount blends."""
    if gen_lo.shape[:2] != det_hi.shape[:2]:
        gen_lo = cv2.resize(gen_lo, (det_hi.shape[1], det_hi.shape[0]),
                            interpolation=cv2.INTER_CUBIC)
    d = det_hi.astype(np.float32)
    g = gen_lo.astype(np.float32)
    d_lo = cv2.GaussianBlur(d, (0, 0), sigma)
    g_lo = cv2.GaussianBlur(g, (0, 0), sigma)
    out = (d - d_lo) + g_lo * amount + d_lo * (1 - amount)
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# budget policy: "minutes are fine, hours are not"
# ---------------------------------------------------------------------------

# seconds of wall-clock per generated FRAME at 480p on an M3 Pro 36 GB.
# These are placeholders derived from published M1 Max GGUF timings scaled
# by a guess; E14/E15 replace them with measured numbers. Until measured,
# the planner is deliberately pessimistic.
COST_PER_FRAME_480P = {
    "ltx2-mlx-int8-distilled": 6.0,
    "ltx2-mlx-int8": 15.0,
    "wan22-ti2v-5b-mlx-q8": 20.0,
    "dreammover-sd15": 12.0,
    "null": 0.0,
}
RES_LADDER = [(854, 480), (1024, 576), (1280, 720)]


def plan_generation(backend, n_frames, budget_s):
    """Pick the largest resolution on the ladder whose estimated cost fits
    the budget. Cost scales ~linearly with pixel count. Returns
    (width, height, est_seconds) or None when even 480p does not fit."""
    base = COST_PER_FRAME_480P.get(backend)
    if base is None:
        return None
    best = None
    for w, h in RES_LADDER:
        est = base * n_frames * (w * h) / (854 * 480)
        if est <= budget_s:
            best = (w, h, est)
    return best


# ---------------------------------------------------------------------------
# adapters: explicit, honest stubs
# ---------------------------------------------------------------------------

class LTX2KeyframeEnricher(Enricher):
    """LTX-2 KeyframeInterpolationPipeline via the MLX port, first+last
    frame conditioning, distilled 8-step variant, int8. License: LTX-2
    Community (commercial use only under $10M annual revenue). Validate
    with E14 before wiring: measure s/frame at 480p and 720p, check that
    frames outside the window are untouched, and that a fixed seed
    reproduces on CPU."""
    name = "ltx2-mlx-int8-distilled"

    def available(self):
        try:
            import mlx.core  # noqa: F401
            return True
        except Exception:
            return False

    def enrich(self, req):
        raise NotImplementedError("E14: wire the MLX LTX-2 keyframe pipeline")


class WanFLF2VEnricher(Enricher):
    """Wan 2.2 TI2V-5B first-last-frame via MLX (q8, ~19.6 GB). Apache-2.0.
    Slower than LTX-2 distilled; keep as the second backend. Validate with
    E15."""
    name = "wan22-ti2v-5b-mlx-q8"

    def enrich(self, req):
        raise NotImplementedError("E15: wire the MLX Wan 2.2 TI2V-5B FLF2V")


class DreamMoverEnricher(Enricher):
    """DreamMover (ECCV 2024): diffusion-feature morphing for photo pairs
    with large motion or unrelated content. SD 1.5 based, minutes per pair.
    The natural backend for the photo use case. Validate with E16."""
    name = "dreammover-sd15"

    def enrich(self, req):
        raise NotImplementedError("E16: wire DreamMover for photo pairs")


BACKENDS = {e.name: e for e in (NullEnricher(), LTX2KeyframeEnricher(),
                                WanFLF2VEnricher(), DreamMoverEnricher())}


def run_enrichment(frames, disp_fields, spec, backend="null", mask=None):
    """Apply the budgeted, bounded enrichment. Returns (frames, report)."""
    enr = BACKENDS.get(backend, NullEnricher())
    n = len(frames)
    i0 = int(round(spec.gen_window[0] * (n - 1)))
    i1 = int(round(spec.gen_window[1] * (n - 1)))
    h, w = frames[0].shape[:2]
    req = EnrichRequest(frames, disp_fields, (i0, i1),
                        np.ones((h, w), np.float32) if mask is None else mask,
                        spec.dreaminess / 100.0, spec.seed,
                        spec.budget_minutes * 60.0)
    report = {"backend": enr.name, "window": (i0, i1),
              "strength": req.strength, "seed": spec.seed}
    if spec.dreaminess <= 0 or isinstance(enr, NullEnricher):
        report["applied"] = False
        return frames, report
    if not enr.available():
        report.update(applied=False, reason="backend not installed")
        return frames, report
    plan = plan_generation(enr.name, i1 - i0 + 1, req.budget_s)
    if plan is None:
        report.update(applied=False, reason="does not fit the budget even at 480p")
        return frames, report
    report["plan"] = {"width": plan[0], "height": plan[1], "est_s": round(plan[2])}
    t = time.time()
    out = enr.enrich(req)
    report.update(applied=True, wall_s=round(time.time() - t, 1))
    return out, report
