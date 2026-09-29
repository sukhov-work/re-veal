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
  change  (round 7) what explains a frame's change, the owner on round 6's skyline clips: "some
          form of reveal with solid margin ... nothing is transforming there". Per step and per
          region three shares of the change of the luminance: `motion` (a dense flow between the
          two frames explains it: content travels), `reveal` (no flow explains it and it comes
          from a matte that moves over content that stays: an outline sweeps) and `mix` (no flow
          explains it and it comes from a layer's content changing where it stands: a crossfade).
          With --clip FILE.mp4 (a clip from outside the probe, no mattes) `motion` and the rest.
  edge    (round 7) per drawn object layer, on its matte at rest, the owner on round 6: "very
          crudely cut out of background with rough edges". `rough`: the length of the matte's
          outline over the length of the same outline smoothed at 6 px (1 = a smooth outline);
          `soft_px`: the width of the matte's ramp (the area with alpha between 0.05 and 0.95
          over the outline's length); `fringe`: the share of the inner rim whose colour, as the
          layer carries it, is nearer to the colour outside the matte than to the matte's core.

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


def outline_len(hard):
    cs, _ = cv2.findContours(hard.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return float(sum(cv2.arcLength(c, True) for c in cs if len(c) >= 8))


def cmd_edge(a):
    """Round 7 (backlog T28). Per drawn layer that is not a backdrop and does not cover the canvas,
    and per target of a `morph_to`, on the matte at rest and the colour the layer carries (after
    `unmix`, the un-premultiplied colour): rough, soft_px, fringe (see the module docstring).
    Controls, printed first: a disc of radius 120 px (rough near 1), the same disc with its
    outline displaced by up to 12 px by noise at a 2-px scale (rough over 1.3), and the disc
    blurred at 4 px (soft_px 12.6)."""
    score, scene, layers, A, B, n = build(a.score)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    def rough_of(al):
        hard = al > 0.5
        L0 = outline_len(hard)
        sm = cv2.GaussianBlur(hard.astype(np.float32), (0, 0), 6.0) > 0.5
        L1 = outline_len(sm)
        ramp = float(((al > 0.05) & (al < 0.95)).sum())
        return (L0 / max(L1, 1.0), ramp / max(L0, 1.0), L0)
    yy, xx = np.mgrid[0:600, 0:600].astype(np.float32)
    r = np.sqrt((xx - 300) ** 2 + (yy - 300) ** 2)
    disc = (r < 120).astype(np.float32)
    nz = np.random.default_rng(7).random((600, 600), dtype=np.float32)
    nz = cv2.GaussianBlur(nz, (0, 0), 2.0)
    nz = (nz - nz.min()) / max(float(nz.max() - nz.min()), 1e-6)
    jag = (r + 24.0 * (nz - 0.5) < 120).astype(np.float32)
    ctl = {"disc": rough_of(disc), "jagged disc": rough_of(jag), "disc blurred 4 px": rough_of(cv2.GaussianBlur(disc, (0, 0), 4.0))}
    for k, v in ctl.items():
        print(f"control {k}: rough {v[0]:.3f}, soft {v[1]:.1f} px")
    rows, seen = {}, set()
    for l in scene.layers_all:
        if isinstance(l, P.Backdrop):
            continue
        for lay in (l, getattr(l, "tgt", None)):
            if lay is None or lay.name in seen or not (l.render_it or lay is not l and l.render_it):
                continue
            if float((lay.alpha0 > 0.5).mean()) > 0.9 or float((lay.alpha0 > 0.5).sum()) < 400:
                continue
            seen.add(lay.name)
            rg, soft, L0 = rough_of(lay.alpha0)
            share, npx, apart = rim_of(np.asarray(lay.lab, np.float32), lay.alpha0)
            rows[lay.name] = {"photo": lay.src, "matte_share": round(float((lay.alpha0 > 0.5).mean()), 4), "outline_px": round(L0),
                              "rough": round(rg, 3), "soft_px": round(soft, 2), "fringe": None if share is None else round(share, 3),
                              "unmixed": bool(lay.spec.get("unmix"))}
            r_ = rows[lay.name]
            print(f"{lay.name:>16} ({lay.src}): matte {100 * r_['matte_share']:.1f} %  outline {r_['outline_px']} px  rough {r_['rough']:.3f}  "
                  f"soft {r_['soft_px']:.1f} px  fringe {'n/a' if share is None else f'{100 * share:.1f} %'}{'  (unmixed)' if r_['unmixed'] else ''}")
    (out / "edge.json").write_text(json.dumps({"score": a.score, "controls": {k: [round(v[0], 3), round(v[1], 2)] for k, v in ctl.items()}, "layers": rows}, indent=1))


LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def _flow_split(y0, y1, dis, gx, gy):
    """(d, motion) of one step on the luminance (levels of 0..255): d = |y1 - y0| per pixel and
    the part of it that a DIS flow from the first frame to the second explains,
    max(d - |y1 warped back - y0|, 0)."""
    g0 = np.clip(y0 + 0.5, 0, 255).astype(np.uint8)
    g1 = np.clip(y1 + 0.5, 0, 255).astype(np.uint8)
    f = dis.calc(g0, g1, None)
    yw = cv2.remap(y1, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    d = np.abs(y1 - y0)
    return d, np.clip(d - np.abs(yw - y0), 0.0, None), f


def cmd_change(a):
    """Round 7 (backlog T26). A frame is the sum over its parts of visibility x content, so a
    step between two frames is exactly  sum(mean visibility x change of content)  +  sum(mean
    content x change of visibility): the content term (what the content does under mattes that
    stay) and the matte terms (what the mattes do over content that stays). A part is a layer,
    or for a `morph_to` layer in mid-clip each of its two photos' contents with its weight in
    the layer's picture (the probe's `last_parts`): the outline between the two photos inside
    one layer is a matte like any other. Every part's content has its own motion: a dense flow
    (DIS, medium preset) between the part's two pictures. Per pixel, on the luminance at
    --proxy px (long side):
      mix    = min(|content term|, |content term after each part's picture is warped back along
               its flow|), plus the part of a matte term that no motion explains where both
               photos are present or the visibility changes by under 0.1 per step (a crossfade)
      reveal = the part of a matte term that no motion explains elsewhere: min(|matte term|,
               |matte term counted from the visibility carried along the content's flow|); an
               edge moves and its content does not move with it
      motion = |content term| + sum |matte terms| - mix - reveal: content travels, and outlines
               with it
    summed over a region and over the steps, as shares of the summed |content term| + |matte
    terms|. Regions: the frame, and per drawn layer the pixels where it is seen in one of the
    two frames (visibility over 0.05). Dropped the same day: one flow between the two
    composites (it explained 72 % of a wipe as motion: a flow moves a soft edge over a plain
    sky); one content per layer (a morph layer's picture holds the outline between its two
    photos, and the flow explained that outline as motion).
    Controls: `--control` writes three scores from the score's two photos (a wipe, a crossfade,
    a pan of the first photo) and measures them through the same path; each must read its own
    share highest. With --clip (no mattes) one flow between the frames: motion and the rest."""
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)

    def proxy_size(h, w):
        s = min(1.0, a.proxy / float(max(h, w)))
        return max(8, int(round(w * s))), max(8, int(round(h * s)))

    def shares(acc):
        tot = max(acc[0], 1e-9)
        return {"change": round(acc[0], 1), "motion": round(acc[1] / tot, 4), "reveal": round(acc[2] / tot, 4), "mix": round(acc[3] / tot, 4)}

    def run_frames(frames, tag):
        """A clip with no mattes (a list of RGB uint8 frames): motion and the rest."""
        h, w = frames[0].shape[:2]
        pw, ph = proxy_size(h, w)
        gx, gy = np.meshgrid(np.arange(pw, dtype=np.float32), np.arange(ph, dtype=np.float32))
        ys = [cv2.resize(f.astype(np.float32), (pw, ph), interpolation=cv2.INTER_AREA) @ LUMA for f in frames]
        acc, rows = np.zeros(4), []
        for i in range(1, len(ys) - 2, a.every):
            d, m, f = _flow_split(ys[i], ys[i + 1], dis, gx, gy)
            acc += (float(d.sum()), float(m.sum()), 0.0, float((d - m).sum()))
            rows.append({"i": i, "t": round(i / (len(ys) - 1), 4), "step": round(float(d.mean()), 3),
                         "motion": round(float(m.sum() / max(d.sum(), 1e-9)), 4), "flow_px": round(float(np.sqrt((f ** 2).sum(-1)).mean()), 2)})
        r = shares(acc)
        r["rest"] = round(r.pop("reveal") + r.pop("mix"), 4)
        print(f"{tag}: steps {len(rows)}  motion {100 * r['motion']:.1f} %  rest {100 * r['rest']:.1f} %  (no mattes: the rest is not split)")
        return {"frame": r, "rows": rows}

    def measure(score_path, quiet=False):
        score, scene, layers, A, B, n = build(score_path)
        h, w = scene.h, scene.w
        pw, ph = proxy_size(h, w)
        gx, gy = np.meshgrid(np.arange(pw, dtype=np.float32), np.arange(ph, dtype=np.float32))

        def small(x):
            return cv2.resize(np.ascontiguousarray(np.asarray(x, np.float32)), (pw, ph), interpolation=cv2.INTER_AREA)

        def state(t):
            """The parts of the frame at t, back to front: per part (layer index, luminance of
            its content, its visibility in the frame, the weight with which both photos are
            present there). A `morph_to` layer in mid-clip is two parts, the first photo's
            content and the second's (the probe's `last_parts`); any other layer is one."""
            rs = []
            for l in layers:
                l.last_parts = None
                rgb, al = l.render(t)
                rs.append((rgb, al, getattr(l, "last_parts", None)))
            al = [small(x) for _, x, _ in rs]
            vis, above = [None] * len(layers), np.ones((ph, pw), np.float32)
            for k in range(len(layers) - 1, -1, -1):
                vis[k] = al[k] * above
                above = above * (1.0 - al[k])
            parts = []
            for k, (rgb, _, lp) in enumerate(rs):
                if lp is None:
                    parts.append((k, 0, small(rgb) @ LUMA, vis[k], np.zeros((ph, pw), np.float32)))
                    continue
                c_a, c_b, a_a, a_b, w_a, w_b = lp
                wa, wb = small(w_a), small(w_b)
                sa = wa / np.maximum(wa + wb, 1e-4)
                both = np.minimum(small(a_a), small(a_b))
                parts.append((k, 0, small(c_a) @ LUMA, vis[k] * sa, both))
                parts.append((k, 1, small(c_b) @ LUMA, vis[k] * (1.0 - sa), both))
            return parts, vis
        names = [l.name for l in layers]
        acc = {nm: np.zeros(4) for nm in ["frame"] + names}
        rows = []
        i_prev, st_prev = None, None
        for i in range(1, n - 2, a.every):
            s0 = st_prev if i_prev == i else state(i / (n - 1))
            s1 = state((i + 1) / (n - 1))
            i_prev, st_prev = i + 1, s1
            p0 = {(k, j): (c, v, b_) for k, j, c, v, b_ in s0[0]}
            p1 = {(k, j): (c, v, b_) for k, j, c, v, b_ in s1[0]}
            zero = np.zeros((ph, pw), np.float32)
            content = content_res = matte = np.zeros((ph, pw), np.float32)
            rv = np.zeros((ph, pw), np.float32)
            mxm = np.zeros((ph, pw), np.float32)
            y0 = np.zeros((ph, pw), np.float32)
            y1 = np.zeros((ph, pw), np.float32)
            fl = 0.0
            for key in sorted(set(p0) | set(p1)):
                # a part that exists in one of the two frames only (a morph that starts or ends
                # between them) has the other frame's content of its layer and no visibility there
                c0, v0, b0 = p0.get(key, (None, zero, zero))
                c1, v1, b1 = p1.get(key, (None, zero, zero))
                if c0 is None:
                    c0 = c1
                if c1 is None:
                    c1 = c0
                y0 = y0 + c0 * v0
                y1 = y1 + c1 * v1
                vm = 0.5 * (v0 + v1)
                dc = c1 - c0
                res, adv = dc, v0
                if float(vm.max()) >= 0.02 and float(np.abs(dc).max()) >= 1e-3:
                    # the part's content has its own motion: a flow between its two pictures
                    g0 = np.clip(c0 + 0.5, 0, 255).astype(np.uint8)
                    g1 = np.clip(c1 + 0.5, 0, 255).astype(np.uint8)
                    f = dis.calc(g0, g1, None)
                    res = cv2.remap(c1, gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) - c0
                    adv = cv2.remap(v0, gx - f[..., 0], gy - f[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                    fl += float((np.sqrt((f ** 2).sum(-1)) * vm).sum())
                cm = 0.5 * (c0 + c1)
                content = content + vm * dc
                content_res = content_res + vm * res
                m_all = cm * (v1 - v0)
                m_res = cm * (v1 - adv)
                matte = matte + m_all
                # what no motion of the part's content explains of its visibility's change: a
                # crossfade where both photos are present or the change is gradual (under 0.1
                # of visibility per step; all of it a reveal over 0.3), a reveal elsewhere
                un = np.minimum(np.abs(m_all), np.abs(m_res))
                dv = np.abs(v1 - adv)
                grad = 1.0 - np.clip((dv - 0.1) / 0.2, 0.0, 1.0)
                mixw = np.maximum(np.maximum(b0, b1), grad)
                rv = rv + un * (1.0 - mixw)
                mxm = mxm + un * mixw
            mx = np.minimum(np.abs(content), np.abs(content_res)) + mxm
            d = np.abs(content) + sum_abs_matte(p0, p1, zero)
            m = np.clip(d - mx - rv, 0.0, None)
            vis0, vis1 = s0[1], s1[1]
            row = {"i": i, "t": round(i / (n - 1), 4), "step": round(float(np.abs(y1 - y0).mean()), 3), "parts": round(float(d.mean()), 3),
                   "flow_px": round(fl / (pw * ph), 2),
                   "identity_err": round(float(np.abs((y1 - y0) - (matte + content)).max()), 4), "regions": {}}
            regs = [("frame", np.ones((ph, pw), bool))] + [(nm, (p_ > 0.05) | (q_ > 0.05)) for nm, p_, q_ in zip(names, vis0, vis1)]
            for nm, sel in regs:
                part = np.array([float(d[sel].sum()), float(m[sel].sum()), float(rv[sel].sum()), float(mx[sel].sum())])
                acc[nm] += part
                if part[0] > 0:
                    row["regions"][nm] = shares(part)
            rows.append(row)
            fr = row["regions"].get("frame", {"motion": 0, "reveal": 0, "mix": 0})
            if not quiet:
                print(f"{row['t']:.3f} step {row['step']:.3f}  motion {100 * fr['motion']:5.1f} %  reveal {100 * fr['reveal']:5.1f} %  mix {100 * fr['mix']:5.1f} %  flow {row['flow_px']:.2f} px")
        summ = {nm: shares(v) for nm, v in acc.items() if v[0] > 0}
        if not quiet:
            print("whole clip, per region (change = the summed |content term| + |matte terms| of the luminance, levels x px of the proxy):")
            for nm, r in summ.items():
                print(f"{nm:>16}: change {r['change']:12.1f}  motion {100 * r['motion']:5.1f} %  reveal {100 * r['reveal']:5.1f} %  mix {100 * r['mix']:5.1f} %")
        return {"summary": summ, "rows": rows}

    def sum_abs_matte(p0, p1, zero):
        out = zero.copy()
        for key in sorted(set(p0) | set(p1)):
            c0, v0, _ = p0.get(key, (None, zero, zero))
            c1, v1, _ = p1.get(key, (None, zero, zero))
            c0 = c1 if c0 is None else c0
            c1 = c0 if c1 is None else c1
            out = out + np.abs(0.5 * (c0 + c1) * (v1 - v0))
        return out

    if a.clip:
        cap = cv2.VideoCapture(a.clip)
        frames = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        if len(frames) < 4:
            raise SystemExit(f"{a.clip}: {len(frames)} frames decoded")
        res = run_frames(frames, Path(a.clip).parent.name)
        (out / "change.json").write_text(json.dumps({"clip": a.clip, "proxy": a.proxy, "every": a.every, **res}, indent=1))
        return
    if a.control:
        # three clips whose answer is known, as scores of the same pair, length and canvas,
        # measured through the same path as any clip: a wipe (the second photo's matte grows
        # from the top over content that stands), a crossfade (one layer, its content changes
        # where it stands) and a pan (the first photo travels a quarter of the width)
        base = json.loads(Path(a.score).read_text())
        head = {k: base[k] for k in ("pair", "seconds", "fps", "max_long") if k in base}
        A_, _ = P.canvas_pair(head["pair"], head.get("max_long", 1920))
        ctl = {
            "wipe": [{"name": "a", "from": "A", "mask": {"rule": "all"}, "depth": 0, "action": "hold"},
                     {"name": "b", "from": "B", "mask": {"rule": "all"}, "depth": 1, "action": "materialise", "order": "rows",
                      "noise_gain": 0.0, "feather": 0.02, "window": [0.0, 1.0], "curve": "linear"}],
            "crossfade": [{"name": "b", "from": "B", "mask": {"rule": "all"}, "render": False},
                          {"name": "a", "from": "A", "mask": {"rule": "all"}, "depth": 0, "action": "morph_to", "to": "b",
                           "window": [0.0, 1.0], "curve": "linear", "mix_window": [0.0, 1.0], "ot_gain": 0.0, "exact": True,
                           "match_colour": False}],
            "pan": [{"name": "b", "from": "B", "mask": {"rule": "all"}, "depth": 0, "action": "hold"},
                    {"name": "a", "from": "A", "mask": {"rule": "all"}, "depth": 1, "action": "move", "direction": [-1, 0],
                     "travel_px": round(0.25 * A_.shape[1], 1), "window": [0.0, 1.0], "curve": "linear"}],
        }
        want = {"wipe": "reveal", "crossfade": "mix", "pan": "motion"}
        res = {}
        for tag, lays in ctl.items():
            f = out / f"control_{tag}.json"
            f.write_text(json.dumps(dict(head, tag="control_" + tag, layers=lays), indent=1))
            r = measure(str(f), quiet=True)["summary"]["frame"]
            top = max(("motion", "reveal", "mix"), key=lambda k: r[k])
            res[tag] = dict(r, highest=top, passed=(top == want[tag]))
            print(f"control {tag}: motion {100 * r['motion']:.1f} %  reveal {100 * r['reveal']:.1f} %  mix {100 * r['mix']:.1f} %  "
                  f"highest {top} ({'as expected' if top == want[tag] else 'EXPECTED ' + want[tag]})")
        (out / "change_control.json").write_text(json.dumps({"score": a.score, "proxy": a.proxy, "every": a.every, "controls": res}, indent=1))
        return
    res = measure(a.score)
    (out / "change.json").write_text(json.dumps({"score": a.score, "proxy": a.proxy, "every": a.every, **res}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ed = sub.add_parser("edge")
    ed.add_argument("--score", required=True)
    ed.add_argument("--out", required=True)
    ed.set_defaults(fn=cmd_edge)
    ch = sub.add_parser("change")
    ch.add_argument("--score", default="")
    ch.add_argument("--clip", default="", help="an mp4 from outside the probe (no mattes): motion and the rest")
    ch.add_argument("--control", action="store_true", help="three synthetic clips from the score's photos: a wipe, a crossfade, a pan")
    ch.add_argument("--proxy", type=int, default=960, help="the long side at which the step is measured, px")
    ch.add_argument("--every", type=int, default=1)
    ch.add_argument("--out", required=True)
    ch.set_defaults(fn=cmd_change)
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
