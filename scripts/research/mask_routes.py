#!/usr/bin/env python3
"""Two routes to cut a photo into layers, side by side on the owner's fixtures (Track E, 2026-09-27
evening; TRANSITIONS.md §12.5 question 3, backlog row T18).

Route R (rules): the depth model the tool already has (Depth Anything V2 Small, offline through
`transitions.model_disparity`) plus photometric tests, through `layered_probe.Scene.mask`.
  R-generic: ONE fixed rule set (`GENERIC` below) applied to every photo, no per-photo tuning.
  R-tuned:   the rendered layers of the hand-tuned round-2 scores (mismatch_6_r2, mismatch_4_r2).
Route P (panoptic): Mask2Former Swin-Tiny through `transformers`, CPU, 6 torch threads.
  coco: facebook/mask2former-swin-tiny-coco-panoptic (133 labels, panoptic: instances + stuff).
  ade:  facebook/mask2former-swin-tiny-ade-semantic (150 labels, semantic: one region per label;
        no Swin-Tiny ADE20K panoptic checkpoint exists on the hub, 2026-09-27).
Weights are fetched ONCE into OUT/hf_home (never models/, never ~/.cache); `--stage offline`
re-runs route P with HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 into OUT/offline and compares the
label maps byte for byte.

Research script: changes nothing in reveal.py / transitions.py / layered_probe.py / the scores.

  .venv/bin/python scripts/research/mask_routes.py --stage all        # rules, coco, ade, offline, page
  .venv/bin/python scripts/research/mask_routes.py --stage page       # rebuild the page from the caches
"""
import argparse
import hashlib
import html
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "research"))

OUT = ROOT / "benchmarks" / "runs" / "2026-09-27" / "masks"
PAIRS = ["mismatch_1", "mismatch_2", "mismatch_3", "mismatch_4", "mismatch_5", "mismatch_6",
         "mismatch_7", "match_3", "match_5"]
MAX_LONG = 1920
THREADS = 6
TILE = 720              # long side of every page image, px
SCORES = {"mismatch_6": "mismatch_6_r2.json", "mismatch_4": "mismatch_4_r2.json"}

MODELS = {
    "coco": {"repo": "facebook/mask2former-swin-tiny-coco-panoptic", "kind": "panoptic",
             # upstream test settings: detectron2 INPUT.MIN/MAX_SIZE_TEST 800 / 1333,
             # maskformer2 panoptic configs OBJECT_MASK_THRESHOLD / OVERLAP_THRESHOLD 0.8
             "short": 800, "long": 1333, "threshold": 0.8, "overlap": 0.8, "mask_threshold": 0.5},
    "ade": {"repo": "facebook/mask2former-swin-tiny-ade-semantic", "kind": "semantic",
            # upstream Base-ADE20K-SemanticSegmentation.yaml: MIN/MAX_SIZE_TEST 512 / 2048
            "short": 512, "long": 2048},
}

# R-generic: the one rule set a universal tool could ship today. Every value is the probe's default
# for that rule (layered_probe.Scene.mask); the disparity bands cut 0..1 at fixed values.
GENERIC = {
    "sky":    {"rule": "depth_bg", "lo": 0.02, "hi": 0.08},
    "clouds": {"rule": "clouds", "within": "sky", "channel": "b", "b_cloud": -4.0, "opaque": 0.35,
               "clear_pct": 5, "window": 100, "blur": 2.0},
    "stars":  {"rule": "stars", "within": "sky", "tophat": 8.0, "max_area": 80, "jitter": 0.4},
    "sun":    {"rule": "sun", "within": "sky", "thr": 92.0, "grow": 12},
    "ground": {"rule": "skyline_below", "d": 0.03, "run": 20, "frac": 0.7, "bottom": 0.6,
               "median": 9, "feather": 3.0},
    "far":    {"rule": "depth_band", "lo": 0.04, "hi": 0.34, "soft": 0.02},
    "mid":    {"rule": "depth_band", "lo": 0.34, "hi": 0.64, "soft": 0.02},
    "near":   {"rule": "depth_band", "lo": 0.64, "hi": 1.00, "soft": 0.02},
}
# paint order of the R-generic partition, front first; "ground" is drawn as its skyline line
GENERIC_PRIORITY = ["sun", "stars", "clouds", "sky", "near", "mid", "far"]

# label groups for the IoU numbers; every name is matched exactly against the model's id2label
GROUPS = {
    "sky":      {"coco": ["sky-other-merged"], "ade": ["sky"]},
    "tree":     {"coco": ["tree-merged"], "ade": ["tree", "plant", "palm"]},
    "building": {"coco": ["building-other-merged", "house", "roof"],
                 "ade": ["building", "skyscraper", "house", "tower"]},
    "water":    {"coco": ["water-other", "sea", "river"], "ade": ["water", "sea", "river", "lake"]},
}
# the tuned layer compared with each group (pair, source photo, layer name, rendered?)
TUNED_VS = [
    ("mismatch_6", "A", "sky", "sky"), ("mismatch_6", "A", "buildings", "building"),
    ("mismatch_6", "B", "trees", "tree"), ("mismatch_6", "B", "trees_core", "tree"),
    ("mismatch_4", "A", "sky", "sky"), ("mismatch_4", "A", "band", "building"),
    ("mismatch_4", "B", "band_b", "building"), ("mismatch_4", "A", "water", "water"),
    ("mismatch_4", "B", "water_b", "water"),
]
MIN_SHARE = 0.01        # a route "returns a sky" when its sky covers at least 1 % of the canvas

COLOURS = {  # RGB
    "sky": (70, 130, 235), "clouds": (225, 225, 235), "stars": (255, 245, 110), "sun": (255, 150, 20),
    "tree": (60, 175, 60), "building": (235, 120, 50), "water": (30, 205, 205),
    "near": (215, 60, 200), "mid": (160, 95, 230), "far": (115, 120, 210), "person": (230, 60, 110),
}
TUNED_GROUP = {"sky": "sky", "clouds": "clouds", "stars": "stars", "buildings": "building",
               "trees": "tree", "ac_unit": None, "band": "building", "band_b": "building",
               "water": "water", "sun": "sun", "sun_b_layer": "sun"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rss_bytes():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(r if sys.platform == "darwin" else r * 1024)


def photo_id(pair, src):
    return f"{pair}_{'S' if src == 'A' else 'F'}"


def canvases():
    import layered_probe as P
    for pair in PAIRS:
        A, B = P.canvas_pair(pair, MAX_LONG)
        yield pair, A, B


# ---------------------------------------------------------------------------
# Route R
# ---------------------------------------------------------------------------

def stage_rules(out):
    import layered_probe as P
    import transitions as T
    import torch
    torch.set_num_threads(THREADS)
    cache = out / "cache" / "rules"
    cache.mkdir(parents=True, exist_ok=True)
    meta = {"layered_probe_md5": md5((ROOT / "scripts/research/layered_probe.py").read_bytes()),
            "generic": GENERIC, "photos": {}, "tuned": {}}
    for pair, A, B in canvases():
        scene = P.Scene(A, B, seed=0)
        for src, img in (("A", A), ("B", B)):
            pid = photo_id(pair, src)
            t0 = time.perf_counter()
            d = scene.disparity(src)
            t_depth = time.perf_counter() - t0
            t0 = time.perf_counter()
            masks, notes = {}, {}
            for name, rule in GENERIC.items():
                m = dict(rule)
                if "within" in m:
                    m["within"] = f"sky@{src}"
                try:
                    a = scene.mask({"name": f"{name}@{src}", "from": src, "mask": m})
                except SystemExit as e:      # the sun rule raises when no blob exists
                    a = np.zeros(d.shape, np.float32)
                    scene.masks[f"{name}@{src}"] = a
                    notes[name] = str(e)
                masks[name] = a > 0.5
            skyline = scene.masks["_skyline_" + src].astype(np.float32)
            t_rules = time.perf_counter() - t0
            np.savez_compressed(cache / f"{pid}.npz", disp=(d * 255).astype(np.uint8), skyline=skyline,
                                **{k: v for k, v in masks.items()})
            cv2.imwrite(str(cache / f"{pid}.jpg"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])
            meta["photos"][pid] = {"pair": pair, "src": src, "h": int(img.shape[0]), "w": int(img.shape[1]),
                                   "depth_s": round(t_depth, 3), "rules_s": round(t_rules, 3), "notes": notes}
            print(f"[rules] {pid} {img.shape[1]}x{img.shape[0]} depth {t_depth:.2f}s rules {t_rules:.2f}s {notes}",
                  flush=True)
        if pair in SCORES:
            score = json.loads((ROOT / "scripts/research/scores" / SCORES[pair]).read_text())
            ts = P.Scene(A, B, seed=0)
            ts.disp = scene.disp          # the same disparity, not recomputed
            t0 = time.perf_counter()
            tm, info = {}, []
            for lay in score["layers"]:
                a = ts.mask(lay)
                tm[lay["name"]] = a > 0.5
                info.append({"name": lay["name"], "from": lay["from"], "render": lay.get("render", True),
                             "depth": lay.get("depth", 0), "rule": lay["mask"]["rule"]})
            t_tuned = time.perf_counter() - t0
            np.savez_compressed(cache / f"{pair}_tuned.npz", **tm)
            meta["tuned"][pair] = {"score": SCORES[pair], "layers": info, "masks_s": round(t_tuned, 3)}
            print(f"[rules] {pair} tuned {len(info)} layers {t_tuned:.2f}s", flush=True)
    meta["peak_rss_bytes"] = rss_bytes()
    (cache / "meta.json").write_text(json.dumps(meta, indent=1))


# ---------------------------------------------------------------------------
# Route P
# ---------------------------------------------------------------------------

def blob_bytes(hf_home, repo):
    """Bytes of the files in the repo's snapshot (huggingface_hub 1.x keeps the blobs in a shared
    store under hub/blobs/; the snapshot links point there)."""
    d = Path(hf_home) / "hub" / ("models--" + repo.replace("/", "--")) / "snapshots"
    if not d.exists():
        return 0
    return sum(f.resolve().stat().st_size for f in d.rglob("*") if f.is_file())


def hub_bytes(hf_home):
    d = Path(hf_home) / "hub"
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file() and not f.is_symlink()) if d.exists() else 0


LOSS_STUB_NOTE = (
    "Mask2FormerForUniversalSegmentation.__init__ builds its training loss (Mask2FormerLoss), whose "
    "constructor calls requires_backends(self, ['scipy']) for the Hungarian matcher; scipy is not in "
    "the venv and nothing may be installed. Inference never calls the loss (it runs only when "
    "mask_labels are passed), so the script swaps in an empty module at run time. Nothing on disk "
    "changes; a tool that ships route P needs scipy in requirements or the same stub.")


def compute_segments(torch, mask_probs, pred_scores, pred_labels, mask_threshold, overlap, fuse, size):
    """transformers 5.17 image_processing_mask2former.compute_segments + check_segment_validity,
    copied: that module is a torchvision-gated placeholder in this venv (no torchvision), so its
    helpers cannot be imported. Pixel ids start at 1; 0 = no segment."""
    mask_probs = torch.nn.functional.interpolate(mask_probs[None], size=size, mode="bilinear",
                                                 align_corners=False)[0]
    seg = torch.zeros(size, dtype=torch.int32)
    segments, stuff, cur = [], {}, 0
    mask_probs = mask_probs * pred_scores.view(-1, 1, 1)
    mask_labels = mask_probs.argmax(0)
    for k in range(pred_labels.shape[0]):
        c = int(pred_labels[k].item())
        mk = mask_labels == k
        area, orig = mk.sum(), (mask_probs[k] >= mask_threshold).sum()
        if not (area > 0 and orig > 0 and (area / orig).item() > overlap):
            continue
        if c in stuff:
            cur_id = stuff[c]
        else:
            cur += 1
            cur_id = cur
        seg[mk] = cur_id
        segments.append({"id": cur_id, "label_id": c, "was_fused": c in fuse,
                         "score": round(float(pred_scores[k].item()), 6)})
        if c in fuse:
            stuff[c] = cur_id
    return seg, segments


def stage_panoptic(out, key, dest):
    hf_home = out / "hf_home"
    os.environ["HF_HOME"] = str(hf_home)            # before transformers / huggingface_hub import
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    offline = os.environ.get("HF_HUB_OFFLINE") == "1"
    import torch
    import transformers
    from transformers import Mask2FormerForUniversalSegmentation
    torch.set_num_threads(THREADS)
    torch.manual_seed(0)
    torch.set_grad_enabled(False)
    transformers.logging.set_verbosity_error()
    spec = MODELS[key]
    repo = spec["repo"]
    cache_dir = str(hf_home / "hub")
    from transformers.models.mask2former import modeling_mask2former as mm

    class _NoLoss(torch.nn.Module):       # see LOSS_STUB_NOTE
        def __init__(self, config, weight_dict=None):
            super().__init__()
            # the fields _init_weights touches; no matcher, so no scipy
            self.num_labels = config.num_labels
            self.eos_coef = config.no_object_weight
            self.empty_weight = torch.nn.Buffer(torch.ones(self.num_labels + 1))

    mm.Mask2FormerLoss = _NoLoss
    hub_before = hub_bytes(hf_home)
    t0 = time.perf_counter()
    model = Mask2FormerForUniversalSegmentation.from_pretrained(repo, cache_dir=cache_dir).eval()
    # AutoImageProcessor needs torchvision (not in the venv); the model's own preprocessor_config.json
    # gives rescale 1/255 + mean/std, applied below by hand (resize is ours in any case)
    from huggingface_hub import hf_hub_download
    pcfg = json.loads(Path(hf_hub_download(repo, "preprocessor_config.json", cache_dir=cache_dir)).read_text())
    t_first = time.perf_counter() - t0
    bytes_after = blob_bytes(hf_home, repo)
    hub_after = hub_bytes(hf_home)
    t0 = time.perf_counter()
    model, load_info = Mask2FormerForUniversalSegmentation.from_pretrained(
        repo, cache_dir=cache_dir, local_files_only=True, output_loading_info=True)
    model = model.eval()
    t_load = time.perf_counter() - t0
    load_info = {k: sorted(str(x) for x in v) for k, v in load_info.items() if isinstance(v, (list, set))}
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    dest.mkdir(parents=True, exist_ok=True)
    meta = {"repo": repo, "kind": spec["kind"], "offline": offline, "transformers": transformers.__version__,
            "torch": torch.__version__, "threads": torch.get_num_threads(),
            "downloaded_bytes": hub_after - hub_before, "blob_bytes": bytes_after, "load_info": load_info,
            "loss_stub": LOSS_STUB_NOTE,
            "first_load_s": round(t_first, 2), "load_s": round(t_load, 2),
            "params": int(sum(p.numel() for p in model.parameters())), "id2label": id2label, "photos": {}}
    for pair, A, B in canvases():
        for src, img in (("A", A), ("B", B)):
            pid = photo_id(pair, src)
            h, w = img.shape[:2]
            s = min(spec["short"] / min(h, w), spec["long"] / max(h, w))
            nh, nw = max(32, int(round(h * s / 32)) * 32), max(32, int(round(w * s / 32)) * 32)
            x = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
            xf = (x.astype(np.float32) * np.float32(pcfg["rescale_factor"]) - np.float32(pcfg["image_mean"])) \
                / np.float32(pcfg["image_std"])
            pv = torch.from_numpy(np.ascontiguousarray(xf.transpose(2, 0, 1)))[None]
            t0 = time.perf_counter()
            o = model(pixel_values=pv, pixel_mask=torch.ones((1, nh, nw), dtype=torch.long))
            t_inf = time.perf_counter() - t0
            t0 = time.perf_counter()
            # transformers 5.17's post-processing squeezes the mask logits to 384 x 384 before the
            # target size (image_processing_mask2former.py, "(384, 384) for all models"); this keeps
            # them at 1/4 of the model input and interpolates straight to the input size instead
            cls = o.class_queries_logits[0]
            mq = o.masks_queries_logits[0]
            segs = []
            if spec["kind"] == "panoptic":
                scores, labels = torch.nn.functional.softmax(cls, dim=-1).max(-1)
                keep = labels.ne(cls.shape[-1] - 1) & (scores > spec["threshold"])
                mp, sc, lb = mq.sigmoid()[keep], scores[keep], labels[keep]
                fuse = {i for i, n in id2label.items() if i >= 80}      # COCO stuff classes 80..132
                if mp.shape[0]:
                    seg, info = compute_segments(torch, mp, sc, lb, spec["mask_threshold"], spec["overlap"],
                                                 fuse, (nh, nw))
                    seg = seg.numpy().astype(np.int32)
                else:
                    seg, info = np.zeros((nh, nw), np.int32), []
                best = {}
                for it in info:
                    if it["id"] not in best or it["score"] > best[it["id"]]["score"]:
                        best[it["id"]] = it
                segs = [{"id": int(i), "label": id2label[int(v["label_id"])], "score": float(v["score"])}
                        for i, v in sorted(best.items())]
            else:
                probs = torch.einsum("qc,qhw->chw", cls.softmax(-1)[..., :-1], mq.sigmoid())
                probs = torch.nn.functional.interpolate(probs[None], size=(nh, nw), mode="bilinear",
                                                        align_corners=False)[0]
                lab = probs.argmax(0).numpy().astype(np.int32)
                seg = np.zeros((nh, nw), np.int32)
                for c in np.unique(lab):
                    seg[lab == c] = int(c) + 1
                    segs.append({"id": int(c) + 1, "label": id2label[int(c)], "score": None})
            full = cv2.resize(seg.astype(np.uint16), (w, h), interpolation=cv2.INTER_NEAREST)
            t_post = time.perf_counter() - t0
            cv2.imwrite(str(dest / f"{pid}.png"), full)
            meta["photos"][pid] = {"model_in": [nw, nh], "canvas": [w, h], "infer_s": round(t_inf, 3),
                                   "post_s": round(t_post, 3), "segments": segs,
                                   "labels_md5": md5(full.tobytes())}
            print(f"[{key}] {pid} in {nw}x{nh} infer {t_inf:.2f}s post {t_post:.2f}s "
                  f"{len(segs)} segs: {', '.join(s['label'] for s in segs)}", flush=True)
    meta["peak_rss_bytes"] = rss_bytes()
    (dest / "meta.json").write_text(json.dumps(meta, indent=1))


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def colour_of(name):
    if name in COLOURS:
        return COLOURS[name]
    for g, per in GROUPS.items():
        if any(name in v for v in per.values()):
            return COLOURS[g]
    hsh = int(md5(name.encode())[:6], 16)
    hsv = np.uint8([[[hsh % 180, 150 + (hsh >> 8) % 90, 170 + (hsh >> 16) % 80]]])
    return tuple(int(c) for c in cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)[0, 0])


def small(img, tw, th, nearest=False):
    return cv2.resize(img, (tw, th), interpolation=cv2.INTER_NEAREST if nearest else cv2.INTER_AREA)


def overlay(photo, regions, lines=None):
    """photo RGB uint8 (tile size); regions: [(name, bool mask at tile size, rgb)], painted in order
    (a later region does not overwrite an earlier one's pixels). Returns RGB uint8."""
    th, tw = photo.shape[:2]
    base = photo.astype(np.float32) * 0.38
    taken = np.zeros((th, tw), bool)
    labels = []
    for name, m, rgb in regions:
        m = m & ~taken
        taken |= m
        if not m.any():
            continue
        col = np.float32(rgb)
        base[m] = base[m] * 0.45 + col * 0.55
        edge = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
        base[edge] = 255.0 * 0.85
        if m.sum() >= 0.004 * th * tw:
            dt = cv2.distanceTransform(np.pad(m, 1).astype(np.uint8), cv2.DIST_L2, 5)[1:-1, 1:-1]
            y, x = np.unravel_index(int(np.argmax(dt)), dt.shape)
            labels.append((name, int(x), int(y)))
    out = np.clip(base, 0, 255).astype(np.uint8)
    if lines is not None:
        pts = np.stack([np.arange(tw), np.clip(lines, 0, th - 1)], 1).astype(np.int32)
        cv2.polylines(out, [pts], False, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.polylines(out, [pts], False, (20, 20, 20), 1, cv2.LINE_AA)
    fs = max(0.6, tw / 900.0)
    for name, x, y in labels:
        (lw, lh), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
        x0 = int(np.clip(x - lw // 2, 2, max(2, tw - lw - 2)))
        y0 = int(np.clip(y + lh // 2, lh + 2, th - 4))
        cv2.putText(out, name, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(out, name, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, fs, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def iou(a, b):
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else None


def group_mask(seg, segs, key, group):
    names = set(GROUPS[group][key])
    ids = [s["id"] for s in segs if s["label"] in names]
    return np.isin(seg, ids) if ids else np.zeros(seg.shape, bool)


def fmt_share(x):
    return f"{100 * x:.1f} %"


def save_jpg(path, rgb):
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 80])


EXPLAIN = """REPLACED_BY_EXPLAIN_FILE"""


def stage_page(out):
    rules = json.loads((out / "cache/rules/meta.json").read_text())
    pmeta = {k: json.loads((out / f"cache/{k}/meta.json").read_text()) for k in MODELS
             if (out / f"cache/{k}/meta.json").exists()}
    offm = {k: json.loads((out / f"offline/{k}/meta.json").read_text()) for k in MODELS
            if (out / f"offline/{k}/meta.json").exists()}
    img_dir = out / "img"
    img_dir.mkdir(exist_ok=True)
    for key, pm in pmeta.items():   # prove every group name exists in the vocabulary it is matched against
        vocab = set(pm["id2label"].values())
        for g, per in GROUPS.items():
            missing = [n for n in per[key] if n not in vocab]
            assert not missing, (key, g, missing)
    numbers = {"photos": {}, "tuned": [], "counts": {}, "matching": {}, "offline_identical": {}}
    rows_html = []
    tuned_cache = {p: dict(np.load(out / f"cache/rules/{p}_tuned.npz")) for p in rules["tuned"]}
    for pid, ph in rules["photos"].items():
        pair, src, H, W = ph["pair"], ph["src"], ph["h"], ph["w"]
        s = TILE / max(H, W)
        tw, th = int(round(W * s)), int(round(H * s))
        photo = cv2.cvtColor(cv2.imread(str(out / f"cache/rules/{pid}.jpg")), cv2.COLOR_BGR2RGB)
        photo_s = small(photo, tw, th)
        z = np.load(out / f"cache/rules/{pid}.npz")
        rec = {"canvas": [W, H], "depth_s": ph["depth_s"], "rules_s": ph["rules_s"], "generic_share": {},
               "iou_sky": {}, "p_share": {}}
        tiles = []
        save_jpg(img_dir / f"{pid}_photo.jpg", photo_s)
        tiles.append(("photo", f"img/{pid}_photo.jpg", [], f"canvas {W}×{H} px"))
        disp = cv2.applyColorMap(small(z["disp"], tw, th), cv2.COLORMAP_MAGMA)[..., ::-1]
        save_jpg(img_dir / f"{pid}_depth.jpg", disp)
        tiles.append(("depth (what route R sees)", f"img/{pid}_depth.jpg", [],
                      f"disparity 0 far (black) … 1 near (yellow); {ph['depth_s']:.2f} s"))
        # R-generic
        regs, legend = [], []
        for name in GENERIC_PRIORITY:
            m = z[name]
            rec["generic_share"][name] = float(m.mean())
            regs.append((name, small(m.astype(np.uint8), tw, th, True) > 0, colour_of(name)))
            legend.append((name, colour_of(name), m.mean()))
        rec["generic_share"]["ground"] = float(z["ground"].mean())
        legend.append(("ground (below the white skyline line)", (255, 255, 255), z["ground"].mean()))
        sky_line = np.interp((np.arange(tw) + 0.5) / s - 0.5, np.arange(W), z["skyline"]) * s
        save_jpg(img_dir / f"{pid}_generic.jpg", overlay(photo_s, regs, sky_line))
        sun_note = " · no sun blob (L > 92)" if "sun" in ph["notes"] else ""
        tiles.append(("R-generic (one rule set, no tuning)", f"img/{pid}_generic.jpg", legend,
                      f"{ph['rules_s']:.2f} s rules + {ph['depth_s']:.2f} s depth{sun_note}"))
        # R-tuned
        if pair in tuned_cache:
            tinfo = rules["tuned"][pair]
            layers = [l for l in tinfo["layers"] if l["from"] == src and l["render"]]
            layers.sort(key=lambda l: -l["depth"])
            regs, legend = [], []
            for l in layers:
                m = tuned_cache[pair][l["name"]]
                g = TUNED_GROUP.get(l["name"])
                c = COLOURS[g] if g else colour_of(l["name"])
                regs.append((l["name"], small(m.astype(np.uint8), tw, th, True) > 0, c))
                legend.append((l["name"], c, m.mean()))
            save_jpg(img_dir / f"{pid}_tuned.jpg", overlay(photo_s, regs))
            tiles.append((f"R-tuned ({tinfo['score']}, hand-tuned over two sessions)", f"img/{pid}_tuned.jpg",
                          legend, f"{len(layers)} rendered layers from this photo; masks {tinfo['masks_s']:.2f} s "
                                  "for the pair"))
        # P
        rsky = z["sky"]
        for key, pm in pmeta.items():
            pp = pm["photos"][pid]
            seg = cv2.imread(str(out / f"cache/{key}/{pid}.png"), cv2.IMREAD_UNCHANGED).astype(np.int32)
            segs = pp["segments"]
            area = {sg["id"]: float((seg == sg["id"]).mean()) for sg in segs}
            order = sorted(segs, key=lambda sg: area[sg["id"]])        # small ones on top
            seg_s = small(seg.astype(np.uint16), tw, th, True)
            regs = [(sg["label"], seg_s == sg["id"], colour_of(sg["label"])) for sg in order]
            save_jpg(img_dir / f"{pid}_{key}.jpg", overlay(photo_s, regs))
            byl = {}
            for sg in segs:
                byl.setdefault(sg["label"], 0.0)
                byl[sg["label"]] += area[sg["id"]]
            legend = [(lab, colour_of(lab), v) for lab, v in sorted(byl.items(), key=lambda kv: -kv[1])]
            void = float((seg == 0).mean())
            if void > 0:
                legend.append(("(no segment)", (60, 60, 60), void))
            rec["p_share"][key] = byl
            psky = group_mask(seg, segs, key, "sky")
            rec["iou_sky"][key] = iou(rsky, psky)
            rec.setdefault("p_sky_share", {})[key] = float(psky.mean())
            n_inst = len(segs)
            tiles.append((f"P-{key} ({'COCO panoptic, 133 labels' if key == 'coco' else 'ADE20K semantic, 150 labels'})",
                          f"img/{pid}_{key}.jpg", legend,
                          f"{n_inst} segments, {len(byl)} labels · model input {pp['model_in'][0]}×{pp['model_in'][1]} "
                          f"px · {pp['infer_s']:.2f} s inference + {pp['post_s']:.2f} s post"))
        rec["r_sky_share"] = float(rsky.mean())
        numbers["photos"][pid] = rec
        # row html
        th_ = []
        for title, src_, legend, note in tiles:
            lg = "".join(f'<li><span class="sw" style="background:rgb{tuple(c)}"></span>{html.escape(n)}'
                         f' <b>{fmt_share(v)}</b></li>' for n, c, v in legend)
            th_.append(f'<figure><figcaption>{html.escape(title)}</figcaption>'
                       f'<img loading="lazy" src="{src_}" width="{tw}" height="{th}" alt="{html.escape(pid)} {html.escape(title)}">'
                       f'<ul class="lg">{lg}</ul><p class="note">{html.escape(note)}</p></figure>')
        ious = " · ".join(f"IoU sky R-generic vs P-{k}: " + ("—" if v is None else f"{v:.2f}")
                          for k, v in rec["iou_sky"].items())
        rows_html.append(f'<section class="row" id="{pid}"><h3>{pid} <span>({pair}, '
                         f'{"start" if src == "A" else "finish"} photo)</span></h3>'
                         f'<div class="tiles">{"".join(th_)}</div><p class="nums">{ious} · sky share R-generic '
                         f'{fmt_share(rec["r_sky_share"])}, '
                         + ", ".join(f"P-{k} {fmt_share(v)}" for k, v in rec.get("p_sky_share", {}).items())
                         + "</p></section>")
    # tuned IoUs
    for pair, src, lname, group in TUNED_VS:
        pid = photo_id(pair, src)
        m = tuned_cache[pair][lname]
        rendered = next(l["render"] for l in rules["tuned"][pair]["layers"] if l["name"] == lname)
        row = {"pair": pair, "photo": pid, "layer": lname, "rendered": rendered, "group": group,
               "tuned_share": float(m.mean())}
        for key, pm in pmeta.items():
            seg = cv2.imread(str(out / f"cache/{key}/{pid}.png"), cv2.IMREAD_UNCHANGED).astype(np.int32)
            pmask = group_mask(seg, pm["photos"][pid]["segments"], key, group)
            row[f"iou_{key}"] = iou(m, pmask)
            row[f"p_share_{key}"] = float(pmask.mean())
        numbers["tuned"].append(row)
    # counts
    numbers["counts"]["photos"] = len(rules["photos"])
    numbers["counts"]["r_generic_sky"] = sum(r["r_sky_share"] >= MIN_SHARE for r in numbers["photos"].values())
    for key in pmeta:
        numbers["counts"][f"p_{key}_sky"] = sum(r["p_sky_share"][key] >= MIN_SHARE
                                                for r in numbers["photos"].values())
    # layer matching
    for pair in [p for p in PAIRS if p.startswith("mismatch")]:
        a, b = numbers["photos"][photo_id(pair, "A")], numbers["photos"][photo_id(pair, "B")]
        numbers["matching"][pair] = {}
        for key in pmeta:
            la, lb = a["p_share"][key], b["p_share"][key]
            both = {l: (la[l], lb[l]) for l in la if l in lb}
            numbers["matching"][pair][key] = {
                "both": dict(sorted(both.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))),
                "A_only": dict(sorted(((l, v) for l, v in la.items() if l not in lb), key=lambda kv: -kv[1])),
                "B_only": dict(sorted(((l, v) for l, v in lb.items() if l not in la), key=lambda kv: -kv[1]))}
    # offline check
    for key in pmeta:
        if key in offm:
            same = [pid for pid in pmeta[key]["photos"]
                    if pmeta[key]["photos"][pid]["labels_md5"] == offm[key]["photos"][pid]["labels_md5"]]
            numbers["offline_identical"][key] = {"identical": len(same), "of": len(pmeta[key]["photos"]),
                                                 "offline_load_s": offm[key]["load_s"],
                                                 "offline_first_load_s": offm[key]["first_load_s"],
                                                 "offline_downloaded_bytes": offm[key]["downloaded_bytes"]}
    numbers["models"] = {k: {kk: vv for kk, vv in v.items() if kk not in ("photos", "id2label")}
                         | {"n_labels": len(v["id2label"]),
                            "infer_s": [p["infer_s"] for p in v["photos"].values()],
                            "model_in": {pid: p["model_in"] for pid, p in v["photos"].items()}}
                         for k, v in pmeta.items()}
    numbers["rules_peak_rss_bytes"] = rules["peak_rss_bytes"]
    numbers["layered_probe_md5"] = rules["layered_probe_md5"]
    (out / "numbers.json").write_text(json.dumps(numbers, indent=1))
    write_html(out, numbers, rules, pmeta, rows_html)


def write_html(out, numbers, rules, pmeta, rows_html):
    esc = html.escape
    explain_f = out / "explain.html"
    explain = explain_f.read_text() if explain_f.exists() else "<p>(explanation not written yet)</p>"
    # tables
    t_models = ["<tr><th>route P model</th><th>labels</th><th>weights on disk</th><th>params</th>"
                "<th>first load (download + load)</th><th>load</th><th>inference per photo</th>"
                "<th>peak RSS</th><th>offline re-run identical</th></tr>"]
    for k, m in numbers["models"].items():
        inf = m["infer_s"]
        off = numbers["offline_identical"].get(k)
        t_models.append(
            f"<tr><td><a href='https://huggingface.co/{m['repo']}'>{m['repo']}</a> ({m['kind']})</td>"
            f"<td>{m['n_labels']}</td><td>{m['blob_bytes']:,} B</td><td>{m['params']:,}</td>"
            f"<td>{m['first_load_s']} s</td><td>{m['load_s']} s</td>"
            f"<td>median {np.median(inf):.2f} s, max {max(inf):.2f} s</td>"
            f"<td>{m['peak_rss_bytes'] / 2**20:.0f} MiB</td>"
            f"<td>{'—' if not off else str(off['identical']) + ' of ' + str(off['of']) + ' label maps'}</td></tr>")
    dep = [p["depth_s"] for p in rules["photos"].values()]
    rul = [p["rules_s"] for p in rules["photos"].values()]
    t_models.append(f"<tr><td>route R: Depth Anything V2 Small (already in models/depth) + rules</td><td>none</td>"
                    f"<td>0 B new</td><td>—</td><td>—</td><td>—</td>"
                    f"<td>depth median {np.median(dep):.2f} s + rules median {np.median(rul):.2f} s</td>"
                    f"<td>{numbers['rules_peak_rss_bytes'] / 2**20:.0f} MiB</td><td>—</td></tr>")
    t_sky = ["<tr><th>photo</th><th>R-generic sky share</th>"
             + "".join(f"<th>P-{k} sky share</th><th>IoU R-generic ∩ P-{k}</th>" for k in pmeta) + "</tr>"]
    for pid, r in numbers["photos"].items():
        t_sky.append(f"<tr><td><a href='#{pid}'>{pid}</a></td><td>{fmt_share(r['r_sky_share'])}</td>"
                     + "".join(f"<td>{fmt_share(r['p_sky_share'][k])}</td><td>"
                               + ("—" if r['iou_sky'][k] is None else f"{r['iou_sky'][k]:.2f}") + "</td>"
                               for k in pmeta) + "</tr>")
    t_tuned = ["<tr><th>photo</th><th>tuned layer</th><th>P group</th><th>tuned share</th>"
               + "".join(f"<th>P-{k} share</th><th>IoU with P-{k}</th>" for k in pmeta) + "</tr>"]
    for r in numbers["tuned"]:
        t_tuned.append(f"<tr><td>{r['photo']}</td><td>{r['layer']}{'' if r['rendered'] else ' (not rendered)'}</td>"
                       f"<td>{r['group']}</td><td>{fmt_share(r['tuned_share'])}</td>"
                       + "".join(f"<td>{fmt_share(r['p_share_' + k])}</td><td>"
                                 + ("—" if r['iou_' + k] is None else f"{r['iou_' + k]:.2f}") + "</td>" for k in pmeta)
                       + "</tr>")
    t_match = ["<tr><th>pair</th><th>model</th><th>labels in both photos (start share / finish share)</th>"
               "<th>start only</th><th>finish only</th></tr>"]
    for pair, per in numbers["matching"].items():
        for k, mm in per.items():
            both = ", ".join(f"{l} ({fmt_share(a)} / {fmt_share(b)})" for l, (a, b) in mm["both"].items()) or "none"
            ao = ", ".join(f"{l} {fmt_share(v)}" for l, v in mm["A_only"].items()) or "none"
            bo = ", ".join(f"{l} {fmt_share(v)}" for l, v in mm["B_only"].items()) or "none"
            t_match.append(f"<tr><td>{pair}</td><td>P-{k}</td><td>{esc(both)}</td><td>{esc(ao)}</td><td>{esc(bo)}</td></tr>")
    c = numbers["counts"]
    counts = (f"Photos with a sky of at least 1 % of the canvas: R-generic {c['r_generic_sky']} of {c['photos']}, "
              + ", ".join(f"P-{k} {c[f'p_{k}_sky']} of {c['photos']}" for k in pmeta) + ".")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mask routes</title>
<style>
:root{{--bg:#111316;--fg:#e6e6e6;--mut:#9aa0a6;--card:#1b1e22;--line:#30343a;--acc:#8ab4f8}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif;margin:0;padding:16px}}
main{{max-width:1500px;margin:0 auto}} a{{color:var(--acc)}}
h1{{font-size:1.5em;margin:.2em 0}} h2{{margin-top:1.6em;border-bottom:1px solid var(--line)}}
.explain{{max-width:860px}} .explain p,.explain li{{margin:.4em 0}}
pre{{background:var(--card);padding:10px;overflow-x:auto;font-size:12px;border-radius:6px}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;font-size:13px}} td,th{{border:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}}
.row{{border-top:1px solid var(--line);padding:10px 0}} .row h3{{margin:.3em 0}} .row h3 span{{color:var(--mut);font-weight:normal;font-size:.8em}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:10px}}
figure{{margin:0;background:var(--card);padding:6px;border-radius:6px;min-width:0}}
figcaption{{font-weight:600;font-size:13px;margin-bottom:4px}} figure img{{width:100%;height:auto;display:block}}
.lg{{list-style:none;padding:0;margin:6px 0 0;font-size:12px;columns:2}} .lg li{{break-inside:avoid}}
.sw{{display:inline-block;width:10px;height:10px;margin-right:5px;border:1px solid #000;vertical-align:middle}}
.note,.nums{{color:var(--mut);font-size:12px;margin:4px 0}} .nums{{color:var(--fg)}}
</style></head><body><main>
<h1>Two ways to cut a photo into layers</h1>
<p class="note">Track E, 2026-09-27 evening · script <code>scripts/research/mask_routes.py</code> · numbers <a href="numbers.json">numbers.json</a> · canvas = <code>layered_probe.canvas_pair(pair, 1920)</code> · 18 photos: mismatch_1…7 and match_3, match_5, both photos each</p>
<div class="explain">{explain}</div>
<h2>Cost</h2><div class="tw"><table>{''.join(t_models)}</table></div>
<p class="note">Times on the M3 Pro with 6 torch threads while other render jobs ran on the same machine; each P model ran in its own process. Inference = one forward pass at the model input size; post = segment assembly and the nearest-neighbour upsample to the canvas. Peak RSS = <code>getrusage</code> maximum resident set of that process. Loading needed two run-time workarounds in the script, both without installing anything: the training-only loss class is replaced by an empty module (its constructor requires scipy), and the pixel normalisation and segment assembly are done in the script (the transformers image processor requires torchvision). The ADE20K repository holds only a pickle <code>pytorch_model.bin</code>; transformers also fetched a converted <code>model.safetensors</code> from the hub's conversion branch, so its cache holds 2 × 190 MB.</p>
<h2>The R-generic rule set (one dict, every photo)</h2>
<pre>{esc(json.dumps(GENERIC, indent=1))}</pre>
<p class="note">Paint order front first: {', '.join(GENERIC_PRIORITY)}; "ground" (the skyline rule) is the white line. A pixel belongs to the first layer whose matte exceeds 0.5. Rule code: <code>layered_probe.Scene.mask</code> (md5 {rules['layered_probe_md5']} at run time).</p>
<h2>Sky: R-generic against P</h2>
<p class="note">IoU = |R ∩ P| / |R ∪ P| over canvas pixels, R = the R-generic sky matte &gt; 0.5 (clouds, stars and sun inside it included), P = the union of the segments labelled {esc(', '.join(f'{k}: ' + '/'.join(GROUPS['sky'][k]) for k in pmeta))}. Share = fraction of the canvas.</p>
<p>{counts}</p>
<div class="tw"><table>{''.join(t_sky)}</table></div>
<h2>The hand-tuned layers against P</h2>
<p class="note">IoU as above between the tuned matte &gt; 0.5 and the P segments of the group: tree = {esc('; '.join(f'{k}: ' + '/'.join(GROUPS['tree'][k]) for k in pmeta))}; building = {esc('; '.join(f'{k}: ' + '/'.join(GROUPS['building'][k]) for k in pmeta))}; water = {esc('; '.join(f'{k}: ' + '/'.join(GROUPS['water'][k]) for k in pmeta))}.</p>
<div class="tw"><table>{''.join(t_tuned)}</table></div>
<h2>Which P labels both photos of a mismatch pair share</h2>
<p class="note">A label in both photos is a candidate for a layer-to-layer transformation; share = fraction of that photo's canvas.</p>
<div class="tw"><table>{''.join(t_match)}</table></div>
<h2>The photos</h2>
<p class="note">Each tile: the photo dimmed, each layer or segment in its colour with its name at its widest point (names are drawn only on regions of at least 0.4 % of the tile), the legend with each layer's share of the canvas. Same label, same colour across routes (sky blue, trees green, buildings orange, water cyan).</p>
{''.join(rows_html)}
</main></body></html>"""
    (out / "index.html").write_text(page)
    print(f"[page] {out / 'index.html'} {len(page)} B", flush=True)


def run_stage(args_list, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    cmd = [sys.executable, str(Path(__file__).resolve())] + args_list
    print("[run]", " ".join(args_list), env_extra or "", flush=True)
    subprocess.run(cmd, env=env, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, choices=["all", "rules", "panoptic", "offline", "page"])
    ap.add_argument("--model", choices=list(MODELS))
    ap.add_argument("--dest")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.stage == "rules":
        stage_rules(out)
    elif a.stage == "panoptic":
        stage_panoptic(out, a.model, Path(a.dest) if a.dest else out / "cache" / a.model)
    elif a.stage == "offline":
        for k in MODELS:
            run_stage(["--stage", "panoptic", "--model", k, "--out", str(out), "--dest", str(out / "offline" / k)],
                      {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    elif a.stage == "page":
        stage_page(out)
    else:
        run_stage(["--stage", "rules", "--out", str(out)])
        for k in MODELS:
            run_stage(["--stage", "panoptic", "--model", k, "--out", str(out)])
        run_stage(["--stage", "offline", "--out", str(out)])
        run_stage(["--stage", "page", "--out", str(out)])


if __name__ == "__main__":
    main()
