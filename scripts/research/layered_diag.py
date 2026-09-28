#!/usr/bin/env python3
"""Diagnosis of a layered clip on its composite (round 5, 2026-09-28): numbers for a fault the
owner names, measured before the score or the probe changes.

Research script. Imports `layered_probe.py` and `transitions.py` read-only; writes a JSON and,
with --frames, PNG frames under --out. Changes nothing in either tool or in a score.

  end     the owner on mismatch_4 round 4: "at the very end it still seems some boundary where it
          crossfades to final B shot( both buildings and river )". Per frame step from --from to the
          last frame and per region (every `render: false` or rendered layer named in --regions,
          taken from the score's masks), on the L channel of the composite:
            to_B        mean |frame - B| (levels of L, 0..100)
            step        mean |frame[i+1] - frame[i]|
            fade_r2     R^2 of (frame[i+1] - frame[i]) ~ beta (B - frame[i]): the share of the step
                        that a fade toward the final picture explains (a crossfade gives 1)
            motion      (|d| - |d after a DIS warp|) / |d|: the share that motion explains
          and per layer the mean |change| of its premultiplied picture (which layer acts when).
  outline per frame the ridge of L along a layer's running matte contour (a line brighter than
          both of its sides, 10 px outside the contour against 6 px inside and 16 px outside),
          beside the photos' own at t = 0 and t = 1.
  rest    the first and last interior frames against the photos (mean, largest difference, share of
          the canvas more than 4 levels off).
  contrast  per frame the signed contrast of a layer against what lies under it.
  step    frame-to-frame steps between two clip times (a warp switched off at a window's end).
  layers  per frame and per `morph_to` layer its matte, its mix, the px it has moved and has to go,
          and where two layers both show the second photo's content (a duplicate).
  seam    per frame the L step across a line (the running top edge of a `slide_between` backdrop, or
          the alpha 0.5 contour of a layer): a 12-px band above against a 12-px band below, beside
          the same number on A and on B at their own lines.
  fields  (round 6) per `morph_to` layer the travel and the strain of its field ("clouds skewed").
  rim     (round 6) per matte the share of its inner rim that holds the outside colour (a pale
          outline once the layer lies over another).
  holes   (round 6) per frame the share of the canvas where a backdrop's hole fill is seen (a
          smooth dome in the sky, a pale band beside a matte).

  .venv/bin/python scripts/research/layered_diag.py end --score scripts/research/scores/mismatch_4_r4.json \
      --regions sky_b band_core_b water_b --from 0.5 --out DIR [--frames]
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import transitions as T  # noqa: E402
import layered_probe as P  # noqa: E402


def build(score_path, seed=0):
    score = json.loads(Path(score_path).read_text())
    A, B = P.canvas_pair(score["pair"], score.get("max_long", 1920))
    scene = P.Scene(A, B, seed)
    n = max(2, int(round(score.get("seconds", 2.0) * float(score.get("fps", 30)))))
    scene.n = n
    layers = P.build_layers(scene, score)
    return score, scene, layers, A, B, n


def frame_at(layers, A, B, i, n):
    if i == 0:
        return A.copy()
    if i == n - 1:
        return B.copy()
    return P.composite(layers, i / (n - 1))


def L_of(rgb_u8):
    return T.lab_of(rgb_u8)[..., 0].astype(np.float32)


def region_masks(scene, names):
    out = {}
    for nm in names:
        m = scene.masks[nm]
        out[nm] = (m > 0.5)
    return out


def cmd_end(a):
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    regs = region_masks(scene, a.regions)
    regs["frame"] = np.ones((scene.h, scene.w), bool)
    i0 = int(round(getattr(a, "from") * (n - 1)))
    LB = L_of(B)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    gx, gy = np.meshgrid(np.arange(scene.w, dtype=np.float32), np.arange(scene.h, dtype=np.float32))
    rows = []
    prev = frame_at(layers, A, B, i0, n)
    prev_lay = {l.name: _premult(l, i0 / (n - 1)) for l in layers}
    for i in range(i0, n - 1):
        cur = frame_at(layers, A, B, i + 1, n)
        if a.frames:
            cv2.imwrite(str(out / f"f_{i:03d}.png"), cv2.cvtColor(prev, cv2.COLOR_RGB2BGR))
        La, Lb = L_of(prev), L_of(cur)
        d = Lb - La
        e = LB - La
        g0 = cv2.cvtColor(prev, cv2.COLOR_RGB2GRAY)
        g1 = cv2.cvtColor(cur, cv2.COLOR_RGB2GRAY)
        f = dis.calc(g0, g1, None)
        Lw = cv2.remap(Lb, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR)
        dw = Lw - La
        row = {"i": i, "t": round(i / (n - 1), 4), "regions": {}, "layers": {}}
        for nm, m in regs.items():
            dd, ee = d[m], e[m]
            den = float(np.dot(ee, ee)) + 1e-6
            beta = float(np.dot(dd, ee)) / den
            res = dd - beta * ee
            ss = float(np.dot(dd, dd))
            r2 = 1.0 - float(np.dot(res, res)) / (ss + 1e-6) if ss > 1e-3 else 0.0
            raw = float(np.abs(dd).mean())
            row["regions"][nm] = {"to_B": round(float(np.abs(ee).mean()), 3), "step": round(raw, 4),
                                  "fade_r2": round(r2, 3), "beta": round(beta, 4),
                                  "motion": round((raw - float(np.abs(dw[m]).mean())) / max(raw, 1e-6), 3) if raw > 1e-3 else 0.0}
        t1 = (i + 1) / (n - 1)
        for l in layers:
            nxt = _premult(l, t1)
            row["layers"][l.name] = round(float(np.abs(nxt - prev_lay[l.name]).mean()), 4)
            prev_lay[l.name] = nxt
        rows.append(row)
        prev = cur
    (out / "end.json").write_text(json.dumps({"score": a.score, "n": n, "from": i0, "rows": rows}, indent=1))
    names = list(regs)
    print("t      " + "  ".join(f"{nm[:12]:>32}" for nm in names))
    print("       " + "  ".join(f"{'to_B   step  fadeR2 motion':>32}" for _ in names))
    for r in rows:
        print(f"{r['t']:.3f}  " + "  ".join(
            f"{r['regions'][nm]['to_B']:7.2f} {r['regions'][nm]['step']:6.3f} {r['regions'][nm]['fade_r2']:6.2f} {r['regions'][nm]['motion']:6.2f}".rjust(32)
            for nm in names))
    print("layers (mean |change| of the premultiplied picture, levels of 0..255):")
    lay_names = [l.name for l in layers]
    print("t      " + " ".join(f"{nm[:11]:>11}" for nm in lay_names))
    for r in rows:
        print(f"{r['t']:.3f}  " + " ".join(f"{r['layers'][nm]:11.3f}" for nm in lay_names))


def _premult(layer, t):
    rgb, al = layer.render(t)
    return (np.asarray(rgb, np.float32) * al[..., None]).astype(np.float32)


def line_step(L, line, band=12, gap=2):
    """Mean L in the `band` px above a per-column line against the band below it."""
    h, w = L.shape
    yy = np.arange(h, dtype=np.float32)[:, None]
    ln = line[None, :]
    up = (yy < ln - gap) & (yy >= ln - gap - band)
    dn = (yy > ln + gap) & (yy <= ln + gap + band)
    if up.sum() < 50 or dn.sum() < 50:
        return None
    return float(L[dn].mean() - L[up].mean())


def cmd_seam(a):
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lay = next(l for l in layers if l.name == a.layer)
    if getattr(lay, "slide", None) is None:
        raise SystemExit(f"{a.layer} has no slide_between line")
    la, lb, _ = lay.slide
    i0 = int(round(getattr(a, "from") * (n - 1)))
    rows = []
    for i in range(i0, n):
        t = i / (n - 1)
        fr = frame_at(layers, A, B, i, n)
        p = lay.progress(t)
        line = la * (1 - p) + lb * p
        rows.append({"i": i, "t": round(t, 4), "p": round(float(p), 4), "line_mean_y": round(float(line.mean()), 1),
                     "step_L": line_step(L_of(fr), line)})
    ref = {"A_at_its_line": line_step(L_of(A), la), "B_at_its_line": line_step(L_of(B), lb)}
    (out / f"seam_{a.layer}.json").write_text(json.dumps({"score": a.score, "layer": a.layer, "ref": ref, "rows": rows}, indent=1))
    print("reference:", ref)
    for r in rows:
        print(f"{r['t']:.3f} p={r['p']:.3f} line y={r['line_mean_y']:7.1f} step L={r['step_L']}")


def ridge_along(L, alpha, reach=10, inside=6, outside=16):
    """The ridge of L along a matte's contour: for every pixel within `reach` px outside the
    alpha 0.5 contour, L there minus the larger of L `inside` px inside the contour and L
    `outside` px outside it, both taken along the contour's normal (the gradient of the signed
    distance). Positive = a line brighter than both of its sides. Returns the values of the band."""
    hard = (alpha > 0.5).astype(np.uint8)
    if hard.sum() < 100 or (1 - hard).sum() < 100:
        return np.zeros(0, np.float32), np.zeros(alpha.shape, bool)
    d_out = cv2.distanceTransform(1 - hard, cv2.DIST_L2, 5)
    d_in = cv2.distanceTransform(hard, cv2.DIST_L2, 5)
    sd = cv2.GaussianBlur(d_out - d_in, (0, 0), 2.0)
    gy, gx = np.gradient(sd)
    nrm = np.maximum(np.sqrt(gx * gx + gy * gy), 1e-3)
    nx, ny = gx / nrm, gy / nrm
    h, w = alpha.shape
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    Ls = cv2.GaussianBlur(L, (0, 0), 1.5)
    band = (d_out > 0) & (d_out <= reach)
    band[:2] = band[-2:] = False
    band[:, :2] = band[:, -2:] = False
    to_in = -(d_out + inside)
    to_out = (outside - d_out)
    L_in = cv2.remap(Ls, (xs + to_in * nx).astype(np.float32), (ys + to_in * ny).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    L_out = cv2.remap(Ls, (xs + to_out * nx).astype(np.float32), (ys + to_out * ny).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    ridge = Ls - np.maximum(L_in, L_out)
    return ridge, band


def cmd_outline(a):
    """Per frame: the ridge of L along the layer's running matte contour (see ridge_along): the
    mean of its positive part over the band and the share of the band above 2 L, beside the same
    numbers on A with the layer's matte at t = 0 and on B with its matte at t = 1 (what the
    photos hold there themselves)."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lay = next(l for l in layers if l.name == a.layer)
    rows = []

    def one(fr, al):
        ridge, band = ridge_along(L_of(fr), al)
        if a.rows:
            band[: int(a.rows[0] * scene.h)] = False
            band[int(a.rows[1] * scene.h):] = False
        v = ridge[band]
        return {"band_px": int(band.sum()), "ridge_pos_mean": round(float(np.clip(v, 0, None).mean()), 3),
                "share_over_2L": round(float((v > 2.0).mean()), 4), "p95": round(float(np.percentile(v, 95)), 2)}
    ref = {"A_rest": one(A, lay.render(0.0)[1]), "B_rest": one(B, lay.render(1.0)[1])}
    print("reference:", ref)
    for i in range(1, n - 1, a.every):
        t = i / (n - 1)
        fr = frame_at(layers, A, B, i, n)
        r = one(fr, lay.render(t)[1])
        r.update({"i": i, "t": round(t, 4)})
        rows.append(r)
        print(f"{r['t']:.3f} band {r['band_px']:6d} px  ridge+ mean {r['ridge_pos_mean']:.3f} L  share > 2 L {100 * r['share_over_2L']:.2f} %  p95 {r['p95']:.2f}")
    (out / f"outline_{a.layer}.json").write_text(json.dumps({"score": a.score, "layer": a.layer, "ref": ref, "rows": rows}, indent=1))


def cmd_rest(a):
    """The frames beside the endpoints against the photos: for the first and the last --k interior
    frames the mean and the largest difference (8-bit levels, the largest channel) and the share of
    the canvas more than 4 levels off, against A at the start and against B at the end."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in list(range(1, 1 + a.k)) + list(range(n - 1 - a.k, n - 1)):
        fr = frame_at(layers, A, B, i, n).astype(np.float32)
        ref = A if i <= a.k else B
        d = np.abs(fr - ref.astype(np.float32)).max(-1)
        rows.append({"i": i, "t": round(i / (n - 1), 4), "against": "A" if i <= a.k else "B", "mean": round(float(d.mean()), 3),
                     "max": int(d.max()), "share_over_4": round(float((d > 4).mean()), 5)})
        r = rows[-1]
        print(f"{r['t']:.3f} against {r['against']}: mean {r['mean']:.3f} max {r['max']} share over 4 levels {100 * r['share_over_4']:.3f} %")
    (out / "rest.json").write_text(json.dumps({"score": a.score, "rows": rows}, indent=1))


def cmd_contrast(a):
    """Per frame the signed contrast of a layer against what lies under it: the alpha-weighted mean
    of L(the layers up to and including it) minus L(the layers under it). A cloud that turns darker
    than the sky behind it changes the sign."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lay = next(l for l in layers if l.name == a.layer)
    below = [l for l in layers if l.depth < lay.depth]
    upto = [l for l in layers if l.depth <= lay.depth]
    rows = []
    for i in range(1, n - 1, a.every):
        t = i / (n - 1)
        _, al = lay.render(t)
        if float(al.sum()) < 1.0:
            rows.append({"i": i, "t": round(t, 4), "alpha_mean": 0.0, "contrast_L": None})
            print(f"{t:.3f} the layer is gone")
            continue
        c = L_of(P.composite(upto, t)) - L_of(P.composite(below, t))
        rows.append({"i": i, "t": round(t, 4), "alpha_mean": round(float(al.mean()), 3),
                     "contrast_L": round(float((c * al).sum() / al.sum()), 2)})
        print(f"{t:.3f} alpha mean {rows[-1]['alpha_mean']:.3f} contrast {rows[-1]['contrast_L']:+.2f} L")
    (out / f"contrast_{a.layer}.json").write_text(json.dumps({"score": a.score, "layer": a.layer, "rows": rows}, indent=1))


def cmd_step(a):
    """Frame-to-frame steps between two clip times: the mean difference (levels, the largest
    channel), the same in the rows --rows, and the share of those rows over 8 levels. A warp that
    is switched off at the end of a window shows as one step far above its neighbours."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    i0, i1 = int(round(a.span[0] * (n - 1))), int(round(a.span[1] * (n - 1)))
    r0, r1 = (int(a.rows[0] * scene.h), int(a.rows[1] * scene.h)) if a.rows else (0, scene.h)
    prev, rows = None, []
    for i in range(i0, i1 + 1):
        fr = frame_at(layers, A, B, i, n).astype(np.float32)
        if prev is not None:
            d = np.abs(fr - prev).max(-1)
            rows.append({"from": i - 1, "to": i, "t": round(i / (n - 1), 4), "mean": round(float(d.mean()), 3),
                         "rows_mean": round(float(d[r0:r1].mean()), 3), "rows_share_over_8": round(float((d[r0:r1] > 8).mean()), 4)})
            r = rows[-1]
            print(f"{r['from']:3d} -> {r['to']:3d}: mean {r['mean']:.3f}, rows mean {r['rows_mean']:.3f}, rows over 8 levels {100 * r['rows_share_over_8']:.2f} %")
        prev = fr
    (out / "step.json").write_text(json.dumps({"score": a.score, "rows": rows}, indent=1))


def cmd_layers(a):
    """Per frame and per `morph_to` layer: the share of the canvas its matte covers, the mean of its
    mix inside the matte (0 = the first photo's content, 1 = the second's), the px it has moved and
    the px it still has to go (95th percentile of its field x the progress). Two layers that both
    show the second photo's content over the same place, one at rest and one still on its way, are
    the owner's "duplicate final picture that is already there" (round-5 picks, 2026-09-28).
    `overlap`: the share of the canvas where this layer and a layer under it both hold alpha above
    0.5 and a mix above 0.5. `semi` (round 6): the share of the canvas where the layer's alpha lies
    between 0.05 and 0.95 (a part shown half transparent: the owner's "minor building boders
    overlap" on mismatch_4 round 5)."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    morphs = [l for l in layers if l.action == "morph_to"]
    rows = []
    for i in range(a.every, n - 1, a.every):
        t = i / (n - 1)
        seen = []
        row = {"i": i, "t": round(t, 4), "layers": {}}
        for l in morphs:
            _, al = l.render(t)
            u = l.linear(t)
            m0, m1 = l.mix_window
            if u >= 1:
                qm = np.ones(al.shape, np.float32)
            elif u <= 0:
                qm = np.zeros(al.shape, np.float32)
            elif getattr(l, "stag", None) is not None:
                qm = np.asarray(l.last_q, np.float32)          # a map, set by the render above
            else:
                qm = np.full(al.shape, float(P.smoothstep((u - m0) / max(m1 - m0, 1e-6))), np.float32)
            m = al > 0.5
            mv = l.away(t)
            b_here = m & (qm > 0.5)
            if getattr(l, "last_vb", None) is not None:
                # round 6: a plate shows the second photo's content only where it holds that
                # photo's own pixels; under an object it holds a fill
                b_here &= np.asarray(l.last_vb) > 0.5
            semi = float(((al > 0.05) & (al < 0.95)).mean())
            ov = 0.0
            for other, other_to_go in seen:
                # two layers at rest hold the same pixels at the same place (a plate under an
                # object that has arrived): a duplicate is one of them still on its way
                if max(float(mv[1]), other_to_go) > 3.0:
                    ov = max(ov, float((b_here & other).mean()))
            seen.append((b_here, float(mv[1])))
            row["layers"][l.name] = {"alpha_share": round(float(m.mean()), 3), "mix_mean": round(float(qm[m].mean()), 3) if m.any() else None,
                                     "moved_px": round(float(mv[0]), 1), "to_go_px": round(float(mv[1]), 1), "overlap": round(ov, 3),
                                     "semi_share": round(semi, 4)}
        rows.append(row)
        print(f"{t:.3f} " + " | ".join(f"{k}: a {v['alpha_share']:.2f} mix {v['mix_mean']} to go {v['to_go_px']:.0f} px overlap {v['overlap']:.2f} semi {100 * v['semi_share']:.1f} %" for k, v in row["layers"].items()))
    (out / "layers.json").write_text(json.dumps({"score": a.score, "rows": rows}, indent=1))


def cmd_fields(a):
    """Per `morph_to` layer and per direction (A -> B inside the layer's matte, B -> A inside its
    target's): the travel (mean and 95th percentile of the field's length, px) and the strain (see
    layered_probe.strain_of: median, 95th percentile, the share of the matte over 0.5 and the
    share that folds), then the strain of the field's affine part (the layer grows, turns or
    shears as a whole) and the 95th percentile of the strain of what the affine part leaves out
    (`bend`: a straight line becomes a curve).
    The owner on round 5: "clouds skewed alot"; a cloud stretched into a peak is a place whose
    strain is near 1."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = {}
    for l in layers:
        if l.action != "morph_to":
            continue
        F, G = l.fields()
        row = {}
        for nm, fld, al in (("a_to_b", F, l.alpha0), ("b_to_a", G, l.tgt.alpha0)):
            sel = al > 0.5
            if sel.sum() < 100:
                row[nm] = None
                continue
            mag = np.sqrt((fld ** 2).sum(-1))[sel]
            st, fold = P.strain_of(fld)
            aff, _ = P.affine_part(fld, al)
            st_aff, _ = P.strain_of(aff)
            st_bend, _ = P.strain_of(fld - aff)
            row[nm] = {"matte_share": round(float(sel.mean()), 3), "travel_mean_px": round(float(mag.mean()), 1),
                       "travel_p95_px": round(float(np.percentile(mag, 95)), 1),
                       "strain_median": round(float(np.median(st[sel])), 3), "strain_p95": round(float(np.percentile(st[sel], 95)), 3),
                       "share_strain_over_0.5": round(float((st[sel] > 0.5).mean()), 4), "share_fold": round(float(fold[sel].mean()), 4),
                       "affine_strain": round(float(np.median(st_aff[sel])), 3),
                       "bend_p95": round(float(np.percentile(st_bend[sel], 95)), 3)}
        rows[l.name] = row
        for nm, r in row.items():
            if r:
                print(f"{l.name:>16} {nm}: matte {100 * r['matte_share']:.1f} %  travel mean {r['travel_mean_px']:.1f} px, p95 {r['travel_p95_px']:.1f} px  "
                      f"strain median {r['strain_median']:.3f}, p95 {r['strain_p95']:.3f}, over 0.5 on {100 * r['share_strain_over_0.5']:.2f} %, folds on {100 * r['share_fold']:.2f} %  "
                      f"affine part {r['affine_strain']:.3f}, bend p95 {r['bend_p95']:.3f}")
    (out / "fields.json").write_text(json.dumps({"score": a.score, "layers": rows}, indent=1))


def rim_of(lab, alpha, ring=4, core=(10, 24), outside=(4, 16), sigma=12.0, contrast=10.0):
    """How much of a matte's inner rim holds the colour of what lies outside the matte. For every
    pixel within `ring` px inside the alpha 0.5 contour: its Lab distance to the local mean colour
    of the matte's core (`core` px inside) against its distance to the local mean colour outside
    (`outside` px out); both means are normalized convolutions at `sigma` px. Counted where the two
    means stand more than `contrast` apart (Lab distance), so a rim between two like colours does
    not count. Returns (the share of those rim pixels nearer to the outside colour, the rim pixels
    counted, the mean Lab distance between the two means there)."""
    hard = (alpha > 0.5).astype(np.uint8)
    if hard.sum() < 200 or (1 - hard).sum() < 200:
        return None, 0, None
    d_in = cv2.distanceTransform(hard, cv2.DIST_L2, 5)
    d_out = cv2.distanceTransform(1 - hard, cv2.DIST_L2, 5)
    m_core = ((d_in > core[0]) & (d_in <= core[1])).astype(np.float32)
    m_out = ((d_out > outside[0]) & (d_out <= outside[1])).astype(np.float32)
    rim = (d_in > 0) & (d_in <= ring)

    def local(m):
        den = cv2.GaussianBlur(m, (0, 0), sigma)
        num = cv2.GaussianBlur(lab * m[..., None], (0, 0), sigma)
        return num / np.maximum(den, 1e-6)[..., None], den
    c_core, w_core = local(m_core)
    c_out, w_out = local(m_out)
    apart = np.sqrt(((c_core - c_out) ** 2).sum(-1))
    use = rim & (w_core > 0.02) & (w_out > 0.02) & (apart > contrast)
    if use.sum() < 50:
        return None, int(use.sum()), None
    to_core = np.sqrt(((lab - c_core) ** 2).sum(-1))[use]
    to_out = np.sqrt(((lab - c_out) ** 2).sum(-1))[use]
    return float((to_out < to_core).mean()), int(use.sum()), float(apart[use].mean())


def cmd_rim(a):
    """Per layer with a matte of its own (every rendered layer but the backdrops, and the target of
    every `morph_to`): the share of the matte's inner rim that holds the outside colour (see
    rim_of), on the layer's own photo at rest. A matte cut from an upsampled label map sits a few
    px outside the object; the rim then carries sky, and over another layer it shows as a pale
    outline (the owner's screenshots of round 5)."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = {}
    seen = set()
    for l in layers:
        if isinstance(l, P.Backdrop):
            continue
        for lay in (l, getattr(l, "tgt", None)):
            if lay is None or lay.name in seen or float(lay.alpha0.mean()) > 0.97:
                continue
            seen.add(lay.name)
            share, npx, apart = rim_of(scene.lab[lay.src], lay.alpha0)
            rows[lay.name] = {"photo": lay.src, "matte_share": round(float((lay.alpha0 > 0.5).mean()), 3), "rim_px": npx,
                              "outside_colour_share": None if share is None else round(share, 3),
                              "apart_lab": None if apart is None else round(apart, 1)}
            r = rows[lay.name]
            print(f"{lay.name:>16} ({lay.src}): matte {100 * r['matte_share']:.1f} %  rim px counted {npx}  "
                  f"rim nearer to the outside colour {'n/a' if share is None else f'{100 * share:.1f} %'}  means apart {r['apart_lab']}")
    (out / "rim.json").write_text(json.dumps({"score": a.score, "layers": rows}, indent=1))


def cmd_holes(a):
    """Per frame: the share of the canvas where a backdrop's hole fill is what the viewer sees. A
    backdrop's residual is the photo's own where the sky is known and a fill (a normalized
    convolution of the surroundings) in its holes, under the layers drawn over it. `fill`: the
    weight of the fill in the backdrop's picture at that pixel (both photos' holes, carried by the
    backdrop's flow and mixed as its textures are; under `settle` a hole whose layer rests counts
    as the photo's own). `cover`: 1 - the product of (1 - alpha) of the layers above the backdrop.
    Counted: fill > 0.5 and cover < 0.5. The owner's screenshots of round 5 show it as a smooth
    dome in the lower sky and as pale outlines along the mattes. A plate (round 6: a layer that
    holds a fill under the objects drawn over it) counts the same way: its fill where the plate is
    drawn and no layer above covers it."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    bds = [l for l in layers if isinstance(l, P.Backdrop)]
    plates = [l for l in layers if getattr(l, "valid", None) is not None or getattr(getattr(l, "tgt", None), "valid", None) is not None]
    if not bds and not plates:
        print("no backdrop and no plate in this score: every layer holds pixels of a photo")
        (out / "holes.json").write_text(json.dumps({"score": a.score, "rows": []}, indent=1))
        return
    bd = bds[0] if bds else None
    rows = []
    for i in range(1, n - 1, a.every):
        t = i / (n - 1)
        rend = {l.name: l.render(t)[1] for l in layers if l is not bd}

        def cover_above(lay):
            c = np.zeros((scene.h, scene.w), np.float32)
            for l in layers:
                if l is not bd and l.depth > lay.depth:
                    c = 1.0 - (1.0 - c) * (1.0 - rend[l.name])
            return c
        seen = np.zeros((scene.h, scene.w), bool)
        seen_mv = np.zeros((scene.h, scene.w), bool)
        fill = np.zeros((scene.h, scene.w), np.float32)
        cover = np.ones((scene.h, scene.w), np.float32)
        if bd is not None:
            fill = bd.fill_weight(t)
            fill_mv = bd.fill_weight(t, moving_only=True)
            cover = cover_above(bd)
            seen = (fill > 0.5) & (cover < 0.5)
            seen_mv = (fill_mv > 0.5) & (cover < 0.5)
        for pl in plates:
            # round 6: a plate's fill, where the plate is drawn and nothing above covers it
            if getattr(pl, "last_fill", None) is None:
                continue
            pf = (np.asarray(pl.last_fill) > 0.5) & (rend[pl.name] > 0.5) & (cover_above(pl) < 0.5)
            fill = np.maximum(fill, np.asarray(pl.last_fill, np.float32) * (rend[pl.name] > 0.5))
            cover = np.minimum(cover, cover_above(pl))
            seen |= pf
            seen_mv |= pf
        rows.append({"i": i, "t": round(t, 4), "fill_share": round(float((fill > 0.5).mean()), 4),
                     "uncovered_share": round(float((cover < 0.5).mean()), 4), "fill_seen_share": round(float(seen.mean()), 4),
                     "fill_seen_under_moved_layers": round(float(seen_mv.mean()), 4)})
        r = rows[-1]
        print(f"{r['t']:.3f} fill over {100 * r['fill_share']:.1f} % of the canvas, uncovered {100 * r['uncovered_share']:.1f} %, fill seen {100 * r['fill_seen_share']:.2f} %"
              f" (of it where a layer has moved off: {100 * r['fill_seen_under_moved_layers']:.2f} %)")
        if a.frames:
            fr = frame_at(layers, A, B, i, n).copy()
            fr[seen] = (0.5 * fr[seen] + 0.5 * np.array([255, 0, 255])).astype(np.uint8)
            cv2.imwrite(str(out / f"holes_{i:03d}.jpg"), cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    worst = max(rows, key=lambda r: r["fill_seen_share"]) if rows else None
    if worst:
        print(f"largest: {100 * worst['fill_seen_share']:.2f} % at t {worst['t']:.3f}; mean over the frames {100 * float(np.mean([r['fill_seen_share'] for r in rows])):.2f} %")
    (out / "holes.json").write_text(json.dumps({"score": a.score, "backdrop": bd.name if bd is not None else None,
                                               "plates": [l.name for l in plates], "rows": rows}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    fl = sub.add_parser("fields")
    fl.add_argument("--score", required=True)
    fl.add_argument("--out", required=True)
    fl.set_defaults(fn=cmd_fields)
    rm = sub.add_parser("rim")
    rm.add_argument("--score", required=True)
    rm.add_argument("--out", required=True)
    rm.set_defaults(fn=cmd_rim)
    ho = sub.add_parser("holes")
    ho.add_argument("--score", required=True)
    ho.add_argument("--every", type=int, default=4)
    ho.add_argument("--frames", action="store_true", help="write the frames with the seen fill tinted magenta")
    ho.add_argument("--out", required=True)
    ho.set_defaults(fn=cmd_holes)
    e = sub.add_parser("end")
    e.add_argument("--score", required=True)
    e.add_argument("--regions", nargs="*", default=[])
    e.add_argument("--from", type=float, default=0.5)
    e.add_argument("--out", required=True)
    e.add_argument("--frames", action="store_true")
    e.set_defaults(fn=cmd_end)
    s = sub.add_parser("seam")
    s.add_argument("--score", required=True)
    s.add_argument("--layer", required=True)
    s.add_argument("--from", type=float, default=0.0)
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_seam)
    o = sub.add_parser("outline")
    o.add_argument("--score", required=True)
    o.add_argument("--layer", required=True)
    o.add_argument("--every", type=int, default=4)
    o.add_argument("--rows", type=float, nargs=2, default=None, help="keep the ring between two row fractions")
    o.add_argument("--out", required=True)
    o.set_defaults(fn=cmd_outline)
    r = sub.add_parser("rest")
    r.add_argument("--score", required=True)
    r.add_argument("--k", type=int, default=2)
    r.add_argument("--out", required=True)
    r.set_defaults(fn=cmd_rest)
    c = sub.add_parser("contrast")
    c.add_argument("--score", required=True)
    c.add_argument("--layer", required=True)
    c.add_argument("--every", type=int, default=9)
    c.add_argument("--out", required=True)
    c.set_defaults(fn=cmd_contrast)
    st = sub.add_parser("step")
    st.add_argument("--score", required=True)
    st.add_argument("--span", type=float, nargs=2, required=True, help="two clip times")
    st.add_argument("--rows", type=float, nargs=2, default=None, help="two row fractions")
    st.add_argument("--out", required=True)
    st.set_defaults(fn=cmd_step)
    ly = sub.add_parser("layers")
    ly.add_argument("--score", required=True)
    ly.add_argument("--every", type=int, default=8)
    ly.add_argument("--out", required=True)
    ly.set_defaults(fn=cmd_layers)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
