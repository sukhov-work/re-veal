#!/usr/bin/env python3
"""Chain research (2026-10-09, the owner's box photos): several photos of one subject become ONE
continuous transition in ONE frame. Every photo but the last is warped onto the LAST photo's frame
by Reveal's own aligner (reveal.run_alignment: BEFORE = the reference, the strict `reshot` profile,
ECC and the gated residual) and kept in the reference's FULL frame (`--crop none`, the default since
the owner's "do not crop anything"; a pixel no photo covers keeps its last known content: the
previous still's, or for the first still the next still's, or the reference's; `--crop valid` crops
to the rectangle every warped photo covers instead),
then each still is pinned to the last one by a homography (MAGSAC++; `--pin similarity` for 4 DOF)
estimated from SIFT matches in the WALL RING around the two boxes (the changed objects; `--no-anchor`
skips it), and the TR14 `luma` effect (inside the changed-region mask B appears in order of A's
brightness) runs across the consecutive pairs under a single ease over --seconds; then the last photo
holds --hold s. The field between two pinned stills is the mask-held one (`--field hold-dis`: no
camera motion, the DIS residual zeroed inside the feathered mask, so the boxes' content stays put;
`--field hold` is the TR14 `luma` clip's field, the residual scaled by the DIS certainty).
`--variant tool-luma` is the transitions tool's own `luma` preset instead (no field, no mask: the
whole frame of B appears in order of A's brightness, the tool's `luma_mask`), on the pinned stills;
`--variant tool-luma-melt-soft` adds melt-soft's swirl inside the changed-region mask to it.
Not part of either tool; imports reveal and transitions (research only, as tr14_variants.py does).
Runs in `.venv`.

  chain_luma.py PHOTO... --out DIR [--seconds 3] [--hold 3] [--lead 0] [--max-long 1920]
                [--mode reshot|loose] [--ease smootherstep|linear] [--variant luma|hold-dis|luma-melt-soft]
                [--size 1080x1350] [--fps 30] [--color 0.7] [--no-anchor] [--pin homography|similarity]
                [--field hold-dis|hold] [--crop none|valid]
Outputs in DIR: aligned/<i>_<name>.jpg (the stills in the common frame, after the pin),
chain.mp4 (and chain_<size>.mp4), strip.jpg (one tile per 0.25 s, labelled), boxes.jpg (the two
boxes and their rings on the first still), report.json: Reveal's metrics per warped photo, the
boxes, the ring drift of every still against the last (dx, dy, response) before and after the
pin, per segment the inliers left between stills, the changed-region share and the largest corner
motion of the leftover homography, and the timeline.
"""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import transitions as T  # noqa: E402
import reveal as rv  # noqa: E402  (research only: the two tools never import each other)
import tr14_variants as V  # noqa: E402

RING_GROW = 0.35          # the ring around a box: its box grown by this fraction of its size
RING_INSET = 10           # px: the box interior blanked that far outside the box too
RANSAC_PX = 3.0


def smootherstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def align_onto(ref_path, path, workdir, mode):
    """Reveal's alignment of PATH onto REF_PATH (B onto A). Returns (A_full, warped_full, valid, metrics)."""
    for m in ((mode,) if mode == "loose" else ("reshot", "loose")):
        job = rv.Job(uuid.uuid4().hex[:16], workdir, m)
        rv.run_alignment(job, str(ref_path), str(path))
        if job.state != "failed":
            break
        print(f"  {Path(path).name}: Reveal {m} refused: {job.error}", flush=True)
    else:
        raise SystemExit(f"{path}: Reveal refused in every mode")
    A, B = job.fullA, job.fullB
    hA, wA = A.shape[:2]
    H = job.H_full / job.H_full[2, 2]
    warped = cv2.warpPerspective(B, H, (wA, hA), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    valid = rv.warp_valid_mask(B.shape, H, (wA, hA))
    if job.flow_work is not None:
        warped = rv.apply_residual(warped, job.flow_work, 1.0)
        valid = (rv.apply_residual(valid, job.flow_work, 1.0) > 200).astype(np.uint8) * 255
    return A, warped, valid, dict(job.metrics, mode=m, residual=job.flow_work is not None)


def find_boxes(S0, S1):
    """The two largest components of the changed region between the first two stills (the repainted objects)."""
    gA, gB = T.gray_of(S0), T.gray_of(S1)
    H, _, _, _ = V.homography_fields(gA, gB)
    mask = V.changed_mask(S0, S1, H)
    n, lab, st, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    comps = sorted(range(1, n), key=lambda i: -st[i, cv2.CC_STAT_AREA])[:2]
    return [tuple(int(v) for v in st[i, :4]) for i in sorted(comps, key=lambda i: st[i, 0])], mask


def ring_mask(shape, boxes):
    """uint8 mask of the wall rings: each box grown by RING_GROW, minus the box itself grown by RING_INSET."""
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    for x, y, bw, bh in boxes:
        gx, gy = int(bw * RING_GROW), int(bh * RING_GROW)
        m[max(0, y - gy):min(h, y + bh + gy), max(0, x - gx):min(w, x + bw + gx)] = 255
    for x, y, bw, bh in boxes:
        m[max(0, y - RING_INSET):min(h, y + bh + RING_INSET), max(0, x - RING_INSET):min(w, x + bw + RING_INSET)] = 0
    return m


def ring_shift(gref, g, box, shape):
    """Phase correlation of the wall ring around one box between two stills -> (dx, dy, response)."""
    h, w = shape
    x, y, bw, bh = box
    gx, gy = int(bw * RING_GROW), int(bh * RING_GROW)
    X0, Y0, X1, Y1 = max(0, x - gx), max(0, y - gy), min(w, x + bw + gx), min(h, y + bh + gy)
    X1, Y1 = X1 - (X1 - X0) % 2, Y1 - (Y1 - Y0) % 2     # an odd window biases phaseCorrelate by 0.5 px
    a, b = gref[Y0:Y1, X0:X1].astype(np.float32).copy(), g[Y0:Y1, X0:X1].astype(np.float32).copy()
    ix0, iy0 = max(0, x - X0 - RING_INSET), max(0, y - Y0 - RING_INSET)
    ix1, iy1 = x - X0 + bw + RING_INSET, y - Y0 + bh + RING_INSET
    for im in (a, b):
        im[iy0:iy1, ix0:ix1] = im.mean()
    win = cv2.createHanningWindow((a.shape[1], a.shape[0]), cv2.CV_32F)
    (dx, dy), r = cv2.phaseCorrelate(a, b, win)
    return round(float(dx), 2), round(float(dy), 2), round(float(r), 3)


def pin_to(gref, g, rmask, kind="similarity"):
    """A similarity (4 DOF) or a homography (8 DOF, MAGSAC++) mapping still g onto the reference from
    SIFT matches inside the ring mask. Returns (M 2x3 | H 3x3 | None, matches, inliers)."""
    sift = cv2.SIFT_create()
    kr, dr = sift.detectAndCompute(gref, rmask)
    kg, dg = sift.detectAndCompute(g, rmask)
    if dr is None or dg is None or len(kr) < 8 or len(kg) < 8:
        return None, 0, 0
    bf = cv2.BFMatcher(cv2.NORM_L2)
    good = [m for m, n in bf.knnMatch(dg, dr, k=2) if m.distance < 0.75 * n.distance]
    if len(good) < 8:
        return None, len(good), 0
    src = np.float32([kg[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kr[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    if kind == "homography":
        M, inl = cv2.findHomography(src, dst, cv2.USAC_MAGSAC, RANSAC_PX, confidence=0.999)
    else:
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=RANSAC_PX, confidence=0.999, refineIters=10)
    return M, len(good), int(inl.sum()) if inl is not None else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=3.0, help="the whole chain of transitions")
    ap.add_argument("--hold", type=float, default=3.0, help="seconds on the last photo")
    ap.add_argument("--lead", type=float, default=0.0, help="seconds on the first photo")
    ap.add_argument("--max-long", type=int, default=1920)
    ap.add_argument("--mode", default="reshot", choices=("reshot", "loose"))
    ap.add_argument("--ease", default="smootherstep", choices=("smootherstep", "linear"))
    ap.add_argument("--variant", default="luma", choices=("luma", "hold-dis", "luma-melt-soft", "tool-luma", "tool-luma-melt-soft"))
    ap.add_argument("--crop", default="none", choices=("none", "valid"), help="none = the reference's full frame (default); valid = the rectangle every warped photo covers")
    ap.add_argument("--size", default="", help="also write chain_<WxH>.mp4 scaled to this size")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--color", type=float, default=0.7, help="the tool's color path strength")
    ap.add_argument("--no-anchor", action="store_true", help="skip the pin to the last still from the wall rings")
    ap.add_argument("--pin", default="homography", choices=("homography", "similarity"), help="the map of the pin (default homography, MAGSAC++)")
    ap.add_argument("--field", default="hold-dis", choices=("hold-dis", "hold"), help="the field between two pinned stills (see the head)")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "aligned").mkdir(exist_ok=True)
    photos = [Path(p).expanduser().resolve() for p in a.photos]
    if len(photos) < 2:
        raise SystemExit("two photos at least")
    ref = photos[-1]
    report = {"photos": [p.name for p in photos], "reference": ref.name, "args": vars(a), "align": {}, "segments": []}

    # 1. every photo onto the last photo's frame (Reveal), one common crop, one canvas
    t0 = time.time()
    warped, valids, refA = [], [], None
    for p in photos[:-1]:
        t1 = time.time()
        A, W, Vm, met = align_onto(ref, p, out / "reveal", a.mode)
        refA = A
        warped.append(W)
        valids.append(Vm)
        met["seconds"] = round(time.time() - t1, 1)
        report["align"][p.name] = met
        print(f"  {p.name} -> {ref.name}: {met.get('method')} {met.get('inliers')} inliers, {met.get('rmse_px')} px, "
              f"confidence {met.get('confidence')}, mode {met['mode']}, residual {met['residual']}, {met['seconds']} s", flush=True)
    fill_share = []
    if a.crop == "valid":
        valid_all = valids[0].copy()
        for v in valids[1:]:
            valid_all = cv2.bitwise_and(valid_all, v)
        x, y, w, h = rv.crop_rect(valid_all)
    else:
        # the full frame; a pixel a photo does not cover keeps its last known content
        x, y, w, h = 0, 0, refA.shape[1], refA.shape[0]
        base = refA
        for j in range(len(warped) - 1, 0, -1):
            base = np.where(valids[j][..., None] > 0, warped[j], base)
        filled = []
        prev = base
        for k, (W, Vm) in enumerate(zip(warped, valids)):
            f = np.where(Vm[..., None] > 0, W, prev)
            filled.append(f)
            prev = f
            fill_share.append(round(float((Vm == 0).mean()), 4))
        warped = filled
    stills = [W[y:y + h, x:x + w] for W in warped] + [refA[y:y + h, x:x + w]]
    report["fill_share"] = fill_share
    stills = [rv.scaled_copy(s, a.max_long)[0] for s in stills]
    H0, W0 = stills[0].shape[:2]
    W0, H0 = W0 - W0 % 2, H0 - H0 % 2
    stills = [np.ascontiguousarray(s[:H0, :W0]) for s in stills]
    report["crop"] = {"full": [int(x), int(y), int(w), int(h)], "canvas": [W0, H0]}
    print(f"  aligned {len(stills)} stills onto {ref.name}: crop {a.crop} {w}x{h} at ({x},{y}) of the full frame, canvas {W0}x{H0}, "
          f"filled share per still {fill_share}, {time.time() - t0:.1f} s", flush=True)

    # 2. the boxes (from the first repaint), the ring drift before the pin, the pin, the drift after
    boxes, mask01 = find_boxes(stills[0], stills[1])
    report["boxes"] = [list(b) for b in boxes]
    if a.crop == "none":
        sc = W0 / refA.shape[1]
        box_fill = []
        for Vm in valids:
            vs = cv2.resize(Vm, (W0, H0), interpolation=cv2.INTER_NEAREST)
            box_fill.append([round(float((vs[by:by + bh, bx:bx + bw] == 0).mean()), 4) for bx, by, bw, bh in boxes])
        report["box_fill_share"] = box_fill
        print(f"  filled share inside the boxes per still (left, right): {box_fill}", flush=True)
    rmask = ring_mask((H0, W0), boxes)
    grays = [T.gray_of(s) for s in stills]
    # phaseCorrelate's sub-pixel peak carries a bias of up to 0.5 px on some windows (the reference
    # against itself read dy 0.5 on the 1->7 pair): every shift is reported minus that self-reading
    def drift(b):
        bias = ring_shift(grays[-1], grays[-1], b, (H0, W0))
        return [(round(dx - bias[0], 2), round(dy - bias[1], 2), r) for dx, dy, r in (ring_shift(grays[-1], g, b, (H0, W0)) for g in grays)], bias
    before, biases = zip(*[drift(b) for b in boxes])
    before = list(before)
    report["ring_bias"] = [list(bb) for bb in biases]
    for bi, b in enumerate(boxes):
        print(f"  box {bi} {b}: ring drift vs the last still before the pin {before[bi]} (self-reading {biases[bi]} subtracted)", flush=True)
    pins = []
    if not a.no_anchor:
        for k in range(len(stills) - 1):
            M, nm, ni = pin_to(grays[-1], grays[k], rmask, a.pin)
            if M is None:
                pins.append({"still": photos[k].name, "matches": nm, "inliers": ni, "applied": False})
                print(f"  pin {photos[k].name}: no similarity ({nm} matches): left as Reveal aligned it", flush=True)
                continue
            if M.shape[0] == 3:
                M = M / M[2, 2]
                stills[k] = cv2.warpPerspective(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            else:
                stills[k] = cv2.warpAffine(stills[k], M, (W0, H0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            s = float(np.hypot(M[0, 0], M[0, 1]))
            rot = float(np.degrees(np.arctan2(M[0, 1], M[0, 0])))
            grays[k] = T.gray_of(stills[k])
            pins.append({"still": photos[k].name, "matches": nm, "inliers": ni, "applied": True,
                         "scale": round(s, 5), "rotation_deg": round(rot, 3), "shift_px": [round(float(M[0, 2]), 2), round(float(M[1, 2]), 2)]})
            print(f"  pin {photos[k].name}: {ni} of {nm} ring matches, scale {s:.5f}, rotation {rot:.3f} deg, shift ({M[0, 2]:.2f}, {M[1, 2]:.2f}) px", flush=True)
    after = [drift(b)[0] for b in boxes]
    for bi, b in enumerate(boxes):
        print(f"  box {bi}: ring drift after the pin {after[bi]}", flush=True)
    report["pin"] = pins
    report["ring_drift"] = {"before": before, "after": after,
                            "max_abs_before_px": round(max(max(abs(r[0]), abs(r[1])) for rows in before for r in rows), 2),
                            "max_abs_after_px": round(max(max(abs(r[0]), abs(r[1])) for rows in after for r in rows), 2)}
    for i, (s, p) in enumerate(zip(stills, photos)):
        cv2.imwrite(str(out / "aligned" / f"{i}_{p.stem}.jpg"), cv2.cvtColor(s, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
    vis = V.mask_overlay(stills[0], mask01, None)
    for bx, by, bw, bh in boxes:
        cv2.rectangle(vis, (bx, by), (bx + bw, by + bh), (0, 255, 0), 3)
    vis[rmask > 0] = T.to_u8(vis[rmask > 0] * 0.6 + np.array([0, 0, 255]) * 0.4)
    cv2.imwrite(str(out / "boxes.jpg"), cv2.cvtColor(vis, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])

    # 3. the segments: what is left between consecutive stills, the changed region, the luma order
    segs = []
    for k in range(len(stills) - 1):
        t1 = time.time()
        A, B = stills[k], stills[k + 1]
        gA, gB = grays[k], grays[k + 1]
        H, dH_AB, dH_BA, sp = V.homography_fields(gA, gB)
        if not a.no_anchor:
            # the stills are pinned in one frame: a whole-frame homography between two of them fits a
            # mix of the wall and the pavement planes and moves the boxes by 1-3 px; the field carries none
            H, dH_AB, dH_BA = np.eye(3), np.zeros_like(dH_AB), np.zeros_like(dH_BA)
        corners = np.array([[0, 0], [W0, 0], [W0, H0], [0, H0]], np.float32).reshape(-1, 1, 2)
        moved = cv2.perspectiveTransform(corners, np.linalg.inv(H)).reshape(-1, 2) - corners.reshape(-1, 2)
        centres = np.array([[bx + bw / 2, by + bh / 2] for bx, by, bw, bh in boxes], np.float32).reshape(-1, 1, 2)
        box_moved = cv2.perspectiveTransform(centres, np.linalg.inv(H)).reshape(-1, 2) - centres.reshape(-1, 2)
        mask = V.changed_mask(A, B, H)
        F = cv2.GaussianBlur((mask > 0).astype(np.float32), (0, 0), V.MIX_FEATHER_SIGMA)
        F_B = cv2.warpPerspective(F, H, (W0, H0), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        if a.variant in ("tool-luma", "tool-luma-melt-soft"):
            dis, corr = {"diag": {}}, None
        else:
            dis = T.dense_displacement(A, B)
            fields = {"dis": dis, "roma": dis}       # the RoMa field was never adopted: the DIS field stands in
            corr = V.build_corr(fields, a.field, dH_AB, dH_BA, F, F_B)
        order = V.order_map(A, B, mask, "luma") if a.variant in ("luma", "luma-melt-soft") else None
        flow = V.curl_noise(H0, W0, mask, feather_px=64) if a.variant in ("luma-melt-soft", "tool-luma-melt-soft") else None
        cache = T.color_cache(A, B)
        sA, sB = T.lab_stats(A, lab=cache[0]), T.lab_stats(B, lab=cache[2])
        segs.append(dict(A=A, B=B, corr=corr, F=F, order=order, flow=flow, cache=cache, sA=sA, sB=sB))
        info = {"pair": f"{photos[k].stem}->{photos[k + 1].stem}", "inliers_left": int(sp[1]) if sp else 0,
                "corner_motion_px": round(float(np.linalg.norm(moved, axis=1).max()), 2),
                "box_centre_motion_px": [round(float(v), 2) for v in np.linalg.norm(box_moved, axis=1)],
                "mask_share": round(float((mask > 0).mean()), 3), "median_disp_px": dis["diag"].get("median_disp_px"),
                "mean_certainty": dis["diag"].get("mean_certainty"), "prep_s": round(time.time() - t1, 1)}
        report["segments"].append(info)
        print(f"  segment {info['pair']}: {info['inliers_left']} inliers between the stills, corner motion "
              f"{info['corner_motion_px']} px, at the box centres {info['box_centre_motion_px']} px, mask {info['mask_share']:.3f}, {info['prep_s']} s", flush=True)

    # 4. the frames: one ease over the whole chain, then the hold
    nseg = len(segs)
    N = int(round(a.seconds * a.fps))
    n_lead, n_hold = int(round(a.lead * a.fps)), int(round(a.hold * a.fps))
    ease = smootherstep if a.ease == "smootherstep" else (lambda v: np.clip(v, 0.0, 1.0))
    gx, gy = T._grid(H0, W0)
    amp = V.MELT_AMP * max(H0, W0)
    enc = T.FrameEncoder(out / "chain.mp4", W0, H0, a.fps)
    enc2 = None
    if a.size:
        sw, sh = [int(v) for v in a.size.lower().split("x")]
        enc2 = T.FrameEncoder(out / f"chain_{sw}x{sh}.mp4", sw, sh, a.fps)
    tiles, every = [], max(1, int(round(a.fps / 4)))
    timeline = []

    def put(f, i_global):
        enc.write(f)
        if enc2 is not None:
            enc2.write(cv2.resize(f, (sw, sh), interpolation=cv2.INTER_AREA))
        if i_global % every == 0:
            tl = cv2.resize(f, (int(W0 * 240 / H0), 240), interpolation=cv2.INTER_AREA)
            lab_ = f"f{i_global} {i_global / a.fps:.2f}s"
            cv2.rectangle(tl, (0, 0), (len(lab_) * 9 + 6, 18), (0, 0, 0), -1)
            cv2.putText(tl, lab_, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(tl)

    t0 = time.time()
    g_i = 0
    for _ in range(n_lead):
        put(stills[0], g_i); g_i += 1
    for i in range(N):
        g = float(ease(i / (N - 1))) if N > 1 else 1.0
        pos = g * nseg
        seg = min(int(np.floor(pos)), nseg - 1)
        u = pos - seg
        if i == N - 1 or (u >= 1.0 - 1e-9):
            f, u = stills[seg + 1].copy(), 1.0
        elif u <= 1e-9:
            f = stills[seg].copy()
        else:
            s = segs[seg]
            Ai, Bi = T.color_pair_at(s["A"], s["B"], s["sA"], s["sB"], u, a.color, T.TCFG, s["cache"])
            if a.variant in ("tool-luma", "tool-luma-melt-soft"):
                m = T.luma_mask(Ai, u)[..., None]
                f = T.to_u8(Ai * (1 - m) + Bi * m)
            else:
                override = None
                if s["order"] is not None:
                    override = u * (1.0 - s["F"]) + V.reveal_mix(s["order"], u) * s["F"]
                f = V.morph_frame_mixed(Ai, Bi, s["corr"], u, u, override)
            if s["flow"] is not None:
                sw_ = amp * float(np.sin(np.pi * u))
                f = cv2.remap(f, gx + sw_ * s["flow"][..., 0], gy + sw_ * s["flow"][..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        timeline.append((i, seg, round(u, 4)))
        put(f, g_i); g_i += 1
    for _ in range(n_hold):
        put(stills[-1], g_i); g_i += 1
    n1 = enc.close()
    n2 = enc2.close() if enc2 is not None else None
    rows = [np.hstack(tiles[j:j + 12]) for j in range(0, len(tiles) - len(tiles) % 12, 12)] or [np.hstack(tiles)]
    cv2.imwrite(str(out / "strip.jpg"), cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 82])
    bounds = {}
    for i, seg, u in timeline:
        bounds.setdefault(seg, [i, i])[1] = i
    report["timeline"] = {"lead_frames": n_lead, "transition_frames": N, "hold_frames": n_hold, "written": n1, "written_scaled": n2,
                          "segment_frames": {report["segments"][k]["pair"]: v for k, v in bounds.items()},
                          "render_s": round(time.time() - t0, 1)}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(f"  wrote {out / 'chain.mp4'}: {n1} frames ({n_lead} lead + {N} transition + {n_hold} hold) at {W0}x{H0}, "
          f"render {report['timeline']['render_s']} s; segments by frame: {report['timeline']['segment_frames']}", flush=True)


if __name__ == "__main__":
    main()
