#!/usr/bin/env python3
"""Soft mattes for the layer source: one alpha per element, from its hard SAM 3 mask.

Round 10 item 1 (TRANSITIONS.md 13.15). The layer source
(benchmarks/runs/2026-09-28/layers_v3/<photo>/layers.{json,npz}) gives every element as a hard
mask on the pair's canvas. This script builds a trimap per element (core = the mask eroded by
r_in, unknown = the mask dilated by r_out minus the core, background = the rest), runs ViTMatte
(hustvl/vitmatte-small-composition-1k, VitMatteForImageMatting) on a crop around the element, and
pastes the alpha back into a canvas-size array. The alpha is forced to 1 inside the core and to 0
outside the dilated mask, so an element's matte never leaks past its band.

Subcommands
  warmup                 download the weights ONCE into benchmarks/runs/2026-10-17/mattes/hf_home/
                         and write MATTE_MANIFEST.json (repo, revision, sha256 per file, date).
  run PHOTO [--ids ..] [--min-share 0.002] [--band-px N] [--device cpu|mps] [--repo ..]
      [--lattice-ids ..]
                         offline (HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1); refuses without the
                         manifest or on a sha256 mismatch. Writes <photo>/el_<id>.png (uint8 alpha,
                         canvas W x H) and <photo>/mattes.json.
  sheet PHOTO --ids ..   contact sheet <photo>/sheet.jpg: photo crop | red hard edge | matte.
  check-crop PHOTO       <photo>/crop_check.jpg: element-map edges over the cover crop.

Numbers: r_in = r_out = max(4, 0.01 x short side) px unless --band-px; r_in is capped at half the
mask's maximum inner distance so a thin element keeps a core; an element with no core keeps its hard
mask ("fallback": "hard"). --lattice-ids switches an element to the lattice trimap (lattice_trimap:
a filled mask over a truss or spoked wheels opens where the photo is brighter than the mask's Otsu
luma). Context margin around the dilated box: max(32 px, 25 % of its size).
Preprocessing reproduces transformers' VitMatteImageProcessorPil (image /255, mean 0.5, std 0.5;
trimap /255; concatenated as a 4th channel; zero-padded bottom/right to a multiple of 32).
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LAYERS = ROOT / "benchmarks/runs/2026-09-28/layers_v3"
OUT = ROOT / "benchmarks/runs/2026-10-17/mattes"
HF_HOME = OUT / "hf_home"
MANIFEST = OUT / "MATTE_MANIFEST.json"
REPOS = ["hustvl/vitmatte-small-composition-1k", "hustvl/vitmatte-small-distinctions-646"]
FILES = ["config.json", "preprocessor_config.json", "model.safetensors"]
FIXTURE_EXTS = [".jpg", ".jpeg", ".png", ".heic", ".dng", ".arw", ".tif", ".tiff"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_warmup(args):
    os.environ["HF_HOME"] = str(HF_HOME)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    from huggingface_hub import snapshot_download, HfApi
    entries = []
    for repo in REPOS:
        rev = HfApi().model_info(repo).sha
        d = Path(snapshot_download(repo, revision=rev, allow_patterns=FILES,
                                   cache_dir=str(HF_HOME / "hub")))
        files = {f: {"sha256": sha256(d / f), "bytes": (d / f).stat().st_size} for f in FILES}
        entries.append({"repo": repo, "revision": rev, "path": str(d.relative_to(ROOT)),
                        "files": files})
        print(f"warmup: {repo}@{rev[:10]} -> {d}")
    MANIFEST.write_text(json.dumps({"date": datetime.date.today().isoformat(),
                                    "models": entries}, indent=1))
    print(f"warmup: manifest {MANIFEST}")


def load_model(repo, device):
    if not MANIFEST.exists():
        sys.exit(f"matte_source: no manifest at {MANIFEST}; run `matte_source.py warmup` first. "
                 "The run step never downloads.")
    man = json.loads(MANIFEST.read_text())
    ent = next((m for m in man["models"] if m["repo"] == repo), None)
    if ent is None:
        sys.exit(f"matte_source: {repo} is not in {MANIFEST}; run warmup.")
    d = ROOT / ent["path"]
    for f, meta in ent["files"].items():
        if not (d / f).exists() or sha256(d / f) != meta["sha256"]:
            sys.exit(f"matte_source: {d / f} missing or sha256 mismatch; re-run warmup.")
    os.environ["HF_HOME"] = str(HF_HOME)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from transformers import VitMatteForImageMatting
    import transformers
    transformers.logging.set_verbosity_error()
    torch.manual_seed(0)
    torch.set_grad_enabled(False)
    if device == "cpu":
        torch.use_deterministic_algorithms(True)
    model = VitMatteForImageMatting.from_pretrained(str(d), local_files_only=True).eval().to(device)
    return model, ent


def find_fixture(photo):
    for e in FIXTURE_EXTS:
        p = ROOT / "fixtures" / f"{photo}{e}"
        if p.exists():
            return p
    sys.exit(f"matte_source: no fixture for {photo} under fixtures/")


def load_canvas(photo):
    sys.path.insert(0, str(ROOT))
    import transitions as T
    lj = json.loads((LAYERS / photo / "layers.json").read_text())
    W, H = lj["canvas"]
    img = T.cover(T.load_image_rgb(find_fixture(photo)), W, H)
    el = np.load(LAYERS / photo / "layers.npz")["element"]
    assert el.shape == (H, W), (el.shape, W, H)
    return img, el, lj


def disk(r):
    r = int(r)
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def trimap_for(mask, r):
    """core, band (unknown), r_in used, fallback flag."""
    m8 = mask.astype(np.uint8)
    inner = cv2.distanceTransform(np.pad(m8, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    maxd = float(inner.max())
    r_in = min(r, int(maxd // 2))
    if r_in < 1:
        return None, None, 0, maxd
    core = cv2.erode(m8, disk(r_in)) > 0
    dil = cv2.dilate(m8, disk(r)) > 0
    return core, dil & ~core, r_in, maxd


def lattice_trimap(img, mask, r):
    """For a lattice (a truss, spoked wheels) whose hard mask is filled: core = the mask's pixels at
    or below the Otsu luma threshold inside the mask (eroded 1 px), background seeds = the brighter
    pixels inside the mask (eroded 2 px), unknown = the rest of the dilated mask."""
    luma = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    t, _ = cv2.threshold(luma[mask].reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    core = cv2.erode(((luma <= t) & mask).astype(np.uint8), disk(1)) > 0
    bgs = cv2.erode(((luma > t) & mask).astype(np.uint8), disk(2)) > 0
    dil = cv2.dilate(mask.astype(np.uint8), disk(r)) > 0
    return core, dil & ~core & ~bgs, bgs, float(t)


def infer(model, device, rgb, tri):
    import torch
    x = rgb.astype(np.float32) / 255.0
    x = (x - 0.5) / 0.5
    t = tri.astype(np.float32)[..., None] / 255.0
    px = np.concatenate([x, t], -1).transpose(2, 0, 1)
    h, w = tri.shape
    ph, pw = (-h) % 32, (-w) % 32
    px = np.pad(px, ((0, 0), (0, ph), (0, pw)))
    pv = torch.from_numpy(np.ascontiguousarray(px))[None].to(device)
    a = model(pixel_values=pv).alphas[0, 0, :h, :w].float().cpu().numpy()
    return a


def matte_element(model, device, img, el, eid, r, lattice=False):
    H, W = el.shape
    mask = el == eid
    area = int(mask.sum())
    rec = {"id": int(eid), "area_px": area, "trimap": "lattice" if lattice else "band"}
    bgs = None
    if lattice:
        core, band, bgs, t = lattice_trimap(img, mask, r)
        rec.update({"r_in": 1, "r_out": r, "otsu_luma": t,
                    "bg_seed_share_of_mask": round(float(bgs.sum()) / area, 4)})
    else:
        core, band, r_in, maxd = trimap_for(mask, r)
        rec.update({"r_in": r_in, "r_out": r, "max_inner_dist": round(maxd, 2)})
    if core is None or not core.any():
        rec["fallback"] = "hard"
        return (mask * 255).astype(np.uint8), rec
    dil = core | band | (bgs if bgs is not None else False)
    ys, xs = np.nonzero(dil)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    my = max(32, int(0.25 * (y1 - y0)))
    mx = max(32, int(0.25 * (x1 - x0)))
    y0, y1, x0, x1 = max(0, y0 - my), min(H, y1 + my), max(0, x0 - mx), min(W, x1 + mx)
    tri = np.zeros(mask.shape, np.uint8)
    tri[band] = 128
    tri[core] = 255                             # background seeds stay 0
    t0 = time.time()
    a = infer(model, device, img[y0:y1, x0:x1], tri[y0:y1, x0:x1])
    rec["infer_s"] = round(time.time() - t0, 3)
    alpha = np.zeros((H, W), np.float32)
    alpha[y0:y1, x0:x1] = a
    alpha[~dil] = 0.0
    alpha[core] = 1.0
    if bgs is not None:
        alpha[bgs] = 0.0
    out = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    af = out.astype(np.float32) / 255.0
    bvals = af[band]
    rec["crop"] = [int(x0), int(y0), int(x1), int(y1)]
    rec["band_px"] = int(band.sum())
    rec["band_soft_share"] = round(float(((bvals > 0.05) & (bvals < 0.95)).mean()), 4)
    rec["band_mean_abs_diff_hard"] = round(float(np.abs(bvals - mask[band]).mean()), 4)
    # alpha on the band's outer ring (the last dilated pixel): a high value means a cut at the end
    ring = dil & ~(cv2.erode(dil.astype(np.uint8), disk(1)) > 0)
    rec["outer_ring_mean_alpha"] = round(float(af[ring].mean()), 4)
    rec["matte_sum"] = round(float(af.sum()), 1)
    return out, rec


def cmd_run(args):
    img, el, lj = load_canvas(args.photo)
    H, W = el.shape
    r = args.band_px or max(4, int(round(0.01 * min(W, H))))
    els = {e["id"]: e for e in lj["elements"]}
    if args.ids:
        ids = args.ids
    else:
        ids = [e["id"] for e in lj["elements"] if e.get("area_share", 0) >= args.min_share]
    out_dir = Path(args.out) if args.out else OUT / args.photo
    out_dir.mkdir(parents=True, exist_ok=True)
    t_load = time.time()
    model, ent = load_model(args.repo, args.device)
    t_load = time.time() - t_load
    js_path = out_dir / "mattes.json"
    js = json.loads(js_path.read_text()) if js_path.exists() else {}
    js.update({"photo": args.photo, "canvas": [W, H], "repo": ent["repo"],
               "revision": ent["revision"], "device": args.device, "band_px": r,
               "model_load_s": round(t_load, 2)})
    js.setdefault("elements", {})
    T0 = time.time()
    for eid in ids:
        t0 = time.time()
        a, rec = matte_element(model, args.device, img, el, eid, r, eid in (args.lattice_ids or []))
        p = out_dir / f"el_{eid}.png"
        cv2.imwrite(str(p), a)
        e = els.get(eid, {})
        box = e.get("box")
        if not box:
            ys, xs = np.nonzero(el == eid)
            box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
            rec["box_from"] = "mask"
        rec.update({"label": e.get("label"), "group": e.get("group"), "box": box,
                    "area_share": e.get("area_share"), "wall_s": round(time.time() - t0, 3),
                    "device": args.device, "md5": hashlib.md5(p.read_bytes()).hexdigest()})
        js["elements"][str(eid)] = rec
        print(f"{args.photo} id {eid:3d} {str(rec['label']):14s} r_in {rec['r_in']:2d} "
              f"soft {rec.get('band_soft_share', '-')} |a-h| {rec.get('band_mean_abs_diff_hard', '-')} "
              f"ring {rec.get('outer_ring_mean_alpha', '-')} {rec['wall_s']:.2f}s"
              + (" FALLBACK hard" if rec.get("fallback") else ""))
    js["run_wall_s"] = round(time.time() - T0, 2)
    js_path.write_text(json.dumps(js, indent=1))
    print(f"{args.photo}: {len(ids)} elements, {js['run_wall_s']} s (+{t_load:.1f} s load) -> {out_dir}")


def label_tile(tile, text):
    t = tile.copy()
    cv2.rectangle(t, (0, 0), (t.shape[1], 18), (0, 0, 0), -1)
    cv2.putText(t, text, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    return t


def sheet_window(el, eid, box, W, H):
    """The element's box + 10 % margin, widened so the aspect stays within 1:2 .. 3:1."""
    if box:
        x0, y0, x1, y1 = box
    else:                                       # some elements carry no box: the mask's extent
        ys, xs = np.nonzero(el == eid)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    mx, my = 0.1 * (x1 - x0) + 4, 0.1 * (y1 - y0) + 4
    x0, y0, x1, y1 = x0 - mx, y0 - my, x1 + mx, y1 + my
    w, h = x1 - x0, y1 - y0
    if w < h / 2:
        x0, x1 = x0 - (h / 2 - w) / 2, x1 + (h / 2 - w) / 2
    elif w > 3 * h:
        y0, y1 = y0 - (w / 3 - h) / 2, y1 + (w / 3 - h) / 2
    return int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))


def cmd_sheet(args):
    img, el, lj = load_canvas(args.photo)
    H, W = el.shape
    els = {e["id"]: e for e in lj["elements"]}
    d = OUT / args.photo
    js = json.loads((d / "mattes.json").read_text())["elements"]
    rows = []
    bw, bh = 520, 340                           # each tile fits in this box
    for eid in args.ids:
        p = d / f"el_{eid}.png"
        if not p.exists():
            continue
        e = els[eid]
        x0, y0, x1, y1 = sheet_window(el, eid, e.get("box"), W, H)
        crop = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_RGB2BGR)
        m = (el[y0:y1, x0:x1] == eid).astype(np.uint8)
        edge = crop.copy()
        cnts, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(edge, cnts, -1, (0, 0, 255), 1)
        mat = cv2.cvtColor(cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
        s = min(bw / crop.shape[1], bh / crop.shape[0])
        sz = (max(1, int(crop.shape[1] * s)), max(1, int(crop.shape[0] * s)))
        lab = f"id {eid} {e['label']}"
        tiles = []
        for t, n in [(crop, "photo"), (edge, "hard edge (red)"), (mat, "matte")]:
            t = cv2.resize(t, sz, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
            t = cv2.copyMakeBorder(t, 0, bh - t.shape[0], 0, bw - t.shape[1], cv2.BORDER_CONSTANT,
                                   value=(40, 40, 40))
            tiles.append(label_tile(t, f"{lab} | {n}"))
        r = js.get(str(eid), {})
        head = np.full((24, 3 * bw + 8, 3), 255, np.uint8)
        txt = (f"id {eid} {e['label']} ({e.get('group')}), area {100 * e.get('area_share', 0):.2f} %, "
               f"r_in {r.get('r_in')} r_out {r.get('r_out')}, band soft share {r.get('band_soft_share')}, "
               f"mean |a-hard| {r.get('band_mean_abs_diff_hard')}" + (" FALLBACK hard" if r.get("fallback") else ""))
        cv2.putText(head, txt, (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        sep = np.full((bh, 4, 3), 255, np.uint8)
        rows.append(np.vstack([head, np.hstack([tiles[0], sep, tiles[1], sep, tiles[2]]),
                               np.full((6, 3 * bw + 8, 3), 255, np.uint8)]))
    if not rows:
        sys.exit("sheet: no mattes found")
    if len(rows) > 6:                           # two columns when long
        half = (len(rows) + 1) // 2
        c1, c2 = rows[:half], rows[half:]
        c2 += [np.full_like(rows[0], 255)] * (len(c1) - len(c2))
        sheet = np.hstack([np.vstack(c1), np.full((sum(r.shape[0] for r in c1), 16, 3), 255, np.uint8),
                           np.vstack(c2)])
    else:
        sheet = np.vstack(rows)
    cv2.imwrite(str(d / "sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"sheet: {d / 'sheet.jpg'} {sheet.shape[1]}x{sheet.shape[0]}, {len(rows)} rows")


def cmd_check_crop(args):
    img, el, lj = load_canvas(args.photo)
    gx = np.abs(np.diff(el.astype(np.int32), axis=1, prepend=el[:, :1])) > 0
    gy = np.abs(np.diff(el.astype(np.int32), axis=0, prepend=el[:1])) > 0
    v = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    v[gx | gy] = (0, 0, 255)
    d = OUT / args.photo
    d.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(d / "crop_check.jpg"), v, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"crop check: {d / 'crop_check.jpg'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("warmup")
    r = sp.add_parser("run")
    r.add_argument("photo")
    r.add_argument("--ids", type=int, nargs="*")
    r.add_argument("--min-share", type=float, default=0.002)
    r.add_argument("--band-px", type=int, default=0)
    r.add_argument("--device", choices=["cpu", "mps"], default="cpu")
    r.add_argument("--lattice-ids", type=int, nargs="*",
                   help="ids whose filled mask is a lattice: dark core + bright background seeds")
    r.add_argument("--repo", default=REPOS[0], choices=REPOS)
    r.add_argument("--out", default="")
    s = sp.add_parser("sheet")
    s.add_argument("photo")
    s.add_argument("--ids", type=int, nargs="+", required=True)
    c = sp.add_parser("check-crop")
    c.add_argument("photo")
    a = ap.parse_args()
    {"warmup": cmd_warmup, "run": cmd_run, "sheet": cmd_sheet, "check-crop": cmd_check_crop}[a.cmd](a)


if __name__ == "__main__":
    main()
