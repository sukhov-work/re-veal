#!/usr/bin/env python3
"""The studio, phase A1 (2026-11-04): one local page over the loop flow of `loop_seq.py` (a research script, not a tool).

Design of record: .claude/claude-docs/STUDIO.md (the brief §1, the stage registry §2, the shell §3, the data model §4,
the backend contract §5, the phases §9). It serves 127.0.0.1 only, opens no outbound connection, imports neither
`reveal` nor `transitions` nor any research script: every heavy call is a subprocess of .venv/bin/python
(`scripts/research/loop_seq.py prep | readers | render | page`). cv2 is imported in this process only to turn stills
and rendered mp4s into thumbnails and JPEG frames for the page.

State is the job folder on disk and nothing else:
  benchmarks/runs/<date>/studio/<job_id>/
    job.json                 {id, flow, created, ui_version, root, seq, inputs: [{name, path, sha256, bytes}], adopted}
    raw/<seq>/<nn>.jpg       symlinks to the originals in capture order (a new job; `prep` reads this folder)
    stages/<stamp>_<name>/   stage.json (state, argv, pid, started, ended, wall_s, exit_code, knobs, outputs with md5s,
                             script_md5, a reason on failure) and log.txt: one record per run; `done` marks a finished one
    plans/<name>.json        the plans this job rendered, each with a provenance block; the frozen plans are never written
    requests/, answers/      the session's inbox (skeptic_<stamp>.json) and what it wrote back
    rounds/<n>/round.json    a page over the candidates, its md5, his grade text verbatim
    owner_frames/            frames he marked
    cache/                   thumbnails and decoded frames (derived; safe to delete)
  The run folder `root` (the job folder itself, or an adopted run folder such as benchmarks/runs/2026-11-04/angel) keeps
  `loop_seq.py page`'s layout: in/<seq>/ the prep, <seq>/<name>/ the full renders, drafts/<seq>/<name>/ the drafts,
  index.html and page.md5 the review page. A stage's outputs are written to a `.part` folder and renamed on success,
  so a folder that exists is one that finished; a finished render is never overwritten (a new name), while a rerun of
  the registration moves the previous prep aside (in/<seq>_prev_<stamp>), a rerun of the readers replaces its folder and
  a new page keeps the previous one under rounds/<n>/. The runner records the process group; after a restart a `running`
  or `cancelling` record whose process is gone is reconciled from its files (done, refused, cancelled) or marked lost,
  never left pending. One server per tree: a lock file under benchmarks/runs/ refuses a second one (`--second` allows it
  for a review; two servers may then reconcile the same record).

Usage:
  .venv/bin/python scripts/research/studio.py [--port 8380] [--no-browser] [--runs-date YYYY-MM-DD]
  .venv/bin/python scripts/research/studio.py requests      # the open requests across every job, with their age
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = str(ROOT / ".venv/bin/python")
LOOP_SEQ = "scripts/research/loop_seq.py"
RUNS = ROOT / "benchmarks/runs"
FROZEN_PLANS = ROOT / "scripts/research/plans/loops"
UI_VERSION = "studio A1 2026-11-04"
DEFAULT_PORT = 8380
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")
BODY_CAP = 2 * 1024 * 1024
METHODS = ("rife", "dissolve", "morph", "teleport", "cut", "rewind", "slices", "sheets", "snap", "slide", "rise")
EASES = ("linear", "smooth", "snap", "accel", "accel3", "decel", "sine")
EFFECTS = ("breath", "parallax", "glow")
PLAN_KEYS = ("seq", "in", "title", "gag", "timeline", "effects", "matte", "crf", "gif_long", "crop", "provenance")
VERDICTS = ("READY", "READY WITH A NOTE", "NOT READY")
RUNS_DATE = dt.date.today().isoformat()
STATE_LOCK = threading.Lock()
PROCS = {}          # record id -> Popen, the children of this process
WATCHING = set()    # record ids re-attached after a restart


class StudioError(Exception):
    def __init__(self, msg, code=400, extra=None):
        super().__init__(msg); self.code = code; self.extra = extra or {}


def log(msg):
    print(f"studio: {msg}", file=sys.stderr, flush=True)


def now_iso():
    return dt.datetime.now().isoformat(timespec="milliseconds")


def stamp():
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_json(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return default


def write_json(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, p)


def rel(p):
    """A path as the repo-relative string the records carry (None stays None)."""
    if p is None:
        return None
    p = Path(p)
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def tail_lines(p, n=20):
    try:
        data = Path(p).read_bytes()[-16384:]
    except OSError:
        return []
    lines = data.decode("utf-8", "replace").splitlines()
    return lines[-n:]


# ------------------------------------------------------------------ the registry (the loop flow, phase A1)
# A stage: one process with inputs, outputs on disk, knobs, a wall time and a visual. A knob's range is null unless the
# script's --help or SCHEMA.md states one (no loop key states one); the sentences are the scripts' own.

def K(key, typ, default, what, flag=None, choices=None, rng=None):
    return {"key": key, "type": typ, "default": default, "what": what, "flag": flag, "choices": choices, "range": rng}


LOOP_STAGES = [
    {"name": "import", "title": "import", "kind": "builtin", "optional": False, "terminal": None,
     "what": "The stills in capture order, read in place: one symlink per still under raw/<seq>/ and a sha256 per file. The originals are never copied or modified.",
     "knobs": []},
    {"name": "registration", "title": "registration", "kind": "script", "optional": False, "backend": "loop_seq.py prep", "terminal": "prep.json",
     "what": "Every still registered onto one still's background: SIFT + MAGSAC on a 1200 px proxy, then a chain through the previous still, then an ECC affine, else identity (said on the log); all stills cropped to the common valid rectangle. Writes in/<seq>/k<i>.png and prep.json.",
     "knobs": [
         K("long", "int", 1920, "the long edge every still is scaled to before registration (downscale only)", "--long"),
         K("ref", "int", -1, "the canvas frame (default: the widest trusted framing, so nothing is upscaled)", "--ref"),
         K("cut", "str", "", "frame indices joined by a cut, not registered (e.g. 4,5)", "--cut"),
         K("bg_depth", "float", 0.0, "register on the far field only: keypoints where the depth model's relative depth is below this (0 = off)", "--bg-depth"),
         K("min_inliers", "int", 40, "the SIFT fit's inlier floor (a far field of a plain wall may hold 30)", "--min-inliers"),
         K("ecc_refine", "bool", False, "with --bg-depth: refine the far-field fit by a masked ECC on the far pixels (measured worse on the angel pair)", "--ecc-refine"),
         K("depth_maps", "bool", False, "write depth_k<i>.npy (the depth model, offline) for the registered stills even without --bg-depth; a plan with a parallax or a breath by depth needs them", "--depth-maps"),
         K("lock_window", "str", "", "windows of the reference frame (px, 'x0,y0,x1,y1;...') that must stay put: each map gains the translation that zeroes their mean measured offset (the gag object as the anchor). Draw the windows on the still and look at them before trusting their numbers.", "--lock-window"),
     ]},
    {"name": "readers", "title": "readers", "kind": "script", "optional": True, "backend": "loop_seq.py readers", "terminal": "readers.json",
     "what": "Per registered still: the depth map (written beside the prep when missing), the face boxes (YuNet), the grey mean, the clipped pixels, the focus (the Laplacian's variance); per neighbouring pair: the share of pixels whose Lab distance is above 14 and above 30.",
     "knobs": []},
    {"name": "plan", "title": "plan", "kind": "builtin", "optional": False, "terminal": None,
     "what": "The JSON that drives a render (plans/loops/SCHEMA.md): holds on the stills, in-betweens per leg with a method and an ease, effects on the finished frames. A plan saved here carries a provenance block (what it came from, which keys changed, his words); the frozen plans under scripts/research/plans/loops/ are never written.",
     "knobs": []},
    {"name": "render", "title": "render", "kind": "script", "optional": False, "backend": "loop_seq.py render", "terminal": "measure.json",
     "what": "The loop the plan describes, at the prep canvas (full) or at a long edge (draft): loop.mp4, loop.gif, sheet.jpg, frames.json (what each frame is), measure.json (the step series on the decoded mp4, the seam, faces, the double-exposure share, the md5s). The plan's `in` is set to this job's prep on every render.",
     "knobs": [
         K("plan", "plan", "", "the plan to render: a plan saved in this job (job:<name>) or a frozen plan (frozen:<name>)"),
         K("name", "str", "", "the render's folder name under <seq>/ (a full render) or drafts/<seq>/ (a draft); a name that exists is refused"),
         K("draft", "int", 0, "render at this long edge (0 = the prep canvas); a draft is a draft in its folder and its chip", "--draft"),
         K("fps", "int", 25, "frames per second of the mp4 and the gif (the gif stores 40 ms per frame at 25 fps exactly; 30 fps gifs run 10 % fast)", "--fps"),
     ]},
    {"name": "skeptic", "title": "skeptic", "kind": "request", "optional": False, "terminal": None,
     "what": "A request file for the Claude Code session: an Opus 5.5 subagent crops every candidate at full size (faces and hands at mid-leg, box edges, halos, stalls and jumps in the step series) and answers with a verdict per candidate on the md5 it judged. The page refuses an unjudged candidate unless he overrides.",
     "knobs": []},
    {"name": "page", "title": "page", "kind": "script", "optional": False, "backend": "loop_seq.py page", "terminal": "index.html",
     "what": "The review page over every full render of the sequence: the keyframes strip, the mp4 and the gif, the numbers, a note per candidate. Built behind the review gate; its md5 opens a round.",
     "knobs": [
         K("title", "str", "", "the page's title", "--title"),
         K("intro", "str", "", "one paragraph under the title: what the round is", "--intro"),
         K("footer", "str", "", "one line at the end; an override is printed here", "--footer"),
     ]},
    {"name": "grades", "title": "grades", "kind": "builtin", "optional": False, "terminal": None,
     "what": "His grade text for a round, saved verbatim with the page md5 it was given on. A new round's first render waits for the previous round's text, or for the round to be marked ungraded by his word.",
     "knobs": []},
]
FLOWS = {"loop": {"title": "loop from a sequence", "stages": LOOP_STAGES,
                  "what": "Two to ten stills of one scene, handheld, registered on an anchor and looped by a plan of holds and in-betweens; the pipeline of the playbook (.claude/skills/reveal/references/loops.md)."}}
STAGE_ORDER = [s["name"] for s in LOOP_STAGES]


def stage_def(flow, name):
    for s in FLOWS[flow]["stages"]:
        if s["name"] == name:
            return s
    raise StudioError(f"no stage {name!r} in the {flow} flow", 404)


# ------------------------------------------------------------------ the hints (one table; the page and the CLI's help say the same thing)
# Every control, knob, chip, measure and region of the page carries one. The sentences for the scripts' flags and the plan
# keys are the scripts' own (loop_seq.py --help, plans/loops/SCHEMA.md); the bars are the playbook's (loops.md §6).

def H(what, default=None, rng=None, stage=None, source=None):
    d = {"what": what}
    if default is not None: d["default"] = default
    if rng is not None: d["range"] = rng
    if stage: d["stage"] = stage
    if source: d["source"] = source
    return d


HINTS = {
    # the plan's keys (SCHEMA.md)
    "plan.seq": H("The sequence's name: the prep folder in/<seq>/ and the renders <seq>/<name>/ take it.", stage="render", source="SCHEMA.md"),
    "plan.in": H("The prep folder the render reads k<i>.png from (repo-relative). The studio sets it to this job's prep on every render (--set in=...), so the value in the plan is overridden.", stage="render", source="SCHEMA.md"),
    "plan.title": H("One line: what differs from the first candidate (optional). The page shows it beside the name.", stage="page", source="SCHEMA.md"),
    "plan.gag": H("One line the owner can read as the idea of the clip.", stage="page", source="SCHEMA.md"),
    "plan.timeline": H("The steps in order. The loop is the concatenation, and the last transition lands on the first step's still, which is not repeated: the loop's frame 0 is that still's hold.", stage="render", source="SCHEMA.md"),
    "plan.timeline.key": H("A hold step: still `key` for `hold` frames at 25 fps, byte-exact pixels.", stage="render", source="SCHEMA.md"),
    "plan.timeline.hold": H("The hold's length in frames at 25 fps. He sets the pace in words ('20 % faster'): apply the percentage to the frame counts.", default=1, stage="render", source="SCHEMA.md"),
    "plan.timeline.to": H("A transition step: `n` in-betweens from the current still to still `to`.", stage="render", source="SCHEMA.md"),
    "plan.timeline.n": H("The number of in-betweens of the step. RIFE: about 1.3 s each at 1900 px, two calls per frame per `local` box.", default=0, stage="render", source="SCHEMA.md"),
    "plan.timeline.method": H("rife: RIFE v4.26 in-betweens inside the change matte (generated content, the page says so). dissolve: the plain blend. morph: transitions.py's DIS morph. teleport: a region squeezed out and in. cut: no frames. rewind: earlier frames played backward. slices: diagonal cards. sheets: whole pictures sliding across the base. snap: a short blurred jump. slide and rise: one person moved in a matte.", default="rife", stage="render", source="SCHEMA.md"),
    "plan.timeline.ease": H("How frame i of N maps to t: linear; smooth (smoothstep); snap (smoothstep twice); accel (t²); accel3 (t³); decel (1 − (1 − t)²); sine (half a cosine). Per-segment eases on a chain stop at every still: use `through` with one profile instead.", default="smooth", stage="render", source="SCHEMA.md"),
    "plan.timeline.margin": H("rife only: t runs over [margin, 1 − margin], so no in-between hugs a still (an in-between within 4 % of a still reads as a stop). The code's default is 0; the angel plans set 0.04.", default=0, stage="render", source="SCHEMA.md"),
    "plan.timeline.local": H("rife only: [{\"box\": [x0, y0, x1, y1] (canvas fractions), \"ease\": \"snap\", \"feather\": 0.01}]: inside each box the in-between is RIFE at the box's own ease of u, blended over a feathered edge (two RIFE calls per frame per box). A mouth that opens crosses its half-open state in about 3 frames under snap while the lean keeps sine.", stage="render", source="SCHEMA.md"),
    "plan.timeline.through": H("A chain of stills passed under ONE global speed profile (the inner stills never held): the list of the inner stills' indices; `weights` per segment, `soft` slows near a still, `knot_margin` keeps every frame off a still.", stage="render", source="SCHEMA.md"),
    "plan.timeline.weights": H("One weight per segment of a `through` chain: the share of the profile each leg takes (the motion's size per leg).", stage="render", source="SCHEMA.md"),
    "plan.timeline.soft": H("How much a `through` chain slows near each inner still (0 none .. 0.5).", default=0.0, stage="render", source="SCHEMA.md"),
    "plan.timeline.knot_margin": H("A `through` chain's margin at each still, as a share of a leg: about half a frame's share so no frame hugs a still.", default=0.0, stage="render", source="SCHEMA.md"),
    "plan.effects": H("Effects run on the finished frame list; frame 0 is always untouched, so the seam is a still. Kinds: breath, parallax, glow.", stage="render", source="SCHEMA.md"),
    "plan.effects.breath": H("A push-in about (cx, cy) (canvas fractions) by 1 + z·sin²(πu) over the loop. Per clip: fine on an idle object, off where the motion is the subject. `depth_k` (0 = off) makes it a dolly: near layers grow more than far ones (needs the depth maps).", stage="render", source="SCHEMA.md"),
    "plan.effects.breath.z": H("The push-in's size as a share of the frame (1.5–2 % reads as a breath).", stage="render", source="SCHEMA.md"),
    "plan.effects.parallax": H("One remap per frame in which a pixel at relative depth d moves by amp × W × (d − ref) × wave(u) along `dir` (`shape` sin: a sway; pulse: one excursion), plus amp2 × that along `dir2` with `shape2` (an orbit); the plane at depth `ref` (or the depth read at `ref_at` in frame 0's map) stays put; the maps are blurred `sigma` px and blended per frame by the in-between's t. With a breath present the two compose into one remap.", stage="render", source="SCHEMA.md"),
    "plan.effects.parallax.amp": H("The sway's size as a share of the width at depth distance 1 from the reference plane (a2: 0.014).", stage="render", source="SCHEMA.md"),
    "plan.effects.parallax.ref": H("The relative depth (0 far .. 1 near) of the plane that stays put (the halo's plane on the angel pair: 0.15). `ref_at` [fx, fy] reads it from frame 0's map instead.", stage="render", source="SCHEMA.md"),
    "plan.effects.glow": H("The frame's pixels above `thr` inside `box` (canvas fractions) are blurred at the `sigma` radii (shares of W), mixed by `mix`, and added back at gain × wave(u): a light source breathing (a bloom); luminance only.", stage="render", source="SCHEMA.md"),
    "plan.effects.glow.gain": H("The bloom's strength at its peak (a3: 0.15).", stage="render", source="SCHEMA.md"),
    "plan.matte": H("The change matte of a leg: `thr` the Lab distance above which a pixel counts as changed (on 2 px blurred copies), `grow` the dilation and `feather` the Gaussian feather, both as shares of the width; `min_share` the matte's floor. `all: true` runs a rife leg on the whole frame (a locked or far-field registration leaves the rest of the scene's drift as motion, and RIFE carries it).", default={"thr": 14, "grow": 0.015, "feather": 0.01, "min_share": 0.0005}, stage="render", source="SCHEMA.md"),
    "plan.crf": H("The mp4's libx264 quality (lower is larger and truer).", default=14, stage="render", source="SCHEMA.md"),
    "plan.gif_long": H("The gif's long edge in px (a two-pass palette, 40 ms per frame).", default=540, stage="render", source="SCHEMA.md"),
    "plan.crop": H("The centre share of the canvas that is output (the seasons plans use 0.75 on a 3600 px prep so a drifting picture never runs out of pixels).", stage="render", source="SCHEMA.md"),
    "plan.provenance": H("Who wrote the plan, what it came from (path and sha256), when, which keys changed, and his words verbatim. The studio writes it; the renderer ignores it (the plan's sha256 in measure.json includes it).", stage="plan"),
    # the measures (measure.json; the bars from loops.md §6)
    "measure.steps": H("The mean absolute difference between consecutive decoded frames, one value per step (grey levels). The bar: no run of steps below 0.3 while motion is open (a stall); no step above 3× its neighbours outside a declared cut or snap (a jump).", stage="render", source="loops.md §6"),
    "measure.step_mean": H("The mean of the step series (grey levels).", stage="render"),
    "measure.step_max": H("The largest step and the index it sits at. Past 3× its neighbours it is a jump unless a cut or a snap is declared there.", stage="render", source="loops.md §6"),
    "measure.seam_step": H("The difference between the last frame and frame 0: the loop's seam. A still gives about 1–3; anything larger is a visible jump at the seam unless a cut is declared.", rng=[0, 3], stage="render", source="loops.md §6"),
    "measure.faces_per_frame": H("YuNet's face count per decoded frame, against the keyframes' counts; noisy on a group and under a breath. A printed face (a cookie) counts.", stage="render", source="loops.md §6"),
    "measure.generated_share": H("The share of frames a model drew (RIFE in-betweens). The page says which frames are generated; the strip outlines them violet.", stage="render"),
    "measure.dexp_max": H("The largest double-exposure share of a generated frame (the share of pixels where the in-between looks like both stills at once). 3–11 % is the floor on handheld pairs; a doubled prop is found by a crop, not by this number.", stage="render", source="loops.md §6"),
    "measure.rife_seconds_per_frame": H("The mean wall time of one RIFE in-between on this laptop.", stage="render"),
    "measure.render_s": H("The wall time of the frame pass (before the encode and the measures).", stage="render"),
    "measure.md5_mp4": H("The mp4's md5: a render reproduces it from the same plan, prep and script (a watch, not a hope). The skeptic's verdict is given on one md5; a changed md5 is unjudged.", stage="render"),
    "measure.plan_sha256": H("The first 16 hex of the sha256 of the plan as rendered (sorted keys).", stage="render"),
    "measure.script_md5": H("The md5 of scripts/research/loop_seq.py at the render; with the plan's sha256 it names what produced the clip.", stage="render"),
    "measure.rife_version": H("The RIFE model the render loaded (from RIFE_MANIFEST.json), null when no leg used it.", stage="render"),
    # the registration record (prep.json)
    "prep.method": H("How the still was registered: sift+magsac (direct), sift+magsac via frame i (a chain), ecc affine, identity (a declared cut or a failed fit, said on the log); '+ lock' when the lock windows shifted it.", stage="registration"),
    "prep.inliers": H("The SIFT fit's inlier count on the 1200 px proxy (the floor is --min-inliers). A few dozen inliers on a subject-filled frame can fit a wrong model: look at the overlay.", stage="registration"),
    "prep.lock": H("Per lock window: where it sat after the fit (dx, dy in px), the template-match correlation, and the translation applied (the mean offset zeroed).", stage="registration"),
    "prep.canvas": H("The reference frame's size and the common valid rectangle after the warps (even sides); every k<i>.png is this crop.", stage="registration"),
    "prep.scale_to_canvas": H("The still's scale onto the canvas; below 1 the still was downscaled first (INTER_AREA), nothing is upscaled.", stage="registration"),
    # the readers
    "readers.lab_above_14": H("The share of pixels whose Lab distance between two neighbouring stills is above 14 (the change matte's threshold): how much of the frame moves or changes.", stage="readers"),
    "readers.laplacian_var": H("The variance of the Laplacian of the grey still: higher is sharper. Two stills that differ by 2× here differ in focus, and the in-betweens will show the shift.", stage="readers"),
    "readers.faces": H("YuNet's face boxes on the registered still (x, y, w, h in canvas px and the score).", stage="readers"),
    # the records and the chips
    "chip.running": H("The process runs; the number is its progress from the log (PROGRESS i n: i frames done of a planned total, an estimate; a sheets step plans one frame more than it renders), the lines are the log's tail. Cancel sends SIGTERM to its process group."),
    "chip.done": H("The process exited 0 and its outputs were renamed from the .part folder: an output that exists is one that finished."),
    "chip.failed": H("The process exited with an error; the reason is the log's last line."),
    "chip.refused": H("The script declined the input on purpose (exit 2 with a FAILED: line): the reason names the problem; the fix is in the knobs or the inputs, never in the detector."),
    "chip.lost": H("The server restarted while the stage ran, and no terminal file was found when its process was gone: run it again."),
    "chip.cancelled": H("Cancelled by you; the .part folder was removed."),
    "chip.stale": H("An upstream stage ran again after this one: its outputs may no longer match the inputs. Rerun from here."),
    "chip.draft": H("Rendered at a long edge below the prep canvas: a draft shows the timing, not what a skeptic can judge."),
    "chip.generated": H("A model drew this frame (a RIFE in-between): the violet mark follows it on the strip, the scrubber and the sheet."),
    "chip.unjudged": H("No skeptic verdict exists for this md5 (none yet, or the render changed after the verdict). The page refuses it unless you override, and the override is printed on the page."),
    "chip.READY": H("The skeptic's verdict: no fault found at full size."),
    "chip.READY WITH A NOTE": H("The skeptic's verdict: a fault worth a note on the page, not a block."),
    "chip.NOT READY": H("The skeptic's verdict: a fault he would see; the page refuses it unless you override."),
    "chip.waiting": H("A request file waits for the Claude Code session; the age is since it was written. `studio.py requests` lists it at the session's boot."),
    "chip.answered": H("The session wrote its answer into answers/."),
    "chip.ungraded": H("The round's page exists and no grade text is saved."),
    "chip.graded": H("His grade text is saved verbatim with the page md5 it was given on."),
    # the regions and controls
    "region.rail": H("The jobs (name, flow, the last render's state, the round), the running tasks with their elapsed seconds, the models' readiness. Up and down move the selection, Enter opens."),
    "region.strip": H("The job's stages as tiles, left to right in the flow's order: the thumbnail, the name, the wall time and the state chip; a violet tick where generated content exists; the selected one outlined amber. Left and right move the selection."),
    "region.panel": H("The selected stage's content: its outputs, its history, rerun from here."),
    "region.inspector": H("One row per knob of the selected stage: the literal key, the value, the range, the default, the sentence; the provenance (the plan's sha256, the script's md5, the outputs' md5s); the command line that reproduces the stage from the shell; cancel for a running stage."),
    "region.viewer": H("One large frame under judgement; A (the first still) and B (the last) small beside it. Space plays at 25 fps; left and right step one frame, shift by ten; `,` and `.` likewise; m marks the frame as a fault (saved under owner_frames/)."),
    "region.axis": H("The shared frame axis: the scrubber, the step series, the generated bands and the skeptic's markers at the same x; a click moves the scrubber; the dashed line is the 0.3 stall bar."),
    "control.rerun": H("Runs the stage again with the inspector's knobs into a new record; the stages after it go stale until they run again."),
    "control.cancel": H("SIGTERM to the stage's process group; the record is marked cancelled and its .part folder removed."),
    "control.command": H("The argv that reproduces this record from the shell: the CLI and the studio read and write the same files."),
    "control.save_plan": H("Saves the editor's JSON as a new plan of this job with a provenance block (from which plan, which keys changed, your words); a plan saved from the page is recorded as the owner's. Unknown top-level keys, methods, eases and effect kinds are refused with the known list."),
    "control.render": H("Renders the chosen plan into <seq>/<name>/ (full) or drafts/<seq>/<name>/ (a draft) with the job's prep as `in`; the record shows the progress number and the log."),
    "control.request_skeptic": H("Writes requests/skeptic_<stamp>.json with the candidates' md5s and your brief; the session answers with answers/skeptic_<stamp>.json (a verdict per candidate on the md5 judged) and a report with crops."),
    "control.page": H("Builds the review page over every full render of the sequence by loop_seq.py page, behind the review gate: refused while a candidate is unjudged or NOT READY unless you override; the override is printed on the page; the page's md5 opens a round."),
    "control.grade": H("Saves his words verbatim for the round, with the page md5 they were given on. The next round's first render waits for this text, or for 'ungraded by his word'."),
    "control.adopt": H("Opens a run folder made before the studio existed (benchmarks/runs/<date>/<run>) as a job: its prep, its renders and its page are read in place; the studio's records live in its own folder. The existing page becomes round 1."),
    "control.new_job": H("A new loop job from a folder of developed JPGs (sorted by name = capture order; ARW and XMP ignored): symlinks and sha256s, nothing copied."),
    "control.mark_frame": H("Saves the frame index and your note under owner_frames/ for the next round."),
}


# ------------------------------------------------------------------ jobs (the job folder is the only state)

def studio_dir(date=None):
    return RUNS / (date or RUNS_DATE) / "studio"


def job_dirs():
    out = [jj.parent for jj in RUNS.glob("*/studio/*/job.json")]
    return sorted(out, key=lambda d: (read_json(d / "job.json", {}) or {}).get("created", ""))


def find_job(jid):
    if not ID_RE.match(jid or ""):
        raise StudioError("a job id is letters, digits, dot, dash and underscore", 400)
    for jj in RUNS.glob(f"*/studio/{jid}/job.json"):
        return jj.parent
    raise StudioError(f"no job {jid}", 404)


def load_job(jid):
    d = find_job(jid)
    job = read_json(d / "job.json")
    if not job:
        raise StudioError(f"{rel(d)}/job.json is unreadable", 500)
    return d, job


def job_root(job):
    return (ROOT / job["root"]).resolve()


def list_stills(folder):
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg") and not p.name.startswith("."))


def inside(p, base):
    try:
        Path(p).resolve().relative_to(Path(base).resolve()); return True
    except ValueError:
        return False


def create_job(flow, folder=None, adopt=None, seq=None):
    if flow not in FLOWS:
        raise StudioError(f"the flow is one of {sorted(FLOWS)} (phase A1 builds the loop flow; align, pair and director are phases B and C)", 400)
    if adopt:
        root = (ROOT / adopt).resolve()
        if not inside(root, RUNS) or not root.is_dir():
            raise StudioError("a run folder to adopt lies under benchmarks/runs/", 400)
        if not seq or not NAME_RE.match(seq):
            raise StudioError("adopt needs the sequence's name (the folder under in/)", 400)
        prep = read_json(root / "in" / seq / "prep.json")
        if not prep:
            raise StudioError(f"{rel(root)}/in/{seq}/prep.json not found: nothing to adopt", 404)
        jid = f"{flow}_{seq}_{stamp()}"
        d = studio_dir() / jid
        d.mkdir(parents=True)
        inputs = [{"name": Path(s["source"]).name, "path": s["source"], "sha256": s["sha256"], "bytes": s["bytes"], "native": s.get("native")}
                  for s in prep.get("sources", [])]
        job = {"id": jid, "flow": flow, "created": now_iso(), "ui_version": UI_VERSION, "root": rel(root), "seq": seq,
               "inputs": inputs, "adopted": True, "adopted_from": rel(root)}
        write_json(d / "job.json", job)
        page = root / "index.html"
        if page.exists():
            md5v = md5_file(page)
            recorded = (root / "page.md5").read_text().split()[0] if (root / "page.md5").exists() else None
            names = [c["name"] for c in candidates(d, job) if c["kind"] == "full"]
            (d / "rounds" / "1").mkdir(parents=True, exist_ok=True)
            shutil.copy2(page, d / "rounds" / "1" / "index.html")
            write_json(d / "rounds" / "1" / "round.json",
                       {"n": 1, "at": now_iso(), "candidates": names, "page_md5": md5v, "page_md5_recorded": recorded, "page": "index.html",
                        "override": None, "grade": None, "ungraded_by_his_word": None,
                        "note": "adopted: the page the session built before the studio existed"})
        log(f"job {jid}: adopted {rel(root)} ({len(inputs)} stills, page {'yes' if page.exists() else 'no'})")
        return job
    if not folder:
        raise StudioError("a new job needs a folder of developed JPGs, or a run folder to adopt", 400)
    src = Path(folder).expanduser()
    if not src.is_absolute():
        src = ROOT / src
    src = src.resolve()
    if not src.is_dir():
        raise StudioError(f"{src} is not a folder", 400)
    stills = list_stills(src)
    if len(stills) < 2:
        raise StudioError(f"{src}: {len(stills)} developed JPGs, need 2 or more (prep reads .jpg and .jpeg only; convert HEIC or PNG stills first)", 400)
    seq = seq or re.sub(r"[^a-z0-9]+", "_", src.name.lower()).strip("_")[:40] or "seq"
    if not NAME_RE.match(seq):
        raise StudioError("the sequence's name is letters, digits, dash and underscore", 400)
    jid = f"{flow}_{seq}_{stamp()}"
    d = studio_dir() / jid
    raw = d / "raw" / seq
    raw.mkdir(parents=True)
    inputs = []
    for i, p in enumerate(stills, 1):
        link = raw / f"{i:02d}.jpg"
        os.symlink(p, link)
        inputs.append({"name": p.name, "path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size, "link": rel(link)})
    job = {"id": jid, "flow": flow, "created": now_iso(), "ui_version": UI_VERSION, "root": rel(d), "seq": seq,
           "inputs": inputs, "adopted": False, "source_folder": str(src)}
    write_json(d / "job.json", job)
    log(f"job {jid}: {len(stills)} stills of {src} linked under {rel(raw)}")
    return job


# ------------------------------------------------------------------ the runner (every heavy call a subprocess; the record on disk)

SCRIPT_FLAGS = {"progress": False, "frames": False, "readers": False}


def probe_script_flags():
    """Which of the studio's default-off flags the research script carries (its --help is the truth)."""
    try:
        h = subprocess.run([PY, LOOP_SEQ, "render", "--help"], capture_output=True, text=True, timeout=60, cwd=str(ROOT)).stdout
        SCRIPT_FLAGS["progress"] = "--progress" in h
        SCRIPT_FLAGS["frames"] = "--frames" in h
        h2 = subprocess.run([PY, LOOP_SEQ, "--help"], capture_output=True, text=True, timeout=60, cwd=str(ROOT)).stdout
        SCRIPT_FLAGS["readers"] = "readers" in h2
    except (OSError, subprocess.SubprocessError) as e:
        log(f"could not probe {LOOP_SEQ} --help: {e}")
    missing = [k for k, v in SCRIPT_FLAGS.items() if not v]
    log(f"{LOOP_SEQ}: progress {SCRIPT_FLAGS['progress']}, frames {SCRIPT_FLAGS['frames']}, readers {SCRIPT_FLAGS['readers']}"
        + (f" (missing: {', '.join(missing)}; the strip shows no progress number and the scrubber decodes the mp4 itself)" if missing else ""))


def coerce(stage, knobs):
    out = {}
    known = {k["key"]: k for k in stage["knobs"]}
    for key, v in (knobs or {}).items():
        if key in ("override", "notes"):
            out[key] = v; continue
        if key not in known:
            raise StudioError(f"the {stage['name']} stage has no knob {key!r}; its knobs are {sorted(known)}", 400)
        k = known[key]
        try:
            if k["type"] == "int":
                out[key] = int(v)
            elif k["type"] == "float":
                out[key] = float(v)
            elif k["type"] == "bool":
                out[key] = bool(v) if not isinstance(v, str) else v.lower() in ("1", "true", "yes", "on")
            else:
                out[key] = str(v)
        except (TypeError, ValueError):
            raise StudioError(f"knob {key} takes a {k['type']}, not {v!r}", 400)
    for key, k in known.items():
        out.setdefault(key, k["default"])
    return out


def flags_of(stage, knobs):
    out = []
    for k in stage["knobs"]:
        if not k["flag"]:
            continue
        v = knobs.get(k["key"], k["default"])
        if k["type"] == "bool":
            if v:
                out.append(k["flag"])
        elif k["type"] == "str":
            if v != "":
                out += [k["flag"], str(v)]
        else:
            out += [k["flag"], str(v)]
    return out


def resolve_plan(d, ref):
    if not isinstance(ref, str) or ":" not in ref:
        raise StudioError("the plan is job:<name> (a plan saved in this job) or frozen:<name> (scripts/research/plans/loops/<name>.json)", 400)
    kind, name = ref.split(":", 1)
    if not NAME_RE.match(name):
        raise StudioError("a plan name is letters, digits, dash and underscore", 400)
    if kind == "job" and d is not None:
        p = d / "plans" / f"{name}.json"
    elif kind == "frozen":
        p = FROZEN_PLANS / f"{name}.json"
    else:
        raise StudioError("the plan is job:<name> or frozen:<name>", 400)
    if not p.exists():
        raise StudioError(f"no plan {rel(p)}", 404)
    return p


def prep_dir(job):
    return job_root(job) / "in" / job["seq"]


def argv_for(stage, d, job, knobs, rec_dir):
    """The argv, the final output path, its .part twin and the inputs of one run of a stage."""
    root, seq, name = job_root(job), job["seq"], stage["name"]
    prep = prep_dir(job)
    if name == "registration":
        src = d / "raw" / seq
        if not src.is_dir():
            raise StudioError("this job has no raw stills to register (an adopted job reads its prep in place)", 409)
        out_final, out_part = prep, prep.with_name(seq + ".part")
        argv = [PY, LOOP_SEQ, "prep", rel(src), "--out", rel(out_part)] + flags_of(stage, knobs)
        inputs = [{"path": i["path"], "sha256": i["sha256"]} for i in job["inputs"]]
    elif name == "readers":
        if not SCRIPT_FLAGS["readers"]:
            raise StudioError(f"{LOOP_SEQ} has no readers command yet (its --help does not list it)", 501)
        if not (prep / "prep.json").exists():
            raise StudioError("registration first: no prep.json", 409)
        out_final, out_part = prep / "readers", prep / "readers.part"
        argv = [PY, LOOP_SEQ, "readers", rel(prep), "--out", rel(out_part)]
        inputs = [{"path": rel(prep / "prep.json"), "sha256": sha256_file(prep / "prep.json")}]
    elif name == "render":
        if not (prep / "prep.json").exists():
            raise StudioError("registration first: no prep.json", 409)
        plan_path = resolve_plan(d, knobs.get("plan"))
        rname = knobs.get("name") or plan_path.stem
        if not NAME_RE.match(rname):
            raise StudioError("a render name is letters, digits, dash and underscore", 400)
        draft, fps = int(knobs.get("draft", 0)), int(knobs.get("fps", 25))
        base = (root / "drafts" / seq) if draft else (root / seq)
        out_final, out_part = base / rname, base / (rname + ".part")
        argv = [PY, LOOP_SEQ, "render", rel(plan_path), "--out", rel(out_part), "--fps", str(fps), "--draft", str(draft),
                "--set", f'in="{rel(prep)}"']
        if SCRIPT_FLAGS["progress"]:
            argv.append("--progress")
        if SCRIPT_FLAGS["frames"]:
            argv.append("--frames")
        inputs = [{"path": rel(plan_path), "sha256": sha256_file(plan_path)}, {"path": rel(prep / "prep.json"), "sha256": sha256_file(prep / "prep.json")}]
    elif name == "page":
        out_final, out_part = root / "index.html", root / "index.part.html"
        notes = knobs.get("notes") or {}
        if not isinstance(notes, dict):
            raise StudioError("notes is {candidate: text}", 400)
        write_json(rec_dir / "notes.json", {seq: notes})
        n = len(rounds(d)) + 1
        argv = [PY, LOOP_SEQ, "page", "--root", rel(root), "--out", rel(out_part), "--order", seq,
                "--title", knobs.get("title") or f"{seq}: round {n}", "--intro", knobs.get("intro") or "", "--footer", knobs.get("footer") or "",
                "--notes", rel(rec_dir / "notes.json")]
        inputs = [{"path": rel(c["dir"] / "loop.mp4"), "md5": c["md5_mp4"]} for c in candidates(d, job) if c["kind"] == "full"]
    else:
        raise StudioError(f"the {name} stage is not a process", 400)
    return argv, out_final, out_part, inputs


def records(d):
    out = []
    for sj in (d / "stages").glob("*/stage.json"):
        r = read_json(sj)
        if r:
            out.append(r)
    return sorted(out, key=lambda r: (r.get("started") or "", r["id"]))


def record_dir(d, rid):
    if not ID_RE.match(rid or ""):
        raise StudioError("bad record id", 400)
    p = d / "stages" / rid
    if not (p / "stage.json").exists():
        raise StudioError(f"no record {rid}", 404)
    return p


def outputs_of(p):
    p = Path(p)
    if p.is_file():
        return [{"path": rel(p), "md5": md5_file(p), "bytes": p.stat().st_size}]
    out = []
    for f in sorted(p.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            out.append({"path": rel(f), "md5": md5_file(f), "bytes": f.stat().st_size})
    return out


def start_stage(d, job, stage, knobs):
    knobs = coerce(stage, knobs)
    if stage["kind"] != "script":
        raise StudioError(f"the {stage['name']} stage is not a process", 400)
    if stage["name"] == "render" and not int(knobs.get("draft", 0)):
        rs = rounds(d)
        if rs and not rs[-1].get("grade") and not rs[-1].get("ungraded_by_his_word"):
            raise StudioError(f"round {rs[-1]['n']} has no grade text: save his words, or mark the round ungraded by his word, before the next round's first full render", 409,
                              {"round": rs[-1]["n"]})
    if stage["name"] == "registration":
        busy = [r["id"] for r in records(d) if r["state"] in ("running", "cancelling")]
        if busy:
            raise StudioError(f"the registration waits: {', '.join(busy)} still read the prep", 409)
    rid = f"{stamp()}_{stage['name']}"
    rec_dir = d / "stages" / rid
    k = 1
    while rec_dir.exists():
        k += 1; rec_dir = d / "stages" / f"{rid}_{k}"
    rid = rec_dir.name
    rec_dir.mkdir(parents=True)
    try:
        argv, out_final, out_part, inputs = argv_for(stage, d, job, knobs, rec_dir)
        if out_final.exists() and stage["name"] == "render":
            raise StudioError(f"{rel(out_final)} exists: choose another name (a finished render is never overwritten)", 409)
        for r in records(d):
            if r["state"] == "running" and r.get("out_part") == rel(out_part):
                raise StudioError(f"{r['id']} is still running into {rel(out_part)}", 409)
        if out_part.exists():
            shutil.rmtree(out_part) if out_part.is_dir() else out_part.unlink()
    except StudioError:
        shutil.rmtree(rec_dir, ignore_errors=True)
        raise
    with open(rec_dir / "log.txt", "ab") as logf:
        p = subprocess.Popen(argv, cwd=str(ROOT), stdout=logf, stderr=subprocess.STDOUT, start_new_session=True,
                             env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    rec = {"id": rid, "stage": stage["name"], "state": "running", "argv": argv, "pid": p.pid, "started": now_iso(), "ended": None,
           "wall_s": None, "exit_code": None, "knobs": knobs, "inputs": inputs, "outputs": [], "script_md5": md5_file(ROOT / LOOP_SEQ),
           "out_part": rel(out_part), "out_final": rel(out_final), "terminal": stage["terminal"], "log": "log.txt", "ui_version": UI_VERSION}
    write_json(rec_dir / "stage.json", rec)
    PROCS[rid] = p
    threading.Thread(target=_wait, args=(d, rid, p), daemon=True).start()
    log(f"{job['id']} {rid}: pid {p.pid}: {' '.join(argv)}")
    return rec


def _wait(d, rid, p):
    rc = p.wait()
    PROCS.pop(rid, None)
    finalize(d, rid, rc)


def finalize(d, rid, rc):
    rec_dir = d / "stages" / rid
    with STATE_LOCK:
        rec = read_json(rec_dir / "stage.json")
        if not rec or rec["state"] not in ("running", "cancelling"):
            return rec
        out_part = (ROOT / rec["out_part"]) if rec.get("out_part") else None
        out_final = (ROOT / rec["out_final"]) if rec.get("out_final") else None
        term = rec.get("terminal")
        have = False
        if out_part is not None and out_part.exists():
            have = (out_part / term).exists() if out_part.is_dir() else True
        lines = [l for l in tail_lines(rec_dir / "log.txt", 60) if l.strip()]
        failed_line = next((l for l in reversed(lines) if l.startswith("FAILED:")), None)
        if rec["state"] == "cancelling":
            rec["state"] = "cancelled"; rec["reason"] = "cancelled; the server restarted before the record was written"
            if out_part is not None and out_part.exists() and ".part" in out_part.name and inside(out_part, RUNS):
                shutil.rmtree(out_part) if out_part.is_dir() else out_part.unlink()
        elif (rc == 0 or rc is None) and have:
            if out_final.exists():
                if rec["stage"] == "registration":
                    prev = out_final.with_name(out_final.name + "_prev_" + stamp())
                    os.replace(out_final, prev)
                    if (prev / "keys.jpg").exists():                 # the existing pages link in/<seq>/keys.jpg
                        shutil.copy2(prev / "keys.jpg", out_part / "keys.jpg")
                    rec["note"] = f"the previous prep moved to {rel(prev)}; the renders and readers made from it are stale"
                elif rec["stage"] == "page":
                    prev = rec_dir / "previous_index.html"
                    shutil.copy2(out_final, prev)
                    rec["note"] = "the previous page is kept under its round and beside this record"
                elif out_final.is_dir():
                    shutil.rmtree(out_final)                     # readers: derived files, replaced
                else:
                    out_final.unlink()
            os.replace(out_part, out_final)
            rec["state"] = "done"
            if rc is None:
                rec["note"] = (rec.get("note", "") + " finished after a restart: the exit code is unknown; the terminal file was present").strip()
            (rec_dir / "done").write_text(now_iso())
        elif failed_line and (rc == 2 or rc is None):
            rec["state"] = "refused"; rec["reason"] = failed_line
        elif rc is None:
            rec["state"] = "lost"; rec["reason"] = "the server restarted while the stage ran and no terminal file was found: run it again"
            if out_part is not None and out_part.exists() and ".part" in out_part.name and inside(out_part, RUNS):
                shutil.rmtree(out_part) if out_part.is_dir() else out_part.unlink()
                rec["note"] = "the partial .part folder was removed"
        else:
            rec["state"] = "failed"; rec["reason"] = (lines[-1] if lines else f"exit {rc} with an empty log")[-300:]
        rec["ended"] = now_iso()
        try:
            rec["wall_s"] = round((dt.datetime.fromisoformat(rec["ended"]) - dt.datetime.fromisoformat(rec["started"])).total_seconds(), 1)
        except ValueError:
            rec["wall_s"] = None
        rec["exit_code"] = rc
        write_json(rec_dir / "stage.json", rec)
    if rec["state"] == "done":                                   # the md5s outside the lock: a render with --frames holds 50–300 files
        outputs = outputs_of(out_final)
        if rec["stage"] == "readers":
            outputs += [{"path": rel(q), "md5": md5_file(q), "bytes": q.stat().st_size, "note": "written beside the prep by readers (a plan's depth effects read it there)"}
                        for q in sorted(out_final.parent.glob("depth_k*.npy"))]
        ident = {"registration": lambda n: n.endswith(".png") or n.endswith(".npy"), "render": lambda n: n == "loop.mp4",
                 "readers": lambda n: n == "readers.json", "page": lambda n: False}.get(rec["stage"], lambda n: False)
        mine = sorted((Path(o["path"]).name, o["md5"]) for o in outputs if ident(Path(o["path"]).name))
        prev = [r for r in records(d) if r["stage"] == rec["stage"] and r["state"] == "done" and r["id"] != rid and r.get("outputs")]
        unchanged = None
        if mine and prev:
            theirs = sorted((Path(o["path"]).name, o["md5"]) for o in prev[-1]["outputs"] if ident(Path(o["path"]).name))
            if theirs == mine:
                unchanged = prev[-1]["id"]
        with STATE_LOCK:
            rec = read_json(rec_dir / "stage.json")
            rec["outputs"] = outputs
            if unchanged:
                rec["unchanged_from"] = unchanged                    # STUDIO.md §4: a rerun whose outputs' md5s equal the previous run's says so
            write_json(rec_dir / "stage.json", rec)
    log(f"{d.name} {rid}: {rec['state']}" + (f" ({rec.get('reason')})" if rec.get("reason") else ""))
    if rec["state"] == "done":
        after_done(d, rec)
    return rec


def after_done(d, rec):
    """What a finished stage adds to the job: a page opens a round and writes page.md5."""
    if rec["stage"] != "page":
        return
    job = read_json(d / "job.json")
    root = job_root(job)
    page = ROOT / rec["out_final"]
    md5v = md5_file(page)
    (root / "page.md5").write_text(md5v + "\n")
    n = len(rounds(d)) + 1
    names = [c["name"] for c in candidates(d, job) if c["kind"] == "full"]
    (d / "rounds" / str(n)).mkdir(parents=True, exist_ok=True)
    shutil.copy2(page, d / "rounds" / str(n) / "index.html")          # the round keeps its page; the root holds the latest
    write_json(d / "rounds" / str(n) / "round.json",
               {"n": n, "at": now_iso(), "candidates": names, "page_md5": md5v, "page": "index.html", "record": rec["id"],
                "override": rec["knobs"].get("override") or None, "grade": None, "ungraded_by_his_word": None})
    log(f"{d.name}: round {n} opened on page md5 {md5v}")


def pid_alive(pid, rec=None):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        args = subprocess.run(["ps", "-o", "args=", "-p", str(pid)], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return True
    if rec is None:
        return bool(args.strip())
    return LOOP_SEQ in args and (rec.get("out_part") or "\0") in args


def _watch_pid(d, rid, pid):
    while pid_alive(pid):
        time.sleep(1)
    WATCHING.discard(rid)
    finalize(d, rid, None)


def reconcile(d, rec):
    """A running record whose process this server did not start: alive → watched; gone → done from its files, else lost."""
    if rec.get("state") not in ("running", "cancelling") or rec["id"] in PROCS:
        return rec
    if pid_alive(rec["pid"], rec):
        if rec["id"] not in WATCHING:
            WATCHING.add(rec["id"])
            threading.Thread(target=_watch_pid, args=(d, rec["id"], rec["pid"]), daemon=True).start()
            log(f"{d.name} {rec['id']}: pid {rec['pid']} still runs after a restart; re-attached")
        return rec
    return finalize(d, rec["id"], None) or rec


def reconcile_all():
    n = 0
    for d in job_dirs():
        for r in records(d):
            if r.get("state") in ("running", "cancelling"):
                reconcile(d, r); n += 1
    if n:
        log(f"reconciled {n} running record(s) at start")


def cancel(d, rid):
    rec_dir = record_dir(d, rid)
    rec = read_json(rec_dir / "stage.json")
    if rec["state"] == "running" and rid not in PROCS and not pid_alive(rec["pid"], rec):
        return reconcile(d, rec)                                     # the process is gone (or the pid is a stranger's): no signal
    with STATE_LOCK:
        rec = read_json(rec_dir / "stage.json")
        if rec["state"] != "running":
            raise StudioError(f"{rid} is {rec['state']}, not running", 409)
        rec["state"] = "cancelling"
        write_json(rec_dir / "stage.json", rec)
    try:
        os.killpg(rec["pid"], signal.SIGTERM)
    except ProcessLookupError:
        pass
    p = PROCS.get(rid)
    deadline = time.time() + 5
    while pid_alive(rec["pid"]) and time.time() < deadline:
        time.sleep(0.2)
    if pid_alive(rec["pid"]):
        try:
            os.killpg(rec["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass
    if p is not None:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    PROCS.pop(rid, None)
    with STATE_LOCK:
        rec = read_json(rec_dir / "stage.json")
        rec["state"] = "cancelled"; rec["ended"] = now_iso()
        rec["wall_s"] = round((dt.datetime.fromisoformat(rec["ended"]) - dt.datetime.fromisoformat(rec["started"])).total_seconds(), 1)
        rec["reason"] = "cancelled by you"
        out_part = (ROOT / rec["out_part"]) if rec.get("out_part") else None
        if out_part is not None and out_part.exists() and ".part" in out_part.name and inside(out_part, RUNS):
            shutil.rmtree(out_part) if out_part.is_dir() else out_part.unlink()
            rec["note"] = "the .part folder was removed"
        write_json(rec_dir / "stage.json", rec)
    log(f"{d.name} {rid}: cancelled")
    return rec


def progress_of(rec_dir):
    for l in reversed(tail_lines(rec_dir / "log.txt", 300)):
        if l.startswith("PROGRESS "):
            parts = l.split()
            try:
                return {"i": int(parts[1]), "n": int(parts[2]), "phase": parts[3] if len(parts) > 3 else ""}
            except (IndexError, ValueError):
                return None
    return None


def record_view(d, rec):
    rec = reconcile(d, rec)
    rec_dir = d / "stages" / rec["id"]
    v = dict(rec)
    v["progress"] = progress_of(rec_dir) if rec["state"] == "running" else None
    v["log_tail"] = tail_lines(rec_dir / "log.txt", 12)
    if rec["state"] == "running":
        try:
            v["elapsed_s"] = round((dt.datetime.now() - dt.datetime.fromisoformat(rec["started"])).total_seconds(), 1)
        except ValueError:
            v["elapsed_s"] = None
    v["command"] = " ".join(a if " " not in a and '"' not in a else "'" + a.replace("'", "'\\''") + "'" for a in rec["argv"])
    return v


# ------------------------------------------------------------------ what the job holds (read from disk on every call)

def candidates(d, job):
    """Every render of the sequence: the full ones under <root>/<seq>/, the drafts under <root>/drafts/<seq>/ or <root>/drafts/."""
    root, seq = job_root(job), job["seq"]
    verd = verdicts(d)
    out = []
    pairs = [(root / seq, "full")] + [(root / "drafts" / seq, "draft"), (root / "drafts", "draft")]
    seen = set()
    for base, kind in pairs:
        if not base.is_dir():
            continue
        for v in sorted(base.iterdir()):
            if not v.is_dir() or v.name.endswith(".part") or v in seen:   # a .part folder is a render still running
                continue
            m = read_json(v / "measure.json")
            if not m:
                continue
            seen.add(v)
            plan = read_json(v / "plan.json", {}) or {}
            vd = verd.get(v.name) if kind == "full" else None
            c = {"name": v.name, "kind": kind, "dir": v, "path": rel(v), "title": plan.get("title", ""), "gag": plan.get("gag", ""),
                 "md5_mp4": m.get("md5_mp4"), "frames": m.get("frames"), "seconds": m.get("seconds"), "canvas": m.get("canvas"),
                 "draft": m.get("draft", 0), "step_mean": m.get("step_mean"), "step_max": m.get("step_max"), "step_max_at": m.get("step_max_at"),
                 "seam_step": m.get("seam_step"), "generated_frames": m.get("generated_frames"), "generated_share": m.get("generated_share"),
                 "dexp_max": m.get("dexp_max"), "render_s": m.get("render_s"), "faces_keyframes": m.get("faces_keyframes"),
                 "plan_sha256": m.get("plan_sha256"), "script_md5": m.get("script_md5"), "rife_version": m.get("rife_version"),
                 "has_frames": (v / "frames").is_dir(), "mtime": dt.datetime.fromtimestamp((v / "measure.json").stat().st_mtime).isoformat(timespec="seconds"),
                 "verdict": vd, "unjudged": kind == "full" and (not vd or vd.get("judged_md5") != m.get("md5_mp4"))}
            if vd and vd.get("judged_md5") != m.get("md5_mp4"):
                c["unjudged_reason"] = "the render changed after the verdict (judged md5 differs)"
            elif not vd and kind == "full":
                c["unjudged_reason"] = "no skeptic verdict for this candidate"
                before = sorted(q.name for q in (root / "agents").glob("skeptic*.md")) if job.get("adopted") else []
                if before:
                    c["judged_before_studio"] = before
                    c["unjudged_reason"] += f" in the studio (judged before it: {', '.join(before)})"
            out.append(c)
    return out


def candidate(d, job, kind, name):
    if kind not in ("full", "draft") or not NAME_RE.match(name or ""):
        raise StudioError("a render is full|draft/<name>", 400)
    for c in candidates(d, job):
        if c["kind"] == kind and c["name"] == name:
            return c
    raise StudioError(f"no {kind} render {name}", 404)


def verdicts(d):
    """The latest skeptic verdict per candidate, merged over answers/skeptic_*.json in time order."""
    out = {}
    for a in sorted((d / "answers").glob("skeptic_*.json")):
        ans = read_json(a) or {}
        for name, v in (ans.get("candidates") or {}).items():
            if isinstance(v, dict) and v.get("verdict") in VERDICTS:
                out[name] = {"verdict": v["verdict"], "judged_md5": v.get("judged_md5"), "note": v.get("note", ""), "from": a.name, "at": ans.get("at")}
    return out


def rounds(d):
    out = []
    for rj in (d / "rounds").glob("*/round.json"):
        r = read_json(rj)
        if r:
            out.append(r)
    return sorted(out, key=lambda r: r["n"])


def requests_of(d):
    out = []
    for rq in sorted((d / "requests").glob("*.json")):
        r = read_json(rq) or {}
        ans = d / "answers" / rq.name
        age = round((dt.datetime.now() - dt.datetime.fromtimestamp(rq.stat().st_mtime)).total_seconds())
        out.append({"file": rel(rq), "name": rq.name, "kind": r.get("kind"), "at": r.get("at"), "brief": r.get("brief", ""),
                    "candidates": [c.get("name") for c in r.get("candidates", [])], "answered": ans.exists(), "answer": rel(ans) if ans.exists() else None,
                    "age_s": age})
    return out


def plans_of(d):
    out = []
    for pj in sorted((d / "plans").glob("*.json")):
        p = read_json(pj) or {}
        prov = p.get("provenance") or {}
        out.append({"name": pj.stem, "ref": f"job:{pj.stem}", "path": rel(pj), "sha256": sha256_file(pj), "title": p.get("title", ""),
                    "from": prov.get("from"), "author": prov.get("author"), "at": prov.get("at"), "changes": len(prov.get("changes") or []),
                    "words": prov.get("words", "")})
    return out


def frozen_plans():
    out = []
    for pj in sorted(FROZEN_PLANS.glob("*.json")):
        p = read_json(pj) or {}
        out.append({"name": pj.stem, "ref": f"frozen:{pj.stem}", "path": rel(pj), "seq": p.get("seq"), "title": p.get("title", "")[:160], "in": p.get("in")})
    return out


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise StudioError("a plan is a JSON object", 400)
    unknown = sorted(k for k in plan if k not in PLAN_KEYS)
    if unknown:
        raise StudioError(f"unknown plan keys {unknown}; the keys are {list(PLAN_KEYS)} (plans/loops/SCHEMA.md)", 400)
    tl = plan.get("timeline")
    if not isinstance(tl, list) or not tl:
        raise StudioError("the plan needs a non-empty timeline", 400)
    for i, st in enumerate(tl):
        if not isinstance(st, dict) or not ("key" in st or "to" in st):
            raise StudioError(f"timeline[{i}] is a hold {{key, hold}} or a transition {{to, n, method, ease}}", 400)
        if "to" in st:
            m = st.get("method", "rife")
            if m not in METHODS:
                raise StudioError(f"timeline[{i}]: method {m!r} is not one of {list(METHODS)}", 400)
            e = st.get("ease", "smooth")
            if e not in EASES:
                raise StudioError(f"timeline[{i}]: ease {e!r} is not one of {list(EASES)}", 400)
    for i, e in enumerate(plan.get("effects") or []):
        if not isinstance(e, dict) or e.get("kind") not in EFFECTS:
            raise StudioError(f"effects[{i}]: kind is one of {list(EFFECTS)}", 400)
    if "matte" in plan and not isinstance(plan["matte"], dict):
        raise StudioError("matte is an object", 400)


def plan_diff(old, new, path="", out=None, cap=300):
    out = [] if out is None else out
    if len(out) >= cap:
        return out
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            if k == "provenance":
                continue
            if k not in old:
                out.append({"path": f"{path}/{k}", "old": None, "new": new[k]})
            elif k not in new:
                out.append({"path": f"{path}/{k}", "old": old[k], "new": None})
            else:
                plan_diff(old[k], new[k], f"{path}/{k}", out, cap)
    elif isinstance(old, list) and isinstance(new, list):
        for i in range(max(len(old), len(new))):
            if i >= len(old):
                out.append({"path": f"{path}/{i}", "old": None, "new": new[i]})
            elif i >= len(new):
                out.append({"path": f"{path}/{i}", "old": old[i], "new": None})
            else:
                plan_diff(old[i], new[i], f"{path}/{i}", out, cap)
    elif old != new:
        out.append({"path": path or "/", "old": old, "new": new})
    return out


def save_plan(d, job, name, plan, from_ref=None, words=""):
    if not NAME_RE.match(name or ""):
        raise StudioError("a plan name is letters, digits, dash and underscore", 400)
    validate_plan(plan)
    dest = d / "plans" / f"{name}.json"
    if dest.exists():
        raise StudioError(f"plans/{name}.json exists: a saved plan is never overwritten; choose another name", 409)
    prov = {"author": "owner", "at": now_iso(), "ui_version": UI_VERSION, "words": str(words or "")}
    if from_ref:
        src = resolve_plan(d, from_ref)
        old = read_json(src) or {}
        prov["from"] = rel(src); prov["from_sha256"] = sha256_file(src)
        prov["changes"] = plan_diff(old, plan)
    else:
        prov["from"] = None; prov["changes"] = []
    plan = dict(plan); plan["provenance"] = prov
    write_json(dest, plan)
    log(f"{d.name}: plan {name} saved ({len(prov['changes'])} changes from {prov['from']})")
    return {"name": name, "ref": f"job:{name}", "path": rel(dest), "sha256": sha256_file(dest), "changes": prov["changes"]}


def prep_summary(job):
    p = read_json(prep_dir(job) / "prep.json")
    if not p:
        return None
    frames = []
    for i, r in enumerate(p.get("frames", [])):
        frames.append({"i": i, "method": r.get("method"), "trusted": r.get("trusted"), "inliers": r.get("inliers"), "matches": r.get("matches"),
                       "residual_px": r.get("residual_px", r.get("rmse")), "cc": r.get("cc"), "scale_to_canvas": r.get("scale_to_canvas"),
                       "lock": r.get("lock"), "depth_blend": bool(r.get("depth_blend"))})
    return {"date": p.get("date"), "long": p.get("long"), "reference": p.get("reference"), "reference_size": p.get("reference_size"),
            "crop": p.get("crop"), "canvas": p.get("canvas"), "cuts": p.get("cuts"), "bg_depth": p.get("bg_depth"), "min_inliers": p.get("min_inliers"),
            "ecc_refine": p.get("ecc_refine"), "ref_requested": p.get("ref_requested"), "lock_window": p.get("lock_window"),
            "depth_maps": sorted(q.name for q in prep_dir(job).glob("depth_k*.npy")), "frames": frames, "n": len(frames),
            "sources": [{"name": Path(s["source"]).name, "sha256": s["sha256"], "native": s.get("native"), "scaled": s.get("scaled")} for s in p.get("sources", [])]}


def readers_summary(job):
    r = read_json(prep_dir(job) / "readers" / "readers.json")
    return r


def stage_views(d, job):
    recs = [reconcile(d, r) for r in records(d)]
    by = {}
    for r in recs:
        by.setdefault(r["stage"], []).append(r)
    root, seq = job_root(job), job["seq"]
    cands = candidates(d, job)
    full = [c for c in cands if c["kind"] == "full"]
    drafts = [c for c in cands if c["kind"] == "draft"]
    reqs = requests_of(d)
    rs = rounds(d)
    pl = plans_of(d)
    prep = prep_summary(job)
    views = []
    latest_started = {}
    for s in FLOWS[job["flow"]]["stages"]:
        name = s["name"]
        hist = by.get(name, [])
        latest = hist[-1] if hist else None
        v = {"name": name, "title": s["title"], "kind": s["kind"], "optional": s["optional"], "what": s["what"], "backend": s.get("backend"),
             "knobs": s["knobs"], "state": "none", "detail": "", "wall_s": None, "thumb": None, "latest": latest["id"] if latest else None,
             "history": [{"id": r["id"], "state": r["state"], "started": r["started"], "wall_s": r.get("wall_s"), "reason": r.get("reason")} for r in hist],
             "stale": False, "generated": False, "progress": None, "reason": None}
        if latest:
            v["state"] = latest["state"]; v["wall_s"] = latest.get("wall_s"); v["reason"] = latest.get("reason")
            v["unchanged_from"] = latest.get("unchanged_from")
            v["latest_knobs"] = latest.get("knobs") or {}
            if latest["state"] == "running":
                v["progress"] = progress_of(d / "stages" / latest["id"])
            latest_started[name] = latest["started"]
        if name == "import":
            v["state"] = "done"; v["detail"] = f"{len(job['inputs'])} stills" + (" (adopted)" if job.get("adopted") else "")
            v["thumb"] = f"/api/jobs/{job['id']}/thumb/still/0" if prep else (f"/api/jobs/{job['id']}/thumb/raw/0" if job["inputs"] else None)
        elif name == "registration":
            if prep:
                if not latest:
                    v["state"] = "done"; v["detail"] = "adopted"
                regs = [f"k{f['i']} {f['method']}" + (f" {f['inliers']} inl." if f.get("inliers") else "") for f in prep["frames"][1:]]
                v["detail"] = "; ".join(regs)[:160] + f" · {prep['canvas'][0]}×{prep['canvas'][1]}"
                v["thumb"] = f"/api/jobs/{job['id']}/thumb/still/0"
            elif not latest:
                v["state"] = "none"; v["detail"] = "not run"
        elif name == "readers":
            rd = readers_summary(job)
            if rd and not latest:
                v["state"] = "done"; v["detail"] = "adopted"
            if rd:
                pairs = rd.get("pairs") or []
                v["detail"] = (f"Lab>14 " + ", ".join(f"{p.get('lab_above_14', 0):.1%}" for p in pairs)) if pairs else f"{len(rd.get('stills', []))} stills read"
            elif not latest:
                v["state"] = "none"; v["detail"] = "optional, not run"
        elif name == "plan":
            v["state"] = "saved" if pl else "none"; v["detail"] = f"{len(pl)} saved in this job; {len(frozen_plans())} frozen" if pl else "none saved; frozen plans available"
        elif name == "render":
            unj = [c["name"] for c in full if c["unjudged"]]
            v["detail"] = f"{len(full)} full, {len(drafts)} drafts" + (f"; unjudged: {', '.join(unj)}" if unj else "")
            if latest and latest["state"] in ("failed", "refused", "lost", "cancelled") and (full or drafts):
                v["last_attempt"] = f"{latest['state']}: {(latest.get('knobs') or {}).get('name', latest['id'])}"
                v["detail"] += f" · last attempt {v['last_attempt']}"
                v["state"] = "done"                                  # the tile says what the stage holds; the attempt is beside it
            if not latest and full:
                v["state"] = "done"
            pick = (full or drafts)
            if pick:
                last = sorted(pick, key=lambda c: c["mtime"])[-1]
                v["thumb"] = f"/api/jobs/{job['id']}/thumb/render/{last['kind']}/{last['name']}"
                v["generated"] = any((c.get("generated_share") or 0) > 0 for c in full)
        elif name == "skeptic":
            sk = [r for r in reqs if r["kind"] == "skeptic"]
            if sk:
                last = sk[-1]
                v["state"] = "answered" if last["answered"] else "waiting"
                v["detail"] = f"{last['name']} · {last['age_s']} s old" if not last["answered"] else f"{last['name']} answered"
                v["wall_s"] = None
            else:
                v["detail"] = "no request yet"
            v["verdicts"] = verdicts(d)
        elif name == "page":
            page = root / "index.html"
            if page.exists():
                if not latest:
                    v["state"] = "done"
                v["detail"] = f"md5 {md5_file(page)[:8]}… · round {rs[-1]['n'] if rs else '—'}"
                v["page"] = f"/api/jobs/{job['id']}/file/index.html"
            elif not latest:
                v["detail"] = "not built"
        elif name == "grades":
            if rs:
                last = rs[-1]
                v["state"] = "graded" if last.get("grade") else ("ungraded by his word" if last.get("ungraded_by_his_word") else "ungraded")
                v["detail"] = f"round {last['n']}: " + (last["grade"]["text"][:120] if last.get("grade") else v["state"])
            else:
                v["detail"] = "no round yet"
        views.append(v)
    # stale: an earlier stage's latest record started after this stage's latest record
    for i, v in enumerate(views):
        if v["state"] not in ("done",) or not v["latest"]:
            continue
        mine = latest_started.get(v["name"])
        for u in views[:i]:
            if u["kind"] == "script" and latest_started.get(u["name"], "") > (mine or "") and by.get(u["name"], [{}])[-1].get("state") == "done":
                v["stale"] = True; v["stale_after"] = u["name"]
    return views


def job_view(d, job):
    cands = candidates(d, job)
    for c in cands:
        c.pop("dir", None)
    return {"job": job, "stages": stage_views(d, job), "candidates": cands, "plans": plans_of(d), "frozen_plans": frozen_plans(),
            "requests": requests_of(d), "rounds": rounds(d), "prep": prep_summary(job), "readers": readers_summary(job),
            "page": {"exists": (job_root(job) / "index.html").exists(), "md5": md5_file(job_root(job) / "index.html") if (job_root(job) / "index.html").exists() else None,
                     "url": f"/api/jobs/{job['id']}/file/index.html"},
            "owner_frames": [read_json(f) for f in sorted((d / "owner_frames").glob("*.json"))],
            "script_flags": SCRIPT_FLAGS}


def job_row(d):
    job = read_json(d / "job.json") or {}
    if not job:
        return None
    recs = records(d)
    running = [r for r in recs if r["state"] == "running"]
    cands = candidates(d, job)
    full = [c for c in cands if c["kind"] == "full"]
    rs = rounds(d)
    last_render = next((r for r in reversed(recs) if r["stage"] == "render"), None)
    last_state = last_render["state"] if last_render else ("done" if full else "none")
    if full and last_state in ("failed", "refused", "lost", "cancelled"):
        last_state = "done"
    return {"id": job["id"], "flow": job["flow"], "seq": job["seq"], "created": job["created"], "adopted": job.get("adopted", False), "root": job["root"],
            "source": Path(job["source_folder"]).name if job.get("source_folder") else ("adopted: " + Path(job.get("adopted_from", "")).name if job.get("adopted") else None),
            "stills": len(job.get("inputs", [])), "candidates": len(full), "unjudged": sum(1 for c in full if c["unjudged"]),
            "round": rs[-1]["n"] if rs else 0, "graded": bool(rs and rs[-1].get("grade")), "ungraded_by_his_word": bool(rs and rs[-1].get("ungraded_by_his_word")),
            "last_render": last_state, "last_attempt": last_render["state"] if last_render and last_render["state"] != last_state else None,
            "running": [r["id"] for r in running]}


def write_request(d, job, kind, body):
    if kind not in ("skeptic", "plan", "reading", "director", "keyframe"):
        raise StudioError("a request kind is skeptic, plan, reading, director or keyframe", 400)
    names = body.get("candidates") or [c["name"] for c in candidates(d, job) if c["kind"] == "full"]
    cands = candidates(d, job)
    chosen = []
    for n in names:
        c = next((c for c in cands if c["name"] == n and c["kind"] == "full"), None)
        if not c:
            raise StudioError(f"no full render {n}", 404)
        chosen.append({"name": n, "path": c["path"], "md5_mp4": c["md5_mp4"], "frames": c["frames"], "canvas": c["canvas"], "plan_sha256": c["plan_sha256"]})
    (d / "requests").mkdir(exist_ok=True)
    fname = f"{kind}_{stamp()}.json"
    req = {"kind": kind, "at": now_iso(), "job": job["id"], "job_dir": rel(d), "root": job["root"], "seq": job["seq"], "brief": str(body.get("brief", "")),
           "candidates": chosen, "crops": body.get("crops") or [], "owner_frames": [read_json(f) for f in sorted((d / "owner_frames").glob("*.json"))],
           "answer": {"file": f"answers/{fname}", "shape": {"at": "<iso>", "candidates": {"<name>": {"verdict": "READY | READY WITH A NOTE | NOT READY", "judged_md5": "<the md5_mp4 judged>", "note": "<one line>"}},
                                                             "report": f"answers/{fname[:-5]}.md (the crops beside it)"}}}
    write_json(d / "requests" / fname, req)
    log(f"{d.name}: request {fname} ({len(chosen)} candidates)")
    return {"file": rel(d / "requests" / fname), "name": fname}


def save_grade(d, body):
    rs = rounds(d)
    if not rs:
        raise StudioError("no round yet: build the page first", 409)
    try:
        n = int(body.get("round") or rs[-1]["n"])
    except (TypeError, ValueError):
        raise StudioError("round is a number", 400)
    r = next((r for r in rs if r["n"] == n), None)
    if not r:
        raise StudioError(f"no round {n}", 404)
    if body.get("ungraded_by_his_word"):
        r["ungraded_by_his_word"] = {"at": now_iso(), "words": str(body.get("words", ""))}
    else:
        text = str(body.get("text", "")).strip()
        if not text:
            raise StudioError("the grade text is empty: his words, verbatim", 400)
        r["grade"] = {"text": text, "at": now_iso(), "page_md5": r["page_md5"]}
    write_json(d / "rounds" / str(n) / "round.json", r)
    log(f"{d.name}: round {n} {'graded' if r.get('grade') else 'marked ungraded by his word'}")
    return r


def mark_frame(d, job, body):
    kind, name, i = body.get("kind", "full"), body.get("name"), body.get("frame")
    c = candidate(d, job, kind, name)
    try:
        i = int(i)
    except (TypeError, ValueError):
        raise StudioError("frame is a number", 400)
    if i < 0 or (c.get("frames") and i >= int(c["frames"])):
        raise StudioError(f"frame {i} is outside 0..{int(c['frames']) - 1}", 400)
    (d / "owner_frames").mkdir(exist_ok=True)
    f = d / "owner_frames" / f"{kind}_{name}_f{i:04d}.json"
    obj = {"kind": kind, "name": name, "frame": i, "md5_mp4": c["md5_mp4"], "note": str(body.get("note", "")), "at": now_iso()}
    write_json(f, obj)
    return obj


# ------------------------------------------------------------------ pictures for the page (cv2 only here)

def jpeg_thumb(src, dest, long=160):
    import cv2
    im = cv2.imread(str(src))
    if im is None:
        raise StudioError(f"cannot read {rel(src)}", 500)
    h, w = im.shape[:2]
    s = long / max(h, w)
    if s < 1:
        im = cv2.resize(im, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(dest), im, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return dest


DECODE_LOCKS = {}


def frames_dir(d, c):
    """The render's JPEG frames: its own frames/ when the script wrote it, else a decode of loop.mp4 cached by the mp4's md5."""
    own = c["dir"] / "frames"
    if (own / "f0000.jpg").exists():
        return own
    cache = d / "cache" / "frames" / f"{c['kind']}_{c['name']}_{(c['md5_mp4'] or 'x')[:8]}"
    if (cache / "done").exists():
        return cache
    lock = DECODE_LOCKS.setdefault(str(cache), threading.Lock())
    with lock:
        if (cache / "done").exists():
            return cache
        import cv2
        cache.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(c["dir"] / "loop.mp4"))
        i = 0
        while True:
            ok, f = cap.read()
            if not ok:
                break
            cv2.imwrite(str(cache / f"f{i:04d}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 90])
            i += 1
        (cache / "done").write_text(str(i))
        log(f"{d.name}: decoded {i} frames of {c['kind']}/{c['name']} into the cache")
    return cache


def thumb_path(d, job, what, a, b=None):
    cache = d / "cache" / "thumbs"
    if what == "still":
        i = int(a); src = prep_dir(job) / f"k{i}.png"
        if not src.exists():
            raise StudioError(f"no k{i}.png", 404)
        dest = cache / f"still_{i}_{int(src.stat().st_mtime)}.jpg"
    elif what == "raw":
        i = int(a)
        if i < 0 or i >= len(job["inputs"]):
            raise StudioError("no such still", 404)
        src = Path(job["inputs"][i].get("link") and ROOT / job["inputs"][i]["link"] or job["inputs"][i]["path"])
        if not src.exists():
            raise StudioError("the original is not reachable", 404)
        dest = cache / f"raw_{i}_{job['inputs'][i]['sha256'][:8]}.jpg"
    elif what == "render":
        c = candidate(d, job, a, b)
        fd = frames_dir(d, c)
        src = fd / "f0000.jpg"
        if not src.exists():
            raise StudioError("no frame 0", 404)
        dest = cache / f"render_{c['kind']}_{c['name']}_{(c['md5_mp4'] or 'x')[:8]}.jpg"
    else:
        raise StudioError("a thumb is still/<i>, raw/<i> or render/<kind>/<name>", 404)
    if not dest.exists():
        jpeg_thumb(src, dest, 192)
    return dest


def render_view(d, job, kind, name):
    c = candidate(d, job, kind, name)
    m = read_json(c["dir"] / "measure.json") or {}
    rows = read_json(c["dir"] / "frames.json") or []
    plan = read_json(c["dir"] / "plan.json") or {}
    tags = []
    for i, r in enumerate(rows):
        g = r.get("generated", "")
        if g.startswith("none (photo)"):
            tag = "photo"
        elif g.startswith("none (blend + motion blur)"):
            tag = "snap"
        elif g.startswith("none (blend"):
            tag = "blend"
        elif g.startswith("none (rewind"):
            tag = "rewind"
        elif g.startswith("none"):
            tag = g[6:-1] if g.endswith(")") else g[5:]
        else:
            tag = "generated"
        tags.append({"i": i, "tag": tag, "t": r.get("t"), "key": r.get("key"), "step": r.get("step"), "from": r.get("from"), "to": r.get("to"),
                     "method": r.get("method"), "dexp": r.get("dexp", r.get("dexp_rest")), "generated": not g.startswith("none")})
    fd = frames_dir(d, c) if (c["dir"] / "loop.mp4").exists() else None
    nf = len(list(fd.glob("f*.jpg"))) if fd else 0
    own = {k: v for k, v in c.items() if k != "dir"}
    own["measure"] = m
    own["frames_tags"] = tags
    own["frames_available"] = nf
    own["plan"] = plan
    own["frame_url"] = f"/api/jobs/{job['id']}/render/{kind}/{name}/frame/"
    own["mp4_url"] = f"/api/jobs/{job['id']}/file/{Path(c['path']).relative_to(job['root']) if c['path'].startswith(job['root']) else c['path']}/loop.mp4"
    own["owner_frames"] = [o for o in (read_json(f) for f in sorted((d / "owner_frames").glob("*.json"))) if o and o.get("name") == name and o.get("kind") == kind]
    return own


def models_view():
    items = [("reveal matcher", "models/MANIFEST.json", "matcher"), ("depth model", "models/DEPTH_MANIFEST.json", "model"),
             ("RIFE", "benchmarks/runs/2026-10-21/rife/RIFE_MANIFEST.json", "model"), ("faces (YuNet)", "benchmarks/runs/2026-10-18/face/FACE_MANIFEST.json", "model")]
    out = []
    for name, p, key in items:
        m = read_json(ROOT / p)
        out.append({"name": name, "manifest": p, "ready": m is not None, "version": (m or {}).get(key) or (m or {}).get("model") or None,
                    "verified": (m or {}).get("verified") or (m or {}).get("date")})
    return out


def open_requests():
    rows = []
    for d in job_dirs():
        job = read_json(d / "job.json") or {}
        for r in requests_of(d):
            if not r["answered"]:
                rows.append({"job": job.get("id"), "job_dir": rel(d), **r})
    return sorted(rows, key=lambda r: -r["age_s"])


def build_page(d, job, body):
    full = [c for c in candidates(d, job) if c["kind"] == "full"]
    if not full:
        raise StudioError("no full render to put on a page", 409)
    def why(c):
        if c["verdict"] and c["verdict"]["verdict"] == "NOT READY":
            return "NOT READY" + (f": {c['verdict'].get('note')}" if c["verdict"].get("note") else "")
        return "unjudged: " + (c.get("unjudged_reason") or "")
    bad = [c for c in full if c["unjudged"] or (c["verdict"] and c["verdict"]["verdict"] == "NOT READY")]
    override = bool(body.get("override"))
    knobs = {k: str(body.get(k) or "") for k in ("title", "intro", "footer")}
    knobs["notes"] = body.get("notes") or {}
    if bad and not override:
        raise StudioError("the page is refused: " + "; ".join(f"{c['name']} ({why(c)})" for c in bad)
                          + ". Request the skeptic, or override (the page prints the override).", 409, {"refused": [c["name"] for c in bad]})
    if bad:
        text = "Override: built on his word with " + ", ".join(f"{c['name']} ({why(c)})" for c in bad) + f" ({now_iso()})."
        knobs["footer"] = (knobs["footer"] + " " + text).strip()
        knobs["override"] = text
    return start_stage(d, job, stage_def(job["flow"], "page"), knobs)


MIME = {".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif", ".mp4": "video/mp4", ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
        ".npy": "application/octet-stream", ".svg": "image/svg+xml"}
PORT = DEFAULT_PORT
PAGE = ""


class Handler(BaseHTTPRequestHandler):
    server_version = "studio/A1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode()
        elif isinstance(body, str):
            data = body.encode()
        else:
            data = body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _err(self, code, msg, extra=None):
        self._send(code, {"error": msg, **(extra or {})})

    def _host_ok(self):
        host = (self.headers.get("Host") or "").strip()
        return host in (f"127.0.0.1:{PORT}", f"localhost:{PORT}", "127.0.0.1", "localhost")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > BODY_CAP:
            raise StudioError("the body is above 2 MB", 413)
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise StudioError("POST bodies are application/json (a cross-site form cannot send that)", 415)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        try:
            obj = json.loads(raw)
        except ValueError as e:
            raise StudioError(f"bad JSON: {e}", 400)
        if not isinstance(obj, dict):
            raise StudioError("the body is a JSON object", 400)
        return obj

    def _file(self, p, cacheable=False):
        p = Path(p)
        if not p.is_file():
            return self._err(404, "no such file")
        ctype = MIME.get(p.suffix.lower(), "application/octet-stream")
        size = p.stat().st_size
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        code = 200
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            try:
                start = int(a) if a else max(0, size - int(b))
                end = int(b) if (b and a) else size - 1
            except ValueError:
                return self._err(416, "bad range")
            if start > end or start >= size:
                return self._err(416, "range out of file", {"size": size})
            end = min(end, size - 1)
            code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "private, max-age=3600" if cacheable else "no-store")   # a thumbnail's name carries its md5 or mtime
        self.send_header("X-Content-Type-Options", "nosniff")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(p, "rb") as f:
            f.seek(start)
            left = length
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def _safe_file(self, d, job, relpath):
        if ".." in relpath.split("/") or relpath.startswith("/"):
            raise StudioError("forbidden", 403)
        for base in (job_root(job), d):
            p = (base / relpath)
            if p.exists() and inside(p, base):
                return p
        raise StudioError("no such file", 404)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        try:
            if not self._host_ok():
                return self._err(403, "the studio answers 127.0.0.1 only")
            path = self.path.split("?", 1)[0]
            if path == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if path == "/favicon.ico":
                return self._send(204, b"", "image/x-icon")
            if path == "/api/registry":
                return self._send(200, {"flows": FLOWS, "stage_order": STAGE_ORDER, "hints": HINTS, "methods": METHODS, "eases": EASES, "effects": EFFECTS,
                                        "plan_keys": PLAN_KEYS, "verdicts": VERDICTS, "ui_version": UI_VERSION, "script_flags": SCRIPT_FLAGS,
                                        "frozen_plans": frozen_plans(), "runs_date": RUNS_DATE, "port": PORT})
            if path == "/api/jobs":
                return self._send(200, [r for r in (job_row(d) for d in job_dirs()) if r])
            if path == "/api/requests":
                return self._send(200, open_requests())
            if path == "/api/models":
                return self._send(200, models_view())
            m = re.match(r"^/api/plans/frozen/([^/]+)$", path)
            if m:
                p = resolve_plan(None, f"frozen:{m.group(1)}")
                return self._send(200, read_json(p))
            m = re.match(r"^/api/jobs/([^/]+)(/.*)?$", path)
            if not m:
                return self._err(404, "no such route")
            d, job = load_job(m.group(1))
            sub = m.group(2) or ""
            if sub == "":
                return self._send(200, job_view(d, job))
            m2 = re.match(r"^/stages/([^/]+)$", sub)
            if m2:
                rd = record_dir(d, m2.group(1))
                return self._send(200, record_view(d, read_json(rd / "stage.json")))
            m2 = re.match(r"^/file/(.+)$", sub)
            if m2:
                return self._file(self._safe_file(d, job, m2.group(1)))
            m2 = re.match(r"^/thumb/(still|raw)/(\d+)$", sub)
            if m2:
                return self._file(thumb_path(d, job, m2.group(1), m2.group(2)), cacheable=True)
            m2 = re.match(r"^/thumb/render/(full|draft)/([^/]+)$", sub)
            if m2:
                return self._file(thumb_path(d, job, "render", m2.group(1), m2.group(2)), cacheable=True)
            m2 = re.match(r"^/render/(full|draft)/([^/]+)$", sub)
            if m2:
                return self._send(200, render_view(d, job, m2.group(1), m2.group(2)))
            m2 = re.match(r"^/render/(full|draft)/([^/]+)/frame/(\d+)$", sub)
            if m2:
                c = candidate(d, job, m2.group(1), m2.group(2))
                fd = frames_dir(d, c)
                return self._file(fd / f"f{int(m2.group(3)):04d}.jpg", cacheable=True)
            m2 = re.match(r"^/plans/([^/]+)$", sub)
            if m2:
                return self._send(200, read_json(resolve_plan(d, f"job:{m2.group(1)}")))
            return self._err(404, "no such route")
        except StudioError as e:
            return self._err(e.code, str(e), e.extra)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # the reason reaches the page, never a silent 500
            log(f"GET {self.path}: {type(e).__name__}: {e}")
            return self._err(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        try:
            if not self._host_ok():
                return self._err(403, "the studio answers 127.0.0.1 only")
            path = self.path.split("?", 1)[0]
            body = self._body()
            if path == "/api/jobs":
                job = create_job(body.get("flow", "loop"), folder=body.get("folder"), adopt=body.get("adopt"), seq=body.get("seq"))
                return self._send(201, {"id": job["id"], "job": job})
            m = re.match(r"^/api/jobs/([^/]+)(/.*)$", path)
            if not m:
                return self._err(404, "no such route")
            d, job = load_job(m.group(1))
            sub = m.group(2)
            m2 = re.match(r"^/stages/([^/]+)/run$", sub)
            if m2:
                stage = stage_def(job["flow"], m2.group(1))
                if stage["name"] == "page":
                    raise StudioError("the page runs through POST /api/jobs/<id>/page (the review gate), not through the stage runner", 409)
                rec = start_stage(d, job, stage, body.get("knobs") or {})
                return self._send(202, {"record": rec["id"], "state": rec["state"], "argv": rec["argv"]})
            m2 = re.match(r"^/stages/([^/]+)/cancel$", sub)
            if m2:
                return self._send(200, cancel(d, m2.group(1)))
            if sub == "/plans":
                return self._send(201, save_plan(d, job, body.get("name"), body.get("plan"), body.get("from"), body.get("words", "")))
            m2 = re.match(r"^/requests/([a-z]+)$", sub)
            if m2:
                return self._send(201, write_request(d, job, m2.group(1), body))
            if sub == "/page":
                rec = build_page(d, job, body)
                return self._send(202, {"record": rec["id"], "state": rec["state"], "override": rec["knobs"].get("override")})
            if sub == "/picks":
                return self._send(200, save_grade(d, body))
            if sub == "/frames/mark":
                return self._send(201, mark_frame(d, job, body))
            return self._err(404, "no such route")
        except StudioError as e:
            return self._err(e.code, str(e), e.extra)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            log(f"POST {self.path}: {type(e).__name__}: {e}")
            return self._err(500, f"{type(e).__name__}: {e}")


# ------------------------------------------------------------------ main

def cmd_requests():
    rows = open_requests()
    if not rows:
        print("no open requests")
        return
    for r in rows:
        age = r["age_s"]
        age_t = f"{age // 3600} h {age % 3600 // 60} min" if age >= 3600 else f"{age // 60} min" if age >= 60 else f"{age} s"
        print(f"{age_t:>12}  {r['job']}  {r['file']}  {r['kind']}: {r['brief'][:90]}" + (f"  [{', '.join(r['candidates'])}]" if r["candidates"] else ""))
    print(f"{len(rows)} open request(s); the oldest {rows[0]['age_s'] // 60} min")


def take_lock(port, second):
    """One server per tree: the lock file names the port and pid of the one that holds it (two servers would reconcile the
    same record twice); `--second` lets a review run another one knowingly."""
    import fcntl
    RUNS.mkdir(parents=True, exist_ok=True)
    lock = RUNS / "studio.lock"
    fh = open(lock, "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.seek(0); who = fh.read().strip()
        if not second:
            sys.exit(f"another studio holds {rel(lock)} ({who}); stop it, or pass --second for a review server")
        log(f"a second server beside {who} (--second): a record can be reconciled by both")
        return fh
    fh.seek(0); fh.truncate(); fh.write(f"port {port} pid {os.getpid()} since {now_iso()}\n"); fh.flush()
    return fh


def main():
    global PORT, RUNS_DATE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="serve", choices=["serve", "requests"])
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--runs-date", default=RUNS_DATE, help="the benchmarks/runs/<date>/studio/ folder new jobs are made in (default: today)")
    ap.add_argument("--second", action="store_true", help="allow a second server on this tree (a review); two servers may reconcile the same record")
    a = ap.parse_args()
    RUNS_DATE = a.runs_date
    if a.cmd == "requests":
        return cmd_requests()
    PORT = a.port
    lock_fh = take_lock(a.port, a.second)
    probe_script_flags()
    reconcile_all()
    httpd = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{a.port}/"
    log(f"{UI_VERSION}: serving {url} (jobs under {rel(studio_dir())}; {len(job_dirs())} job(s) found)")
    if not a.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        running = [(rid, p.pid) for rid, p in PROCS.items()]
        log(f"stopped; {len(running)} child process(es) keep running and are reconciled at the next start" + (f": {running}" if running else ""))




# ------------------------------------------------------------------ the page (one embedded string; DESIGN.md's tokens; no framework)

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Reveal studio</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--ground:#141618;--panel:#1c1f22;--raised:#24282c;--line:#30353a;--line-strong:#454b52;--text:#e8e8e6;--muted:#9aa1a8;--faint:#8a9198;
--amber:#e0a65a;--amber-deep:#c78a3b;--amber-ink:#1a1200;--ok:#5cc48a;--failed:#e8706a;--info:#6aa9f0;--gen:#b48ef0;--pa:#6aa9f0;--pb:#f0a06a;
--sans:system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;--mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--ground);color:var(--text);font:400 0.875rem/1.45 var(--sans);caret-color:var(--amber);scrollbar-width:thin;scrollbar-color:var(--line) transparent;text-wrap:pretty}
::selection{background:rgba(224,166,90,.3);color:var(--text)}
:focus-visible{outline:2px solid var(--amber);outline-offset:2px}
a{color:var(--info)}
h1{font:600 1.25rem/1.25 var(--sans);margin:0}
h2{font:600 1rem/1.3 var(--sans);margin:0}
h3{font:600 0.875rem/1.3 var(--sans);margin:0 0 8px}
.data,code,.num,td.num{font-family:var(--mono);font-size:0.8125rem;line-height:1.4;font-variant-numeric:tabular-nums}
.label{font:500 0.75rem/1.3 var(--sans);letter-spacing:.01em}
.muted{color:var(--muted)}.faint{color:var(--faint)}
.chip{display:inline-block;background:var(--raised);color:var(--muted);font:500 0.75rem/1.3 var(--sans);letter-spacing:.01em;padding:1px 6px;border-radius:3px;white-space:nowrap;vertical-align:baseline}
.chip.ok{color:var(--ok)}.chip.run{color:var(--amber)}.chip.bad{color:var(--failed)}.chip.info{color:var(--info)}.chip.gen{color:var(--gen)}
.btn{font:500 0.75rem/1.3 var(--sans);letter-spacing:.01em;border-radius:3px;padding:6px 14px;cursor:pointer;transition:background-color 150ms ease-out,border-color 150ms ease-out;background:var(--raised);color:var(--text);border:1px solid var(--line)}
.btn:hover{border-color:var(--line-strong)}
.btn.primary{background:var(--amber);color:var(--amber-ink);border-color:var(--amber)}
.btn.primary:hover{background:var(--amber-deep);border-color:var(--amber-deep)}
.btn.ghost{background:none;border-color:transparent;color:var(--muted);padding:2px 6px}
.btn.ghost:hover{color:var(--text)}
.btn[disabled]{opacity:.4;pointer-events:none}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:3px;overflow:hidden}
.seg button{font:500 0.75rem/1.3 var(--sans);background:var(--raised);color:var(--muted);border:0;border-right:1px solid var(--line);padding:5px 12px;cursor:pointer}
.seg button:last-child{border-right:0}.seg button:hover{color:var(--text)}
.seg button[aria-pressed="true"]{background:var(--ground);color:var(--text);box-shadow:inset 0 -2px 0 var(--amber)}
input,select,textarea{background:var(--ground);color:var(--text);border:1px solid var(--line);border-radius:3px;font:400 0.8125rem/1.4 var(--mono);padding:4px 8px}
input:focus,select:focus,textarea:focus{border-color:var(--amber);outline:none}
::placeholder{color:var(--faint);opacity:1}
input[type=checkbox]{width:14px;height:14px;accent-color:var(--amber)}
textarea{width:100%;min-height:120px;resize:vertical}
table{border-collapse:collapse;font-size:13px}
th{text-align:left;font:500 0.75rem/1.3 var(--sans);letter-spacing:.01em;color:var(--muted);background:var(--raised);padding:4px 8px;border-bottom:1px solid var(--line)}
td{padding:4px 8px;border-bottom:1px solid var(--line);vertical-align:top}
td.num{text-align:right}
tr:hover td{background:var(--raised)}
.unit{color:var(--muted);margin-left:4px}
.hint{display:inline-block;width:14px;height:14px;line-height:12px;text-align:center;border:1px solid var(--line-strong);border-radius:3px;color:var(--muted);font:500 10px/12px var(--sans);cursor:help;margin-left:4px;vertical-align:middle;background:none;padding:0}
.hint:hover,.hint:focus{color:var(--text);border-color:var(--amber)}
#pop{position:fixed;z-index:40;max-width:420px;background:var(--panel);border:1px solid var(--line-strong);border-radius:6px;padding:10px 12px;box-shadow:0 8px 24px rgba(0,0,0,.45);font-size:0.8125rem;line-height:1.45;display:none}
#pop .k{font-family:var(--mono);color:var(--text);margin-bottom:4px}
#pop .meta{color:var(--muted);margin-top:6px;font-size:0.75rem}
#pop .meta code{color:var(--text)}
.shell{display:grid;grid-template-columns:240px minmax(0,1fr) 320px;height:100vh}
@media (max-width:1280px){.shell{height:auto;grid-template-columns:240px minmax(0,1fr);grid-template-rows:100vh auto}.inspector{grid-column:1/-1;border-left:0;border-top:1px solid var(--line);height:auto}}
.rail{background:var(--panel);border-right:1px solid var(--line);padding:16px 0;overflow:auto}
.wordmark{padding:0 16px 12px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:8px}
.wordmark b{font:600 1rem/1.3 var(--sans)}
.rail section{padding:12px 0 8px;border-bottom:1px solid var(--line)}
.rail h2{padding:0 16px 6px;font-size:0.875rem;display:flex;align-items:center}
.rail ul{list-style:none;margin:0;padding:0}
.job{padding:8px 16px 8px 14px;border-left:2px solid transparent;cursor:pointer}
.job:hover{background:var(--raised)}
.job[aria-current="true"]{border-left-color:var(--amber);background:var(--raised)}
.job .name{font-weight:600;word-break:break-all}
.job .meta{color:var(--muted);font-size:0.75rem;margin:2px 0 4px}
.kv{display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding:3px 16px}
.rail .new{margin:8px 16px 0}
.work{padding:16px 24px 0;overflow:auto;min-width:0}
.jobhead{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
.stripwrap{margin:12px 0 0;padding:3px 3px 16px;border-bottom:1px solid var(--line)}
.strip{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:8px}
@media (max-width:1600px){.stage .ft .data{display:none}.stage .nm .hint{display:none}.thumb,.thumb img{height:72px}}
.stage{display:flex;flex-direction:column;min-width:0;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:6px;cursor:pointer;position:relative;transition:border-color 150ms ease-out;text-align:left;color:var(--text);font:inherit}
.stage:hover{border-color:var(--line-strong)}
.stage[aria-selected="true"]{outline:2px solid var(--amber);outline-offset:-1px;border-color:var(--amber)}
.stage.failed{border-color:var(--failed)}
.stage.running{border-color:var(--amber)}
.thumb{height:96px;width:100%;background:var(--ground);display:flex;align-items:center;justify-content:center;overflow:hidden}
.thumb img{height:96px;width:auto;max-width:100%;object-fit:contain;display:block}
.thumb.empty{color:var(--muted);font:500 0.75rem/1.3 var(--sans)}
.stage .nm{display:flex;justify-content:space-between;align-items:baseline;margin-top:6px;gap:4px;min-width:0}
.stage .dt{color:var(--muted);font:400 0.75rem/1.4 var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stage .ft{display:flex;justify-content:space-between;align-items:baseline;margin-top:4px;gap:4px;min-width:0}
.stage .ft .chip{overflow:hidden;text-overflow:ellipsis;max-width:100%}
.stage .tick{position:absolute;top:6px;right:6px;width:10px;height:10px;background:var(--gen);border-radius:2px}
.panel{padding:16px 0 24px}
.panel p.muted,.panel .box p,.panel blockquote{max-width:62ch}
.panel .head .muted{max-width:62ch;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.panel .head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.panel .head .acts{margin-left:auto;display:flex;gap:8px;align-items:center}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.box{border:1px solid var(--line);border-radius:3px;padding:12px;background:var(--panel)}
.inspector{background:var(--panel);border-left:1px solid var(--line);padding:16px;overflow:auto}
.inspector section{padding:0 0 12px;margin-bottom:12px;border-bottom:1px solid var(--line)}
.inspector h3{display:flex;align-items:center}
.knob{display:grid;grid-template-columns:1fr auto;gap:2px 8px;padding:6px 0;border-bottom:1px solid var(--line)}
.knob .key{font-family:var(--mono);font-size:0.8125rem}
.knob .key.changed{color:var(--amber);font-weight:600}
.knob .what{grid-column:1/-1;color:var(--muted);font-size:0.75rem}
.knob input,.knob select{width:160px}
.knob input[type=checkbox]{width:14px}
.knob .def{grid-column:1/-1;color:var(--faint);font-size:0.75rem;font-family:var(--mono)}
.log{background:var(--ground);border:1px solid var(--line);border-radius:3px;padding:8px;font-family:var(--mono);font-size:0.75rem;line-height:1.4;white-space:pre-wrap;word-break:break-all;max-height:200px;overflow:auto;color:var(--muted)}
.cmd{background:var(--ground);border:1px solid var(--line);border-radius:3px;padding:8px;font-family:var(--mono);font-size:0.75rem;word-break:break-all;color:var(--muted);max-width:80ch}
.inspector .log{max-width:80ch}
.stills{display:flex;gap:8px;flex-wrap:wrap}
.stills figure{margin:0;background:var(--panel);border:1px solid var(--line);padding:4px}
.stills img{height:160px;display:block}
.stills figcaption{font:500 0.75rem/1.3 var(--sans);color:var(--muted);padding:4px 2px 0}
.viewer{display:grid;grid-template-columns:minmax(0,1fr) 150px;gap:16px;margin-top:8px;align-items:start}
.refs{overflow:auto}
.frame{background:var(--ground);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;position:relative;height:calc(100vh - 760px);min-height:380px}
.frame img{max-height:100%;max-width:100%;display:block;flex-shrink:0}
.frame img.gen{outline:2px solid var(--gen);outline-offset:-2px}
.frame img.px{image-rendering:pixelated}
.frame .tag{position:absolute;left:8px;top:8px}
.frame .tag .chip{margin-right:4px}
.refs figure{margin:0 0 8px;border:1px solid var(--line);padding:4px;background:var(--panel)}
.refs img{width:100%;display:block}
.refs figcaption{font:500 0.75rem/1.3 var(--sans);padding:4px 2px 0}
.refs .a figcaption{color:var(--pa)}.refs .b figcaption{color:var(--pb)}
.axis{margin-top:12px}
.axis .ctl{display:flex;align-items:center;gap:12px;margin-bottom:6px;flex-wrap:wrap}
.axis input[type=range]{display:block;width:calc(100% - 34px);margin:0 0 0 32px;accent-color:var(--amber)}
.axis input[type=range]:focus-visible{outline:none}
.axis input[type=range]:focus-visible::-webkit-slider-thumb{outline:2px solid var(--amber);outline-offset:2px}
.axis svg{width:100%;height:auto;display:block}
.cands{display:flex;flex-wrap:wrap;gap:8px;padding-bottom:8px}
.cand{width:210px}
.cand{display:flex;flex-direction:column;min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:6px;cursor:pointer;text-align:left;color:var(--text);font:inherit}
.cand[aria-selected="true"]{outline:2px solid var(--amber);outline-offset:-1px}
.cand .thumb{height:72px}
.cand .thumb img{height:72px}
.cand .nm{display:flex;justify-content:space-between;align-items:baseline;margin-top:6px;gap:4px}
.cand .dt{color:var(--muted);font:400 0.75rem/1.4 var(--mono);font-variant-numeric:tabular-nums}
.msg{padding:8px 12px;border:1px solid var(--line);border-radius:3px;margin:8px 0;background:var(--panel)}
.msg.bad{border-color:var(--failed)}.msg.ok{border-color:var(--ok)}
.box .msg{border:0;padding:0;background:none}.box .msg.bad{color:var(--failed)}
.empty{color:var(--muted);padding:24px 0}
.kbd{font-family:var(--mono);font-size:0.75rem;color:var(--muted);border:1px solid var(--line);border-radius:3px;padding:0 4px}
.req{border:1px solid var(--line);border-radius:3px;padding:8px;margin-bottom:8px;background:var(--panel)}
.ro{opacity:.6}
</style>
</head>
<body>
<div class="shell">
<nav class="rail" aria-label="jobs, tasks and models">
  <div class="wordmark"><b>Reveal studio</b><span class="muted label" id="ver"></span><button class="hint" data-hint="region.rail" aria-label="what the rail shows">?</button></div>
  <section><h2>Jobs <button class="hint" data-hint="control.new_job" aria-label="about new jobs">?</button></h2>
    <ul id="jobs"></ul>
    <div class="new"><button class="btn" id="btnNew">new loop job…</button> <button class="btn ghost" id="btnAdopt">adopt a run folder…</button></div>
    <div id="newForm" style="display:none;padding:8px 16px 0">
      <div class="label muted">folder of JPGs <button class="hint" data-hint="control.new_job">?</button></div><input id="newFolder" style="width:100%" placeholder="/Users/…/angel-portrait">
      <div class="label muted" style="margin-top:6px">sequence name</div><input id="newSeq" style="width:100%" placeholder="angel">
      <div style="margin-top:6px"><button class="btn primary" id="newGo">create</button> <button class="btn ghost" id="newCancel">cancel</button></div>
      <div id="newErr" style="color:var(--failed);font-size:.75rem;margin-top:6px"></div>
    </div>
    <div id="adoptForm" style="display:none;padding:8px 16px 0">
      <div class="label muted">run folder under benchmarks/runs <button class="hint" data-hint="control.adopt">?</button></div><input id="adoptRoot" style="width:100%" placeholder="benchmarks/runs/2026-11-04/angel">
      <div class="label muted" style="margin-top:6px">sequence (the folder under in/)</div><input id="adoptSeq" style="width:100%" placeholder="angel">
      <div style="margin-top:6px"><button class="btn primary" id="adoptGo">adopt</button> <button class="btn ghost" id="adoptCancel">cancel</button></div>
      <div id="adoptErr" style="color:var(--failed);font-size:.75rem;margin-top:6px"></div>
    </div>
  </section>
  <section><h2>Running <button class="hint" data-hint="chip.running">?</button></h2><ul id="tasks"></ul></section>
  <section><h2>Requests <button class="hint" data-hint="chip.waiting">?</button></h2><ul id="reqs"></ul></section>
  <section><h2>Models</h2><ul id="models"></ul></section>
</nav>
<main class="work" id="work">
  <div class="jobhead"><h1 id="title">no job open</h1><span class="muted" id="subtitle"></span><button class="hint" data-hint="region.strip" aria-label="what the strip shows">?</button></div>
  <div class="stripwrap"><div class="strip" id="strip" role="tablist" aria-label="stages"></div></div>
  <div class="panel" id="panel"><div class="empty">Open a job in the rail, or make one from a folder of stills.</div></div>
</main>
<aside class="inspector" id="inspector" aria-label="inspector"><h3>Inspector <button class="hint" data-hint="region.inspector">?</button></h3><div class="muted">Select a stage.</div></aside>
</div>
<div id="pop" role="tooltip"></div>
<script>
'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const S={reg:null,jobs:[],jid:null,view:null,stage:null,cand:null,render:null,frame:0,playing:null,knobs:{},msg:null,mode:'fit',timer:null,planText:'',planFrom:'',editorDirty:false};
function fmtS(s){return s==null?'—':(s<60?s.toFixed(1)+' s':Math.floor(s/60)+' min '+Math.round(s%60)+' s');}
function fmtAge(s){return s>=3600?Math.floor(s/3600)+' h '+Math.floor(s%3600/60)+' min':s>=60?Math.floor(s/60)+' min':s+' s';}
function stateClass(st){return ({done:'ok',saved:'ok',graded:'ok',answered:'ok',running:'run',queued:'run',cancelling:'run',waiting:'run',failed:'bad',refused:'bad',lost:'bad',cancelled:'bad',ungraded:'info',stale:'info'})[st]||'';}
function hintBtn(key){return '<button class="hint" data-hint="'+esc(key)+'" aria-label="hint">?</button>';}
function chip(text,cls){const key='chip.'+String(text).replace(/ \(.*$|\d+\/\d+.*$| \d+ s old$/,'').trim();const has=S.reg&&S.reg.hints[key];return '<span class="chip '+(cls||'')+'"'+(has?' data-hint="'+esc(key)+'" tabindex="0"':'')+'>'+esc(text)+'</span>';}
async function api(path,body,method){const r=await fetch(path,body?{method:method||'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const t=await r.text();let j;try{j=JSON.parse(t)}catch(e){j={error:t.slice(0,200)}}if(!r.ok){const e=new Error(j.error||('HTTP '+r.status));e.extra=j;throw e;}return j;}
function setMsg(text,cls){S.msg={text,cls};const m=$('#msg');if(m){m.className='msg '+(cls||'');m.textContent=text;m.style.display=text?'':'none';}}
// hints: one popover, from the registry's table
const pop=$('#pop');
function showHint(btn){const key=btn.dataset.hint;const h=(S.reg&&S.reg.hints[key])||null;const stageKnob=btn.dataset.knob?JSON.parse(btn.dataset.knob):null;let html='';
 if(stageKnob){html='<div class="k">'+esc(stageKnob.key)+(stageKnob.flag?' <span class="muted">('+esc(stageKnob.flag)+')</span>':'')+'</div>'+esc(stageKnob.what)+'<div class="meta">default <code>'+esc(JSON.stringify(stageKnob.default))+'</code> · range '+(stageKnob.range?'<code>'+esc(JSON.stringify(stageKnob.range))+'</code>':'none stated by the script')+' · type '+esc(stageKnob.type)+'</div>';}
 else if(h){html='<div class="k">'+esc(key)+'</div>'+esc(h.what);const meta=[];if(h.default!==undefined)meta.push('default <code>'+esc(JSON.stringify(h.default))+'</code>');if(h.range)meta.push('range <code>'+esc(JSON.stringify(h.range))+'</code>');if(h.stage)meta.push('read by the '+esc(h.stage)+' stage');if(h.source)meta.push('from '+esc(h.source));if(meta.length)html+='<div class="meta">'+meta.join(' · ')+'</div>';}
 else html='<div class="k">'+esc(key)+'</div><span class="muted">no hint recorded for this key (a gap: add it to the hints table in studio.py)</span>';
 pop.innerHTML=html;pop.style.display='block';const r=btn.getBoundingClientRect();let x=r.left,y=r.bottom+6;if(x+430>innerWidth)x=innerWidth-430;if(y+pop.offsetHeight>innerHeight)y=r.top-pop.offsetHeight-6;pop.style.left=x+'px';pop.style.top=y+'px';}
function hideHint(){pop.style.display='none';}
document.addEventListener('mouseover',e=>{const b=e.target.closest('.hint,[data-hint]');if(b)showHint(b);});
document.addEventListener('mouseout',e=>{if(e.target.closest('.hint,[data-hint]'))hideHint();});
document.addEventListener('focusin',e=>{const b=e.target.closest('.hint,[data-hint]');if(b)showHint(b);});
document.addEventListener('focusout',e=>{if(e.target.closest('.hint,[data-hint]'))hideHint();});
document.addEventListener('click',e=>{const b=e.target.closest('.hint');if(b){e.preventDefault();showHint(b);}});
// the rail
async function loadJobs(){S.jobs=await api('/api/jobs');const ul=$('#jobs');const jsig=JSON.stringify(S.jobs)+'|'+S.jid;if(jsig!==S.jobsSig){S.jobsSig=jsig;const focusedJob=document.activeElement&&document.activeElement.closest('.job')?document.activeElement.dataset.id:null;ul.innerHTML=S.jobs.length?S.jobs.map(j=>'<li class="job" data-id="'+esc(j.id)+'" tabindex="0" aria-current="'+(j.id===S.jid)+'"><div class="name">'+esc(j.seq)+' <span class="muted">'+esc(j.source||j.flow)+'</span></div><div class="meta">'+esc(j.id)+'</div><div>'+chip(j.last_render,stateClass(j.last_render))+' '+(j.candidates?chip(j.candidates+' candidates'+(j.unjudged?', '+j.unjudged+' unjudged':''),j.unjudged?'info':''):'')+' '+(j.round?chip('round '+j.round+(j.graded?' graded':(j.ungraded_by_his_word?' ungraded by his word':' ungraded')),j.graded?'ok':'info'):'')+(j.adopted?' '+chip('adopted'):'')+'</div></li>').join(''):'<li class="muted" style="padding:4px 16px">no jobs yet</li>';
 ul.querySelectorAll('.job').forEach(li=>{li.onclick=()=>openJob(li.dataset.id);li.onkeydown=e=>{e.stopPropagation();if(e.key==='Enter')openJob(li.dataset.id);if(e.key==='ArrowDown'&&li.nextElementSibling)li.nextElementSibling.focus();if(e.key==='ArrowUp'&&li.previousElementSibling)li.previousElementSibling.focus();};});
 if(focusedJob){const li=ul.querySelector('.job[data-id="'+focusedJob+'"]');if(li)li.focus();}}
 const running=[];S.jobs.forEach(j=>j.running.forEach(r=>running.push({job:j.id,rec:r})));$('#tasks').innerHTML=running.length?running.map(r=>'<li class="kv"><span class="data">'+esc(r.rec)+'</span>'+chip('running','run')+'</li>').join(''):'<li class="kv muted">idle</li>';
 const reqs=await api('/api/requests');$('#reqs').innerHTML=reqs.length?reqs.map(r=>'<li class="kv"><span class="data" title="'+esc(r.file)+'">'+esc(r.name)+'</span>'+chip('waiting '+fmtAge(r.age_s),'run')+'</li>').join(''):'<li class="kv muted">none open</li>';}
async function loadModels(){const ms=await api('/api/models');$('#models').innerHTML=ms.map(m=>'<li class="kv"><span>'+esc(m.name)+'</span>'+chip(m.ready?'ready, offline':'missing',m.ready?'ok':'bad')+'</li>').join('');}
$('#btnNew').onclick=()=>{$('#newForm').style.display='';$('#adoptForm').style.display='none';$('#newFolder').focus();};
$('#newCancel').onclick=()=>{$('#newForm').style.display='none';};
$('#btnAdopt').onclick=()=>{$('#adoptForm').style.display='';$('#newForm').style.display='none';$('#adoptRoot').focus();};
$('#adoptCancel').onclick=()=>{$('#adoptForm').style.display='none';};
$('#newGo').onclick=async()=>{$('#newErr').textContent='';try{const r=await api('/api/jobs',{flow:'loop',folder:$('#newFolder').value,seq:$('#newSeq').value||undefined});$('#newForm').style.display='none';await loadJobs();openJob(r.id);}catch(e){$('#newErr').textContent=e.message;}};
$('#adoptGo').onclick=async()=>{$('#adoptErr').textContent='';try{const r=await api('/api/jobs',{flow:'loop',adopt:$('#adoptRoot').value,seq:$('#adoptSeq').value});$('#adoptForm').style.display='none';await loadJobs();openJob(r.id);}catch(e){$('#adoptErr').textContent=e.message;}};
function alertMsg(t){setMsg(t,'bad');if(!$('#msg')){$('#panel').insertAdjacentHTML('afterbegin','<div class="msg bad" id="msg">'+esc(t)+'</div>');}}
// the job
async function openJob(id,keep){if(!keep){S.jid=id;S.stage='render';S.cand=null;S.render=null;S.frame=0;S.msg=null;S.sig=null;stopPlay();}
 try{localStorage.setItem('studio_job',id)}catch(e){}
 S.view=await api('/api/jobs/'+encodeURIComponent(id));const v=S.view;$('#title').textContent=v.job.seq+' · '+v.job.flow;$('#subtitle').textContent=v.job.id+(v.job.adopted?' · adopted from '+v.job.root:'')+' · '+v.job.inputs.length+' stills';
 document.querySelectorAll('#jobs .job').forEach(li=>li.setAttribute('aria-current',li.dataset.id===id));
 renderStrip();if(!v.stages.find(s=>s.name===S.stage))S.stage='render';
 // a poll re-renders the panel and the inspector only when their data changed and nothing in them has the focus (typed text is never wiped)
 const st=stageOf(S.stage);const sig=JSON.stringify([st,v.candidates.length,v.requests.length,v.rounds.length,v.plans.length,v.page.md5]);
 const typing=el=>el&&document.activeElement&&el.contains(document.activeElement)&&document.activeElement.matches('input,textarea,select');
 if(!keep||(sig!==S.sig&&!typing($('#panel'))))renderPanel();
 if(!keep||(sig!==S.sig&&!typing($('#inspector'))))renderInspector();
 S.sig=sig;
 const busy=v.stages.some(s=>s.state==='running');schedulePoll(id,busy?1000:5000);}
function schedulePoll(id,ms){clearTimeout(S.timer);S.timer=setTimeout(async()=>{if(S.jid!==id)return;try{await openJob(id,true);await loadJobs();}catch(e){const t=$('#tasks');if(t)t.innerHTML='<li class="kv">'+chip('server unreachable, retrying','bad')+'</li>';schedulePoll(id,5000);}},ms);}
function renderStrip(){const v=S.view;const ssig=JSON.stringify(v.stages.map(s=>[s.name,s.state,s.stale,s.detail,s.wall_s,s.progress,s.thumb,s.generated,s.unchanged_from]))+'|'+S.stage;if(ssig===S.stripSig)return;S.stripSig=ssig;const focusedTile=document.activeElement&&document.activeElement.closest('.stage')?document.activeElement.dataset.stage:null;$('#strip').innerHTML=v.stages.map(s=>{const st=s.stale?'stale':s.state;const cls=['stage',(s.state==='failed'||s.state==='refused'||s.state==='lost')?'failed':'',s.state==='running'?'running':''].join(' ');
 const prog=s.progress?' '+s.progress.i+'/'+s.progress.n+' '+esc(s.progress.phase||''):(s.unchanged_from?' (unchanged)':'');
 return '<div class="'+cls+'" role="tab" tabindex="0" data-stage="'+esc(s.name)+'" aria-selected="'+(s.name===S.stage)+'">'+(s.generated?'<span class="tick" title="generated content"></span>':'')+'<div class="thumb'+(s.thumb?'':' empty')+'">'+(s.thumb?'<img src="'+esc(s.thumb)+'" alt="">':esc(s.title))+'</div><div class="nm"><span class="label">'+esc(s.title)+(s.optional?' <span class="muted">(optional)</span>':'')+'</span>'+hintBtn('stage.'+s.name)+'</div><div class="dt" title="'+esc(s.detail)+'">'+esc(s.detail||'')+'</div><div class="ft"><span class="data muted">'+(s.wall_s!=null?esc(fmtS(s.wall_s)):(s.state==='running'&&s.progress?'':'—'))+'</span>'+chip(st+prog,stateClass(st))+'</div></div>';}).join('');
 $('#strip').querySelectorAll('.stage').forEach(b=>{b.onclick=e=>{if(e.target.closest('.hint'))return;S.stage=b.dataset.stage;S.msg=null;renderStrip();renderPanel();renderInspector();};b.onkeydown=e=>{if(e.target.closest('.hint'))return;e.stopPropagation();if(e.key==='ArrowRight'&&b.nextElementSibling){b.nextElementSibling.focus();e.preventDefault();}if(e.key==='ArrowLeft'&&b.previousElementSibling){b.previousElementSibling.focus();e.preventDefault();}if(e.key==='Enter'||e.key===' '){b.click();e.preventDefault();}};});
 if(focusedTile){const b=$('#strip').querySelector('.stage[data-stage="'+focusedTile+'"]');if(b)b.focus();}}
function stageHint(name){const s=S.view.stages.find(x=>x.name===name);if(s&&S.reg)S.reg.hints['stage.'+name]={what:s.what,stage:name,source:s.backend||'the studio'};}
function stageOf(name){return S.view.stages.find(s=>s.name===name);}
function snapForms(root){const m={};if(!root)return m;root.querySelectorAll('input,textarea,select').forEach(el=>{const k=el.id||(el.className+'|'+(el.dataset.name||el.dataset.round||el.dataset.knob||el.value));if(el.type==='checkbox')m[k]=el.checked;else m[k]=el.value;});return m;}
function restoreForms(root,m){if(!root)return;root.querySelectorAll('input,textarea,select').forEach(el=>{const k=el.id||(el.className+'|'+(el.dataset.name||el.dataset.round||el.dataset.knob||el.value));if(!(k in m))return;if(el.type==='checkbox')el.checked=m[k];else if(el.type!=='range'&&m[k]!==undefined&&m[k]!=='')el.value=m[k];});}
function renderPanel(){const v=S.view;const s=stageOf(S.stage);v.stages.forEach(x=>stageHint(x.name));const p=$('#panel');const keep=S.panelStage===S.stage?snapForms(p):{};S.panelStage=S.stage;let h='<div class="head"><h2>'+esc(s.title)+' '+hintBtn('stage.'+s.name)+hintBtn('region.panel')+'</h2>'+chip(s.stale?'stale after '+s.stale_after:s.state,stateClass(s.stale?'stale':s.state))+(s.reason?' <span class="muted">'+esc(s.reason)+'</span>':'')+'<div class="acts" id="acts"></div></div><div class="msg" id="msg" style="display:none"></div>';
 if(s.name==='import')h+=panelImport();else if(s.name==='registration')h+=panelRegistration();else if(s.name==='readers')h+=panelReaders();else if(s.name==='plan')h+=panelPlan();else if(s.name==='render')h+=panelRender();else if(s.name==='skeptic')h+=panelSkeptic();else if(s.name==='page')h+=panelPage();else if(s.name==='grades')h+=panelGrades();
 p.innerHTML=h;restoreForms(p,keep);wirePanel();if(S.msg&&S.msg.text)setMsg(S.msg.text,S.msg.cls);}
function panelImport(){const v=S.view;return '<p class="muted">'+esc(stageOf('import').what)+'</p><table><tr><th>#</th><th>still</th><th>sha256</th><th>bytes</th><th>native</th></tr>'+v.job.inputs.map((i,k)=>'<tr><td class="num">'+k+'</td><td>'+esc(i.name)+'</td><td class="data">'+esc(i.sha256.slice(0,16))+'…</td><td class="num">'+i.bytes+'</td><td class="num">'+(i.native?i.native.join('×'):'—')+'</td></tr>').join('')+'</table><p class="muted">Read from '+esc(v.job.source_folder||v.job.adopted_from||'')+(v.job.adopted?'':', linked under raw/'+esc(v.job.seq)+'/ in capture order')+'. '+(v.job.adopted?'Adopted: the prep and the renders are read in place; the studio\'s records live in '+esc(v.job.id)+'.':'')+'</p>';}
function panelRegistration(){const v=S.view,pr=v.prep;let h='<p class="muted">'+esc(stageOf('registration').what)+'</p>';if(!pr)return h+'<div class="empty">Not run. Set the knobs in the inspector (the lock windows as x0,y0,x1,y1;… on the reference still) and run it.</div>';
 h+='<div class="stills">'+pr.frames.map(f=>'<figure><img src="/api/jobs/'+esc(v.job.id)+'/thumb/still/'+f.i+'" alt="k'+f.i+'"><figcaption>k'+f.i+' · '+esc(f.method)+(f.inliers?' · '+f.inliers+' inliers':'')+(f.cc?' · cc '+f.cc:'')+'</figcaption></figure>').join('')+'</div>';
 h+='<table style="margin-top:12px"><tr><th>still</th><th>method '+hintBtn('prep.method')+'</th><th>inliers '+hintBtn('prep.inliers')+'</th><th>matches</th><th>scale '+hintBtn('prep.scale_to_canvas')+'</th><th>lock shift (px) '+hintBtn('prep.lock')+'</th><th>windows: offset before the lock, correlation</th></tr>'+pr.frames.map(f=>'<tr><td>k'+f.i+'</td><td>'+esc(f.method)+'</td><td class="num">'+(f.inliers??'—')+'</td><td class="num">'+(f.matches??'—')+'</td><td class="num">'+(f.scale_to_canvas??'—')+'</td><td class="num">'+(f.lock?esc(f.lock.shift_px.join(', ')):'—')+'</td><td class="data">'+(f.lock?f.lock.windows.map((w,k)=>'['+w.join(',')+'] ('+f.lock.offsets_px[k].join(', ')+') r '+f.lock.corr[k]).join('<br>'):'—')+'</td></tr>').join('')+'</table>';
 h+='<p class="muted">Canvas: frame '+pr.reference+' ('+pr.reference_size.join('×')+'), the common crop ['+pr.crop.join(', ')+'] → '+pr.canvas.join('×')+' '+hintBtn('prep.canvas')+' · long edge '+pr.long+' · cuts ['+(pr.cuts||[]).join(', ')+'] · far-field gate '+pr.bg_depth+' · inlier floor '+pr.min_inliers+' · depth maps: '+(pr.depth_maps.length?pr.depth_maps.join(', '):'none')+' · lock windows: '+esc(pr.lock_window||'none')+'</p>';
 return h;}
function panelReaders(){const v=S.view,rd=v.readers;let h='<p class="muted">'+esc(stageOf('readers').what)+'</p>';if(stageOf('readers').stale)h+='<div class="msg">stale: the readers ran on the previous prep (moved to in/'+esc(v.job.seq)+'_prev_…); run them again.</div>';if(!v.script_flags.readers)h+='<div class="msg">loop_seq.py has no readers command yet (its --help does not list it): the stage waits for it.</div>';
 if(!rd)return h+'<div class="empty">Not run.</div>';
 h+='<table><tr><th>still</th><th>size</th><th>faces '+hintBtn('readers.faces')+'</th><th>grey mean</th><th>clipped high / low (px)</th><th>focus '+hintBtn('readers.laplacian_var')+'</th><th>depth min / mean / max</th></tr>'+(rd.stills||[]).map(s=>'<tr><td>'+esc(s.still)+'</td><td class="num">'+(s.size||[]).join('×')+'</td><td class="num">'+(s.faces||[]).length+'</td><td class="num">'+s.mean_level+'</td><td class="num">'+s.clipped_high_px+' / '+s.clipped_low_px+'</td><td class="num">'+s.laplacian_var+'</td><td class="num">'+(s.depth_stats?[s.depth_stats.min,s.depth_stats.mean,s.depth_stats.max].join(' / '):'—')+'</td></tr>').join('')+'</table>';
 h+='<table style="margin-top:12px"><tr><th>pair</th><th>Lab above 14 '+hintBtn('readers.lab_above_14')+'</th><th>Lab above 30</th></tr>'+(rd.pairs||[]).map(p=>'<tr><td>k'+p.a+' → k'+p.b+'</td><td class="num">'+(p.lab_above_14*100).toFixed(1)+'<span class="unit">%</span></td><td class="num">'+(p.lab_above_30*100).toFixed(1)+'<span class="unit">%</span></td></tr>').join('')+'</table>';
 h+='<div class="stills" style="margin-top:12px">'+(rd.stills||[]).map(s=>'<figure><img src="/api/jobs/'+esc(v.job.id)+'/file/in/'+esc(v.job.seq)+'/readers/'+esc((s.depth||'').replace('.npy','.jpg'))+'" alt="depth of '+esc(s.still)+'"><figcaption>depth of '+esc(s.still)+'</figcaption></figure>').join('')+'</div>';
 return h;}
function panelPlan(){const v=S.view;let h='<p class="muted">'+esc(stageOf('plan').what)+' '+hintBtn('control.save_plan')+'</p><div class="cols"><div><div class="label muted" style="margin-bottom:4px">start from</div><select id="planFrom"><option value="">— empty —</option>'+v.plans.map(p=>'<option value="'+esc(p.ref)+'"'+(S.planFrom===p.ref?' selected':'')+'>'+esc(p.ref)+' · '+esc(p.title.slice(0,60))+'</option>').join('')+v.frozen_plans.map(p=>'<option value="'+esc(p.ref)+'"'+(S.planFrom===p.ref?' selected':'')+'>'+esc(p.ref)+(p.seq?' · '+esc(p.seq):'')+'</option>').join('')+'</select> <button class="btn ghost" id="planLoad">load</button> <span class="muted" style="font-size:.75rem">the plan\'s `in` is overridden by this job\'s prep at render</span>';
 h+='<textarea id="planText" spellcheck="false" style="min-height:420px;margin-top:8px">'+esc(S.planText)+'</textarea><div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap"><input id="planName" placeholder="name (letters, digits, - _)" style="width:200px"><input id="planWords" placeholder="your words (why)" style="width:260px"><button class="btn primary" id="planSave">save as a new plan</button></div><div id="planErr" class="muted" style="margin-top:6px;font-family:var(--mono);font-size:.75rem"></div></div>';
 h+='<div><h3>Saved plans</h3>'+(v.plans.length?'<table><tr><th>name</th><th>from</th><th>changes</th><th>words</th><th>sha256</th></tr>'+v.plans.map(p=>'<tr><td class="data">'+esc(p.name)+'</td><td class="data">'+esc(p.from||'—')+'</td><td class="num">'+p.changes+'</td><td>'+esc(p.words)+'</td><td class="data">'+esc(p.sha256.slice(0,12))+'…</td></tr>').join('')+'</table>':'<p class="muted">none yet</p>')+'<h3 style="margin-top:16px">The keys '+hintBtn('plan.timeline')+'</h3><p class="muted" style="font-size:.8125rem">Hover a key for its sentence: '+['plan.seq','plan.in','plan.title','plan.gag','plan.timeline','plan.timeline.key','plan.timeline.hold','plan.timeline.to','plan.timeline.n','plan.timeline.method','plan.timeline.ease','plan.timeline.margin','plan.timeline.local','plan.timeline.through','plan.timeline.weights','plan.timeline.soft','plan.timeline.knot_margin','plan.effects','plan.effects.breath','plan.effects.breath.z','plan.effects.parallax','plan.effects.parallax.amp','plan.effects.parallax.ref','plan.effects.glow','plan.effects.glow.gain','plan.matte','plan.crf','plan.gif_long','plan.crop','plan.provenance'].map(k=>'<code>'+esc(k.replace('plan.',''))+'</code>'+hintBtn(k)).join(' ')+'</p><p class="muted" style="font-size:.8125rem">methods: '+S.reg.methods.map(m=>'<code>'+m+'</code>').join(' ')+'<br>eases: '+S.reg.eases.map(m=>'<code>'+m+'</code>').join(' ')+'<br>effects: '+S.reg.effects.map(m=>'<code>'+m+'</code>').join(' ')+'</p></div></div>';
 return h;}
function candLabel(c){return c.name+(c.kind==='draft'?' (draft '+c.draft+')':'');}
function panelRender(){const v=S.view;const full=v.candidates.filter(c=>c.kind==='full'),drafts=v.candidates.filter(c=>c.kind==='draft');let h=v.candidates.length?'':'<p class="muted">'+esc(stageOf('render').what)+'</p>';
 if(!v.candidates.length)h+='<div class="empty">No render yet. Pick a plan and a name in the inspector and render a draft (960) or the full canvas.</div>';
 const cl=c=>'<button class="cand" data-kind="'+c.kind+'" data-name="'+esc(c.name)+'" aria-selected="'+(S.cand&&S.cand.kind===c.kind&&S.cand.name===c.name)+'"><div class="thumb"><img src="/api/jobs/'+esc(v.job.id)+'/thumb/render/'+c.kind+'/'+esc(c.name)+'" alt=""></div><div class="nm"><span class="label">'+esc(c.name)+'</span>'+(c.kind==='draft'?chip('draft '+c.draft,'info'):(c.unjudged?chip('unjudged','info'):chip(c.verdict.verdict,c.verdict.verdict==='NOT READY'?'bad':'ok')))+'</div><div class="dt">'+c.frames+' f · '+c.seconds+' s · step max '+c.step_max+' · seam '+c.seam_step+(c.generated_share?' · '+Math.round(c.generated_share*100)+'% generated':'')+'</div><div class="dt data">'+esc((c.md5_mp4||'').slice(0,8))+'…</div></button>';
 if(v.candidates.length)h+='<h3>Renders <span class="muted label">'+full.length+' full '+hintBtn('chip.unjudged')+' · '+drafts.length+' drafts '+hintBtn('chip.draft')+'</span></h3><div class="cands">'+full.concat(drafts).map(cl).join('')+'</div>';
 h+='<div id="viewerWrap"></div>';return h;}
function panelSkeptic(){const v=S.view;const reqs=v.requests.filter(r=>r.kind==='skeptic');const full=v.candidates.filter(c=>c.kind==='full');let h='<p class="muted">'+esc(stageOf('skeptic').what)+' '+hintBtn('control.request_skeptic')+'</p>';
 h+='<div class="cols"><div class="box"><h3>Request</h3><div class="label muted">candidates</div>'+(full.length?full.map(c=>'<label style="display:block"><input type="checkbox" class="skc" value="'+esc(c.name)+'" checked> '+esc(c.name)+' <span class="data muted">'+esc((c.md5_mp4||'').slice(0,8))+'</span> '+(c.unjudged?chip('unjudged','info'):chip(c.verdict.verdict,c.verdict.verdict==='NOT READY'?'bad':'ok'))+'</label>').join(''):'<p class="muted">no full render yet</p>')+'<div class="label muted" style="margin-top:8px">brief (what to look at, in words)</div><textarea id="skBrief" placeholder="the left mouth at mid-leg; the ring\'s top arc; the couch texture under the breath"></textarea><div style="margin-top:8px"><button class="btn primary" id="skGo"'+(full.length?'':' disabled')+'>write the request</button></div></div>';
 h+='<div><h3>Requests and answers</h3>'+(reqs.length?reqs.map(r=>'<div class="req"><div><span class="data">'+esc(r.name)+'</span> '+(r.answered?chip('answered','ok'):chip('waiting '+fmtAge(r.age_s),'run'))+'</div><div class="muted">'+esc(r.brief)+'</div><div class="data muted">'+esc(r.candidates.join(', '))+'</div>'+(r.answer?'<div><a href="/api/jobs/'+esc(v.job.id)+'/file/'+esc(r.answer.split('/').slice(-2).join('/'))+'" target="_blank">the answer</a></div>':'')+'</div>').join(''):'<p class="muted">none yet. The session lists open requests at boot with <code>studio.py requests</code>.</p>');
 const vd=stageOf('skeptic').verdicts||{};const names=Object.keys(vd);if(names.length)h+='<h3 style="margin-top:12px">Verdicts</h3><table><tr><th>candidate</th><th>verdict</th><th>judged md5</th><th>note</th><th>from</th></tr>'+names.map(n=>'<tr><td>'+esc(n)+'</td><td>'+chip(vd[n].verdict,vd[n].verdict==='NOT READY'?'bad':'ok')+'</td><td class="data">'+esc((vd[n].judged_md5||'').slice(0,8))+'</td><td>'+esc(vd[n].note||'')+'</td><td class="data">'+esc(vd[n].from)+'</td></tr>').join('')+'</table>';
 h+='</div></div>';return h;}
function panelPage(){const v=S.view;const full=v.candidates.filter(c=>c.kind==='full');const bad=full.filter(c=>c.unjudged||(c.verdict&&c.verdict.verdict==='NOT READY'));let h='<p class="muted">'+esc(stageOf('page').what)+' '+hintBtn('control.page')+'</p>';
 h+='<div class="cols"><div class="box"><h3>Build the page</h3><p class="muted">Every full render of '+esc(v.job.seq)+' goes on it ('+full.length+'): '+full.map(c=>esc(c.name)+' '+(c.unjudged?chip('unjudged','info'):chip(c.verdict.verdict,c.verdict.verdict==='NOT READY'?'bad':'ok'))).join(', ')+'</p>'+(bad.length?'<div class="msg bad">The review gate refuses: '+bad.map(c=>esc(c.name)+' ('+esc(c.unjudged?(c.unjudged_reason||'unjudged'):'NOT READY')+')').join('; ')+'. Request the skeptic, or override below: the page prints the override.</div>':'')+'<div class="label muted">title</div><input id="pgTitle" style="width:100%" value="'+esc(v.job.seq+': round '+(v.rounds.length+1))+'"><div class="label muted" style="margin-top:6px">intro</div><input id="pgIntro" style="width:100%"><div class="label muted" style="margin-top:6px">notes per candidate (what to look at)</div>'+full.map(c=>'<div style="display:flex;gap:6px;margin-top:4px;align-items:center"><span class="data" style="width:60px">'+esc(c.name)+'</span><input class="pgNote" data-name="'+esc(c.name)+'" style="flex:1"></div>').join('')+'<div style="margin-top:8px"><label><input type="checkbox" id="pgOverride"> override the gate (on his word)</label></div><div style="margin-top:8px"><button class="btn primary" id="pgGo"'+(full.length?'':' disabled')+'>build the page</button></div></div>';
 h+='<div>'+(v.page.exists?'<h3>The page</h3><p><a href="'+esc(v.page.url)+'" target="_blank">open index.html</a> <span class="data muted">md5 '+esc(v.page.md5)+'</span></p><iframe src="'+esc(v.page.url)+'" style="width:100%;height:600px;border:1px solid var(--line);background:#fff"></iframe>':'<p class="muted">no page yet</p>')+'</div></div>';return h;}
function panelGrades(){const v=S.view;let h='<p class="muted">'+esc(stageOf('grades').what)+' '+hintBtn('control.grade')+'</p>';if(!v.rounds.length)return h+'<div class="empty">No round yet: build the page first.</div>';
 h+='<div class="cols">'+v.rounds.slice().reverse().map(r=>'<div class="box"><h3>Round '+r.n+' '+(r.grade?chip('graded','ok'):(r.ungraded_by_his_word?chip('ungraded by his word','info'):chip('ungraded','info')))+'</h3><p class="muted">'+esc(r.at)+' · candidates '+esc(r.candidates.join(', '))+' · page md5 <span class="data">'+esc(r.page_md5)+'</span>'+(r.override?'<br>'+esc(r.override):'')+(r.note?'<br>'+esc(r.note):'')+'</p>'+(r.grade?'<blockquote style="margin:0;border-left:2px solid var(--line-strong);padding-left:12px;white-space:pre-wrap">'+esc(r.grade.text)+'</blockquote><p class="muted">saved '+esc(r.grade.at)+' on page md5 '+esc(r.grade.page_md5.slice(0,8))+'…</p>':(r.ungraded_by_his_word?'<p class="muted">marked '+esc(r.ungraded_by_his_word.at)+(r.ungraded_by_his_word.words?': '+esc(r.ungraded_by_his_word.words):'')+'</p>':'<div class="label muted">his words, verbatim</div><textarea class="grText" data-round="'+r.n+'"></textarea><div style="margin-top:8px;display:flex;gap:8px"><button class="btn primary grSave" data-round="'+r.n+'">save the grade</button><button class="btn ghost grSkip" data-round="'+r.n+'">mark ungraded by his word</button></div>'))+'</div>').join('')+'</div>';return h;}
function wirePanel(){const v=S.view;
 document.querySelectorAll('.cand').forEach(b=>b.onclick=()=>selectCand(b.dataset.kind,b.dataset.name));
 if(S.stage==='render'){if(!S.cand&&v.candidates.length){const full=v.candidates.filter(c=>c.kind==='full');const c=(full.length?full:v.candidates).slice().sort((a,b)=>a.mtime<b.mtime?1:-1)[0];selectCand(c.kind,c.name);}else if(S.cand)loadRender();}
 const pl=$('#planLoad');if(pl)pl.onclick=async()=>{const ref=$('#planFrom').value;S.planFrom=ref;if(!ref){S.planText='';$('#planText').value='';return;}const [kind,name]=ref.split(':');const p=await api(kind==='job'?'/api/jobs/'+encodeURIComponent(v.job.id)+'/plans/'+encodeURIComponent(name):'/api/plans/frozen/'+encodeURIComponent(name));delete p.provenance;S.planText=JSON.stringify(p,null,1);$('#planText').value=S.planText;$('#planName').value=name+'_v2';};
 const pt=$('#planText');if(pt)pt.oninput=()=>{S.planText=pt.value;try{JSON.parse(pt.value);$('#planErr').textContent='';}catch(e){$('#planErr').textContent='JSON: '+e.message;}};
 const ps=$('#planSave');if(ps)ps.onclick=async()=>{let plan;try{plan=JSON.parse($('#planText').value);}catch(e){$('#planErr').textContent='JSON: '+e.message;return;}try{const r=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/plans',{name:$('#planName').value,plan,from:S.planFrom||undefined,words:$('#planWords').value});setMsg('saved '+r.path+' ('+r.changes.length+' changes from '+(S.planFrom||'nothing')+')','ok');S.knobs.plan=r.ref;await openJob(v.job.id,true);}catch(e){setMsg(e.message,'bad');}};
 const sk=$('#skGo');if(sk)sk.onclick=async()=>{const names=[...document.querySelectorAll('.skc:checked')].map(c=>c.value);try{const r=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/requests/skeptic',{brief:$('#skBrief').value,candidates:names});setMsg('written '+r.file+'; the session lists it with studio.py requests','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}};
 const pg=$('#pgGo');if(pg)pg.onclick=async()=>{const notes={};document.querySelectorAll('.pgNote').forEach(i=>{if(i.value.trim())notes[i.dataset.name]=i.value.trim();});try{const r=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/page',{title:$('#pgTitle').value,intro:$('#pgIntro').value,notes,override:$('#pgOverride').checked});setMsg('building the page: record '+r.record+(r.override?' · '+r.override:''),'ok');await openJob(v.job.id,true);}catch(e){setMsg(e.message,'bad');}};
 document.querySelectorAll('.grSave').forEach(b=>b.onclick=async()=>{const n=b.dataset.round;const t=document.querySelector('.grText[data-round="'+n+'"]').value;try{await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/picks',{round:+n,text:t});setMsg('round '+n+' graded; his words saved verbatim','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}});
 document.querySelectorAll('.grSkip').forEach(b=>b.onclick=async()=>{const n=b.dataset.round;try{await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/picks',{round:+n,ungraded_by_his_word:true});await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}});}
// the viewer
async function selectCand(kind,name){S.cand={kind,name};S.frame=0;stopPlay();document.querySelectorAll('.cand').forEach(b=>b.setAttribute('aria-selected',b.dataset.kind===kind&&b.dataset.name===name));await loadRender();renderInspector();}
async function loadRender(){if(!S.cand)return;const v=S.view;try{S.render=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/render/'+S.cand.kind+'/'+encodeURIComponent(S.cand.name));}catch(e){setMsg(e.message,'bad');return;}renderViewer();}
function renderViewer(){const r=S.render,v=S.view;const w=$('#viewerWrap');if(!w||!r)return;const n=r.frames_available||r.frames||0;const m=r.measure||{};
 let h='<div class="head" style="margin-top:12px"><h3 style="margin:0">'+esc(candLabel(r))+' '+hintBtn('region.viewer')+'</h3>'+(r.kind==='draft'?chip('draft '+r.draft,'info'):(r.unjudged?chip('unjudged','info'):chip(r.verdict.verdict,r.verdict.verdict==='NOT READY'?'bad':'ok')))+'<span class="muted" title="'+esc(r.title||'')+'">'+esc(r.title||'')+'</span><div class="acts"><div class="seg" role="group" aria-label="view"><button data-mode="fit" aria-pressed="'+(S.mode==='fit')+'">fit</button><button data-mode="1:1" aria-pressed="'+(S.mode==='1:1')+'">1:1</button><button data-mode="2x" aria-pressed="'+(S.mode==='2x')+'">2×</button></div><a class="btn ghost" href="'+esc(r.mp4_url)+'" target="_blank">mp4</a></div></div>';
 h+='<div class="viewer"><div class="frame" id="frameBox"><div class="tag" id="frameTag"></div><img id="frameImg" alt="frame"></div><div class="refs"><figure class="a"><img src="/api/jobs/'+esc(v.job.id)+'/thumb/still/0" alt="A"><figcaption>A · k0 (the first still)</figcaption></figure><figure class="b"><img src="/api/jobs/'+esc(v.job.id)+'/thumb/still/'+Math.max(0,(v.prep?v.prep.n:1)-1)+'" alt="B"><figcaption>B · k'+Math.max(0,(v.prep?v.prep.n:1)-1)+' (the last still)</figcaption></figure><div class="muted" style="font-size:.75rem"><span class="kbd">space</span> play · <span class="kbd">←</span><span class="kbd">→</span> one frame · <span class="kbd">shift</span> ten · <span class="kbd">m</span> mark a fault</div></div></div>';
 h+='<div class="axis"><div class="ctl"><button class="btn" id="play">play</button><span class="data" id="frameNo"></span><span class="muted label">of '+n+' · 25 fps '+hintBtn('region.axis')+'</span><input id="markText" placeholder="what you see at this frame" style="width:260px" aria-label="note for the marked frame"><button class="btn ghost" id="markBtn">mark this frame as a fault</button>'+hintBtn('control.mark_frame')+'<span class="muted" id="markNote"></span></div><input type="range" id="scrub" min="0" max="'+Math.max(0,n-1)+'" value="'+S.frame+'" step="1" aria-label="frame"><div id="plots"></div></div>';
 w.innerHTML=h;sizeFrame();$('#play').onclick=togglePlay;$('#scrub').oninput=e=>{S.frame=+e.target.value;showFrame();};$('#markBtn').onclick=markFrame;w.querySelectorAll('.seg button').forEach(b=>b.onclick=()=>{S.mode=b.dataset.mode;renderViewer();const fb=$('#frameBox');if(fb&&S.mode!=='fit'){const im=$('#frameImg');const go=()=>fb.scrollTo((fb.scrollWidth-fb.clientWidth)/2,(fb.scrollHeight-fb.clientHeight)/2);if(im&&im.complete)go();else if(im)im.onload=go;}});
 drawPlots();showFrame();}
function sizeFrame(){const fb=$('#frameBox');if(!fb)return;const h=Math.max(380,innerHeight-fb.getBoundingClientRect().top-290);fb.style.height=h+'px';const rf=document.querySelector('.refs');if(rf)rf.style.height=h+'px';}
function showFrame(){const r=S.render;if(!r)return;const img=$('#frameImg');if(!img)return;const t=r.frames_tags[S.frame]||{};img.src=r.frame_url+S.frame;img.className=(t.generated?'gen ':'')+(S.mode==='2x'?'px':'');const box=$('#frameBox');const W=r.canvas?r.canvas[0]:0;img.style.maxHeight=S.mode==='fit'?'100%':'none';img.style.maxWidth=S.mode==='fit'?'100%':'none';img.style.width=S.mode==='2x'?(2*W)+'px':(S.mode==='1:1'?W+'px':'');img.style.height=S.mode==='fit'?'':'auto';box.style.display=S.mode==='fit'?'flex':'block';box.style.overflow=S.mode==='fit'?'hidden':'auto';
 const tag=t.tag||'';$('#frameTag').innerHTML=chip('f '+S.frame,'')+(t.generated?chip('generated'+(t.t!=null?' t '+t.t:''),'gen'):chip(tag+(t.key!=null?' k'+t.key:'')+(t.t!=null?' t '+t.t:''),''))+(t.method&&!t.generated&&t.tag!=='photo'?chip(t.method):'')+(t.dexp!=null?chip('dexp '+t.dexp):'');
 const marks=(r.owner_frames||[]).filter(o=>o.frame===S.frame);$('#markNote').textContent=marks.length?'marked: '+marks.map(o=>o.note||'(no note)').join('; '):'';
 $('#frameNo').textContent='f '+S.frame+(t.t!=null?' · t '+t.t:'');const sc=$('#scrub');if(sc&&+sc.value!==S.frame)sc.value=S.frame;const cur=$('#cursor');if(cur){const x=xOf(S.frame);cur.setAttribute('x1',x);cur.setAttribute('x2',x);}}
function xOf(i){const n=S.render.frames_available||S.render.frames||1;return 40+(i/(Math.max(1,n-1)))*(plotW()-40-10);}
function plotW(){const p=$('#plots');return Math.max(600,(p&&p.clientWidth)||1000);}
function drawPlots(){const r=S.render;const m=r.measure||{};const steps=m.steps||[];const n=r.frames_available||r.frames||steps.length+1;const W=plotW(),H=120,x0=40,x1=W-10,y0=10,y1=H-22;const maxv=Math.max(1,...steps,m.seam_step||0);const yOf=v=>y1-(v/maxv)*(y1-y0);
 const pts=steps.map((v,i)=>xOf(i+0.5).toFixed(1)+','+yOf(v).toFixed(1)).join(' ');
 let s='<svg viewBox="0 0 '+W+' '+(H+48)+'" width="'+W+'" height="'+(H+48)+'" style="width:100%;height:auto" aria-label="the step series and the frame tags">';
 s+='<line x1="'+x0+'" y1="'+y1+'" x2="'+x1+'" y2="'+y1+'" stroke="#454b52"/><line x1="'+x0+'" y1="'+y0+'" x2="'+x0+'" y2="'+y1+'" stroke="#454b52"/>';
 [0,maxv/2,maxv].forEach(v=>{s+='<text x="'+(x0-4)+'" y="'+(yOf(v)+4)+'" font-size="12" text-anchor="end" fill="#9aa1a8" font-family="ui-monospace,Menlo,monospace">'+v.toFixed(1)+'</text>';});
 s+='<text x="'+(x0+4)+'" y="'+(y0+10)+'" font-size="12" fill="#9aa1a8">step, grey levels</text>';
 s+='<line x1="'+x0+'" y1="'+yOf(0.3)+'" x2="'+x1+'" y2="'+yOf(0.3)+'" stroke="#e8706a" stroke-dasharray="4 4" opacity=".8"/><text x="'+(x1)+'" y="'+(yOf(0.3)-3)+'" font-size="12" text-anchor="end" fill="#e8706a">0.3 stall bar</text>';
 r.frames_tags.forEach(t=>{if(t.generated){const xa=xOf(t.i-0.5),xb=xOf(t.i+0.5);s+='<rect x="'+xa+'" y="'+(y1+4)+'" width="'+(xb-xa)+'" height="8" fill="#b48ef0" opacity=".8"/>';}});
 s+='<text x="'+x0+'" y="'+(H+44)+'" font-size="12" fill="#9aa1a8">generated frames (violet) · step: mean '+m.step_mean+' · max '+m.step_max+' at f '+m.step_max_at+' · seam '+m.seam_step+'</text>';
 (r.owner_frames||[]).forEach(o=>{const x=xOf(o.frame);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="#e8706a" opacity=".7"/>';});
 s+='<polyline points="'+pts+'" fill="none" stroke="#e8e8e6" stroke-width="1.5"/>';
 s+='<line id="cursor" x1="'+xOf(S.frame)+'" y1="'+y0+'" x2="'+xOf(S.frame)+'" y2="'+(y1+12)+'" stroke="#e0a65a" stroke-width="1.5"/>';
 for(let i=0;i<n;i+=Math.max(1,Math.round(n/20))){s+='<text x="'+xOf(i)+'" y="'+(H+24)+'" font-size="12" text-anchor="middle" fill="#8a9198" font-family="ui-monospace,Menlo,monospace">'+i+'</text>';}
 s+='</svg>';const p=$('#plots');p.innerHTML=s;p.querySelector('svg').onclick=e=>{const svg=e.currentTarget;const rect=svg.getBoundingClientRect();const x=(e.clientX-rect.left)/rect.width*W;const i=Math.round((x-x0)/(x1-x0)*(n-1));S.frame=Math.max(0,Math.min(n-1,i));showFrame();};}
function togglePlay(){if(S.playing)stopPlay();else{const n=S.render.frames_available||S.render.frames;S.playing=setInterval(()=>{S.frame=(S.frame+1)%n;showFrame();},40);$('#play').textContent='pause';}}
function stopPlay(){if(S.playing){clearInterval(S.playing);S.playing=null;}const b=$('#play');if(b)b.textContent='play';}
async function markFrame(){if(!S.render)return;const inp=$('#markText');const note=inp?inp.value:'';try{await api('/api/jobs/'+encodeURIComponent(S.view.job.id)+'/frames/mark',{kind:S.cand.kind,name:S.cand.name,frame:S.frame,note});if(inp)inp.value='';const f=S.frame;await loadRender();S.frame=f;showFrame();}catch(e){setMsg(e.message,'bad');}}
window.addEventListener('resize',()=>{if(S.render&&$('#plots')){sizeFrame();drawPlots();}});
document.addEventListener('keydown',e=>{if(!S.render||(e.target.matches('input,textarea,select')&&e.target.id!=='scrub'))return;const n=S.render.frames_available||S.render.frames;const d=e.shiftKey?10:1;if(e.key==='ArrowRight'||e.key==='.'){S.frame=Math.min(n-1,S.frame+d);showFrame();e.preventDefault();}else if(e.key==='ArrowLeft'||e.key===','){S.frame=Math.max(0,S.frame-d);showFrame();e.preventDefault();}else if(e.key===' '){togglePlay();e.preventDefault();}else if(e.key==='m'){markFrame();}});
// the inspector
function knobState(v,s){return S.knobs[v.job.id+'/'+s.name]||(S.knobs[v.job.id+'/'+s.name]={});}
function knobBase(s,k){const last=s.latest_knobs||{};return (k.key!=='name'&&last[k.key]!==undefined)?last[k.key]:k.default;}
function renderInspector(){const v=S.view;const s=stageOf(S.stage);const ins=$('#inspector');let h='<h3>'+esc(s.title)+' '+hintBtn('region.inspector')+'</h3>';let kh='',mh='';
 const latest=s.latest?s.history.find(x=>x.id===s.latest):null;const K=knobState(v,s);const nChanged=s.knobs.filter(k=>K[k.key]!==undefined&&JSON.stringify(K[k.key])!==JSON.stringify(knobBase(s,k))).length;
 if(s.kind==='script'&&s.name!=='page'){kh+='<section><h3>Knobs</h3>'+(s.knobs.length?s.knobs.map(k=>{const base=knobBase(s,k);const val=K[k.key]!==undefined?K[k.key]:base;const changed=JSON.stringify(val)!==JSON.stringify(base);const fromLast=s.latest_knobs&&k.key!=='name'&&s.latest_knobs[k.key]!==undefined;let inp;if(k.type==='bool')inp='<input type="checkbox" data-knob="'+esc(k.key)+'"'+(val?' checked':'')+'>';else if(k.type==='plan')inp='<select data-knob="'+esc(k.key)+'"><option value="">— choose —</option>'+v.plans.map(p=>'<option value="'+esc(p.ref)+'"'+(val===p.ref?' selected':'')+'>'+esc(p.ref)+'</option>').join('')+v.frozen_plans.map(p=>'<option value="'+esc(p.ref)+'"'+(val===p.ref?' selected':'')+'>'+esc(p.ref)+'</option>').join('')+'</select>';else inp='<input data-knob="'+esc(k.key)+'" value="'+esc(val)+'"'+(k.type==='int'||k.type==='float'?' inputmode="decimal"':'')+'>';
  return '<div class="knob"><span class="key'+(changed?' changed':'')+'">'+esc(k.key)+'<button class="hint" data-hint="knob.'+esc(s.name)+'.'+esc(k.key)+'" data-knob=\''+esc(JSON.stringify(k))+'\'>?</button></span><span>'+inp+'</span><span class="what">'+esc(k.what)+'</span><span class="def">default '+esc(JSON.stringify(k.default))+(fromLast?' · last run '+esc(JSON.stringify(s.latest_knobs[k.key])):'')+' · range '+(k.range?esc(JSON.stringify(k.range)):'none stated')+(changed?' · <button class="btn ghost" data-reset="'+esc(k.key)+'">reset</button>':'')+'</span></div>';}).join(''):'<p class="muted">no knobs</p>')+(s.name==='page'?'<p class="muted" style="font-size:.75rem">The page is built from its panel, behind the review gate; its title, intro and footer are typed there.</p>':'<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" id="runStage">'+(latest?(nChanged?'rerun '+esc(s.title)+' with '+nChanged+' change'+(nChanged>1?'s':''):'rerun '+esc(s.title)+' with the last run\'s knobs'):'run '+esc(s.title))+'</button>'+hintBtn(s.name==='render'?'control.render':'control.rerun')+'</div>');
  if(s.name==='render')kh+='<p class="muted" style="font-size:.75rem;margin-top:8px">A full render (draft 0) is a candidate; a draft goes under drafts/. The first full render of a new round waits for the previous round\'s grade text '+hintBtn('control.grade')+'</p>';
  kh+='</section>';}
 if(latest){kh+='<section><h3>Latest record</h3><div class="data">'+esc(latest.id)+'</div><div>'+chip(latest.state,stateClass(latest.state))+' <span class="muted">'+esc(latest.started)+'</span>'+(latest.wall_s!=null?' <span class="data">'+esc(fmtS(latest.wall_s))+'</span>':'')+'</div>'+(latest.reason?'<div class="muted" style="margin-top:4px">'+esc(latest.reason)+'</div>':'')+(latest.state==='running'?'<div style="margin-top:8px"><button class="btn" id="cancelStage">cancel</button>'+hintBtn('control.cancel')+'</div>':'')+'<div id="recDetail"></div></section>';loadRecord(latest.id);}
 if(s.history.length>1)kh+='<section><h3>History</h3>'+s.history.slice().reverse().map(x=>'<div class="kv" style="padding:2px 0"><span class="data" style="font-size:.75rem">'+esc(x.id)+'</span>'+chip(x.state,stateClass(x.state))+'</div>').join('')+'</section>';
 if(S.stage==='render'&&S.render){const r=S.render,m=r.measure||{};mh+='<section><h3>Measures '+hintBtn('measure.steps')+'</h3><table style="width:100%">'+[['frames',r.frames,'','measure.steps'],['seconds',r.seconds,'s',null],['canvas',(r.canvas||[]).join('×'),'px',null],['step mean',m.step_mean,'levels','measure.step_mean'],['step max',m.step_max,'levels at f '+m.step_max_at,'measure.step_max'],['seam step',m.seam_step,'levels','measure.seam_step'],['generated',m.generated_frames+' ('+Math.round((m.generated_share||0)*100)+'%)','frames','measure.generated_share'],['dexp max',m.dexp_max,'','measure.dexp_max'],['faces on keys',(m.faces_keyframes||[]).join(', '),'','measure.faces_per_frame'],['RIFE s / frame',m.rife_seconds_per_frame,'s','measure.rife_seconds_per_frame'],['render',m.render_s,'s','measure.render_s']].map(x=>'<tr><td>'+esc(x[0])+(x[3]?hintBtn(x[3]):'')+'</td><td class="num">'+esc(x[1]??'—')+(x[2]?'<span class="unit">'+x[2]+'</span>':'')+'</td><td>'+verdictOf(x[0],m)+'</td></tr>').join('')+'</table></section>';
  mh+='<section><h3>Provenance</h3><div class="data" style="font-size:.75rem;word-break:break-all">mp4 md5 '+esc(m.md5_mp4||'')+hintBtn('measure.md5_mp4')+'<br>gif md5 '+esc(m.md5_gif||'')+'<br>plan sha256 '+esc(m.plan_sha256||'')+hintBtn('measure.plan_sha256')+'<br>script md5 '+esc(m.script_md5||'not stamped (older render)')+hintBtn('measure.script_md5')+'<br>RIFE '+esc(m.rife_version||'—')+hintBtn('measure.rife_version')+'</div>'+(r.verdict?'<div style="margin-top:6px">'+chip(r.verdict.verdict,r.verdict.verdict==='NOT READY'?'bad':'ok')+' on md5 '+esc((r.verdict.judged_md5||'').slice(0,8))+' <span class="muted">'+esc(r.verdict.note||'')+'</span></div>':'')+'</section>';
  mh+='<section><h3>The plan as rendered</h3><div class="muted" style="font-size:.75rem">'+esc(r.gag||'')+'</div><div class="log" style="max-height:260px">'+esc(JSON.stringify(r.plan,null,1))+'</div></section>';}
 h+=(S.stage==='render'&&S.render)?mh+kh:kh+mh;
 ins.innerHTML=h;
 ins.querySelectorAll('[data-knob]').forEach(i=>{i.onchange=()=>{const k=s.knobs.find(k=>k.key===i.dataset.knob);K[k.key]=k.type==='bool'?i.checked:(k.type==='int'?parseInt(i.value||k.default,10):(k.type==='float'?parseFloat(i.value||k.default):i.value));renderInspector();};});
 ins.querySelectorAll('[data-reset]').forEach(b=>b.onclick=()=>{delete K[b.dataset.reset];renderInspector();});
 const run=$('#runStage');if(run)run.onclick=async()=>{const knobs={};s.knobs.forEach(k=>{knobs[k.key]=K[k.key]!==undefined?K[k.key]:knobBase(s,k);});run.textContent='working…';run.disabled=true;try{const r=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/stages/'+s.name+'/run',{knobs});setMsg('started '+r.record,'ok');await openJob(v.job.id,true);loadJobs();}catch(e){if(e.extra&&e.extra.round)setMsg(e.message+' (grades stage)','bad');else setMsg(e.message,'bad');run.textContent='run';run.disabled=false;}};
 const cn=$('#cancelStage');if(cn)cn.onclick=async()=>{try{await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/stages/'+latest.id+'/cancel',{});await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}};}
function verdictOf(name,m){if(name==='seam step')return m.seam_step<=3?chip('within','ok'):chip('past bar (3)','bad');if(name==='step max'){const st=m.steps||[];const i=m.step_max_at;const nb=Math.max(st[i-1]||0,st[i+1]||0);return i!=null&&nb>0&&m.step_max>3*nb?chip('jump (3× neighbours)','bad'):chip('within','ok');}if(name==='frames'){const st=m.steps||[];let run=0,stall=false;st.forEach(v=>{run=v<0.3?run+1:0;if(run>=2)stall=true;});return stall?chip('a stall (two steps below 0.3)','bad'):chip('no stall','ok');}return '';}
async function loadRecord(rid){try{const r=await api('/api/jobs/'+encodeURIComponent(S.view.job.id)+'/stages/'+encodeURIComponent(rid));const d=$('#recDetail');if(!d)return;d.innerHTML=(r.progress?'<div class="data" style="margin-top:6px">progress '+r.progress.i+' / '+r.progress.n+' '+esc(r.progress.phase)+'</div>':'')+(r.elapsed_s!=null?'<div class="data muted">elapsed '+esc(fmtS(r.elapsed_s))+'</div>':'')+'<div class="label muted" style="margin-top:8px">log tail</div><div class="log">'+esc(r.log_tail.join('\n'))+'</div><div class="label muted" style="margin-top:8px">command '+hintBtn('control.command')+'</div><div class="cmd">'+esc(r.command)+'</div><div class="label muted" style="margin-top:8px">script md5 <span class="data">'+esc(r.script_md5)+'</span></div>'+(r.outputs&&r.outputs.length?'<div class="label muted" style="margin-top:8px">outputs</div><div class="data" style="font-size:.75rem">'+r.outputs.map(o=>esc(o.path.split('/').slice(-1)[0])+' <span class="muted">'+esc(o.md5.slice(0,8))+'</span>').join('<br>')+'</div>':'')+(r.inputs&&r.inputs.length?'<div class="label muted" style="margin-top:8px">inputs</div><div class="data" style="font-size:.75rem">'+r.inputs.map(o=>esc(o.path.split('/').slice(-1)[0])+' <span class="muted">'+esc((o.sha256||o.md5||'').slice(0,8))+'</span>').join('<br>')+'</div>':'');}catch(e){}}
// boot
(async()=>{S.reg=await api('/api/registry');$('#ver').textContent=S.reg.ui_version+' · 127.0.0.1:'+S.reg.port;await loadJobs();await loadModels();let j=null;try{j=localStorage.getItem('studio_job')}catch(e){}if(j&&S.jobs.find(x=>x.id===j))openJob(j);else if(S.jobs.length)openJob(S.jobs[S.jobs.length-1].id);})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
