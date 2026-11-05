"""The loop flow's stage registry (phase A1): one entry per process with its knobs, outputs and sentence.

A stage: one process with inputs, outputs on disk, knobs, a wall time and a visual. A knob's range is null unless the
script's --help or SCHEMA.md states one (no loop key states one); the sentences are the scripts' own.
"""

from __future__ import annotations

from typing import Any

from reveal_studio.errors import StudioError


def K(
    key: str,
    typ: str,
    default: Any,
    what: str,
    flag: str | None = None,
    choices: list[str] | None = None,
    rng: list[float] | None = None,
) -> dict[str, Any]:
    """A knob: the literal key, its type, default and sentence, the script flag it becomes, its choices and range."""
    return {"key": key, "type": typ, "default": default, "what": what, "flag": flag, "choices": choices, "range": rng}


LOOP_STAGES: list[dict[str, Any]] = [
    {
        "name": "import",
        "title": "import",
        "kind": "builtin",
        "optional": False,
        "terminal": None,
        "what": "The stills in capture order, read in place: one symlink per still under raw/<seq>/ and a sha256 per file. The originals are never copied or modified.",
        "knobs": [],
    },
    {
        "name": "registration",
        "title": "registration",
        "kind": "script",
        "optional": False,
        "backend": "loop_seq.py prep",
        "terminal": "prep.json",
        "what": "Every still registered onto one still's background: SIFT + MAGSAC on a 1200 px proxy, then a chain through the previous still, then an ECC affine, else identity (said on the log); all stills cropped to the common valid rectangle. Writes in/<seq>/k<i>.png and prep.json.",
        "knobs": [
            K(
                "long",
                "int",
                1920,
                "the long edge every still is scaled to before registration (downscale only)",
                "--long",
            ),
            K(
                "ref",
                "int",
                -1,
                "the canvas frame (default: the widest trusted framing, so nothing is upscaled)",
                "--ref",
            ),
            K("cut", "str", "", "frame indices joined by a cut, not registered (e.g. 4,5)", "--cut"),
            K(
                "bg_depth",
                "float",
                0.0,
                "register on the far field only: keypoints where the depth model's relative depth is below this (0 = off). On the angel pair the far-field fit holds 31 inliers, under the default floor of 40: set min_inliers to 25 with it.",
                "--bg-depth",
            ),
            K(
                "min_inliers",
                "int",
                40,
                "the SIFT fit's inlier floor (a far field of a plain wall may hold 30)",
                "--min-inliers",
            ),
            K(
                "ecc_refine",
                "bool",
                False,
                "with --bg-depth: refine the far-field fit by a masked ECC on the far pixels (measured worse on the angel pair)",
                "--ecc-refine",
            ),
            K(
                "depth_maps",
                "bool",
                False,
                "write depth_k<i>.npy (the depth model, offline) for the registered stills even without --bg-depth; a plan with a parallax or a breath by depth needs them",
                "--depth-maps",
            ),
            K(
                "lock_window",
                "str",
                "",
                "windows of the reference frame (px, 'x0,y0,x1,y1;...') that must stay put: each map gains the translation that zeroes their mean measured offset (the gag object as the anchor). Draw the windows on the still and look at them before trusting their numbers.",
                "--lock-window",
            ),
            K(
                "windows",
                "str",
                "",
                "named windows of frame 0 in px before the crop (the px of lock_window), 'name:x0,y0,x1,y1;...', measured and never applied. Per registered frame, the prep finds where each window's content sits (dx, dy px, sub-pixel by template match, the correlation, and edge when the peak lies on the ±30 px search's border) under every fit it made: all, far, chain, ecc and final. Written to prep.json and drawn on windows.jpg. A window named for an object is drawn on the still and looked at before its number is used.",
                "--windows",
            ),
        ],
    },
    {
        "name": "readers",
        "title": "readers",
        "kind": "script",
        "optional": True,
        "parent": "registration",
        "backend": "loop_seq.py readers",
        "terminal": "readers.json",
        "what": "Per registered still: the depth map (written beside the prep when missing), the face boxes (YuNet), the grey mean, the clipped pixels, the focus (the Laplacian's variance); per neighbouring pair: the share of pixels whose Lab distance is above 14 and above 30.",
        "knobs": [],
    },
    {
        "name": "probe",
        "title": "probe",
        "kind": "script",
        "optional": True,
        "parent": "registration",
        "branch": True,
        "stale_after": ["registration"],
        "backend": "loop_seq.py probe",
        "terminal": "probe.json",
        "what": "Compares three in-between methods before a plan is written. Per pair of registered stills (adjacent by index, or the listed pairs) it makes the in-betweens at t 0.25, 0.5 and 0.75 by RIFE over the whole frame (offline, behind its manifest; skipped with a log line when the manifest is missing), by the DIS morph and by the plain dissolve. It writes in/<seq>/probe/: the strips probe_<i>_<j>_<method>.jpg, 1:1 crops at the YuNet face boxes and probe.json (the double-exposure share per frame inside the change matte and over the whole frame, the step to each still). A rerun replaces the folder.",
        "knobs": [
            K(
                "long",
                "int",
                960,
                "the long edge the stills are scaled to before the probe (px, downscale only, sides made even; default 960: a probe is a look, not a render)",
                "--long",
            ),
            K(
                "pairs",
                "str",
                "",
                "the pairs to probe, 'i,j;k,l' by still index (default: every adjacent pair)",
                "--pairs",
            ),
        ],
    },
    {
        "name": "plan",
        "title": "plan",
        "kind": "builtin",
        "optional": False,
        "terminal": None,
        "what": "The JSON that drives a render (plans/loops/SCHEMA.md): holds on the stills, in-betweens per leg with a method and an ease, effects on the finished frames. A plan saved here carries a provenance block (what it came from, which keys changed, his words); the frozen plans under scripts/research/plans/loops/ are never written.",
        "knobs": [],
    },
    {
        "name": "render",
        "title": "render",
        "kind": "script",
        "optional": False,
        "backend": "loop_seq.py render",
        "terminal": "measure.json",
        "what": "The loop the plan describes, at the prep canvas (full) or at a long edge (draft): loop.mp4, loop.gif, sheet.jpg, frames.json (what each frame is), measure.json (the step series on the decoded mp4, the seam, faces, the double-exposure share, the md5s). The plan's `in` is set to this job's prep on every render.",
        "knobs": [
            K(
                "plan",
                "plan",
                "",
                "the plan to render: a plan saved in this job (job:<name>) or a frozen plan (frozen:<name>)",
            ),
            K(
                "name",
                "str",
                "",
                "the render's folder name under <seq>/ (a full render) or drafts/<seq>/ (a draft); a name that exists is refused",
            ),
            K(
                "draft",
                "int",
                0,
                "render at this long edge (0 = the prep canvas); a draft is a draft in its folder and its chip",
                "--draft",
            ),
            K(
                "fps",
                "int",
                25,
                "frames per second of the mp4 and the gif (the gif stores 40 ms per frame at 25 fps exactly; 30 fps gifs run 10 % fast)",
                "--fps",
            ),
        ],
    },
    {
        "name": "measure",
        "title": "measure",
        "kind": "script",
        "optional": True,
        "parent": "render",
        "branch": True,
        "stale_after": [],
        "backend": "loop_seq.py measure",
        "terminal": "measure.json",
        "what": "The measures of one render on its decoded mp4, without rendering: the step series, its mean, max and argmax, the seam step and faces per frame. With the render's frames.json it adds the face counts on the stills' frames, the generated share and the largest double-exposure share. With windows it adds each window's offset against frame ref in every frame (dx, dy px, sub-pixel, and the correlation): an object's stability. Each run writes a new folder <render>/measures/<stamp>/ with measure.json; the render's own files stay as they are.",
        "knobs": [
            K(
                "render",
                "str",
                "",
                "the render to measure: full:<name> (a candidate under <seq>/) or draft:<name> (under drafts/<seq>/); the measure reads its loop.mp4 and its frames.json",
            ),
            K(
                "windows",
                "str",
                "",
                "named windows in the clip's px, 'name:x0,y0,x1,y1;...': each window's content of frame ref found in every frame by template match (an object's stability). A draft's px are the canvas px scaled by the draft's long edge (480/1770 on the angel prep). A window needs texture in both directions.",
                "--window",
            ),
            K("ref", "int", 0, "the frame the windows are read from (default 0)", "--ref"),
        ],
    },
    {
        "name": "skeptic",
        "title": "skeptic",
        "kind": "request",
        "optional": False,
        "terminal": None,
        "what": "A request file for the Claude Code session: an Opus 5.5 subagent crops every candidate at full size (faces and hands at mid-leg, box edges, halos, stalls and jumps in the step series) and answers with a verdict per candidate on the md5 it judged. The page refuses an unjudged candidate unless he overrides.",
        "knobs": [],
    },
    {
        "name": "page",
        "title": "page",
        "kind": "script",
        "optional": False,
        "backend": "loop_seq.py page",
        "terminal": "index.html",
        "what": "The review page over the full renders of the sequence, every one in name order or the listed ones in their order: the keyframes strip, the mp4 and the gif, the numbers, a note per candidate. Built behind the review gate, which checks the listed candidates only; its md5 opens a round.",
        "knobs": [
            K("title", "str", "", "the page's title", "--title"),
            K("intro", "str", "", "one paragraph under the title: what the round is", "--intro"),
            K("footer", "str", "", "one line at the end; an override is printed here", "--footer"),
            K(
                "variants",
                "list",
                [],
                "the full renders the page lists, in this order (folder names under <seq>/, set in the page panel); empty lists every full render in name order and passes no flag. A name that is not a full render is refused before the script runs.",
                "--variants",
            ),
        ],
    },
    {
        "name": "grades",
        "title": "grades",
        "kind": "builtin",
        "optional": False,
        "terminal": None,
        "what": "His grade text for a round, saved verbatim with the page md5 it was given on. A new round's first render waits for the previous round's text, or for the round to be marked ungraded by his word.",
        "knobs": [],
    },
]
FLOWS: dict[str, dict[str, Any]] = {
    "loop": {
        "title": "loop from a sequence",
        "stages": LOOP_STAGES,
        "what": "Two to ten stills of one scene, handheld, registered on an anchor and looped by a plan of holds and in-betweens; the pipeline of the playbook (.claude/skills/reveal/references/loops.md).",
    }
}
STAGE_ORDER = [s["name"] for s in LOOP_STAGES]


def stage_def(flow: str, name: str) -> dict[str, Any]:
    stages: list[dict[str, Any]] = FLOWS[flow]["stages"]
    for s in stages:
        if s["name"] == name:
            return s
    raise StudioError(f"no stage {name!r} in the {flow} flow", 404)
