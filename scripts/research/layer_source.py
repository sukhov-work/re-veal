#!/usr/bin/env python3
"""Layer source for one photo (Track E2, 2026-09-28; research script, nothing enters transitions.py).

Cuts one photo into ELEMENTS a layered transition can match across a pair: each element is one
instance of a thing (a person, a car, a boat: the ADE20K panoptic pass) or one connected region of a
label (a sky, a building, a wall, a lake: ADE20K panoptic treats building and tree as stuff, so two
buildings apart are two elements, two touching buildings one), named by an ADE20K model, placed in depth by the depth model the tool already has (Depth Anything
V2 Small through transitions.model_disparity, offline), and, where ADE20K has no word, named by an
open-vocabulary route (sun, cloud, star, moon, galaxy core, meteor streak, air-conditioning unit).

Outputs in OUT (default benchmarks/runs/2026-09-28/layers/<photo>/):
  layers.npz   label (uint16: ADE20K index + 1, 0 = none, EXTRA_LABELS above 150), element (uint16
               element id, 0 = none), disparity (float32 0 far .. 1 near); with --extras also
               normals (int8 x3, unit vector x 127), edges (uint8 0/255), saliency (uint8)
  layers.json  per element: id, label, label_id, group, route, area_share, bbox, centroid,
               median_disparity, depth_rank (0 = nearest), mean_lab, touches, confidence; plus the
               frame block (canvas, skyline, horizon, light, edge density) and the provenance block
  timing.json  seconds per step (kept out of layers.json so two runs can be compared byte for byte)
layers.npz and layers.json are deterministic: the zip entries carry a fixed date, floats are
rounded, the torch thread count is fixed.

Offline: every model load passes a pinned revision and local_files_only unless --fetch is given;
HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 are set before transformers is imported. The one-time
fetch is `--fetch` on any photo. Weights live in --hf-home, never ~/.cache, never models/.

Dependencies: the stock transformers load of every ADE20K model here builds its training loss, whose
constructor requires scipy (Hungarian matcher); without scipy this script swaps in an empty loss
module at run time (inference never calls it; recorded as provenance.loss_stub). The processors
load through AutoProcessor, which picks the PIL backend when torchvision is absent. The Grounding
DINO + SAM 2.1 route needs torchvision (Sam2ImageProcessor has no PIL backend in transformers 5.17).

  .venv/bin/python scripts/research/layer_source.py mismatch_4_S
  .venv/bin/python scripts/research/layer_source.py fixtures/mismatch_6_F.jpg --canvas own --extras
  .venv/bin/python scripts/research/layer_source.py mismatch_4_S --fetch        # one-time download
"""
import argparse
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures"
DEFAULT_HF_HOME = ROOT / "benchmarks" / "runs" / "2026-09-28" / "layers" / "hf_home"
DEFAULT_OUT = ROOT / "benchmarks" / "runs" / "2026-09-28" / "layers"

# ---------------------------------------------------------------------------
# Models (revision = the hub commit measured on 2026-09-28; a load never resolves "main")
# ---------------------------------------------------------------------------
ADE_MODELS = {
    "oneformer_t_sem": {"repo": "shi-labs/oneformer_ade20k_swin_tiny", "rev": "05f2812b1eccf9909b3897777450f8d68148cafc",
                        "arch": "oneformer", "task": "semantic"},
    "oneformer_l_sem": {"repo": "shi-labs/oneformer_ade20k_swin_large", "rev": "4a5bac8e64f82681a12db2e151a4c2f4ce6092b2",
                        "arch": "oneformer", "task": "semantic"},
    # semantic for the name of every pixel (no void), panoptic for one element per thing instance
    "oneformer_l_both": {"repo": "shi-labs/oneformer_ade20k_swin_large", "rev": "4a5bac8e64f82681a12db2e151a4c2f4ce6092b2",
                         "arch": "oneformer", "task": "both"},
    "oneformer_l_pan": {"repo": "shi-labs/oneformer_ade20k_swin_large", "rev": "4a5bac8e64f82681a12db2e151a4c2f4ce6092b2",
                        "arch": "oneformer", "task": "panoptic"},
    "m2f_l_pan640": {"repo": "facebook/mask2former-swin-large-ade-panoptic", "rev": "ae53ed7ab37f8ea74f23d0e4f8c3d83c184a0caa",
                     "arch": "mask2former", "task": "panoptic",
                     "proc_kw": {"size": {"shortest_edge": 640, "longest_edge": 2560}}},
    "m2f_l_sem640": {"repo": "facebook/mask2former-swin-large-ade-semantic", "rev": "aa25c92404a40599614215e76514c79b427c7527",
                     "arch": "mask2former", "task": "semantic",
                     "proc_kw": {"size": {"shortest_edge": 640, "longest_edge": 2560}}},
    "eomt3_l_sem": {"repo": "tue-mps/eomt-dinov3-ade-semantic-large-512", "rev": "1d1f172700ab69371df7afe778fe133fff7dd521",
                    "arch": "eomt_dinov3", "task": "semantic"},
    "eomt_l_pan": {"repo": "tue-mps/ade20k_panoptic_eomt_large_640", "rev": "4d0ace83675d88497d6c4a10e17a0f46047685a5",
                   "arch": "eomt", "task": "panoptic"},
}
OV_MODELS = {
    "clipseg": {"repo": "CIDAS/clipseg-rd64-refined", "rev": "999e0328d9e10b484360c477313983f9afdd7050"},
    "gdino": {"repo": "IDEA-Research/grounding-dino-base", "rev": "12bdfa3120f3e7ec7b434d90674b3396eccf88eb"},
    "sam2": {"repo": "facebook/sam2.1-hiera-large", "rev": "665f8e2ad61cf5f53d65644ff27c8ee525124610"},
}
ONEFORMER_CLASS_INFO = ("shi-labs/oneformer_demo", "ade20k_panoptic.json")
DEFAULT_ADE = "oneformer_l_both"
DEFAULT_OV = "clipseg"

# The ADE20K-150 vocabulary, index order of every checkpoint above (names: first alias of the
# OneFormer config; Mask2Former's config spells ten of them differently, same indices).
ADE150 = ["wall", "building", "sky", "floor", "tree", "ceiling", "road", "bed", "window", "grass", "cabinet",
          "sidewalk", "person", "earth", "door", "table", "mountain", "plant", "curtain", "chair", "car", "water",
          "painting", "sofa", "shelf", "house", "sea", "mirror", "rug", "field", "armchair", "seat", "fence",
          "desk", "rock", "wardrobe", "lamp", "tub", "rail", "cushion", "base", "box", "column", "signboard",
          "chest of drawers", "counter", "sand", "sink", "skyscraper", "fireplace", "refrigerator", "grandstand",
          "path", "stairs", "runway", "case", "pool table", "pillow", "screen door", "stairway", "river", "bridge",
          "bookcase", "blind", "coffee table", "toilet", "flower", "book", "hill", "bench", "countertop", "stove",
          "palm", "kitchen island", "computer", "swivel chair", "boat", "bar", "arcade machine", "hovel", "bus",
          "towel", "light", "truck", "tower", "chandelier", "awning", "street lamp", "booth", "tv", "plane",
          "dirt track", "clothes", "pole", "land", "bannister", "escalator", "ottoman", "bottle", "buffet",
          "poster", "stage", "van", "ship", "fountain", "conveyer belt", "canopy", "washer", "plaything", "pool",
          "stool", "barrel", "basket", "falls", "tent", "bag", "minibike", "cradle", "oven", "ball", "food",
          "step", "tank", "trade name", "microwave", "pot", "animal", "bicycle", "lake", "dishwasher", "screen",
          "blanket", "sculpture", "hood", "sconce", "vase", "traffic light", "tray", "trash can", "fan", "pier",
          "crt screen", "plate", "monitor", "bulletin board", "shower", "radiator", "glass", "clock", "flag"]
assert len(ADE150) == 150
# Labels ADE20K lacks, named by the open-vocabulary route (ids above the 150 ADE ids + 1)
EXTRA_LABELS = {151: "sun", 152: "cloud", 153: "star", 154: "moon", 155: "galaxy core", 156: "meteor streak",
                157: "air conditioning unit"}
# the fixed prompt list of the open-vocabulary route (one list for every photo): the seven words
# ADE20K lacks, plus thirteen it has; a pixel takes the word of the highest map, so an extra word
# names a region only where it beats "sky", "building", "wall" ... (on 2026-09-28 CLIPSeg alone put
# "sun" over 42 % of mismatch_6_F's night sky when each word was thresholded on its own)
OV_EXTRA = ["sun", "cloud", "star", "moon", "galaxy core", "meteor streak", "air conditioning unit"]
OV_PROMPTS = OV_EXTRA + ["building", "tree", "person", "water", "sky", "mountain", "wall", "ceiling", "window",
                         "car", "street lamp", "bridge", "boat"]
# elements of these labels are one element per photo (a star field), not one per connected component
SCATTER = {"star"}

# Proposed label groups for matching an element of photo A with one of photo B: same group first,
# then GROUP_NEIGHBOURS in order. Every ADE20K label and every extra label is in exactly one group
# (asserted below). A proposal for Track A/C; nothing here has been tuned on a pair.
LABEL_GROUPS = {
    "sky": ["sky"],
    "cloud": ["cloud"],
    "luminary": ["sun", "moon", "galaxy core"],
    "star": ["star", "meteor streak"],
    "building": ["building", "house", "skyscraper", "tower", "hovel", "booth", "grandstand"],
    "structure": ["bridge", "pier", "fence", "column", "awning", "canopy", "tent", "stage", "pole", "rail",
                  "bannister", "escalator", "conveyer belt", "tank"],
    "tree": ["tree", "palm", "plant"],
    "vegetation": ["grass", "field", "flower"],
    "water": ["water", "sea", "river", "lake", "pool", "falls", "fountain"],
    "mountain": ["mountain", "hill", "rock"],
    "ground": ["earth", "land", "sand", "dirt track", "road", "sidewalk", "path", "runway"],
    "floor": ["floor", "rug", "stairs", "stairway", "step"],
    "wall": ["wall"],
    "ceiling": ["ceiling"],
    "opening": ["window", "door", "screen door", "curtain", "blind"],
    "person": ["person"],
    "animal": ["animal"],
    "vehicle": ["car", "bus", "truck", "van", "boat", "ship", "plane", "bicycle", "minibike"],
    "light": ["lamp", "street lamp", "light", "chandelier", "sconce", "traffic light"],
    "furniture": ["bed", "cabinet", "table", "chair", "sofa", "shelf", "armchair", "seat", "desk", "wardrobe",
                  "chest of drawers", "counter", "bookcase", "coffee table", "bench", "countertop", "kitchen island",
                  "swivel chair", "bar", "ottoman", "buffet", "stool", "cradle", "pool table", "base", "case"],
    "appliance": ["refrigerator", "stove", "computer", "arcade machine", "tv", "washer", "oven", "microwave",
                  "dishwasher", "screen", "hood", "fan", "crt screen", "monitor", "radiator", "air conditioning unit",
                  "fireplace", "sink", "tub", "toilet", "shower"],
    "picture": ["painting", "mirror", "signboard", "poster", "trade name", "sculpture", "bulletin board", "clock",
                "flag"],
    "object": ["cushion", "box", "pillow", "book", "towel", "clothes", "bottle", "plaything", "barrel", "basket",
               "bag", "ball", "food", "pot", "blanket", "vase", "tray", "trash can", "plate", "glass"],
}
GROUP_NEIGHBOURS = {
    "sky": ["cloud"], "cloud": ["sky", "star"], "luminary": ["light", "star"], "star": ["luminary", "light"],
    "building": ["structure", "tree", "mountain"], "structure": ["building", "tree"],
    "tree": ["vegetation", "building"], "vegetation": ["tree", "ground"], "water": ["ground", "floor", "sky"],
    "mountain": ["building", "tree"], "ground": ["floor", "water", "vegetation"], "floor": ["ground"],
    "wall": ["ceiling", "building"], "ceiling": ["wall", "sky"], "opening": ["picture", "wall"],
    "person": ["animal"], "animal": ["person"], "vehicle": ["furniture", "object"], "light": ["luminary"],
    "furniture": ["object", "appliance"], "appliance": ["furniture", "object"], "picture": ["opening"],
    "object": ["furniture"],
}
GROUP_OF = {lab: g for g, labs in LABEL_GROUPS.items() for lab in labs}
_missing = [l for l in ADE150 + list(EXTRA_LABELS.values()) if l not in GROUP_OF]
assert not _missing and len(GROUP_OF) == len(ADE150) + len(EXTRA_LABELS), _missing
SKY_GROUPS = ("sky", "cloud", "luminary", "star")

LOSS_STUB = ("the model constructor builds its training loss, whose __init__ calls requires_backends(self, "
             "['scipy']); scipy is absent, so an empty module replaces the loss class at run time; inference "
             "never calls it (it runs only when mask_labels are passed)")


def label_name(i):
    return ADE150[i - 1] if 1 <= i <= 150 else EXTRA_LABELS.get(i, "none")


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def resolve_photo(arg):
    """(path, fixture id or None). A fixture id is <pair>_S or <pair>_F under fixtures/."""
    p = Path(arg)
    if p.is_file():
        stem = p.stem
        return p, (stem if p.parent.resolve() == FIX.resolve() and stem[-2:] in ("_S", "_F") else None)
    hits = sorted(FIX.glob(f"{arg}.*"))
    if not hits:
        raise SystemExit(f"no file {arg} and no fixture {arg}.* under {FIX}")
    return hits[0], arg


def canvas_of(path, fixture, mode, max_long):
    """The photo on its canvas. mode pair: the pair canvas of layered_probe.canvas_pair (the FINISH
    photo's aspect, transitions.common_canvas + cover), so a fixture's layers line up with the probe;
    mode own: the photo's own aspect, long side at most max_long (INTER_AREA)."""
    sys.path.insert(0, str(ROOT))
    import transitions as T
    img = T.load_image_rgb(str(path))
    if mode == "pair":
        if fixture is None:
            raise SystemExit("--canvas pair needs a fixture id (<pair>_S / <pair>_F); use --canvas own")
        pair, side = fixture[:-2], fixture[-1]
        other = sorted(FIX.glob(f"{pair}_{'F' if side == 'S' else 'S'}.*"))[0]
        o = T.load_image_rgb(str(other))
        A, B = (img, o) if side == "S" else (o, img)
        w, h = T.common_canvas(A, B, max_long, "finish")
        return T.cover(img, w, h)
    h, w = img.shape[:2]
    s = min(1.0, max_long / float(max(h, w))) if max_long else 1.0
    if s < 1:
        img = cv2.resize(img, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(img)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def _stub_losses_if_needed(torch):
    try:
        import scipy  # noqa: F401
        return False
    except Exception:
        pass
    import importlib

    class _NoLoss(torch.nn.Module):
        """Carries only the fields the models' _init_weights touches (num_labels / num_classes,
        eos_coef, empty_weight, OneFormer's logit_scale); no matcher, so no scipy."""
        def __init__(self, config=None, weight_dict=None, num_classes=None, eos_coef=None, **kw):
            super().__init__()
            n = config.num_labels if config is not None else num_classes
            self.num_labels = self.num_classes = n
            self.eos_coef = eos_coef if eos_coef is not None else getattr(config, "no_object_weight", 0.1)
            self.empty_weight = torch.nn.Buffer(torch.ones(n + 1))
            if kw.get("contrastive_temperature") is not None:        # OneFormer's text-query loss
                self.logit_scale = torch.nn.Parameter(torch.tensor(0.0))

    for mod, cls in (("mask2former.modeling_mask2former", "Mask2FormerLoss"),
                     ("oneformer.modeling_oneformer", "OneFormerLoss"),
                     ("eomt.modeling_eomt", "EomtLoss"),
                     ("eomt_dinov3.modeling_eomt_dinov3", "EomtDinov3Loss")):
        m = importlib.import_module("transformers.models." + mod)
        setattr(m, cls, _NoLoss)
    return True


TVF_SHIM = ("transformers 5.17 image_processing_pil_oneformer.compute_segments (panoptic / instance) calls "
            "tvF.resize without importing torchvision (NameError when torchvision is absent); a module-level "
            "tvF with resize = bilinear torch interpolate (align_corners False) is injected; the resize only "
            "upsamples mask logits, where torchvision's antialias has no effect")


def _shim_tvf_if_needed(torch):
    try:
        import torchvision  # noqa: F401
        return False
    except Exception:
        pass
    import types
    from transformers.models.oneformer import image_processing_pil_oneformer as pil_of

    class _IM:
        BILINEAR = "bilinear"

    def _resize(t, size, interpolation="bilinear", **k):
        return torch.nn.functional.interpolate(t, size=tuple(size), mode="bilinear", align_corners=False)

    pil_of.tvF = types.SimpleNamespace(resize=_resize, InterpolationMode=_IM)
    return True


def _load(cls, spec, hub, fetch, **kw):
    return cls.from_pretrained(spec["repo"], revision=spec["rev"], cache_dir=hub, local_files_only=not fetch, **kw)


def ade_labels(img, key, hub, fetch, torch):
    """(label map uint16 ADE index + 1, confidence float32 0..1, segments list or None, info)."""
    import transformers
    spec = ADE_MODELS[key]
    h, w = img.shape[:2]
    from transformers import AutoProcessor
    if spec["arch"] == "oneformer":
        from transformers import OneFormerForUniversalSegmentation as C
    elif spec["arch"] == "mask2former":
        from transformers import Mask2FormerForUniversalSegmentation as C
    elif spec["arch"] == "eomt":
        from transformers import EomtForUniversalSegmentation as C
    else:
        from transformers import EomtDinov3ForUniversalSegmentation as C
    t0 = time.perf_counter()
    proc = _load(AutoProcessor, spec, hub, fetch)
    model = _load(C, spec, hub, fetch).eval()
    t_load = time.perf_counter() - t0
    ip = getattr(proc, "image_processor", proc)
    tasks = ["semantic", "panoptic"] if spec["task"] == "both" else [spec["task"]]
    t_inf = t_post = 0.0
    lab = conf = segs = pid = None
    shapes = []
    for task in tasks:
        t0 = time.perf_counter()
        if spec["arch"] == "oneformer":
            inp = proc(images=img, task_inputs=[task], return_tensors="pt")
        elif spec["arch"] == "eomt_dinov3" and task == "semantic":
            # sliding-window protocol of the transformers EoMT doc; the card's config pads to 512 x 512
            # and the semantic post-process would then stretch the padded square over the canvas
            inp = proc(images=img, return_tensors="pt", do_split_image=True, do_pad=False, size={"shortest_edge": 512})
        else:
            inp = proc(images=img, return_tensors="pt", **spec.get("proc_kw", {}))
        out = model(**inp)
        t_inf += time.perf_counter() - t0
        shapes.append(list(inp["pixel_values"].shape))
        t0 = time.perf_counter()
        if task == "semantic":
            kw = {"size": {"shortest_edge": 512, "longest_edge": None}} if spec["arch"] == "eomt_dinov3" else {}
            r = ip.post_process_semantic_segmentation(out, target_sizes=[(h, w)], return_segmentation_scores=True, **kw)[0]
            sc = r.segmentation_scores
            lab = (r.segmentation.numpy().astype(np.int32) + 1).astype(np.uint16)
            conf = (sc.max(0).values / sc.sum(0).clamp_min(1e-9)).numpy().astype(np.float32)
            del sc, r
        else:
            if spec["arch"].startswith("eomt"):
                r = ip.post_process_panoptic_segmentation(out, target_sizes=[(h, w)], stuff_classes=ADE_STUFF)[0]
            else:
                r = ip.post_process_panoptic_segmentation(out, target_sizes=[(h, w)], label_ids_to_fuse=set(ADE_STUFF))[0]
            pid = r["segmentation"].numpy().astype(np.int32)
            segs = [{"mask_id": int(x["id"]), "label_id": int(x["label_id"]) + 1, "score": float(x["score"])}
                    for x in r["segments_info"]]
            if lab is None:          # panoptic alone: the label map comes from the segments (void = 0)
                lab = np.zeros((h, w), np.uint16)
                conf = np.zeros((h, w), np.float32)
                for x in segs:
                    m = pid == x["mask_id"]
                    lab[m] = x["label_id"]
                    conf[m] = x["score"]
        t_post += time.perf_counter() - t0
    info = {"model": key, "repo": spec["repo"], "revision": spec["rev"], "task": spec["task"],
            "processor": type(ip).__name__, "model_input": shapes,
            "transformers": transformers.__version__}
    if pid is not None:
        info["_pan"] = pid
    return lab, conf, segs, info, {"load_s": t_load, "infer_s": t_inf, "post_s": t_post}


# ADE20K panoptic stuff classes (isthing 0 in shi-labs/oneformer_demo ade20k_panoptic.json, the class
# file of the OneFormer processor; 50 of 150), used as label_ids_to_fuse / stuff_classes: a stuff
# class is one segment per photo, a thing class one segment per instance. Building and tree are stuff
# in ADE20K panoptic, so no ADE20K model returns one segment per building: those are split into
# elements by connected components here (and, with --depth-split, by disparity jumps).
ADE_STUFF = [0, 1, 2, 3, 4, 5, 6, 9, 11, 13, 16, 17, 21, 25, 26, 28, 29, 34, 40, 46, 48, 51, 52, 54, 59, 60, 61,
             63, 68, 77, 79, 84, 91, 94, 96, 99, 100, 101, 105, 106, 109, 113, 114, 117, 122, 128, 131, 140, 141, 145]


def ov_regions(img, route, hub, fetch, torch, threshold):
    """Open-vocabulary regions for OV_PROMPTS: {prompt: (bool mask, score)}."""
    h, w = img.shape[:2]
    t0 = time.perf_counter()
    res = {}
    if route == "clipseg":
        from transformers import CLIPSegForImageSegmentation, CLIPSegProcessor
        spec = OV_MODELS["clipseg"]
        proc = _load(CLIPSegProcessor, spec, hub, fetch)
        model = _load(CLIPSegForImageSegmentation, spec, hub, fetch).eval()
        t_load = time.perf_counter() - t0
        t0 = time.perf_counter()
        inp = proc(text=OV_PROMPTS, images=[img] * len(OV_PROMPTS), padding=True, return_tensors="pt")
        pr = torch.sigmoid(model(**inp).logits)[None]
        pr = torch.nn.functional.interpolate(pr, size=(h, w), mode="bilinear", align_corners=False)[0].numpy()
        top = pr.argmax(0)
        mx = pr.max(0)
        for k, p in enumerate(OV_PROMPTS):
            m = (top == k) & (mx > threshold)
            if p in OV_EXTRA and m.any():
                res[p] = (m, float(pr[k][m].mean()))
    else:
        from transformers import AutoProcessor, GroundingDinoForObjectDetection, Sam2Model, Sam2Processor
        gs, ss = OV_MODELS["gdino"], OV_MODELS["sam2"]
        gp = _load(AutoProcessor, gs, hub, fetch)
        gm = _load(GroundingDinoForObjectDetection, gs, hub, fetch).eval()
        sp = _load(Sam2Processor, ss, hub, fetch)
        sm = _load(Sam2Model, ss, hub, fetch).eval()
        t_load = time.perf_counter() - t0
        t0 = time.perf_counter()
        boxes, scores, names = [], [], []
        for c0 in range(0, len(OV_PROMPTS), 5):          # 4 fixed chunks of 5 words
            chunk = OV_PROMPTS[c0:c0 + 5]
            inp = gp(images=img, text=". ".join(chunk) + ".", return_tensors="pt")
            out = gm(**inp)
            spans, pos = [], 1
            for p in chunk:
                n = len(gp.tokenizer(p, add_special_tokens=False).input_ids)
                spans.append((pos, pos + n))
                pos += n + 1
            pr = out.logits[0].sigmoid()
            sc = pr.max(-1).values
            for q in (sc > threshold).nonzero().flatten().tolist():  # noqa: E501
                per = [float(pr[q, a:b].max()) for a, b in spans]
                k = int(np.argmax(per))
                if per[k] < 0.25:
                    continue
                cx, cy, bw, bh = out.pred_boxes[0][q].tolist()
                boxes.append([(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h])
                scores.append(float(sc[q]))
                names.append(chunk[k])
        if boxes:
            si = sp(images=img, input_boxes=[boxes], return_tensors="pt")
            so = sm(**si, multimask_output=False)
            mk = sp.post_process_masks(so.pred_masks, si["original_sizes"])[0]
            for i, p in enumerate(names):
                if p not in OV_EXTRA:
                    continue
                m = mk[i, 0].numpy().astype(bool)
                if p in res:
                    res[p] = (res[p][0] | m, max(res[p][1], scores[i]))
                else:
                    res[p] = (m, scores[i])
    return res, {"load_s": t_load, "infer_s": time.perf_counter() - t0}


# ---------------------------------------------------------------------------
# Elements
# ---------------------------------------------------------------------------

def refine_luminary(ov, img):
    """A luminary word (sun, moon, galaxy core) from the open-vocabulary route marks a blob several
    times larger than the disc (CLIPSeg predicts at 352 x 352); keep its bright core: the pixels at or
    above the Otsu threshold of L* inside the blob (parameter-free). On 2026-09-28 this moved the IoU
    with the hand-tuned sun of mismatch_4_S from 0.12 to 0.60 and of mismatch_4_F from 0.04 to 0.07."""
    L8 = np.clip(cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)[..., 0] * 2.55, 0, 255).astype(np.uint8)
    out = {}
    for p, (m, sc) in ov.items():
        if GROUP_OF[p] == "luminary" and m.sum() >= 16:
            thr, _ = cv2.threshold(L8[m].reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            core = m & (L8 >= thr)
            out[p] = (core if core.any() else m, sc)
        else:
            out[p] = (m, sc)
    return out

def absorb_small(elem, min_px, protect=()):
    """Merge every element smaller than min_px (except the ids in `protect`) into the element it
    shares the longest border with (8-neighbourhood), smallest first, deterministic by (area, id)."""
    ids, counts = np.unique(elem, return_counts=True)
    area = dict(zip(ids.tolist(), counts.tolist()))
    small = sorted((a, i) for i, a in area.items() if i != 0 and a < min_px and i not in protect)
    k3 = np.ones((3, 3), np.uint8)
    merged = {}
    for a, i in small:
        m = elem == i
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = max(0, ys.min() - 1), ys.max() + 2, max(0, xs.min() - 1), xs.max() + 2
        sub = elem[y0:y1, x0:x1]
        ms = m[y0:y1, x0:x1]
        ring = cv2.dilate(ms.astype(np.uint8), k3).astype(bool) & ~ms
        nb = sub[ring]
        nb = nb[(nb != 0) & (nb != i)]
        if nb.size == 0:
            continue
        v, c = np.unique(nb, return_counts=True)
        tgt = int(v[np.argmax(c)])
        sub[ms] = tgt
        merged[i] = tgt
    return elem, merged


DEPTH_SPLIT_GROUPS = ("building", "structure", "tree", "mountain")


def depth_cut(disp, jump):
    """Pixels where the disparity changes by more than `jump` over 8 px (Sobel on a 1.5-px blur):
    the boundary between two buildings or two crowns at different depths."""
    d = cv2.GaussianBlur(disp.astype(np.float32), (0, 0), 1.5)
    gx = cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    return np.hypot(gx, gy) * 8.0 > jump


def build_elements(lab, conf, segs, pan, ov, min_share, disp=None, split_jump=0.0, semantic=True):
    """Element id map (uint16) and per-element (label_id, route, confidence) from the ADE label map,
    the panoptic segments (instances) when the model gives them, and the open-vocabulary regions
    painted over the ADE labels they refine."""
    h, w = lab.shape
    lab = lab.copy()
    route_of_px = np.zeros((h, w), np.uint8)       # 0 ade, 1 open-vocabulary
    ov_score = {}
    for p, (m, s) in sorted(ov.items(), key=lambda kv: -int(kv[1][0].sum())):   # large first, small on top
        lid = [k for k, v in EXTRA_LABELS.items() if v == p][0]
        # an open-vocabulary name refines a region only where ADE20K has no better word: inside the
        # sky groups for sky objects, anywhere for the air-conditioning unit (an appliance)
        allow = np.isin(lab, [i + 1 for i in range(150) if GROUP_OF[ADE150[i]] in ("sky", "wall", "building")]) \
            if p != "air conditioning unit" else np.ones_like(m)
        mm = m & allow
        lab[mm] = lid
        route_of_px[mm] = 1
        ov_score[lid] = s
    elem = np.zeros((h, w), np.uint16)
    meta = {}
    nid = 0
    inst = {}
    if pan is not None:
        for s in segs:
            if s["label_id"] - 1 not in ADE_STUFF:
                inst[s["mask_id"]] = s
    # things from panoptic segments (one element per instance, all its components)
    for mid in sorted(inst):
        s = inst[mid]
        m = (pan == mid) & (lab == s["label_id"])
        if not m.any():
            continue
        nid += 1
        elem[m] = nid
        meta[nid] = {"label_id": s["label_id"], "route": "ade-panoptic", "confidence": s["score"]}
    # every remaining labelled pixel: one element per connected component of its label
    for lid in sorted(int(x) for x in np.unique(lab) if x != 0):
        m = (lab == lid) & (elem == 0)
        if not m.any():
            continue
        name = label_name(lid)
        rt = "open-vocabulary" if lid > 150 else ("ade-semantic" if semantic else "ade-panoptic")
        if name in SCATTER:
            nid += 1
            elem[m] = nid
            meta[nid] = {"label_id": lid, "route": rt, "confidence": ov_score.get(lid)}
            continue
        if split_jump > 0 and disp is not None and GROUP_OF[name] in DEPTH_SPLIT_GROUPS:
            # cut the label along disparity jumps, label the pieces, then give the cut pixels back
            # to the piece they touch most (absorb_small below treats them as fragments)
            cut = depth_cut(disp, split_jump) & m
            n, cc = cv2.connectedComponents((m & ~cut).astype(np.uint8), connectivity=4)
            if cut.any():
                k3 = np.ones((3, 3), np.uint8)
                grow = cc.copy()
                for _ in range(6):
                    if not (cut & (grow == 0)).any():
                        break
                    d_ = cv2.dilate(grow.astype(np.float32), k3).astype(np.int32)
                    grow = np.where(cut & (grow == 0), d_, grow)
                cc = np.where(m, grow, 0)
        else:
            n, cc = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
        for c in range(1, n):
            mc = cc == c
            if not mc.any():
                continue
            nid += 1
            elem[mc] = nid
            cf = ov_score.get(lid) if lid > 150 else float(conf[mc].mean())
            meta[nid] = {"label_id": lid, "route": rt, "confidence": cf}
    keep_small = {i for i, v in meta.items() if label_name(v["label_id"]) in SCATTER}
    min_px = max(1, int(round(min_share * h * w)))
    if min_px > 1:
        # small fragments (a stray patch of "floor" in a lake) join their neighbour; a scatter
        # element (a star field) is kept whatever its size
        elem, merged = absorb_small(elem, min_px, keep_small)
        for i in merged:
            meta.pop(i, None)
    # relabel 1..N in raster order of first pixel (deterministic)
    ids = [int(i) for i in np.unique(elem) if i != 0]
    first = {}
    flat = elem.ravel()
    order = np.argsort(flat, kind="stable")
    sf = flat[order]
    starts = np.searchsorted(sf, ids)
    for i, s0 in zip(ids, starts):
        first[i] = int(order[s0])
    ids.sort(key=lambda i: first[i])
    remap = np.zeros(int(elem.max()) + 1, np.uint16)
    out_meta = {}
    for new, old in enumerate(ids, 1):
        remap[old] = new
        out_meta[new] = meta[old]
    elem = remap[elem]
    # the label map follows the elements (an absorbed fragment takes its host's label)
    lab_out = np.zeros_like(lab)
    for i, v in out_meta.items():
        lab_out[elem == i] = v["label_id"]
    return lab_out, elem, out_meta


# ---------------------------------------------------------------------------
# Frame descriptors (no model beyond the depth model)
# ---------------------------------------------------------------------------

def normals_of(disp, sigma=2.0):
    """Unit surface normals from the disparity: n ~ (-k dD/dx, -k dD/dy, 1), k = the long side, so a
    full 0..1 ramp across the frame tilts the normal by 45 degrees. The disparity is relative (scale
    and shift unknown), so the normals are a shape cue, not metric."""
    h, w = disp.shape
    d = cv2.GaussianBlur(disp.astype(np.float32), (0, 0), sigma)
    k = float(max(h, w))
    gx = cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=3) / 8.0 * k
    gy = cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=3) / 8.0 * k
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def edges_of(img):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (0, 0), 1.0)
    med = float(np.median(g))
    return cv2.Canny(g, int(max(10, 0.66 * med)), int(min(255, max(30, 1.33 * med))))


def saliency_of(img, width=64):
    """Spectral-residual saliency (Hou and Zhang, CVPR 2007): numpy FFT on a 64-px-wide grey copy."""
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    sh = max(8, int(round(h * width / w)))
    s = cv2.resize(g, (width, sh), interpolation=cv2.INTER_AREA)
    F = np.fft.fft2(s)
    la = np.log(np.abs(F) + 1e-9)
    ph = np.angle(F)
    res = la - cv2.blur(la.astype(np.float32), (3, 3))
    sal = np.abs(np.fft.ifft2(np.exp(res + 1j * ph))) ** 2
    sal = cv2.GaussianBlur(sal.astype(np.float32), (0, 0), 2.5)
    sal = cv2.resize(sal, (w, h), interpolation=cv2.INTER_LINEAR)
    return (sal - sal.min()) / max(float(sal.max() - sal.min()), 1e-9)


def frame_block(img, lab, elem, meta, disp, normals, edges, sal):
    h, w = lab.shape
    sky_ids = [i for i in range(1, 158) if label_name(i) != "none" and GROUP_OF[label_name(i)] in SKY_GROUPS]
    sky = np.isin(lab, sky_ids)
    # skyline: per column, the first non-sky row below a sky run that starts at the top row
    cols = np.linspace(0, w - 1, 64).round().astype(int)
    line = []
    for x in cols:
        c = sky[:, x]
        if not c[0]:
            line.append(None)
            continue
        nz = np.nonzero(~c)[0]
        line.append(int(nz[0]) if nz.size else h)
    ys = [v for v in line if v is not None]
    sky_share = float(sky.mean())
    skyline = None
    if ys and sky_share >= 0.01:
        skyline = {"x": cols.tolist(), "y": line, "median_share": round(float(np.median(ys)) / h, 4),
                   "std_share": round(float(np.std(ys)) / h, 4), "columns_with_sky": len(ys)}
    # light: the brightest luminary element if one exists, and a Lambertian fit of L* to the normals
    lab_img = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    L = lab_img[..., 0]
    ground = ~sky & (lab > 0)
    step = max(1, int(np.sqrt(h * w / 200000)))
    gs = ground[::step, ::step]
    fit = None
    if gs.sum() > 1000:
        nn = normals[::step, ::step][gs]
        Ls = L[::step, ::step][gs]
        X = np.c_[np.ones(len(Ls)), nn[:, 0], nn[:, 1]]
        coef, *_ = np.linalg.lstsq(X, Ls, rcond=None)
        pred = X @ coef
        r2 = 1.0 - float(((Ls - pred) ** 2).sum()) / max(float(((Ls - Ls.mean()) ** 2).sum()), 1e-9)
        fit = {"direction_xy": [round(float(coef[1]), 3), round(float(coef[2]), 3)],
               "angle_deg": round(float(np.degrees(np.arctan2(coef[2], coef[1]))), 1), "r2": round(r2, 4),
               "note": "image axes x right, y down; the in-plane direction lit normals face; r2 below 0.1 = no shading cue"}
    lum = [(i, v) for i, v in meta.items() if GROUP_OF[label_name(v["label_id"])] == "luminary"]
    source = None
    if lum:
        i, v = max(lum, key=lambda kv: float(L[elem == kv[0]].mean()))
        ys_, xs_ = np.nonzero(elem == i)
        source = {"element": i, "label": label_name(v["label_id"]),
                  "centroid": [round(float(xs_.mean()), 1), round(float(ys_.mean()), 1)]}
    sy, sx = np.unravel_index(int(np.argmax(sal)), sal.shape)
    return {"canvas": [w, h], "sky_share": round(sky_share, 4), "skyline": skyline,
            "light": {"source": source, "shading_fit": fit},
            "edge_density": round(float((edges > 0).mean()), 5),
            "saliency_peak": [int(sx), int(sy)],
            "normals_mean_tilt_deg": round(float(np.degrees(np.arccos(np.clip(normals[..., 2], -1, 1))).mean()), 2)}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_npz(path, arrays):
    """np.savez_compressed stamps each zip entry with the current time; this writer uses a fixed
    date so the file is byte-identical across runs."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(arrays):
            b = io.BytesIO()
            np.lib.format.write_array(b, np.ascontiguousarray(arrays[name]), allow_pickle=False)
            zi = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, b.getvalue())


def r(x, n=4):
    return None if x is None else round(float(x), n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo", help="a path, or a fixture id such as mismatch_4_S (fixtures/<id>.*)")
    ap.add_argument("--out", help="output directory (default benchmarks/runs/2026-09-28/layers/<photo id or stem>)")
    ap.add_argument("--model", default=DEFAULT_ADE, choices=sorted(ADE_MODELS),
                    help=f"the ADE20K model that names regions (default {DEFAULT_ADE})")
    ap.add_argument("--open-vocab", default=DEFAULT_OV, choices=["none", "clipseg", "gdino_sam2"],
                    help=f"the route that names sun / cloud / star / moon / galaxy core / meteor streak / "
                         f"air-conditioning unit (default {DEFAULT_OV})")
    ap.add_argument("--ov-threshold", type=float, default=None,
                    help="open-vocabulary threshold (default 0.40 for clipseg on the sigmoid map, 0.30 for "
                         "Grounding DINO's box score)")
    ap.add_argument("--no-refine", action="store_true",
                    help="keep the open-vocabulary sun / moon / galaxy-core blob as the model gives it (default: "
                         "keep its bright core, Otsu on L* inside the blob)")
    ap.add_argument("--canvas", choices=["pair", "own"], default=None,
                    help="pair: the pair canvas of layered_probe (fixture ids only; the default for them); "
                         "own: the photo's own aspect (the default for a path)")
    ap.add_argument("--max-long", type=int, default=1920, help="long side cap of the canvas in px (default 1920)")
    ap.add_argument("--min-share", type=float, default=0.0005,
                    help="an element smaller than this share of the canvas joins its longest-border neighbour "
                         "(default 0.0005; star fields and open-vocabulary elements are exempt)")
    ap.add_argument("--depth-split", type=float, default=0.0,
                    help="split building / structure / tree / mountain regions where the disparity jumps by more "
                         "than this over 8 px (0 = off, the default; 0.05 is a starting value, untuned)")
    ap.add_argument("--extras", action="store_true", help="also write normals, edges and saliency into layers.npz")
    ap.add_argument("--threads", type=int, default=4, help="torch CPU threads (default 4)")
    ap.add_argument("--hf-home", default=str(DEFAULT_HF_HOME), help="weights cache (default %(default)s)")
    ap.add_argument("--fetch", action="store_true", help="allow the one-time download of missing files")
    a = ap.parse_args()

    os.environ["HF_HOME"] = a.hf_home
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    if not a.fetch:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    hub = str(Path(a.hf_home) / "hub")
    path, fixture = resolve_photo(a.photo)
    mode = a.canvas or ("pair" if fixture else "own")
    out = Path(a.out) if a.out else DEFAULT_OUT / (fixture or path.stem)
    out.mkdir(parents=True, exist_ok=True)
    timing = {}
    t0 = time.perf_counter()
    img = canvas_of(path, fixture, mode, a.max_long)
    timing["canvas_s"] = time.perf_counter() - t0
    import torch
    import transformers
    transformers.logging.set_verbosity_error()
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    torch.set_grad_enabled(False)
    stub = _stub_losses_if_needed(torch)
    shim = _shim_tvf_if_needed(torch)
    if a.model.startswith("oneformer") and a.fetch:
        from huggingface_hub import hf_hub_download
        hf_hub_download(*ONEFORMER_CLASS_INFO, repo_type="dataset", cache_dir=hub)
    lab, conf, segs, info, tm = ade_labels(img, a.model, hub, a.fetch, torch)
    pan = info.pop("_pan", None)
    timing["ade"] = tm
    ov = {}
    if a.open_vocab != "none":
        thr = a.ov_threshold if a.ov_threshold is not None else (0.40 if a.open_vocab == "clipseg" else 0.30)
        ov, tm = ov_regions(img, a.open_vocab, hub, a.fetch, torch, thr)
        if not a.no_refine:
            ov = refine_luminary(ov, img)
        timing["open_vocab"] = tm
    t0 = time.perf_counter()
    sys.path.insert(0, str(ROOT))
    import transitions as T          # the depth model: models/depth, manifest-gated, offline
    disp = T.model_disparity(img).astype(np.float32)
    timing["depth_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    lab2, elem, meta = build_elements(lab, conf, segs, pan, ov, a.min_share, disp, a.depth_split,
                                      semantic=ADE_MODELS[a.model]["task"] != "panoptic")
    timing["elements_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    h, w = lab2.shape
    labc = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    els = []
    for i, v in meta.items():
        m = elem == i
        ys, xs = np.nonzero(m)
        name = label_name(v["label_id"])
        els.append({"id": i, "label": name, "label_id": v["label_id"], "group": GROUP_OF[name], "route": v["route"],
                    "area_share": r(m.mean(), 6), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                    "centroid": [r(xs.mean(), 1), r(ys.mean(), 1)], "median_disparity": r(np.median(disp[m])),
                    "mean_lab": [r(c, 2) for c in labc[m].mean(0)],
                    "touches": {"top": bool(ys.min() == 0), "bottom": bool(ys.max() == h - 1),
                                "left": bool(xs.min() == 0), "right": bool(xs.max() == w - 1)},
                    "confidence": r(v["confidence"])})
    for rank, e in enumerate(sorted(els, key=lambda e: (-e["median_disparity"], e["id"]))):
        e["depth_rank"] = rank
    normals = normals_of(disp)
    edges = edges_of(img)
    sal = saliency_of(img)
    frame = frame_block(img, lab2, elem, meta, disp, normals, edges, sal)
    timing["describe_s"] = time.perf_counter() - t0
    arrays = {"label": lab2.astype(np.uint16), "element": elem.astype(np.uint16), "disparity": disp}
    if a.extras:
        arrays["normals"] = np.clip(np.round(normals * 127), -127, 127).astype(np.int8)
        arrays["edges"] = edges.astype(np.uint8)
        arrays["saliency"] = np.clip(np.round(sal * 255), 0, 255).astype(np.uint8)
    save_npz(out / "layers.npz", arrays)
    doc = {"photo": fixture or path.name, "canvas_mode": mode, "canvas": [w, h],
           "provenance": dict(info, open_vocab=a.open_vocab, ov_prompts=OV_PROMPTS if a.open_vocab != "none" else [],
                              ov_threshold=(a.ov_threshold if a.ov_threshold is not None else
                                            (0.40 if a.open_vocab == "clipseg" else 0.30 if a.open_vocab != "none" else None)),
                              depth="Depth Anything V2 Small via transitions.model_disparity",
                              loss_stub=(LOSS_STUB if stub else False), min_share=a.min_share,
                              depth_split=a.depth_split, luminary_refine=not a.no_refine, tvf_shim=(TVF_SHIM if shim else False),
                              torch=torch.__version__, threads=a.threads),
           "frame": frame, "elements": sorted(els, key=lambda e: e["id"])}
    (out / "layers.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
    timing = {k: ({kk: round(vv, 3) for kk, vv in v.items()} if isinstance(v, dict) else round(v, 3))
              for k, v in timing.items()}
    (out / "timing.json").write_text(json.dumps(timing, indent=1))
    md = {f: hashlib.md5((out / f).read_bytes()).hexdigest() for f in ("layers.npz", "layers.json")}
    print(f"{doc['photo']}: {len(els)} elements, canvas {w}x{h}, {a.model}"
          + (f" + {a.open_vocab}" if a.open_vocab != "none" else "") + f" -> {out}  md5 {md}", flush=True)


if __name__ == "__main__":
    main()
