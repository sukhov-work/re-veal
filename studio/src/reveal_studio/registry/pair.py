"""The pair transition flow (phase B): two photos animated from one into the other by transitions.py.

The stages and their sentences are the entries of .claude/claude-docs/research/2026-11-05/b_pair_research.md, Part 1:
the import, Reveal's verdict (the branch shared with the director flow, registry/common.py), the relation (a 480 px,
one-second read of the pair's class), the render, the skeptic, the page the studio writes and the grades. A knob's
sentence is `transitions.py pair --help`'s where the help has one; its range is TransitionSpec.clamp's where clamp
states one (transitions.py:205-216), else null.

`identity`: the relation's result is its mp4 and its strip, since report.json holds three clock keys
(correspondence_s, render_s, total_s) and changes on every run; a render's is its mp4.
`stale_after`: a render reads A and B only, so a relation rerun leaves the renders as they are; the page goes stale
after a later full render.

`candidates` is the spec jobs/candidates.py reads a pair job's renders by: the folders of the full renders and the
drafts ({root} the job's run folder, {job} the job folder, {seq} the pair's name), the file that marks a finished
render, its mp4, the knobs copied from the record that wrote it, and the terminal file's fields copied onto the
candidate.
"""

from __future__ import annotations

from typing import Any

from reveal_studio.registry.common import VERDICT_STAGE
from reveal_studio.registry.entries import K

RELATION_LONG = 480
"""The relation's long edge: the workbench's (scripts/research/director_ui.py:446) and STUDIO.md §2's."""
RELATION_SECONDS = 1
"""The relation's length in seconds."""
PRESETS = ["morph", "dissolve", "flow-dissolve", "snap-morph", "iris", "wipe", "luma"]
"""transitions.py's PRESETS, in its order (transitions.py:245-254; `pair --help` lists the same seven)."""

PAIR_STAGES: list[dict[str, Any]] = [
    {
        "name": "import",
        "title": "import",
        "kind": "builtin",
        "optional": False,
        "terminal": None,
        "what": "Two photos read in place: A, the start (BEFORE), and B, the finish (AFTER). Each is a symlink under raw/<pair>/ that keeps its extension, with a sha256. Pick a fixture pair by name or give two paths; the originals are never copied or modified.",
        "knobs": [],
    },
    VERDICT_STAGE,
    {
        "name": "relation",
        "title": "relation",
        "kind": "script",
        "optional": False,
        "backend": "transitions.py pair",
        "script": "transitions",
        "terminal": "report.json",
        "identity": ["transition.mp4", "strip.jpg"],
        "what": "A one-second transition at 480 px, read for the relation it reports. Class A: a sane homography with 30 or more SIFT inliers, so the photos morph along a dense flow. Class B: each photo zooms and pans about its salient blob. Writes transition.mp4, strip.jpg and report.json; a rerun replaces the folder.",
        "knobs": [],
    },
    {
        "name": "render",
        "title": "render",
        "kind": "script",
        "optional": False,
        "backend": "transitions.py pair",
        "script": "transitions",
        "terminal": "report.json",
        "identity": ["transition.mp4"],
        "stale_after": [],
        "what": "The transition from A to B with the knobs below. Writes transition.mp4 (libx264, crf 18, yuv420p), strip.jpg (up to 8 tiles 160 px tall, the first and last frames included) and report.json (the class, the method, the correspondence and the quality basket). A finished render is never overwritten.",
        "knobs": [
            K(
                "name",
                "str",
                "",
                "the render's folder name under <pair>/ (a full render) or drafts/<pair>/ (a draft); a name that exists is refused; an empty name becomes <preset>_<seconds>s, for example morph_1s",
            ),
            K(
                "draft",
                "int",
                0,
                "render at this long edge into drafts/<pair>/ (480 for a draft); 0 renders in full at max_long",
            ),
            K(
                "max_long",
                "int",
                1920,
                "cap the canvas long edge (0 = native). The default 1920 is the fixture sweep's (scripts/bench_transitions.py), under which every expectation in fixtures/MANIFEST.md was measured; the CLI's own default is 0",
            ),
            # seconds, fps and preset: the sentences are TRANSITIONS.md §3's; transitions.py --help gives none
            K(
                "seconds",
                "float",
                1.0,
                "the clip's length; it clamps to [0.1, 10] s",
                "--seconds",
                rng=[0.1, 10.0],
            ),
            K(
                "fps",
                "float",
                30.0,
                "frames per second, at least 1; the clip holds round(seconds × fps) frames, at least 2",
                "--fps",
            ),
            K(
                "preset",
                "str",
                "morph",
                "a named spec: morph, dissolve, flow-dissolve, snap-morph, iris, wipe or luma. report.json keeps the expanded style only, so the record's knobs keep the preset's name",
                "--preset",
                choices=PRESETS,
            ),
            K("color", "float", 0.7, "color path strength 0..1", "--color", rng=[0.0, 1.0]),
            # backlog T108: the CLI's --warp overrides every preset's own value
            K(
                "warp",
                "float",
                1.0,
                "geometric warp amount 0..1. The CLI's --warp, 1.0 by default and passed on every run, overrides every preset's own value: flow-dissolve renders at warp 1.0 unless this knob is set to its 0.6",
                "--warp",
                rng=[0.0, 1.0],
            ),
            K(
                "canvas",
                "str",
                "finish",
                "canvas aspect: finish = the AFTER photo's ratio (default); common = the smaller width and height of the two",
                "--canvas",
                choices=["finish", "common"],
            ),
            K("anchors", "str", "", '"ax,ay,bx,by;..." canvas pixels, A -> B, >= 3 pairs', "--anchors"),
            K(
                "anchor_falloff",
                "float",
                0.45,
                "anchors: fade the anchored field to zero at the canvas border over this fraction of the short edge (default 0.45; 0 = the plain MLS field, whose frame edge shows; T16)",
                "--anchor-falloff",
                rng=[0.0, 0.5],
            ),
            K("force_class", "str", "", "force the pair class", "--class", choices=["", "A", "B"]),
            K(
                "camera",
                "str",
                "flat",
                "class B camera move: flat = the pan-and-zoom as is; ramp = near content (bottom rows) moves more, no model; model = the same from Depth Anything V2 Small (needs `transitions.py warmup` once)",
                "--camera",
                choices=["flat", "ramp", "model"],
            ),
            K(
                "zoom",
                "float",
                0.1,
                "class B zoom fraction per frame, clamped to [0.02, 0.5]",
                "--zoom",
                rng=[0.02, 0.5],
            ),
        ],
    },
    {
        "name": "skeptic",
        "title": "skeptic",
        "kind": "request",
        "optional": False,
        "terminal": None,
        "what": "A request file for the Claude Code session. An Opus 5.5 subagent crops every candidate at full size and answers with a verdict per candidate on the transition.mp4 md5 it judged. The page refuses an unjudged candidate unless he overrides.",
        "knobs": [],
    },
    {
        "name": "page",
        "title": "page",
        "kind": "builtin",
        "optional": False,
        "terminal": "index.html",
        "stale_after": ["render"],
        "what": "The review page the studio writes over the listed full renders, in their order: A and B, then per candidate the player, the labelled strip, the class, the method and the quality basket with its bars. Built behind the review gate; its md5 opens a round.",
        "knobs": [
            K("title", "str", "", "the page's title"),
            K("intro", "str", "", "one paragraph under the title: what the round is"),
            K("footer", "str", "", "one line at the end; an override is printed here"),
            K(
                "variants",
                "list",
                [],
                "the full renders the page lists, in this order; empty lists every full render in name order",
            ),
        ],
    },
    {
        "name": "grades",
        "title": "grades",
        "kind": "builtin",
        "optional": False,
        "terminal": None,
        "what": "His grade for a round, saved with the page md5 it was given on: his words verbatim, the best render or none, and per render acceptable, a note and three boxes (one picture, content transforms, nothing invented).",
        "knobs": [],
    },
]

FLOW: dict[str, Any] = {
    "title": "pair transition",
    "what": "Two photos, related or not, animated from one into the other by transitions.py: the relation first, then the renders, then the review.",
    "enabled": True,
    "stages": PAIR_STAGES,
    "candidates": {
        "full": ["{root}/{seq}"],
        "draft": ["{root}/drafts/{seq}"],
        "terminal": "report.json",
        "mp4": "transition.mp4",
        "record_knobs": ["preset"],
        "fields": ["class", "method", "sparse_inliers", "median_disp_px", "mean_certainty", "n_frames", "quality"],
    },
}

RESERVED_NAMES = frozenset(
    {"relation", "verdict", "drafts", "raw", "stages", "plans", "requests", "answers", "rounds", "picks", "cache"}
    | {"owner_frames"}
)
"""The job folder's own folders: a pair of one of these names would put its full renders inside a folder another
stage deletes or reads (a relation rerun replaces relation/); the creator refuses it, and so does the render."""
