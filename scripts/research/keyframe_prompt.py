#!/usr/bin/env python3
"""Dynamic keyframe prompts from a layered score: the state of every layer at a clip time t,
written as an edit instruction for an image-editing model (Qwen-Image-Edit-2511 through
stable-diffusion.cpp on the box, or FLUX.2 [klein]).

Research script (2026-09-26, fourth session late; plan §Rank 2026-09-26 item 4; the prompting note
`.claude/claude-docs/research/keyframe-prompting.md`). Reads a score JSON of
`scripts/research/layered_probe.py` and prints prompts; no model, no network, no tool change.

The first keyframe run asked for "one photograph that is exactly halfway between image 1 and image 2"
with both photos as references and got image 2 back (DECISIONS 2026-09-26, Track B). Edit models are
trained to produce a described target state from a base picture, so the prompt here describes the
midpoint STATE per layer (what moved where, what has thinned, what has appeared) and names the base
picture explicitly. The wording follows the guides read on 2026-09-26: say what changes and what
stays, direct verbs, specific positions, no "halfway", no "make it better"; Qwen sees its references
labelled "Picture 1", "Picture 2" (the diffusers pipeline and stable-diffusion.cpp both label them so);
FLUX.2 guides use "image 1", "image 2".

A layer may carry a "prompt" key: {"a": "the day sky with cumulus clouds", "b": "the night sky",
"where": "the top two thirds of the frame"}; without it the layer's name is used.

  .venv/bin/python scripts/research/keyframe_prompt.py scripts/research/scores/mismatch_4_r2.json --t 0.5
  ... --dialect flux --refs 1         # image-N wording, base picture only
  ... --refs 2                        # both pictures as references, roles stated
"""
import argparse
import json
import math
from pathlib import Path

CURVES = {
    "linear": lambda u: u,
    "ease": lambda u: 0.5 - 0.5 * math.cos(math.pi * u),
    "ease-in": lambda u: u * u,
    "ease-out": lambda u: 1 - (1 - u) ** 2,
    "snap": lambda u: 0.0 if u < 0.5 else 1.0,
    "hold-then-go": lambda u: 0.0 if u < 0.35 else (u - 0.35) / 0.65,
}

DIRECTION_WORDS = {(0, 1): "down", (0, -1): "up", (1, 0): "to the right", (-1, 0): "to the left",
                   (-1, 1): "down and to the left", (1, 1): "down and to the right",
                   (-1, -1): "up and to the left", (1, -1): "up and to the right"}


def progress(layer, t):
    t0, t1 = layer.get("window", [0.0, 1.0])
    u = min(1.0, max(0.0, (t - t0) / max(t1 - t0, 1e-6)))
    return min(1.0, max(0.0, CURVES.get(layer.get("curve", "ease"), CURVES["ease"])(u)))


def fraction(p):
    """Words for a progress value; models read words, not percentages."""
    if p < 0.34:
        return "a third"
    if p < 0.66:
        return "half"
    if p < 0.98:
        return "most"
    return "all"


def names(layer, pic):
    pr = layer.get("prompt") or {}
    a = pr.get("a") or layer["name"].replace("_", " ")
    b = pr.get("b") or a
    where = pr.get("where")
    return (a if layer["from"] == "A" else b), a, b, where


def verbs(layer):
    """(is, has) or (are, have): a layer's prompt may say "plural": true."""
    return ("are", "have") if (layer.get("prompt") or {}).get("plural") else ("is", "has")


def direction_word(layer):
    d = layer.get("direction", [0, 1])
    key = (int(math.copysign(1, d[0])) if d[0] else 0, int(math.copysign(1, d[1])) if d[1] else 0)
    return DIRECTION_WORDS.get(key, "away")


ORIGIN_WORDS = {(0, -1): "from below", (0, 1): "from above", (1, 0): "from the left", (-1, 0): "from the right",
                (-1, 1): "from the top-right corner", (1, 1): "from the top-left corner",
                (-1, -1): "from the bottom-right corner", (1, -1): "from the bottom-left corner"}


def origin_word(layer):
    """Where an entering layer comes from: the opposite of its direction of travel."""
    d = layer.get("direction", [0, -1])
    key = (int(math.copysign(1, d[0])) if d[0] else 0, int(math.copysign(1, d[1])) if d[1] else 0)
    return ORIGIN_WORDS.get(key, "from the edge")


def clause(layer, t, P):
    """One plain sentence for the layer's state at t. P = the picture labels (base, other)."""
    base, other = P
    p = progress(layer, t)
    act = layer.get("action", "hold")
    own, a, b, where = names(layer, base)
    w = f" ({where})" if where else ""
    w_in = f" in {where}" if where else ""
    f = fraction(p)
    IS, HAS = verbs(layer)
    if act == "hold" or (p <= 0.02 and act not in ("enter", "materialise")):
        return None
    if act == "backdrop":
        same = (a == b)
        if p >= 0.98:
            return f"{a}{w} {HAS} the colour and brightness of {other}." if same else f"{a}{w} {HAS} become {b}, as in {other}."
        if p < 0.34:
            return f"{a}{w} {IS} still mostly as in {base}, with a first hint of {other}'s colour and brightness."
        if p < 0.66:
            mid = f"{a}{w} {IS} midway between {base} and {other} in colour and brightness"
            return mid + "." if same else mid + f": no longer {a}, not yet {b}."
        return f"{a}{w} {IS} almost as in {other}, with a last trace of {base}'s colour."
    if act == "exit":
        if p >= 0.98:
            return f"{own}{w} {HAS} left the frame {direction_word(layer)}; the sky shows where it was."
        return f"{own}{w} {HAS} slid {direction_word(layer)} as one solid piece and {f} of it is already out of the frame; the sky shows where it was."
    if act == "enter":
        if p <= 0.02:
            return None
        if p >= 0.98:
            return f"{own} from {other}{w} {IS} fully in the frame."
        org = origin_word(layer)
        # the place words: dropped when they repeat the origin ("from the top-right corner … the
        # top-right corner"); "across / along …" reads without "into"
        if where and not any(k in org for k in where.replace("-", " ").split() if len(k) > 3):
            w_to = f" {where}" if where.startswith(("across", "along", "over")) else f" into {where}"
        else:
            w_to = ""
        return f"{own} from {other} {HAS} slid into the frame {org}{w_to} and {IS} {f} of the way into place."
    if act in ("move", "move_to"):
        if p >= 0.98:
            return f"{own} {IS} now where it is in {other}: {b}."
        return f"{own} {HAS} moved {f} of the way from its place in {base} to its place in {other} ({b}), the same size and brightness."
    if act == "dissolve":
        if p >= 0.98:
            return f"{own}{w_in} {IS} gone; only clear sky remains where it was."
        return f"{own}{w_in} {HAS} thinned and {f} of it is gone, the thin parts first; the dense cores remain, with soft edges."
    if act == "materialise":
        if p <= 0.02:
            return None
        if p >= 0.98:
            return f"{own} from {other}{w_in} {IS} fully present."
        return f"{f} of {own} from {other} {IS} now present{w_in}, the brightest parts first."
    if act == "recolor":
        return f"{own}{w} {HAS} taken on {f} of the colour of {b}."
    return None


def build(score, t, dialect, refs):
    if dialect == "qwen":
        P = ("Picture 1", "Picture 2")
    else:
        P = ("image 1", "image 2")
    base, other = P
    layers = [l for l in score["layers"] if l.get("render", True)]
    layers.sort(key=lambda l: l.get("depth", 0))
    clauses = [c for c in (clause(l, t, P) for l in layers) if c]
    if refs == 1:
        head = (f"Edit {base}. It shows {score.get('scene_a', 'the scene')}. Change it so that the following is true, "
                f"and keep everything not mentioned exactly as it is in {base}:")
    else:
        head = (f"{base} is the scene to edit; {other} shows where the moving parts end up. Edit {base} so that the "
                f"following is true, and keep everything not mentioned exactly as it is in {base}:")
    body = " ".join(f"({i + 1}) {c}" for i, c in enumerate(clauses))
    tail = ("Photorealistic, one continuous photograph, the same camera and framing as "
            f"{base}, no split screen, no border, no text.")
    return f"{head} {body} {tail}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("score")
    ap.add_argument("--t", type=float, default=0.5, help="clip time in 0..1 (default 0.5)")
    ap.add_argument("--dialect", choices=["qwen", "flux"], default="qwen")
    ap.add_argument("--refs", type=int, choices=[1, 2], default=1, help="1 = the base picture only, 2 = both pictures")
    a = ap.parse_args()
    score = json.loads(Path(a.score).read_text())
    print(build(score, a.t, a.dialect, a.refs))


if __name__ == "__main__":
    main()
