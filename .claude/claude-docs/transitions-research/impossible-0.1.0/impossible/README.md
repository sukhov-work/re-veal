# Impossible

Makes a transition between two photos, two video clips, or a whole sequence
of them: the last frame of one flows into the first frame of the next.
Reveal aligns two photos so you can slide between them. Impossible animates
the change from one to the other as a short video.

It lives in the same folder as Reveal but is a separate tool. Reveal is not
affected by anything here.

## One-time setup

    ./setup-impossible.sh

That installs the deterministic engine (works on its own). For the optional
generative "dream" layer, see impossible/RESEARCH-PLAN.md, phase 3; it is
not wired in yet.

## Using it

    source .venv-impossible/bin/activate

    # two photos, a one-second morph
    python -m impossible pair before.jpg after.jpg --out out/ --seconds 1.0

    # two clips: cut clip A at 12.5 s, clip B at 3.0 s, 0.6 s flow-dissolve
    python -m impossible clips a.mov b.mov --cut-a 12.5 --cut-b 3.0 \
        --seconds 0.6 --preset flow-dissolve --out out/

    # many items in one go
    python -m impossible sequence my-sequence.json

`out/` gets `transition.mp4` (just the transition), `stitched.mp4` (for
clips), `strip.jpg` (eight thumbnails, to check at a glance) and
`report.json` (what happened, and quality numbers).

Presets: `morph` (default), `dissolve`, `flow-dissolve`, `snap-morph`,
`iris`, `luma`, `dream` (needs the generative layer). Length 0.1 to 10 s.

To steer it by hand, give it point pairs: `--anchors "ax,ay,bx,by;..."`
means "this point in A should land on this point in B". Three or more
pairs are needed. Use it when the two pictures have nothing in common,
for example a face turning into a cloud.

A sequence file:

    {"items": [
        {"path": "clip1.mov", "cut_in": 0, "cut_out": 4.0},
        {"path": "photo.jpg", "hold": 2.0},
        {"path": "clip2.mov", "cut_in": 1.5}],
     "transitions": [
        {"preset": "flow-dissolve", "seconds": 0.8},
        {"preset": "iris", "seconds": 0.5}],
     "output": "sequence.mp4"}

## Status

v0.1.0: the deterministic engine works end to end; 34/34 checks pass
(`python3 impossible_harness.py`). The generative layer is designed and
stubbed, with a research plan to bring it up on this Mac. Read
impossible/RESEARCH-PLAN.md before extending anything.
