#!/usr/bin/env python3
"""Merged layer source for one or more photos (Track E3, 2026-09-28; research script, nothing enters
transitions.py or reveal.py).

Builds on the layer source (layer_source.py, "the old source"): its OneFormer Swin-L + CLIPSeg
elements are the base; Grounding DINO base + SAM 2.1 Hiera-L (route `gdino_sam2`, default) and,
behind `--routes`, SAM 3 (route `sam3`) give instance masks that split a region element into
instances, add objects the base does not name, and give an element a SAM edge where the two agree.
The output format is the old source's (layers.npz + layers.json + timing.json), so
`layered_probe.py --auto2 PAIR --layers-dir <out>` reads it unchanged.

Stages (the two never hold models at the same time):
  1. base: for every photo, `.venv/bin/python scripts/research/layer_source.py <photo> --extras
     --out <out>/_base/<photo>` in a subprocess (the old source, byte for byte: the tool's venv, no
     torchvision, so the same PIL processors). The element map is checked against --check-base
     (default benchmarks/runs/2026-09-28/layers/<photo>/layers.npz) when that file exists.
  2. merge: this process (the scratch venv with torchvision, which Sam2Processor and SAM 3 need)
     loads the detection route(s) once and merges every photo.

Candidates. Each route gives masks with a prompt, a score and a box on the photo's canvas:
  gdino_sam2  Grounding DINO base boxes for layer_source.OV_PROMPTS (4 fixed chunks of 5 words; a
              query is kept when its best token probability > BOX_T and the best prompt span's
              probability >= TEXT_T; the rule of E2's measure_ov.py), each box turned into one mask
              by SAM 2.1 (multimask_output False); score = the box score; sam_iou = SAM's own
              predicted IoU.
  sam3        SAM 3 (facebook/sam3, transformers Sam3Model, 1008 x 1008 input) with one text prompt per
              word of SAM3_PROMPTS (OV_PROMPTS, which already holds star and air conditioning unit, plus
              house, skyscraper, tower, palm, bus, truck, bicycle, animal), the vision features computed
              once per photo; instances above SAM3_SCORE (post_process_instance_segmentation); SAM 3
              gives no predicted IoU, so MIN_SAM_IOU does not apply to it. The two routes' scores are
              on different scales (Grounding DINO 0.30-0.80 over 214 masks, SAM 3 0.40-0.99 over 977 masks on the 24 fixture photos),
              so where their masks duplicate each other the SAM 3 mask usually stays.
  A candidate is dropped when sam_iou < MIN_SAM_IOU, when its area < MIN_SHARE of the canvas, or
  when its group is in PART_GROUPS (a window or a door is a part of a facade; as an element it would
  shred the building it belongs to). Two candidates with mask IoU >= DEDUP_IOU: the higher score
  stays. The rest are painted largest first, so a smaller mask stays on top; a candidate whose
  visible part is below MIN_VISIBLE of its mask (a box around a group of buildings whose parts were
  also found) is dropped and the rest repainted. V = a candidate's visible part.

The merge rule (quantities per candidate C of group g; G_g = the base pixels whose element is in
group g; E = a base element):
  host share  hs = |V ∩ G_g| / |V|.
  hosted      hs >= CONTAIN_MIN: C belongs to the base element of group g it overlaps most (its host).
              Its claim = V ∩ (G_g dilated by EDGE_BAND_PX): the SAM edge may move the region's
              border by at most EDGE_BAND_PX outward.
  new object  hs < NEW_MAX_NAMED, score >= NEW_MIN_SCORE, area <= NEW_MAX_SHARE of the canvas, and g
              not in STUFF_GROUPS: an object the base does not name here; its claim = V.
  otherwise   dropped (reason recorded in layers.json merge.candidates).
  Candidates of STUFF_GROUPS (sky, water, wall, ceiling, mountain) are never split nor added; they
  can only give an edge (below).
Per base element E with hosted candidates H(E):
  edge        |H(E)| = 1 and IoU(claim, E) >= EDGE_IOU: E keeps its id, label and route and takes the
              candidate's region (its SAM edge); edge_route = the candidate's route.
  split       otherwise, and only when g is not in STUFF_GROUPS: each hosted candidate becomes an
              element with E's label, instance_of = E's id in the old source.
Painting: claims are painted in decreasing area, so where two claims overlap the smaller wins; a
claim takes a pixel unless the pixel's current owner is a base element of another group smaller
than the claim (a person in front of a building keeps its pixels).
Residual of a split or edged E (its pixels no claim took): the pixels an opening with a disc of
radius SLIVER_PX removes (slivers between the SAM edge and the label-map edge) go to the nearest
element that is not E and not one of E's candidates when it is within REASSIGN_MAX_PX, else to the
nearest of E's candidates; the remaining connected components of the residual stay elements of E's
label (instance_of = E's id when E was split). Last, every element below MIN_SHARE of the canvas
joins its longest-border neighbour (layer_source.absorb_small; a star field is exempt).
One id map holds every element, so no pixel belongs to two elements; asserted below.

layers.json per element: the old source's fields (id, label, label_id, group, route, area_share,
bbox, centroid, median_disparity, depth_rank, mean_lab, touches, confidence) plus
  instance_of   the old source's element id this one was split from, or null
  base_id       the old source's element id the pixels came from (the host), or null (new object)
  edge_route    the route whose mask drew this element's region ("gdino_sam2" / "sam3"), or
                "label-map" (the old source's upsampled label map)
  edge_sam_share  share of the element's border pixels that lie within 1 px of a candidate mask's
                border (0 .. 1; the canvas border does not count)
  box, box_score  the detector's box (x0, y0, x1, y1 on the canvas) and score, when a route gave one
  sam_iou       SAM's predicted IoU for that mask, when a route gave one
  median_normal the per-axis median of the unit normals (layer_source.normals_of) inside the
                element, renormalised (x right, y down, z toward the camera)
The merge block lists every candidate with its verdict; timing.json holds seconds per step and the
network guard's count of socket attempts.

Deterministic: fixed torch threads (--threads), seed 0, no grad; fixed zip dates; floats rounded.
Offline: without --fetch, HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 are set before transformers is
imported, every load passes a pinned revision and local_files_only, and every socket connect of this
process is refused and counted. Weights live in --hf-home (never ~/.cache, never models/).

  V=benchmarks/runs/2026-09-28/layers/venv/bin/python
  $V scripts/research/layer_merge.py mismatch_1_S mismatch_1_F            # -> layers_v2/<photo>/
  $V scripts/research/layer_merge.py mismatch_4_S --routes gdino_sam2,sam3 --out-root benchmarks/runs/2026-09-28/layers_v3
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import types
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layer_source as LS  # noqa: E402

ROOT = LS.ROOT
DEFAULT_OUT_ROOT = ROOT / "benchmarks" / "runs" / "2026-09-28" / "layers_v2"
DEFAULT_CHECK_BASE = ROOT / "benchmarks" / "runs" / "2026-09-28" / "layers"
TOOL_PY = ROOT / ".venv" / "bin" / "python"

# ---------------------------------------------------------------------------
# Constants of the merge rule (see the docstring); none is tuned on a named photo
# ---------------------------------------------------------------------------
BOX_T = 0.30            # Grounding DINO: best token probability of a kept query (E2's value)
TEXT_T = 0.25           # Grounding DINO: best prompt-span probability of a kept query (E2's value)
MIN_SAM_IOU = 0.70      # SAM's own predicted IoU below this: the mask is not trusted
MIN_SHARE = 0.0005      # the old source's --min-share: smallest element, share of the canvas
DEDUP_IOU = 0.85        # two candidate masks this similar are one object: the higher score stays
MIN_VISIBLE = 0.50      # a candidate whose visible part is below this share of its mask is dropped
CONTAIN_MIN = 0.50      # host share at or above: the candidate is an instance of its group's element
NEW_MAX_NAMED = 0.20    # host share below: the base does not name this object here
NEW_MIN_SCORE = 0.35    # a new object needs at least this detector score
NEW_MAX_SHARE = 0.20    # a new object larger than this share of the canvas is not trusted
EDGE_IOU = 0.80         # a single hosted candidate this close to its element gives the element its edge
EDGE_BAND_PX = 8        # how far (px) a SAM edge may move a region's border outward
SLIVER_PX = 3           # opening radius (px) that separates slivers from the residual's body
REASSIGN_MAX_PX = 16    # a sliver goes to another element only when one is this close (px)
SAM3_SCORE = 0.40       # SAM 3 instance score threshold (post_process_instance_segmentation)
SAM3_MASK_T = 0.50      # SAM 3 mask threshold (the processor's default)

STUFF_GROUPS = ("sky", "water", "wall", "ceiling", "mountain")
PART_GROUPS = ("opening",)

MODELS = {
    "gdino": LS.OV_MODELS["gdino"],
    "sam2": LS.OV_MODELS["sam2"],
    "sam3": {"repo": "facebook/sam3", "rev": "3c879f39826c281e95690f02c7821c4de09afae7"},
}
GD_PROMPTS = list(LS.OV_PROMPTS)
# SAM 3 takes one noun phrase per pass: the old source's words (OV_PROMPTS) plus the words of the
# groups the merge splits into instances that OV_PROMPTS lacks
SAM3_PROMPTS = list(LS.OV_PROMPTS) + ["house", "skyscraper", "tower", "palm", "bus", "truck", "bicycle", "animal"]


def label_id_of(word):
    if word in LS.ADE150:
        return LS.ADE150.index(word) + 1
    for k, v in LS.EXTRA_LABELS.items():
        if v == word:
            return k
    raise KeyError(word)


def r(x, n=4):
    return None if x is None else round(float(x), n)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Network guard (offline proof beyond the environment flags)
# ---------------------------------------------------------------------------
SOCKET_ATTEMPTS = []


def deny_network():
    import socket

    def _deny(self, addr, *k):
        SOCKET_ATTEMPTS.append(str(addr))
        raise OSError(f"network disabled by layer_merge.py: {addr}")

    def _deny_ex(self, addr):
        SOCKET_ATTEMPTS.append(str(addr))
        return 1
    socket.socket.connect = _deny
    socket.socket.connect_ex = _deny_ex


# ---------------------------------------------------------------------------
# Stage 1: the old source, in the tool's venv
# ---------------------------------------------------------------------------

def run_base(photo, base_dir, hf_home, threads):
    base_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(TOOL_PY), str(ROOT / "scripts" / "research" / "layer_source.py"), photo, "--extras",
           "--out", str(base_dir), "--hf-home", hf_home, "--threads", str(threads)]
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "VIRTUAL_ENV")}
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    (base_dir / "base.log").write_text(p.stdout + p.stderr)
    if p.returncode != 0:
        raise SystemExit(f"layer_source.py failed on {photo} (rc {p.returncode}); log {base_dir / 'base.log'}")
    return time.perf_counter() - t0


# ---------------------------------------------------------------------------
# Stage 2: candidates
# ---------------------------------------------------------------------------

class GdinoSam2:
    name = "gdino_sam2"

    def __init__(self, hub, fetch):
        from transformers import AutoProcessor, GroundingDinoForObjectDetection, Sam2Model, Sam2Processor
        t0 = time.perf_counter()
        g, s = MODELS["gdino"], MODELS["sam2"]
        kw = dict(cache_dir=hub, local_files_only=not fetch)
        self.gp = AutoProcessor.from_pretrained(g["repo"], revision=g["rev"], **kw)
        self.gm = GroundingDinoForObjectDetection.from_pretrained(g["repo"], revision=g["rev"], **kw).eval()
        self.sp = Sam2Processor.from_pretrained(s["repo"], revision=s["rev"], **kw)
        self.sm = Sam2Model.from_pretrained(s["repo"], revision=s["rev"], **kw).eval()
        self.load_s = time.perf_counter() - t0
        self.info = {"gdino": dict(g), "sam2": dict(s), "prompts": GD_PROMPTS, "box_threshold": BOX_T,
                     "text_threshold": TEXT_T, "chunk": 5, "gdino_processor": type(self.gp).__name__,
                     "sam2_processor": type(self.sp.image_processor).__name__}

    def __call__(self, img):
        h, w = img.shape[:2]
        t0 = time.perf_counter()
        boxes, scores, names = [], [], []
        for c0 in range(0, len(GD_PROMPTS), 5):
            chunk = GD_PROMPTS[c0:c0 + 5]
            inp = self.gp(images=img, text=". ".join(chunk) + ".", return_tensors="pt")
            out = self.gm(**inp)
            spans, pos = [], 1
            for p in chunk:
                n = len(self.gp.tokenizer(p, add_special_tokens=False).input_ids)
                spans.append((pos, pos + n))
                pos += n + 1
            pr = out.logits[0].sigmoid()
            sc = pr.max(-1).values
            for q in (sc > BOX_T).nonzero().flatten().tolist():
                per = [float(pr[q, a:b].max()) for a, b in spans]
                k = int(np.argmax(per))
                if per[k] < TEXT_T:
                    continue
                cx, cy, bw, bh = out.pred_boxes[0][q].tolist()
                boxes.append([(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h])
                scores.append(float(sc[q]))
                names.append(chunk[k])
        t_det = time.perf_counter() - t0
        t0 = time.perf_counter()
        cands = []
        if boxes:
            si = self.sp(images=img, input_boxes=[boxes], return_tensors="pt")
            so = self.sm(**si, multimask_output=False)
            mk = self.sp.post_process_masks(so.pred_masks, si["original_sizes"])[0]
            iou = so.iou_scores[0, :, 0].numpy().tolist()
            for i in range(len(boxes)):
                cands.append({"route": self.name, "word": names[i], "score": scores[i], "sam_iou": float(iou[i]),
                              "box": [float(max(0, boxes[i][0])), float(max(0, boxes[i][1])),
                                      float(min(w, boxes[i][2])), float(min(h, boxes[i][3]))],
                              "mask": mk[i, 0].numpy().astype(bool)})
        return cands, {"det_s": t_det, "seg_s": time.perf_counter() - t0}


class Sam3:
    name = "sam3"

    def __init__(self, hub, fetch):
        from transformers import Sam3Model, Sam3Processor
        t0 = time.perf_counter()
        s = MODELS["sam3"]
        kw = dict(cache_dir=hub, local_files_only=not fetch)
        self.proc = Sam3Processor.from_pretrained(s["repo"], revision=s["rev"], **kw)
        self.model = Sam3Model.from_pretrained(s["repo"], revision=s["rev"], **kw).eval()
        self.load_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        ti = self.proc(text=SAM3_PROMPTS, return_tensors="pt")
        self.text = self.model.get_text_features(input_ids=ti["input_ids"], attention_mask=ti["attention_mask"]).pooler_output
        self.text_mask = ti["attention_mask"]
        self.text_s = time.perf_counter() - t0
        self.info = {"sam3": dict(s), "prompts": SAM3_PROMPTS, "score_threshold": SAM3_SCORE,
                     "mask_threshold": SAM3_MASK_T, "processor": type(self.proc.image_processor).__name__}

    def __call__(self, img):
        h, w = img.shape[:2]
        t0 = time.perf_counter()
        vi = self.proc(images=img, return_tensors="pt")
        ve = self.model.get_vision_features(pixel_values=vi["pixel_values"])
        t_vis = time.perf_counter() - t0
        t0 = time.perf_counter()
        cands = []
        for k, word in enumerate(SAM3_PROMPTS):
            # Sam3Model.forward reads text_embeds.pooler_output (transformers 5.17 modeling_sam3.py:2376)
            te = types.SimpleNamespace(pooler_output=self.text[k:k + 1])
            out = self.model(vision_embeds=ve, text_embeds=te, attention_mask=self.text_mask[k:k + 1])
            res = self.proc.post_process_instance_segmentation(out, threshold=SAM3_SCORE, mask_threshold=SAM3_MASK_T,
                                                               target_sizes=[(h, w)])[0]
            for j in range(len(res["scores"])):
                b = res["boxes"][j].tolist()
                cands.append({"route": self.name, "word": word, "score": float(res["scores"][j]), "sam_iou": None,
                              "box": [float(max(0, b[0])), float(max(0, b[1])), float(min(w, b[2])), float(min(h, b[3]))],
                              "mask": res["masks"][j].numpy().astype(bool)})
        return cands, {"vision_s": t_vis, "prompts_s": time.perf_counter() - t0}


def pack_candidates(path, cands, h, w):
    """Every candidate mask (packed bits) + its record, for the measurement and the review page."""
    recs = [{"route": c["route"], "word": c["word"], "score": r(c["score"]), "sam_iou": r(c["sam_iou"]),
             "box": [r(x, 1) for x in c["box"]]} for c in cands]
    arr = np.stack([c["mask"] for c in cands]) if cands else np.zeros((0, h, w), bool)
    LS.save_npz(path, {"packed": np.packbits(arr.ravel()), "shape": np.array([len(cands), h, w], np.int64)})
    return recs


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def nearest_owner(elem, allowed_ids, targets):
    """For each pixel in `targets` (bool), (owner id, distance px) of the nearest pixel whose element
    is in allowed_ids (Euclidean, cv2 distance transform with per-pixel labels)."""
    allowed = np.isin(elem, sorted(allowed_ids))
    if not allowed.any():
        return None, None
    src = np.where(allowed, 0, 1).astype(np.uint8)
    dist, lab = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    zy, zx = np.nonzero(src == 0)           # label k = k-th zero pixel in raster order
    idx = lab[targets] - 1
    return elem[zy[idx], zx[idx]], dist[targets]


def border(m):
    """Border pixels of a bool mask (inside pixels with a 4-neighbour outside); the canvas edge does not count."""
    er = cv2.erode(m.astype(np.uint8), np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8),
                   borderType=cv2.BORDER_REPLICATE).astype(bool)
    return m & ~er


def merge(base_elem, base_meta, cands, h, w):
    """(element map, meta per element, candidate records). base_meta: {base id: element dict of the old source}."""
    area_img = h * w
    min_px = max(1, int(round(MIN_SHARE * area_img)))
    group_of_base = {i: e["group"] for i, e in base_meta.items()}
    area_base = {i: int(e["_area"]) for i, e in base_meta.items()}
    recs = []
    # --- candidate filter
    live = []
    for ci, c in enumerate(cands):
        c["i"] = ci
        c["label_id"] = label_id_of(c["word"])
        c["group"] = LS.GROUP_OF[c["word"]]
        c["area"] = int(c["mask"].sum())
        rec = {"i": ci, "route": c["route"], "word": c["word"], "group": c["group"], "score": r(c["score"]),
               "sam_iou": r(c["sam_iou"]), "box": [r(x, 1) for x in c["box"]], "area_share": r(c["area"] / area_img, 6)}
        recs.append(rec)
        if c["group"] in PART_GROUPS:
            rec["verdict"] = "dropped: part group"
        elif c["sam_iou"] is not None and c["sam_iou"] < MIN_SAM_IOU:
            rec["verdict"] = "dropped: sam_iou"
        elif c["area"] < min_px:
            rec["verdict"] = "dropped: small"
        else:
            live.append(c)
    # --- dedup (higher score first; ties by index)
    live.sort(key=lambda c: (-c["score"], c["i"]))
    kept = []
    for c in live:
        dup = None
        for k in kept:
            inter = int((c["mask"] & k["mask"]).sum())
            if inter and inter / float(c["area"] + k["area"] - inter) >= DEDUP_IOU:
                dup = k
                break
        if dup is not None:
            recs[c["i"]]["verdict"] = f"dropped: duplicate of {dup['i']}"
        else:
            kept.append(c)
    # --- visible parts, largest first (a smaller mask stays on top); drop mostly hidden, repaint
    for _ in range(3):
        order = sorted(kept, key=lambda c: (-c["area"], c["i"]))
        paint = np.full((h, w), -1, np.int32)
        for c in order:
            paint[c["mask"]] = c["i"]
        vis = {c["i"]: int((paint == c["i"]).sum()) for c in kept}
        drop = [c for c in kept if vis[c["i"]] < MIN_VISIBLE * c["area"]]
        if not drop:
            break
        for c in drop:
            recs[c["i"]]["verdict"] = f"dropped: visible {vis[c['i']] / c['area']:.2f}"
        kept = [c for c in kept if c not in drop]
    for c in kept:
        c["V"] = paint == c["i"]
        c["vis"] = int(c["V"].sum())
        recs[c["i"]]["visible_share"] = r(c["vis"] / c["area"])
    # --- host / new / dropped
    groups_present = {}
    for i, g in group_of_base.items():
        groups_present.setdefault(g, []).append(i)
    host_of, new_objs = {}, []
    for c in sorted(kept, key=lambda c: c["i"]):
        same = groups_present.get(c["group"], [])
        Gg = np.isin(base_elem, same) if same else np.zeros((h, w), bool)
        hs = float((c["V"] & Gg).sum()) / max(c["vis"], 1)
        recs[c["i"]]["host_share"] = r(hs)
        if hs >= CONTAIN_MIN:
            ids, cnt = np.unique(base_elem[c["V"] & Gg], return_counts=True)
            host = int(ids[np.argmax(cnt)])
            band = cv2.dilate(Gg.astype(np.uint8), cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (2 * EDGE_BAND_PX + 1, 2 * EDGE_BAND_PX + 1))).astype(bool)
            c["claim"] = c["V"] & band
            c["host"] = host
            host_of.setdefault(host, []).append(c)
        elif (hs < NEW_MAX_NAMED and c["score"] >= NEW_MIN_SCORE and c["vis"] <= NEW_MAX_SHARE * area_img
              and c["group"] not in STUFF_GROUPS):
            c["claim"] = c["V"]
            c["host"] = None
            new_objs.append(c)
            recs[c["i"]]["verdict"] = "new object"
        else:
            recs[c["i"]]["verdict"] = "dropped: host share %.2f" % hs
    # --- per host: edge or split
    edge_c, split_c = {}, []
    for host, cs in sorted(host_of.items()):
        E = base_elem == host
        g = group_of_base[host]
        if len(cs) == 1:
            c = cs[0]
            inter = int((c["claim"] & E).sum())
            iou = inter / float(int(c["claim"].sum()) + int(E.sum()) - inter)
            recs[c["i"]]["iou_with_host"] = r(iou)
            if iou >= EDGE_IOU:
                edge_c[host] = c
                recs[c["i"]]["verdict"] = f"edge of base {host}"
                continue
        if g in STUFF_GROUPS:
            for c in cs:
                recs[c["i"]]["verdict"] = f"dropped: stuff group, no edge agreement with base {host}"
            continue
        for c in cs:
            split_c.append(c)
            recs[c["i"]]["verdict"] = f"instance of base {host}"
    # --- paint: base ids stay; claims get new ids 1000 + candidate index, largest first
    elem = base_elem.astype(np.int32).copy()
    meta = {}
    for i, e in base_meta.items():
        meta[i] = {"label_id": e["label_id"], "route": e["route"], "confidence": e["confidence"], "instance_of": None,
                   "base_id": i, "edge_route": "label-map"}
    claims = [(c, "edge") for c in edge_c.values()] + [(c, "split") for c in split_c] + [(c, "new") for c in new_objs]
    claims.sort(key=lambda t: (-int(t[0]["claim"].sum()), t[0]["i"]))
    touched = set()
    for c, kind in claims:
        cid = c["host"] if kind == "edge" else 1000 + c["i"]
        size = int(c["claim"].sum())
        cur = elem[c["claim"]]
        # a smaller base element of another group in front of the claim keeps its pixels
        protect = [i for i in np.unique(cur).tolist()
                   if i in base_meta and i != c["host"] and group_of_base[i] != c["group"] and area_base[i] < size]
        take = c["claim"] & ~np.isin(elem, protect) if protect else c["claim"]
        if kind == "edge":
            meta[cid].update({"edge_route": c["route"]})
        elif kind == "split":
            hm = base_meta[c["host"]]
            meta[cid] = {"label_id": hm["label_id"], "route": c["route"], "confidence": c["score"],
                         "instance_of": c["host"], "base_id": c["host"], "edge_route": c["route"]}
        else:
            meta[cid] = {"label_id": c["label_id"], "route": c["route"], "confidence": c["score"],
                         "instance_of": None, "base_id": None, "edge_route": c["route"]}
        meta[cid].update({"box": [r(x, 1) for x in c["box"]], "box_score": r(c["score"]), "sam_iou": r(c["sam_iou"]),
                          "_cand": c["i"]})
        if kind == "edge":
            elem[(elem == cid) & ~take] = -cid          # the host's own pixels outside the claim: residual
        elem[take] = cid
        touched.add(c["host"] if c["host"] is not None else -1)
    # --- residuals of edged / split hosts: slivers to the nearest other element, the body stays
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * SLIVER_PX + 1, 2 * SLIVER_PX + 1))
    split_hosts = sorted({c["host"] for c in split_c})
    for host in sorted(set(edge_c) | set(split_hosts)):
        mine = [host] if host in edge_c else []
        mine += [1000 + c["i"] for c in split_c if c["host"] == host]
        R = (elem == host) | (elem == -host)
        if host in edge_c:
            R = elem == -host
        if not R.any():
            continue
        core = cv2.morphologyEx(R.astype(np.uint8), cv2.MORPH_OPEN, k_open).astype(bool)
        n, cc, st, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8), connectivity=8)
        body = np.zeros_like(R)
        for k in range(1, n):
            if st[k, cv2.CC_STAT_AREA] >= min_px:
                body |= cc == k
        sl = R & ~body
        if sl.any():
            others = [i for i in np.unique(elem).tolist() if i > 0 and i not in mine and i != host]
            own, dist = nearest_owner(elem, others, sl) if others else (None, None)
            mine_own, _ = nearest_owner(elem, [m for m in mine if m != host] or mine, sl) if mine else (None, None)
            if own is not None:
                tgt = np.where(dist <= REASSIGN_MAX_PX, own, mine_own if mine_own is not None else own)
            else:
                tgt = mine_own
            if tgt is not None:
                elem[sl] = tgt
        if host in edge_c:
            elem[body] = host                           # the body E kept outside the SAM mask stays E
        else:
            # the body of a split host: one element per connected component, instance_of the host
            n, cc = cv2.connectedComponents(body.astype(np.uint8), connectivity=8)
            elem[body] = 0
            for k in range(1, n):
                assert k < 1000
                rid = 100000 + host * 1000 + k
                elem[cc == k] = rid
                hm = base_meta[host]
                meta[rid] = {"label_id": hm["label_id"], "route": hm["route"], "confidence": hm["confidence"],
                             "instance_of": host, "base_id": host, "edge_route": "label-map"}
    assert (elem >= 0).all(), "a residual pixel was left without an owner"
    for i in list(meta):
        if not (elem == i).any():
            meta.pop(i)
    # --- small fragments join their longest-border neighbour (star fields exempt)
    keep_small = {i for i, v in meta.items() if LS.label_name(v["label_id"]) in LS.SCATTER}
    e2, merged = LS.absorb_small(elem.astype(np.int64), min_px, keep_small)
    for i in merged:
        meta.pop(i, None)
        if isinstance(i, (int, np.integer)) and i >= 1000 and i < 100000:
            ci = i - 1000
            recs[ci]["verdict"] += " (absorbed: below MIN_SHARE after painting)"
    elem = e2
    # --- relabel 1..N in raster order of first pixel (the old source's rule)
    ids = [int(i) for i in np.unique(elem) if i != 0]
    flat = elem.ravel()
    order = np.argsort(flat, kind="stable")
    starts = np.searchsorted(flat[order], ids)
    first = {i: int(order[s0]) for i, s0 in zip(ids, starts)}
    ids.sort(key=lambda i: first[i])
    lut = {old: new for new, old in enumerate(ids, 1)}
    out = np.zeros((h, w), np.uint16)
    for old, new in lut.items():
        out[elem == old] = new
    out_meta = {lut[old]: meta[old] for old in ids}
    for new, m in out_meta.items():
        if "_cand" in m:
            recs[m["_cand"]]["element"] = new
    # one id map: no pixel in two elements; every element in the map has a record and vice versa
    assert set(np.unique(out).tolist()) - {0} == set(out_meta), "element ids and records differ"
    assert sum(int((out == i).sum()) for i in out_meta) == int((out > 0).sum())
    return out, out_meta, recs


def cand_border_map(cands, h, w):
    """Pixels within 1 px of any live candidate mask's border."""
    b = np.zeros((h, w), bool)
    for c in cands:
        if "claim" in c:
            b |= border(c["mask"])
    return cv2.dilate(b.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)


def describe(img, elem, meta, disp, normals, cand_border):
    h, w = elem.shape
    labc = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    els = []
    for i, v in meta.items():
        m = elem == i
        ys, xs = np.nonzero(m)
        name = LS.label_name(v["label_id"])
        nm = np.median(normals[m], axis=0)
        nm = nm / max(float(np.linalg.norm(nm)), 1e-9)
        bd = border(m)
        nb = int(bd.sum())
        e = {"id": i, "label": name, "label_id": int(v["label_id"]), "group": LS.GROUP_OF[name], "route": v["route"],
             "area_share": r(m.mean(), 6), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
             "centroid": [r(xs.mean(), 1), r(ys.mean(), 1)], "median_disparity": r(np.median(disp[m])),
             "mean_lab": [r(c, 2) for c in labc[m].mean(0)],
             "touches": {"top": bool(ys.min() == 0), "bottom": bool(ys.max() == h - 1),
                         "left": bool(xs.min() == 0), "right": bool(xs.max() == w - 1)},
             "confidence": r(v["confidence"]), "instance_of": v["instance_of"], "base_id": v["base_id"],
             "edge_route": v["edge_route"], "edge_sam_share": r(float((bd & cand_border).sum()) / nb if nb else 0.0),
             "median_normal": [r(x, 3) for x in nm]}
        for k in ("box", "box_score", "sam_iou"):
            if k in v:
                e[k] = v[k]
        els.append(e)
    for rank, e in enumerate(sorted(els, key=lambda e: (-e["median_disparity"], e["id"]))):
        e["depth_rank"] = rank
    return sorted(els, key=lambda e: e["id"])


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", nargs="+", help="fixture ids such as mismatch_1_S (the pair canvas of layered_probe)")
    ap.add_argument("--routes", default="gdino_sam2",
                    help="comma list of detection routes: gdino_sam2 (default), sam3 (needs the SAM 3 weights)")
    ap.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT), help="outputs go to <out-root>/<photo>/ (default %(default)s)")
    ap.add_argument("--out", help="with one photo: this output directory instead of <out-root>/<photo>")
    ap.add_argument("--base-root", help="the old source's outputs (with --extras) per photo; default <out-root>/_base")
    ap.add_argument("--skip-base", action="store_true", help="reuse <base-root>/<photo> when it exists")
    ap.add_argument("--check-base", default=str(DEFAULT_CHECK_BASE),
                    help="compare the base element map with <check-base>/<photo>/layers.npz (default %(default)s)")
    ap.add_argument("--threads", type=int, default=4, help="torch CPU threads (default 4)")
    ap.add_argument("--hf-home", default=str(LS.DEFAULT_HF_HOME), help="weights cache (default %(default)s)")
    ap.add_argument("--fetch", action="store_true", help="allow the one-time download of missing files")
    a = ap.parse_args()
    routes = [x for x in a.routes.split(",") if x]
    assert all(x in ("gdino_sam2", "sam3") for x in routes), routes
    out_root = Path(a.out_root)
    base_root = Path(a.base_root) if a.base_root else out_root / "_base"
    if a.out and len(a.photos) != 1:
        raise SystemExit("--out takes one photo")
    os.environ["HF_HOME"] = a.hf_home
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    if not a.fetch:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    hub = str(Path(a.hf_home) / "hub")
    # stage 1: the old source per photo (a subprocess each; no model is loaded here yet)
    base_s = {}
    for ph in a.photos:
        bd = base_root / ph
        if a.skip_base and (bd / "layers.npz").exists():
            base_s[ph] = None
            continue
        base_s[ph] = run_base(ph, bd, a.hf_home, a.threads)
        print(f"[base] {ph} {base_s[ph]:.1f}s", flush=True)
    # stage 2: detection routes + merge
    if not a.fetch:
        deny_network()
    import torch
    import transformers
    transformers.logging.set_verbosity_error()
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    torch.set_grad_enabled(False)
    import torchvision  # noqa: F401  (Sam2ImageProcessor / SAM 3 need it; fail here, not mid-run)
    runners = []
    for rt in routes:
        runners.append(GdinoSam2(hub, a.fetch) if rt == "gdino_sam2" else Sam3(hub, a.fetch))
    for ph in a.photos:
        timing = {"base_s": base_s[ph], "load_s": {rn.name: rn.load_s for rn in runners}}
        path, fixture = LS.resolve_photo(ph)
        bd = base_root / ph
        z = np.load(bd / "layers.npz")
        bj = json.loads((bd / "layers.json").read_text())
        base_elem = z["element"].astype(np.int32)
        disp = z["disparity"]
        h, w = base_elem.shape
        base_check = None
        cb = Path(a.check_base) / ph / "layers.npz"
        if cb.exists():
            ref = np.load(cb)["element"]
            base_check = {"file": str(cb.relative_to(ROOT)) if cb.is_relative_to(ROOT) else str(cb),
                          "element_identical": bool(ref.shape == base_elem.shape and (ref == base_elem).all())}
        t0 = time.perf_counter()
        img = LS.canvas_of(path, fixture, bj["canvas_mode"], 1920)
        assert img.shape[:2] == (h, w), (img.shape, (h, w))
        timing["canvas_s"] = time.perf_counter() - t0
        cands = []
        for rn in runners:
            cs, tm = rn(img)
            timing[rn.name] = tm
            cands += cs
        t0 = time.perf_counter()
        base_meta = {}
        for e in bj["elements"]:
            e = dict(e)
            e["_area"] = int((base_elem == e["id"]).sum())
            base_meta[e["id"]] = e
        elem, meta, recs = merge(base_elem, base_meta, cands, h, w)
        timing["merge_s"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        normals = z["normals"].astype(np.float32) / 127.0
        normals /= np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-9)
        cbm = cand_border_map(cands, h, w)
        els = describe(img, elem, meta, disp, normals, cbm)
        lab = np.zeros((h, w), np.uint16)
        for e in els:
            lab[elem == e["id"]] = e["label_id"]
        frame = LS.frame_block(img, lab, elem, {e["id"]: {"label_id": e["label_id"]} for e in els}, disp,
                               LS.normals_of(disp), z["edges"], z["saliency"].astype(np.float32) / 255.0)
        timing["describe_s"] = time.perf_counter() - t0
        out = Path(a.out) if a.out else out_root / ph
        out.mkdir(parents=True, exist_ok=True)
        cand_dir = out_root / "_candidates"
        cand_dir.mkdir(parents=True, exist_ok=True)
        pack_candidates(cand_dir / f"{ph}_{'+'.join(routes)}.npz", cands, h, w)
        arrays = {"label": lab, "element": elem.astype(np.uint16), "disparity": disp, "normals": z["normals"],
                  "edges": z["edges"], "saliency": z["saliency"]}
        LS.save_npz(out / "layers.npz", arrays)
        prov = dict(bj["provenance"])
        prov["merge"] = {
            "script": "scripts/research/layer_merge.py", "routes": routes,
            "models": {rn.name: rn.info for rn in runners},
            "constants": {k: globals()[k] for k in (
                "BOX_T", "TEXT_T", "MIN_SAM_IOU", "MIN_SHARE", "DEDUP_IOU", "MIN_VISIBLE", "CONTAIN_MIN",
                "NEW_MAX_NAMED", "NEW_MIN_SCORE", "NEW_MAX_SHARE", "EDGE_IOU", "EDGE_BAND_PX", "SLIVER_PX",
                "REASSIGN_MAX_PX", "SAM3_SCORE", "SAM3_MASK_T", "STUFF_GROUPS", "PART_GROUPS")},
            "base": {"command": f".venv/bin/python scripts/research/layer_source.py {ph} --extras",
                     "elements": len(bj["elements"]), "check": base_check},
            "torch": torch.__version__, "transformers": transformers.__version__,
            "torchvision": __import__("torchvision").__version__, "threads": a.threads}
        doc = {"photo": bj["photo"], "canvas_mode": bj["canvas_mode"], "canvas": [w, h], "provenance": prov,
               "frame": frame, "elements": els, "merge": {"candidates": recs}}
        (out / "layers.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
        timing["socket_attempts"] = len(SOCKET_ATTEMPTS)
        timing = json.loads(json.dumps(timing), parse_float=lambda s: round(float(s), 3))
        (out / "timing.json").write_text(json.dumps(timing, indent=1))
        nb = sum(1 for e in els if e["group"] == "building")
        print(f"{ph}: {len(bj['elements'])} -> {len(els)} elements ({nb} building), {len(cands)} candidates, "
              f"base check {base_check and base_check['element_identical']}, md5 npz {md5(out / 'layers.npz')} "
              f"json {md5(out / 'layers.json')}", flush=True)


if __name__ == "__main__":
    main()
