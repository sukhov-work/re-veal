#!/usr/bin/env python3
"""TR6-A research: the generative bridge on the deterministic skeleton (research plan E17).

The tool renders the skeleton (its own frames and displacement field); a diffusion model re-draws
every in-between frame from that skeleton (SDEdit: partial noise, partial denoise), with the noise
either fresh per frame or carried along the skeleton's flow; the result is lifted back to the
native canvas by taking the generator's low frequencies and the skeleton's high frequencies.
Frames 0 and n-1 are the skeleton's byte-exact endpoints in every clip. Not part of either tool.

  --skeleton OUT PAIR...                    (.venv)  render the skeleton for each pair from fixtures/:
        OUT/<pair>/skeleton/f%02d.png (native canvas, capped 1920), small/f%02d.png (long edge 512,
        multiples of 8: the generator's input), A.png / B.png (native), disp_small.npy (the A -> B
        field on the small canvas), mask_native.png / mask_small.png, tw.json, meta.json, thumbs
  --generate OUT PAIR NOISE STRENGTH [SEED] [N_FRAMES]   (the SD scratch venv: torch + diffusers, no cv2)
        SD 1.5 inpainting on MPS fp16 over small/f1..f(n-2) -> OUT/<pair>/gen_<NOISE>_s<STRENGTH>[_seed<SEED>]/
        NOISE = indep (fresh Gaussian per frame, seed SEED*1000+i) | warped (frame 0's noise carried
        along the skeleton's cumulative displacement, nearest-neighbour at pixel resolution, then
        8x8 block-summed / 8 to the latent grid: Gaussian preserved) | warped-ramp (warped noise and
        the strength ramped as STRENGTH * sin(pi u): zero re-drawing at the endpoints, the most in the
        middle; a frame whose strength gives no scheduled step is the skeleton frame itself).
        N_FRAMES limits the run; GB_SUFFIX=_rep in the environment writes a repeat run beside the
        first one (seed reproducibility).
  --measure OUT PAIR...                     (.venv)  assemble clips (skeleton endpoints + generated
        in-betweens; match_4 pastes the skeleton back outside the feathered mask), encode, strip,
        the tool's quality basket, the skeleton-flow warping error, adjacent steps vs the skeleton;
        `smooth_*` = a warped clip filtered along the skeleton's flow (each frame averaged with its
        two neighbours each side warped into it, weights 1 2 3 2 1; the endpoints take part);
        `lift_*` / `lift-smooth_*` = the warped / smoothed clip lifted to the native canvas
        (frequency split, sigma 3 px: the generator's low frequencies under the skeleton's detail)
  --page OUT PAIR...                        (.venv)  OUT/index.html with a pick per pair

Skeleton per pair: class B saliency-panzoom (the tool's own routing) for the mismatches; the
TR14 `hold-dis` field for match_4 (camera motion + DIS residual gated by the changed mask). 2026-09-15.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
N_FRAMES = 30            # 1 s at the tool's 30 fps
SMALL_LONG = 512         # the generator's canvas (research RES_LADDER rung 1 is 854x480; ratio kept)
NATIVE_CAP = 1920        # the bench cap
LIFT_SIGMA = 3.0         # px at the native canvas: generator below, skeleton above
GUIDANCE = 6.0
STEPS = 20
MIX_FEATHER_SIGMA = 8.0  # px, the TR14 feather for the match_4 paste-back
PROMPTS = {              # written from the photos; recorded with the run
    "mismatch_1": "clouds drifting over the city, the blue daytime sky turning to a cloudy dusk, photo",
    "mismatch_4": "the sun sinking toward the horizon over the river, its reflection on the water, the skyline in silhouette, photo",
    "match_4": "a painted mosaic mural on a street utility box, photo",
}
MODEL = "stable-diffusion-v1-5/stable-diffusion-inpainting"


# ---- skeleton (.venv) --------------------------------------------------------------

def skeleton(out, pairs):
    import logging
    import cv2
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts" / "research"))
    import transitions as T
    import tr14_variants as V
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    OUT = Path(out)
    for pid in pairs:
        t0 = time.time()
        a = next(ROOT.glob(f"fixtures/{pid}_S.*"))
        b = next(ROOT.glob(f"fixtures/{pid}_F.*"))
        A, B = T.load_image_rgb(a), T.load_image_rgb(b)
        w, h = T.common_canvas(A, B, NATIVE_CAP, "finish")
        A2, B2 = T.cover(A, w, h), T.cover(B, w, h)
        corr = T.dense_displacement(A2, B2)
        meta = {"pair": pid, "canvas": [w, h], "class": corr["cls"], "method": corr["method"],
                **corr["diag"], "prompt": PROMPTS.get(pid, "")}
        mask = np.full((h, w), 255, np.uint8)
        if pid.startswith("match"):
            gA, gB = T.gray_of(A2), T.gray_of(B2)
            H, dH_AB, dH_BA, sp = V.homography_fields(gA, gB)
            mask = V.changed_mask(A2, B2, H)
            F = cv2.GaussianBlur((mask > 0).astype(np.float32), (0, 0), MIX_FEATHER_SIGMA)
            F_B = cv2.warpPerspective(F, H, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
            corr = V.build_corr({"dis": corr}, "hold-dis", dH_AB, dH_BA, F, F_B)
            meta.update({"skeleton": "hold-dis", "mask_frac": round(float((mask > 0).mean()), 3)})
        else:
            meta.update({"skeleton": corr["method"], "mask_frac": 1.0})
        write_pair_dir(OUT, pid, A2, B2, corr, mask, meta, t0)


def write_pair_dir(OUT, pid, A2, B2, corr, mask, meta, t0=None):
    """The generator's inputs for one pair from a canvas pair and a correspondence dict (also used by
    depth_dolly.py --export to hand its field to the bridge)."""
    import cv2
    sys.path.insert(0, str(ROOT))
    import transitions as T
    t0 = time.time() if t0 is None else t0
    h, w = A2.shape[:2]
    spec = T.spec_from("morph", seconds=N_FRAMES / T.TCFG["fps"])
    n = spec.n_frames()
    assert n == N_FRAMES, n
    s = SMALL_LONG / max(w, h)
    w8, h8 = int(round(w * s / 8)) * 8, int(round(h * s / 8)) * 8
    d = OUT / pid
    (d / "skeleton").mkdir(parents=True, exist_ok=True)
    (d / "small").mkdir(exist_ok=True)
    tw = []
    for i, f in enumerate(T.iter_frames(A2, B2, spec, corr)):
        tw.append(spec.progress(i)[0])
        cv2.imwrite(str(d / "skeleton" / f"f{i:02d}.png"), cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        fs = cv2.resize(f, (w8, h8), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(d / "small" / f"f{i:02d}.png"), cv2.cvtColor(fs, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(d / "A.png"), cv2.cvtColor(A2, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(d / "B.png"), cv2.cvtColor(B2, cv2.COLOR_RGB2BGR))
    for name, img in (("thumb_A.jpg", A2), ("thumb_B.jpg", B2)):
        th = cv2.resize(img, (int(w * 400 / max(w, h)), int(h * 400 / max(w, h))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(d / name), cv2.cvtColor(th, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 80])
    dAB = corr["dAB"]
    ds = cv2.resize(dAB, (w8, h8), interpolation=cv2.INTER_AREA)
    ds[..., 0] *= w8 / w
    ds[..., 1] *= h8 / h
    np.save(str(d / "disp_small.npy"), ds.astype(np.float32))
    np.save(str(d / "disp_native.npy"), dAB.astype(np.float32))
    cv2.imwrite(str(d / "mask_native.png"), mask)
    cv2.imwrite(str(d / "mask_small.png"), cv2.resize(mask, (w8, h8), interpolation=cv2.INTER_NEAREST))
    meta.update({"small": [w8, h8], "n_frames": n, "fps": T.TCFG["fps"],
                 "median_disp_small_px": round(float(np.median(np.linalg.norm(ds, axis=2))), 2),
                 "skeleton_s": round(time.time() - t0, 1)})
    (d / "tw.json").write_text(json.dumps(tw))
    (d / "meta.json").write_text(json.dumps(meta, indent=2))
    print(pid, json.dumps(meta), flush=True)


# ---- generate (the SD scratch venv) ---------------------------------------------------

def warped_noise_latent(base, rng, disp, tw):
    """Frame 0's pixel-resolution noise carried along the skeleton: noise_t(p) = base(p - tw * dAB(p))
    (nearest neighbour, the tool's backward-warp form); uncovered pixels get fresh noise; then 8x8
    block sums / 8 give the latent grid with unit variance (a sum of 64 N(0,1) over 8 is N(0,1))."""
    h, w = disp.shape[:2]
    gx, gy = np.meshgrid(np.arange(w), np.arange(h))
    sx = np.rint(gx - tw * disp[..., 0]).astype(int)
    sy = np.rint(gy - tw * disp[..., 1]).astype(int)
    ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    out = rng.standard_normal((h, w, 4)).astype(np.float32)
    out[ok] = base[sy[ok], sx[ok]]
    lat = out.reshape(h // 8, 8, w // 8, 8, 4).sum(axis=(1, 3)) / 8.0
    return lat.astype(np.float32), float(1.0 - ok.mean())


def generate(out, pid, noise, strength, seed=0, n_limit=0):
    import resource
    import torch
    from PIL import Image
    from diffusers import StableDiffusionInpaintPipeline
    import diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion_inpaint as PSI
    assert noise in ("indep", "warped", "warped-ramp"), noise
    d = Path(out) / pid
    meta = json.loads((d / "meta.json").read_text())
    tw = json.loads((d / "tw.json").read_text())
    n = meta["n_frames"]
    w8, h8 = meta["small"]
    tag = f"gen_{noise}_s{strength:g}" + (f"_seed{seed}" if seed else "") + os.environ.get("GB_SUFFIX", "")
    o = d / tag
    o.mkdir(exist_ok=True)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    t0 = time.time()
    pipe = StableDiffusionInpaintPipeline.from_pretrained(MODEL, dtype=torch.float16, variant="fp16",
                                                          safety_checker=None).to(dev)
    pipe.set_progress_bar_config(disable=True)
    load_s = round(time.time() - t0, 1)
    mask = Image.open(d / "mask_small.png").convert("L")
    disp = np.load(str(d / "disp_small.npy"))
    inject = {"t": None}
    orig = PSI.randn_tensor

    def patched(shape, generator=None, device=None, dtype=None, layout=None):
        if inject["t"] is not None and tuple(shape) == tuple(inject["t"].shape):
            return inject["t"].to(device=device, dtype=dtype)
        return orig(shape, generator=generator, device=device, dtype=dtype, layout=layout)
    PSI.randn_tensor = patched
    base = np.random.default_rng(seed).standard_normal((h8, w8, 4)).astype(np.float32)
    rep = {"pair": pid, "noise": noise, "strength": strength, "seed": seed, "steps": STEPS,
           "effective_steps": max(1, int(STEPS * strength)), "guidance": GUIDANCE, "model": MODEL,
           "prompt": meta["prompt"], "device": dev, "torch": torch.__version__, "load_s": load_s,
           "size": [w8, h8], "frames": []}
    last = n - 1 if not n_limit else min(n - 1, n_limit + 1)
    for i in range(1, last):
        img = Image.open(d / "small" / f"f{i:02d}.png").convert("RGB")
        hole = 0.0
        s_i = strength * math.sin(math.pi * i / (n - 1)) if noise == "warped-ramp" else strength
        if int(STEPS * s_i) < 1:
            img.save(o / f"f{i:02d}.png")
            rep["frames"].append({"i": i, "wall_s": 0.0, "noise_hole_frac": 0.0, "strength": round(s_i, 3), "steps": 0})
            print(f"{pid} {tag} f{i:02d} skeleton (strength {s_i:.3f})", flush=True)
            continue
        if noise.startswith("warped"):
            lat, hole = warped_noise_latent(base, np.random.default_rng(seed * 1000 + i), disp, tw[i])
            inject["t"] = torch.from_numpy(lat.transpose(2, 0, 1)[None])
            g = torch.Generator(device="cpu").manual_seed(seed)
        else:
            inject["t"] = None
            g = torch.Generator(device="cpu").manual_seed(seed * 1000 + i)
        if dev == "mps":
            torch.mps.synchronize()
        t = time.time()
        res = pipe(prompt=meta["prompt"], image=img, mask_image=mask, strength=s_i,
                   num_inference_steps=STEPS, guidance_scale=GUIDANCE, generator=g,
                   width=w8, height=h8).images[0]
        if dev == "mps":
            torch.mps.synchronize()
        wall = round(time.time() - t, 2)
        res.save(o / f"f{i:02d}.png")
        rep["frames"].append({"i": i, "wall_s": wall, "noise_hole_frac": round(hole, 4), "strength": round(s_i, 3),
                              "steps": int(STEPS * s_i)})
        print(f"{pid} {tag} f{i:02d} {wall}s hole={hole:.3f} strength={s_i:.3f}", flush=True)
    walls = [f["wall_s"] for f in rep["frames"]]
    rep.update({"n_generated": len(walls), "s_per_frame_mean": round(float(np.mean(walls)), 2),
                "s_per_frame_max": round(float(np.max(walls)), 2),
                "peak_rss_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2)})
    (o / "gen.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: v for k, v in rep.items() if k != "frames"}), flush=True)


# ---- measure (.venv) --------------------------------------------------------------------

def skeleton_flow_error(frames, disp, tw):
    """Mean |g_(i+1) - g_i warped by the skeleton's inter-frame displacement| on gray in [0, 1]:
    how far each clip's motion is from the skeleton's own motion (the skeleton clip is the floor)."""
    import cv2
    h, w = disp.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    errs = []
    for i in range(len(frames) - 1):
        dt = tw[i + 1] - tw[i]
        ga = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
        gb = cv2.cvtColor(frames[i + 1], cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
        pred = cv2.remap(ga, gx - dt * disp[..., 0], gy - dt * disp[..., 1], cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT)
        errs.append(float(np.abs(gb - pred).mean()))
    return round(float(np.mean(errs)), 4), [round(e, 4) for e in errs]


def encode_clip(frames, path, fps, A, B):
    import cv2
    sys.path.insert(0, str(ROOT))
    import transitions as T
    h, w = frames[0].shape[:2]
    stats = T.StreamStats(len(frames))
    enc = T.FrameEncoder(path, w, h, fps)
    try:
        for i, f in enumerate(frames):
            enc.write(f)
            stats.add(i, f)
        written = enc.close()
    except BaseException:
        enc.abort()
        raise
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(stats.strip(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    Path(path).with_name("strip.jpg").write_bytes(buf.tobytes())
    return written, stats.quality(A, B)


def frequency_split_blend(det_hi, gen_lo, sigma=LIFT_SIGMA):
    """The research artifact's lift (generative.frequency_split_blend, amount 1): the generator's
    low frequencies under the skeleton's high frequencies at the native canvas."""
    import cv2
    if gen_lo.shape[:2] != det_hi.shape[:2]:
        gen_lo = cv2.resize(gen_lo, (det_hi.shape[1], det_hi.shape[0]), interpolation=cv2.INTER_CUBIC)
    dd = det_hi.astype(np.float32)
    g = gen_lo.astype(np.float32)
    return np.clip((dd - cv2.GaussianBlur(dd, (0, 0), sigma)) + cv2.GaussianBlur(g, (0, 0), sigma) + 0.5,
                   0, 255).astype(np.uint8)


def flow_smooth(frames, disp, tw, weights=(1, 2, 3, 2, 1)):
    """Each in-between frame averaged with its neighbours warped into it along the skeleton's field
    (frame j's pixel q shows what frame i shows at q + (tw_j - tw_i) * dAB(q)); the endpoints stay."""
    import cv2
    n = len(frames)
    h, w = disp.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    k0 = len(weights) // 2
    out = [frames[0]]
    for i in range(1, n - 1):
        acc = np.zeros(frames[0].shape, np.float32)
        tot = 0.0
        for k, wt in zip(range(-k0, k0 + 1), weights):
            j = min(n - 1, max(0, i + k))
            dt = tw[j] - tw[i]
            f = frames[j].astype(np.float32) if j == i else cv2.remap(
                frames[j], gx + dt * disp[..., 0], gy + dt * disp[..., 1], cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT).astype(np.float32)
            acc += wt * f
            tot += wt
        out.append(np.clip(acc / tot + 0.5, 0, 255).astype(np.uint8))
    out.append(frames[-1])
    return out


def _steps(frames):
    import cv2
    g = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32) for f in frames]
    return [float(np.abs(g[i + 1] - g[i]).mean()) for i in range(len(g) - 1)]


def measure(out, pairs):
    import cv2
    OUT = Path(out)
    summary_path = OUT / "gen_bridge.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    rd = lambda p: cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
    for pid in pairs:
        d = OUT / pid
        meta = json.loads((d / "meta.json").read_text())
        tw = json.loads((d / "tw.json").read_text())
        n, fps = meta["n_frames"], meta["fps"]
        small = [rd(d / "small" / f"f{i:02d}.png") for i in range(n)]
        native = [rd(d / "skeleton" / f"f{i:02d}.png") for i in range(n)]
        disp_s, disp_n = np.load(str(d / "disp_small.npy")), np.load(str(d / "disp_native.npy"))
        Fs = None
        if meta["mask_frac"] < 1.0:
            m = cv2.imread(str(d / "mask_small.png"), cv2.IMREAD_GRAYSCALE)
            Fs = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), MIX_FEATHER_SIGMA * meta["small"][0] / meta["canvas"][0])[..., None]
            mn = cv2.imread(str(d / "mask_native.png"), cv2.IMREAD_GRAYSCALE)
            Fn = cv2.GaussianBlur((mn > 0).astype(np.float32), (0, 0), MIX_FEATHER_SIGMA)[..., None]
        rows = summary.setdefault(pid, {"meta": meta})
        clips = {}
        # the skeleton itself, at both canvases (the floor every number is read against)
        for name, frames, dsp, A, B in (("skeleton_small", small, disp_s, small[0], small[-1]),
                                         ("skeleton_native", native, disp_n, native[0], native[-1])):
            o = d / name
            o.mkdir(exist_ok=True)
            written, q = encode_clip(frames, o / "transition.mp4", fps, A, B)
            sfe, _ = skeleton_flow_error(frames, dsp, tw)
            st = _steps(frames)
            clips[name] = {"n_frames": written, "canvas": [frames[0].shape[1], frames[0].shape[0]],
                           "step_mean": round(float(np.mean(st)), 3), "step_max": round(float(np.max(st)), 3),
                           "step_first": round(st[0], 3), "step_last": round(st[-1], 3),
                           "skeleton_flow_error": sfe, "warping_error": q["warping_error"],
                           "edge_ratio": q["flicker"]["edge_ratio"],
                           "endpoint": [q["endpoint"]["first_vs_A"], q["endpoint"]["last_vs_B"]]}
        for g in sorted(d.glob("gen_*")):
            if not (g / "gen.json").exists():
                continue
            gen = json.loads((g / "gen.json").read_text())
            if gen["n_generated"] < n - 2:
                clips[g.name] = {"partial": gen["n_generated"], "s_per_frame_mean": gen["s_per_frame_mean"]}
                continue
            frames = [small[0]]
            for i in range(1, n - 1):
                f = rd(g / f"f{i:02d}.png")
                if Fs is not None:
                    f = np.clip(f * Fs + small[i] * (1 - Fs) + 0.5, 0, 255).astype(np.uint8)
                frames.append(f)
            frames.append(small[-1])
            written, q = encode_clip(frames, g / "transition.mp4", fps, small[0], small[-1])
            sfe, per = skeleton_flow_error(frames, disp_s, tw)
            st = _steps(frames)
            mid = n // 2
            cv2.imwrite(str(g / "mid.jpg"), cv2.cvtColor(frames[mid], cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
            gen_vs_skel = round(float(np.mean([np.abs(frames[i].astype(np.float32) - small[i]).mean()
                                               for i in range(1, n - 1)])), 2)
            clips[g.name] = {"n_frames": written, "canvas": [frames[0].shape[1], frames[0].shape[0]],
                             "noise": gen["noise"], "strength": gen["strength"], "seed": gen["seed"],
                             "s_per_frame_mean": gen["s_per_frame_mean"], "peak_rss_gb": gen["peak_rss_gb"],
                             "step_mean": round(float(np.mean(st)), 3), "step_max": round(float(np.max(st)), 3),
                             "step_first": round(st[0], 3), "step_last": round(st[-1], 3),
                             "skeleton_flow_error": sfe, "warping_error": q["warping_error"],
                             "edge_ratio": q["flicker"]["edge_ratio"],
                             "endpoint": [q["endpoint"]["first_vs_A"], q["endpoint"]["last_vs_B"]],
                             "gen_vs_skeleton_mad": gen_vs_skel,
                             "noise_hole_frac_max": max(f["noise_hole_frac"] for f in gen["frames"])}
            if gen["noise"].startswith("warped") and not gen["seed"]:
                suffix = f"{'-ramp' if gen['noise'] == 'warped-ramp' else ''}_s{gen['strength']:g}"
                smoothed = flow_smooth(frames, disp_s, tw)
                for name, src_frames, dsp, base in ((f"smooth{suffix}", smoothed, disp_s, small),
                                                     (f"lift{suffix}", frames, disp_n, native),
                                                     (f"lift-smooth{suffix}", smoothed, disp_n, native)):
                    lo = d / name
                    lo.mkdir(exist_ok=True)
                    if name.startswith("lift"):
                        outf = [native[0]]
                        for i in range(1, n - 1):
                            f = frequency_split_blend(native[i], src_frames[i])
                            if Fs is not None:
                                f = np.clip(f * Fn + native[i] * (1 - Fn) + 0.5, 0, 255).astype(np.uint8)
                            outf.append(f)
                        outf.append(native[-1])
                    else:
                        outf = src_frames
                    written, q = encode_clip(outf, lo / "transition.mp4", fps, base[0], base[-1])
                    sfe, _ = skeleton_flow_error(outf, dsp, tw)
                    st = _steps(outf)
                    cv2.imwrite(str(lo / "mid.jpg"), cv2.cvtColor(outf[mid], cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
                    clips[name] = {"n_frames": written, "canvas": [outf[0].shape[1], outf[0].shape[0]],
                                   "from": g.name, "sigma_px": LIFT_SIGMA if name.startswith("lift") else None,
                                   "step_mean": round(float(np.mean(st)), 3), "step_max": round(float(np.max(st)), 3),
                                   "step_first": round(st[0], 3), "step_last": round(st[-1], 3),
                                   "skeleton_flow_error": sfe, "warping_error": q["warping_error"],
                                   "edge_ratio": q["flicker"]["edge_ratio"],
                                   "endpoint": [q["endpoint"]["first_vs_A"], q["endpoint"]["last_vs_B"]],
                                   "gen_vs_skeleton_mad": round(float(np.mean([np.abs(outf[i].astype(np.float32) - base[i]).mean()
                                                                              for i in range(1, n - 1)])), 2)}
        # seed reproducibility: a repeat dir (seed 0 rerun into gen_<noise>_s<x>_rep) vs the first run
        for r in sorted(d.glob("gen_*_rep")):
            src = d / r.name[:-4]
            diffs = []
            for f in sorted(r.glob("f*.png")):
                if (src / f.name).exists():
                    diffs.append(int(np.abs(rd(f).astype(int) - rd(src / f.name).astype(int)).max()))
            clips[r.name] = {"repeat_of": src.name, "frames_compared": len(diffs),
                             "same_seed_max_abs_diff": max(diffs) if diffs else None}
        rows.update(clips)
        for k, v in clips.items():
            print(pid, k, json.dumps(v), flush=True)
        summary_path.write_text(json.dumps(summary, indent=2))


# ---- page (.venv) -----------------------------------------------------------------------

def page(out, pairs):
    sys.path.insert(0, str(ROOT / "scripts"))
    from bench_transitions import label_strip
    OUT = Path(out)
    summary = json.loads((OUT / "gen_bridge.json").read_text())
    rel = lambda p: os.path.relpath(p, OUT)
    html = ["<!doctype html><meta charset=utf-8><title>TR6-A — the generative bridge on the skeleton</title>",
            "<style>body{font:14px system-ui;margin:16px;background:#111;color:#ddd;max-width:1750px}h2{margin-top:40px;border-top:1px solid #333;padding-top:16px}"
            ".top{display:flex;gap:12px;align-items:flex-start;margin:8px 0}.top img{height:200px}"
            ".row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:10px 0 18px;padding:8px;background:#181818;border-radius:6px}"
            ".cell video{width:100%;max-height:560px;background:#000}.cell img{max-width:100%;display:block;margin-top:6px}"
            "code{color:#9cf}.legend td{padding:3px 10px;vertical-align:top}.pick label{margin-right:12px}"
            "textarea{width:100%;max-width:900px;background:#222;color:#ddd;border:1px solid #444}button{padding:6px 12px}"
            ".note{color:#bbb}.hint{background:#26210a;padding:10px;border-radius:6px;margin:12px 0}"
            "table.num{border-collapse:collapse;font-size:13px}table.num td,table.num th{border:1px solid #333;padding:3px 8px;text-align:right}table.num th:first-child,table.num td:first-child{text-align:left}</style>",
            "<h1>TR6-A — the generative bridge on the deterministic skeleton (2026-09-15)</h1>",
            "<div class=hint><b>What varies: whether a diffusion model re-draws the in-between frames, how much (strength), and "
            "whether its noise follows the skeleton's motion.</b> The skeleton is the tool's own clip (class B pan-and-zoom for the "
            "mismatches; TR14's <code>hold-dis</code> field for match_4), 30 frames, 1 s. Every generated clip keeps the skeleton's "
            "frames 0 and 29 byte for byte; frames 1–28 are SD 1.5 inpainting on MPS re-drawing the skeleton frame from partial noise "
            "(strength 0.4 = 8 of 20 steps, 0.6 = 12 of 20; guidance 6; the prompt is under each pair). <code>indep</code>: fresh noise "
            "per frame. <code>warped</code>: frame 0's noise carried along the skeleton's displacement (Go-with-the-Flow, simplified). "
            "<code>warped-ramp</code>: warped noise with the strength ramped as sin(πu), so nothing is re-drawn at the endpoints. "
            "<code>smooth</code>: the warped clip filtered along the skeleton's flow (each frame averaged with two neighbours each side, "
            "warped into it). <code>lift</code> / <code>lift-smooth</code>: the warped / smoothed clip lifted to the native canvas — the "
            "model's low frequencies under the skeleton's fine detail (σ 3 px). match_4 keeps the skeleton outside the changed mask. Numbers: adjacent step = mean gray change between "
            "frames (levels); skeleton-flow error = how far each clip's motion is from the skeleton's own (the skeleton row is the floor); "
            "warping error and edge_ratio are the tool's basket. Pick the clip closest to what you want per pair, tick "
            "<b>acceptable as-is</b> only if it is, say what is wrong, then <b>Export picks</b> (gen_bridge_picks.json).</div>",
            "<p><button onclick='exportPicks()'>Export picks</button> <span id=status class=note></span></p>"]
    order = lambda k: (0 if k.startswith("skeleton") else 1 if k.startswith("gen_indep") else 2 if k.startswith("gen_warped")
                       else 3 if k.startswith("smooth") else 4, k)
    for pid in pairs:
        s = summary.get(pid, {})
        meta = s.get("meta", {})
        d = OUT / pid
        keys = sorted([k for k in s if k != "meta" and "n_frames" in s[k]], key=order)
        html.append(f"<h2 id='{pid}'>{pid} <small>skeleton <code>{meta.get('skeleton')}</code> · canvas {meta.get('canvas')} → "
                    f"generator {meta.get('small')} · mask {meta.get('mask_frac')} of the canvas · prompt “{meta.get('prompt')}”</small></h2>")
        html.append(f"<div class=top><img src='{rel(d / 'thumb_A.jpg')}' title='A'><img src='{rel(d / 'thumb_B.jpg')}' title='B'></div>")
        html.append("<table class=num><tr><th>clip</th><th>canvas</th><th>step mean / max</th><th>step first / last</th>"
                    "<th>skeleton-flow error</th><th>warping error</th><th>edge_ratio</th><th>endpoints</th><th>gen vs skeleton (levels)</th><th>s / frame</th></tr>")
        for k in keys:
            r = s[k]
            html.append(f"<tr><td><code>{k}</code></td><td>{r['canvas'][0]}×{r['canvas'][1]}</td><td>{r['step_mean']} / {r['step_max']}</td>"
                        f"<td>{r['step_first']} / {r['step_last']}</td><td>{r['skeleton_flow_error']}</td><td>{r['warping_error']}</td>"
                        f"<td>{r['edge_ratio']}</td><td>{r['endpoint'][0]} / {r['endpoint'][1]}</td><td>{r.get('gen_vs_skeleton_mad', '')}</td>"
                        f"<td>{r.get('s_per_frame_mean', '')}</td></tr>")
        html.append("</table>")
        reps = [k for k in s if k.endswith("_rep")]
        if reps:
            html.append("<p class=note>seed reproducibility: " + "; ".join(
                f"<code>{k}</code> vs <code>{s[k]['repeat_of']}</code>: max abs diff {s[k]['same_seed_max_abs_diff']} over {s[k]['frames_compared']} frames" for k in reps) + "</p>")
        html.append(f"<div class=pick><b>Closest to what you want:</b> " + " ".join(
            f"<label><input type=radio name='pick_{pid}' value='{k}' onchange='save()'> {k}</label>" for k in keys)
            + f" <label><input type=radio name='pick_{pid}' value='none' onchange='save()'> none</label>"
            + f" &nbsp; <label><input type=checkbox id='ok_{pid}' onchange='save()'> <b>acceptable as-is</b></label></div>")
        html.append(f"<textarea id='note_{pid}' rows=2 placeholder='what is wrong in the closest clip? is the motion a transformation or a fade?' oninput='save()'></textarea>")
        cells = []
        for k in keys:
            r = s[k]
            o = d / k
            if (o / "strip.jpg").exists() and not (o / "strip_labeled.jpg").exists():
                label_strip(o / "strip.jpg", o / "strip_labeled.jpg", r["n_frames"], r["n_frames"] / meta.get("fps", 30))
            cells.append(f"<div class=cell><code>{k}</code> · step {r['step_mean']} / {r['step_max']} · skeleton-flow {r['skeleton_flow_error']} · "
                         f"warping {r['warping_error']} · edge_ratio {r['edge_ratio']}"
                         f"<br><video src='{rel(o / 'transition.mp4')}' controls loop muted playsinline preload=metadata></video>"
                         f"<img src='{rel(o / 'strip_labeled.jpg')}'></div>")
        for i in range(0, len(cells), 2):
            html.append("<div class=row>" + "".join(cells[i:i + 2]) + "</div>")
    html.append("""<script>
const KEY='gen_bridge_picks:'+location.pathname;
function collect(){const p={};document.querySelectorAll('h2[id]').forEach(h=>{const id=h.id;const r=document.querySelector(`input[name='pick_${id}']:checked`);
 const n=document.getElementById('note_'+id);const ok=document.getElementById('ok_'+id);
 if((r&&r.value)||(n&&n.value)||(ok&&ok.checked))p[id]={pick:r?r.value:'',acceptable_as_is:!!(ok&&ok.checked),note:n?n.value:''};});return p;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(collect()));document.getElementById('status').textContent='saved locally '+new Date().toLocaleTimeString();}catch(e){}}
function restore(){try{const p=JSON.parse(localStorage.getItem(KEY)||'{}');for(const id in p){const r=document.querySelector(`input[name='pick_${id}'][value='${p[id].pick}']`);if(r)r.checked=true;
 const n=document.getElementById('note_'+id);if(n&&p[id].note)n.value=p[id].note;const ok=document.getElementById('ok_'+id);if(ok)ok.checked=!!p[id].acceptable_as_is;}}catch(e){}}
function exportPicks(){const blob=new Blob([JSON.stringify({date:new Date().toISOString(),page:'gen_bridge',picks:collect()},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='gen_bridge_picks.json';a.click();document.getElementById('status').textContent='gen_bridge_picks.json downloaded';}
restore();
</script>""")
    (OUT / "index.html").write_text("\n".join(html))
    print(f"wrote {OUT / 'index.html'}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) > 2 and a[0] == "--skeleton":
        skeleton(a[1], a[2:])
    elif len(a) >= 5 and a[0] == "--generate":
        generate(a[1], a[2], a[3], float(a[4]), int(a[5]) if len(a) > 5 else 0, int(a[6]) if len(a) > 6 else 0)
    elif len(a) > 2 and a[0] == "--measure":
        measure(a[1], a[2:])
    elif len(a) > 2 and a[0] == "--page":
        page(a[1], a[2:])
    else:
        sys.exit(__doc__)
