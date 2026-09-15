#!/usr/bin/env python3
"""TR14 research: what the CHANGED region does between the endpoints (runs in `.venv`).

  --render DIR OUT SECONDS PAIR...   for each pair dir DIR/pair_<PAIR>/ (A.png, B.png, dis_*.npy,
                                     roma_*.npy from compare_fields.py --prepare and roma_probe.py)
                                     render morph SECONDS for every variant below and write
                                     OUT/<pair>/<variant>_<SECONDS>s/{transition.mp4,strip.jpg,
                                     mid.jpg,report.json}, OUT/<pair>/mask.jpg and OUT/tr14.json
  --page OUT PAIR...                 OUT/index.html: the clips of one pair side by side, the numbers,
                                     the mask, a pick per pair exported as tr14_picks.json

Variants (field · what happens inside the changed-region mask):
  dis          the current tool: homography + DIS residual, DIS consistency as the splat weight
  roma         the RoMa outdoor field with RoMa's certainty as the splat weight (2026-09-15 clips)
  roma-x-cert  TR2d as written in the plan: RoMa displacement x certainty, both directions
  hold         TR2d, residual form: homography motion + (RoMa - homography) x certainty, so an
               uncertain region follows the camera motion and its content crossfades IN PLACE
  hold-dis     the same hold with the tool's own DIS field and NO RoMa: homography motion +
               (DIS - homography) x (1 - feathered changed mask); the mask, not a certainty, gates it
  luma         hold field; inside the mask B appears in order of A's brightness (bright first)
  edge-grow    hold field; inside the mask B grows outward from its own edges (Canny distance)
  melt         hold field; inside the feathered mask the composited frame is swirled by a
               divergence-free noise field scaled by sin(pi u): zero at both endpoints
  melt-soft    melt with the feather moved off the object: zero within 24 px of the mask boundary
               (the detector's dilation), then a 64 px ramp, so the swirl stays off the object's
               edge (the mask is dilated 21 px past it)
The mask is Reveal's changed-region detector on the homography-aligned pair (reveal.py
changed_region_mask), the same mask Reveal uses to protect its residual field. Not part of
either tool. 2026-09-15.
"""
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import transitions as T  # noqa: E402
import reveal as rv  # noqa: E402  (research only: the two tools never import each other)

VARIANTS = ("dis", "roma", "roma-x-cert", "hold", "hold-dis", "luma", "edge-grow", "melt", "melt-soft")
RUN = tuple(v for v in os.environ.get("TR14_VARIANTS", ",".join(VARIANTS)).split(",") if v)
MELT_AMP = 0.012          # of the canvas long edge (23 px at 1920)
MELT_SIGMA = 0.04         # noise correlation length, of the canvas short edge
FEATHER_PX = int(os.environ.get("TR14_FEATHER", 32))   # melt feather, px inside the mask edge;
                          # the detector dilates the mask 21 px past the object, so 32 still
                          # swirls the object's edge (match_4: straightness 2.5 -> 5.3 px)
MIX_FEATHER_SIGMA = 8.0   # px, softens the mask for the reveal mixes
REVEAL_SOFT = 0.15        # width of the reveal front in order units (as luma_mask)


# ---- fields -----------------------------------------------------------------

def load_field(d, name):
    return {k: np.load(str(d / f"{name}_{k}.npy")) for k in ("dAB", "dBA", "wA", "wB")}


def homography_fields(gA, gB):
    """(H_BA, dH_AB, dH_BA): the camera motion alone as displacement fields."""
    cv2.setRNGSeed(0)
    sp = T.sparse_homography(gA, gB)
    H = sp[0] if sp and T._sane(sp[0], gB.shape) else np.eye(3)
    h, w = gA.shape
    gx, gy = T._grid(h, w)
    pts = np.stack([gx, gy], -1).reshape(-1, 1, 2)
    to_b = cv2.perspectiveTransform(pts, np.linalg.inv(H)).reshape(h, w, 2)
    to_a = cv2.perspectiveTransform(pts, H).reshape(h, w, 2)
    grid = np.stack([gx, gy], -1)
    return H, (to_b - grid).astype(np.float32), (to_a - grid).astype(np.float32), sp


def changed_mask(A, B, H_BA):
    """Reveal's changed-region detector on the homography-aligned pair, uint8 0/255."""
    h, w = A.shape[:2]
    Bw = cv2.warpPerspective(B, H_BA, (w, h), flags=cv2.INTER_LINEAR)
    valid = rv.warp_valid_mask(B.shape, H_BA, (w, h))
    return rv.changed_region_mask(A, Bw, valid)


def build_corr(fields, variant, dH_AB, dH_BA, F=None, F_B=None):
    if variant == "dis":
        f = fields["dis"]
        return {**f, "cls": "A", "method": "homography+dis", "diag": {}}
    if variant == "hold-dis":
        f = fields["dis"]
        dAB = dH_AB + (f["dAB"] - dH_AB) * (1.0 - F)[..., None]
        dBA = dH_BA + (f["dBA"] - dH_BA) * (1.0 - F_B)[..., None]
        return {"dAB": dAB.astype(np.float32), "dBA": dBA.astype(np.float32),
                "wA": f["wA"], "wB": f["wB"], "cls": "A", "method": variant, "diag": {}}
    r = fields["roma"]
    dAB, dBA, wA, wB = r["dAB"], r["dBA"], r["wA"], r["wB"]
    if variant == "roma":
        pass
    elif variant == "roma-x-cert":
        dAB, dBA = dAB * wA[..., None], dBA * wB[..., None]
    else:                                   # hold and the effects on top of it
        dAB = dH_AB + (dAB - dH_AB) * wA[..., None]
        dBA = dH_BA + (dBA - dH_BA) * wB[..., None]
    return {"dAB": dAB.astype(np.float32), "dBA": dBA.astype(np.float32),
            "wA": wA, "wB": wB, "cls": "A", "method": variant, "diag": {}}


# ---- effects inside the mask --------------------------------------------------

def rank_order(values, mask):
    """values inside the mask -> uniform order in [0, 1] (small value = appears first)."""
    o = np.zeros(values.shape, np.float32)
    idx = np.flatnonzero(mask.ravel() > 0)
    v = values.ravel()[idx]
    ranks = np.empty(len(idx), np.float64)
    ranks[np.argsort(v, kind="stable")] = np.arange(len(idx))
    o.ravel()[idx] = ranks / max(1, len(idx) - 1)
    return o


def order_map(A, B, mask, kind):
    if kind == "luma":
        L = T.gray_of(A).astype(np.float32)
        return rank_order(-L, mask)                      # bright first, like luma_mask
    edges = cv2.Canny(T.gray_of(B), 60, 160)
    dist = cv2.distanceTransform(255 - edges, cv2.DIST_L2, 5).astype(np.float32)
    return rank_order(dist, mask)                        # B's own edges first


def reveal_mix(order, tm, soft=REVEAL_SOFT):
    """0 = A, 1 = B; every pixel is 0 at tm = 0 and 1 at tm = 1 (the luma_mask formula)."""
    p = tm * (1.0 + soft) - soft / 2.0
    return np.clip((p - order) / soft + 0.5, 0.0, 1.0).astype(np.float32)


def curl_noise(h, w, mask, seed=0, feather_px=None):
    rng = np.random.default_rng(seed)
    psi = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0),
                           MELT_SIGMA * min(h, w))
    vx = cv2.Sobel(psi, cv2.CV_32F, 0, 1, ksize=3)
    vy = -cv2.Sobel(psi, cv2.CV_32F, 1, 0, ksize=3)
    v = np.stack([vx, vy], -1)
    mag = np.linalg.norm(v, axis=2)
    ref = np.percentile(mag[mask > 0], 99) if (mask > 0).any() else mag.max()
    v /= max(ref, 1e-6)
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    if feather_px is None:
        feather = np.clip(dist / FEATHER_PX, 0, 1)
    else:
        # melt-soft: the detector dilates the mask 21 px past the object, so the ramp starts
        # 24 px inside the mask boundary and is fully on at 24 + feather_px
        feather = np.clip((dist - 24.0) / feather_px, 0, 1)
    feather = cv2.GaussianBlur(feather.astype(np.float32), (0, 0), 4)
    return (v * feather[..., None]).astype(np.float32)


def morph_frame_mixed(A, B, corr, t_warp, t_mix, mix_override=None, cfg=T.TCFG):
    """transitions.morph_frame with the per-pixel mix replaced inside the mask."""
    dAB, dBA = corr["dAB"], corr["dBA"]
    IA, cA = T.forward_splat(A, dAB, t_warp, corr["wA"], cfg)
    IB, cB = T.forward_splat(B, dBA, 1.0 - t_warp, corr["wB"], cfg)
    fA = T.backward_warp(A, -t_warp * dAB).astype(np.float32)
    fB = T.backward_warp(B, -(1.0 - t_warp) * dBA).astype(np.float32)
    th = cfg["hole_thresh"]
    IA = T.fill_holes(IA, cA, fA, th)
    IB = T.fill_holes(IB, cB, fB, th)
    mix = (np.full(cA.shape, t_mix, np.float32) if mix_override is None
           else mix_override.astype(np.float32))
    mix = np.where(cA < th, 1.0, mix)
    mix = np.where(cB < th, 0.0, mix)
    mix = cv2.GaussianBlur(mix, (0, 0), cfg["mix_blur"])[..., None]
    return T.to_u8(IA * (1 - mix) + IB * mix)


def iter_frames_tr14(A, B, spec, corr, variant, mask):
    """transitions.iter_frames for the morph style with the variant's effect inside the mask."""
    n = spec.n_frames()
    h, w = A.shape[:2]
    cache = T.color_cache(A, B)
    sA, sB = T.lab_stats(A, lab=cache[0]), T.lab_stats(B, lab=cache[2])
    F = cv2.GaussianBlur((mask > 0).astype(np.float32), (0, 0), MIX_FEATHER_SIGMA)
    order = order_map(A, B, mask, variant) if variant in ("luma", "edge-grow") else None
    flow = (curl_noise(h, w, mask, feather_px=64) if variant == "melt-soft"
            else curl_noise(h, w, mask) if variant == "melt" else None)
    gx, gy = T._grid(h, w)
    amp = MELT_AMP * max(h, w)
    for i in range(n):
        if i == 0:
            yield A.copy()
            continue
        if i == n - 1:
            yield B.copy()
            continue
        tw, tm, u = spec.progress(i)
        Ai, Bi = T.color_pair_at(A, B, sA, sB, u, spec.color_strength, T.TCFG, cache)
        override = None
        if order is not None:
            override = tm * (1.0 - F) + reveal_mix(order, tm) * F
        f = morph_frame_mixed(Ai, Bi, corr, tw, tm, override)
        if flow is not None:
            s = amp * float(np.sin(np.pi * u))
            f = cv2.remap(f, gx + s * flow[..., 0], gy + s * flow[..., 1],
                          cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        yield f


# ---- the box-edge metric (Reveal harness O, adapted to a real photo) ------------

def pick_edge(gA, mask):
    """A vertical edge inside the mask's largest component on which straightness can be
    measured: among the three strongest columns (|Sobel x| summed over the component's rows,
    6 px apart) the one whose own residual on A is lowest. Returns
    (x0, y_lo, y_hi, sign, bbox, wobble_A) or None. sign = -1 for a light->dark step."""
    n, lab, st, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if n <= 1:
        return None
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = [int(v) for v in st[i, :4]]
    y_lo, y_hi = y + h // 10, y + h - h // 10
    if y_hi - y_lo < 60:
        return None
    sx = cv2.Sobel(gA.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
    x_lo, x_hi = max(30, x - 20), min(gA.shape[1] - 30, x + w + 20)
    if x_hi <= x_lo:
        return None
    col = sx[y_lo:y_hi, x_lo:x_hi].sum(0)
    mag = np.abs(col).copy()
    best = None
    for _ in range(3):
        k = int(np.argmax(mag))
        if mag[k] <= 0:
            break
        x0 = x_lo + k
        sign = -1.0 if col[k] < 0 else 1.0
        wa = edge_wobble(gA, x0, y_lo, y_hi, sign)
        if wa is not None and (best is None or wa < best[5]):
            best = (x0, y_lo, y_hi, sign, (x, y, w, h), wa)
        mag[max(0, k - 6):k + 7] = 0
    return best


def edge_wobble(gray, x0, y_lo, y_hi, sign, half=10):
    """Residual of the tracked edge from a fitted quadratic (harness _edge_wobble: signed
    single-transition tracking in a +-half px window; the caller shifts x0 by the camera
    motion expected at that frame)."""
    g = gray.astype(np.float32)
    x0 = int(round(x0))
    xs, ys = [], []
    for yy in range(y_lo, y_hi, 6):
        d = np.diff(g[yy, x0 - half:x0 + half]) * sign
        k = int(np.argmax(d))
        if d[k] > 20 and 0 < k < len(d) - 1:
            sub = (d[k + 1] - d[k - 1]) / (2 * (2 * d[k] - d[k - 1] - d[k + 1]) + 1e-9)
            xs.append(x0 - half + k + 0.5 + float(np.clip(sub, -0.5, 0.5)))
            ys.append(float(yy))
    if len(xs) < 8:
        return None
    xs, ys = np.array(xs), np.array(ys)
    Q = np.vstack([ys ** 2, ys, np.ones_like(ys)]).T
    c, *_ = np.linalg.lstsq(Q, xs, rcond=None)
    # 90th percentile, not the harness's max: on a real box edge (door frame, dents,
    # strokes crossing it) a few rows latch onto the wrong transition in every frame
    return round(float(np.percentile(np.abs(xs - Q @ c), 90)), 2)


# ---- render ---------------------------------------------------------------------

def mask_overlay(A, mask, edge):
    img = A.copy()
    red = np.zeros_like(img)
    red[..., 0] = 255
    m = (mask > 0)[..., None]
    img = np.where(m, T.to_u8(img * 0.55 + red * 0.45), img)
    if edge is not None:
        x0, y_lo, y_hi = edge[:3]
        cv2.line(img, (x0, y_lo), (x0, y_hi), (0, 255, 0), 3)
    return img


def render(base, out, seconds, pairs):
    OUT = Path(out)
    summary_path = OUT / "tr14.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    for pid in pairs:
        d = Path(base) / f"pair_{pid}"
        A = cv2.cvtColor(cv2.imread(str(d / "A.png")), cv2.COLOR_BGR2RGB)
        B = cv2.cvtColor(cv2.imread(str(d / "B.png")), cv2.COLOR_BGR2RGB)
        h, w = A.shape[:2]
        gA, gB = T.gray_of(A), T.gray_of(B)
        fields = {"dis": load_field(d, "dis"), "roma": load_field(d, "roma")}
        H, dH_AB, dH_BA, sp = homography_fields(gA, gB)
        mask = changed_mask(A, B, H)
        F = cv2.GaussianBlur((mask > 0).astype(np.float32), (0, 0), MIX_FEATHER_SIGMA)
        F_B = cv2.warpPerspective(F, H, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        edge = pick_edge(gA, mask)
        shift_x = 0.0
        if edge is not None:
            ym = (edge[1] + edge[2]) // 2
            shift_x = float(dH_AB[ym, edge[0], 0])       # camera motion at the edge, A -> B
        po = OUT / pid
        po.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(po / "mask.jpg"), cv2.cvtColor(mask_overlay(A, mask, edge), cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 85])
        pair_info = {"canvas": [w, h], "sparse_inliers": sp[1] if sp else 0,
                     "mask_frac": round(float((mask > 0).mean()), 3),
                     "edge": None if edge is None else {"x0": edge[0], "y_lo": edge[1], "y_hi": edge[2],
                                                        "sign": edge[3], "bbox": list(edge[4]),
                                                        "camera_shift_x": round(shift_x, 2)},
                     "wobble_A": None if edge is None else edge[5],
                     "wobble_B": None if edge is None else edge_wobble(gB, edge[0] + shift_x, *edge[1:4])}
        print(pid, json.dumps(pair_info), flush=True)
        summary.setdefault(pid, {}).update(pair_info)
        for variant in RUN:
            tag = f"{variant}_{seconds:g}s"
            o = po / tag
            o.mkdir(parents=True, exist_ok=True)
            corr = build_corr(fields, variant, dH_AB, dH_BA, F, F_B)
            spec = T.spec_from("morph", seconds=seconds)
            n = spec.n_frames()
            stats = T.StreamStats(n)
            enc = T.FrameEncoder(o / "transition.mp4", w, h, spec.fps)
            probe_idx = {n // 4, n // 2, (3 * n) // 4}
            wob = []
            t0 = time.time()
            try:
                for i, f in enumerate(iter_frames_tr14(A, B, spec, corr, variant, mask)):
                    enc.write(f)
                    stats.add(i, f)
                    if i == n // 2:
                        cv2.imwrite(str(o / "mid.jpg"), cv2.cvtColor(f, cv2.COLOR_RGB2BGR),
                                    [cv2.IMWRITE_JPEG_QUALITY, 90])
                    if i in probe_idx and edge is not None:
                        tw = spec.progress(i)[0]
                        wob.append(edge_wobble(T.gray_of(f), edge[0] + tw * shift_x, *edge[1:4]))
                written = enc.close()
            except BaseException:
                enc.abort()
                raise
            render_s = round(time.time() - t0, 2)
            ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR),
                                   [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ok:
                (o / "strip.jpg").write_bytes(buf.tobytes())
            in_mask = np.linalg.norm(corr["dAB"], axis=2)[mask > 0]
            wob_ok = [v for v in wob if v is not None]
            rep = {"pair": pid, "variant": variant, "tag": tag, "seconds": seconds,
                   "spec": T.asdict(spec), "canvas": [w, h], "n_frames": written,
                   "render_s": render_s,
                   "median_disp_px": round(float(np.median(np.linalg.norm(corr["dAB"], axis=2))), 2),
                   "in_mask_disp_median_px": round(float(np.median(in_mask)), 2) if in_mask.size else None,
                   "wobble_frames": wob, "wobble_max": max(wob_ok) if wob_ok else None,
                   "quality": stats.quality(A, B)}
            (o / "report.json").write_text(json.dumps(rep, indent=2))
            summary[pid][tag] = {k: rep[k] for k in ("render_s", "median_disp_px", "in_mask_disp_median_px",
                                                     "wobble_max", "wobble_frames")}
            q = rep["quality"]
            summary[pid][tag].update({"warping_error": q["warping_error"],
                                      "edge_ratio": q["flicker"]["edge_ratio"],
                                      "max_step": q["flicker"]["max"],
                                      "endpoint": [q["endpoint"]["first_vs_A"], q["endpoint"]["last_vs_B"]]})
            print(f"  {pid} {tag}: {written} frames, render {render_s}s, in-mask disp "
                  f"{rep['in_mask_disp_median_px']} px, wobble {rep['wobble_max']}, edge_ratio "
                  f"{q['flicker']['edge_ratio']}, warping {q['warping_error']}, endpoints "
                  f"{q['endpoint']['first_vs_A']}/{q['endpoint']['last_vs_B']}", flush=True)
            summary_path.write_text(json.dumps(summary, indent=2))


# ---- page -------------------------------------------------------------------------

DESC = {
    "dis": "the current tool: homography + DIS residual, DIS consistency as the splat weight",
    "roma": "the RoMa field, RoMa certainty as the splat weight (the clips you graded on 2026-09-15)",
    "roma-x-cert": "TR2d as written: RoMa displacement × certainty (both directions)",
    "hold": "TR2d, residual form: camera motion + (RoMa − camera) × certainty; uncertain content crossfades in place — the named 'fade in place' mode",
    "hold-dis": "the same hold built from the tool's own DIS field, no RoMa: camera motion + (DIS − camera) × (1 − changed mask); the mask gates the residual instead of a certainty",
    "luma": "hold field; inside the changed mask the new content appears in order of the old content's brightness (bright first)",
    "edge-grow": "hold field; inside the changed mask the new content grows outward from its own edges (lines first, fills after)",
    "melt": "hold field; inside the changed mask the picture is swirled by a smooth divergence-free noise field that rises and falls with sin(πu): zero at both ends; feather 32 px (the swirl reaches the object's edge)",
    "melt-soft": "melt with the feather moved off the object: zero within 24 px of the mask boundary (the detector's dilation), then a 64 px ramp",
}


def page(out, pairs):
    from bench_transitions import label_strip
    OUT = Path(out)
    summary = json.loads((OUT / "tr14.json").read_text())
    rel = lambda p: os.path.relpath(p, OUT)
    html = ["<!doctype html><meta charset=utf-8><title>TR14 — what the changed region does</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1750px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".top{display:flex;gap:12px;align-items:flex-start;margin:8px 0}.top img{height:200px}"
            ".row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".cell video{width:100%;max-height:560px;background:#000}.cell img{max-width:100%;display:block;margin-top:6px}"
            "code{color:#9cf}.legend td{padding:3px 10px;vertical-align:top}.pick label{margin-right:12px}"
            "textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}button{padding:6px 12px}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}"
            "table.num{border-collapse:collapse;font-size:13px}table.num td,table.num th{border:1px solid #333;padding:3px 8px;text-align:right}table.num th:first-child,table.num td:first-child{text-align:left}</style>",
            "<h1>TR14 — what the changed region does between the endpoints (2026-09-15)</h1>",
            "<div class=hint><b>What varies: the correspondence field and what happens inside the changed-region mask.</b> "
            "Every clip is the <code>morph</code> preset (ease curves, color path 0.7) at the same canvas from the same photos; the "
            "encoder and the quality basket are the tool's. The mask (red overlay on the start photo) is Reveal's changed-region "
            "detector on the homography-aligned pair; the green line is the vertical edge on which straightness is measured "
            "(90th percentile of the residual from a fitted quadratic, px; Reveal harness O's tracker, on the photos' own edge first). "
            "Pick the variant closest to what you want per pair, tick <b>acceptable as-is</b> only if it is, write what the changed "
            "region should do instead if nothing fits, then <b>Export picks</b> (tr14_picks.json, drop it next to this page).</div>",
            "<h3>The nine variants</h3><table class=legend>"]
    for v in VARIANTS:
        html.append(f"<tr><td><code>{v}</code></td><td>{DESC[v]}</td></tr>")
    html.append("</table><p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>")
    for pid in pairs:
        s = summary.get(pid, {})
        tags = [t for t in s if isinstance(s[t], dict) and "warping_error" in s[t]]
        secs = sorted({float(t.rsplit("_", 1)[1].rstrip("s")) for t in tags})
        html.append(f"<h2 id='{pid}'>{pid} <small>canvas {s.get('canvas')} · mask {s.get('mask_frac')} of the canvas · "
                    f"edge straightness on the photos themselves A {s.get('wobble_A')} / B {s.get('wobble_B')} px</small></h2>")
        html.append(f"<div class=top><img src='{rel(OUT / pid / 'mask.jpg')}' title='changed-region mask and the measured edge'></div>")
        html.append("<table class=num><tr><th>variant</th><th>s</th><th>in-mask disp px</th><th>edge straightness px (max of t=¼,½,¾)</th>"
                    "<th>warping error</th><th>edge_ratio</th><th>endpoints</th><th>render s</th></tr>")
        for sec in secs:
            for v in VARIANTS:
                tag = f"{v}_{sec:g}s"
                r = s.get(tag)
                if not r:
                    continue
                html.append(f"<tr><td><code>{v}</code></td><td>{sec:g}</td><td>{r['in_mask_disp_median_px']}</td><td>{r['wobble_max']}</td>"
                            f"<td>{r['warping_error']}</td><td>{r['edge_ratio']}</td><td>{r['endpoint'][0]} / {r['endpoint'][1]}</td><td>{r['render_s']}</td></tr>")
        html.append("</table>")
        html.append(f"<div class=pick><b>Closest to what you want:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pid}' value='{v}' onchange='save()'> {v}</label>" for v in VARIANTS)
            + f" <label><input type=radio name='pick_{pid}' value='none' onchange='save()'> none</label>"
            + f" &nbsp; <label><input type=checkbox id='ok_{pid}' onchange='save()'> <b>acceptable as-is</b></label></div>")
        html.append(f"<textarea id='note_{pid}' rows=2 placeholder='what should the changed region do here? what is wrong in the closest clip?' oninput='save()'></textarea>")
        for sec in secs:
            cells = []
            for v in VARIANTS:
                tag = f"{v}_{sec:g}s"
                r = s.get(tag)
                if not r:
                    continue
                o = OUT / pid / tag
                if (o / "strip.jpg").exists() and not (o / "strip_labeled.jpg").exists():
                    label_strip(o / "strip.jpg", o / "strip_labeled.jpg", int(round(sec * 30)), sec)
                cells.append(f"<div class=cell><code>{tag}</code> · in-mask disp {r['in_mask_disp_median_px']} px · straightness {r['wobble_max']} px · "
                             f"warping {r['warping_error']} · edge_ratio {r['edge_ratio']}"
                             f"<br><video src='{rel(o / 'transition.mp4')}' controls loop muted playsinline preload=metadata></video>"
                             f"<img src='{rel(o / 'strip_labeled.jpg')}'></div>")
            for i in range(0, len(cells), 2):
                html.append("<div class=row>" + "".join(cells[i:i + 2]) + "</div>")
    html.append("""<script>
const KEY='tr14_picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);const ok=document.getElementById('ok_'+id);
 if((r&&r.value)||(n&&n.value)||(ok&&ok.checked))p[id]={pick:r?r.value:'',acceptable_as_is:!!(ok&&ok.checked),note:n?n.value:''};});return p;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(collect()));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].pick}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;const ok=document.getElementById('ok_'+id);if(ok)ok.checked=!!p[id].acceptable_as_is;}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),page:'tr14',picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tr14_picks.json';a.click();document.getElementById('status').textContent='tr14_picks.json downloaded';}
restore();
</script>""")
    (OUT / "index.html").write_text("\n".join(html))
    print(f"wrote {OUT / 'index.html'}")


if __name__ == "__main__":
    if len(sys.argv) > 5 and sys.argv[1] == "--render":
        render(sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5:])
    elif len(sys.argv) > 3 and sys.argv[1] == "--page":
        page(sys.argv[2], sys.argv[3:])
    else:
        sys.exit(__doc__)
