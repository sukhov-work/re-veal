"""The hints table: one sentence per control, knob, chip, measure and region of the page.

The page and the CLI's help say the same thing. The sentences for the scripts' flags and the plan keys are the
scripts' own (loop_seq.py --help, plans/loops/SCHEMA.md); the bars are the playbook's (loops.md §6).

This module holds the loop flow's rows (LOOP_HINTS: the 290 of 2026-11-05, the two still-count chips of phase B's
slice and the four rows of the repaint leg). HINTS, the one table the page and the tests read, merges them with the pair's (hints_pair.py) and the
director's (hints_director.py); a key in two tables fails the import.
"""

from __future__ import annotations

from typing import Any

from reveal_studio.registry.entries import H, merge_hints
from reveal_studio.registry.hints_director import HINTS as DIRECTOR_HINTS
from reveal_studio.registry.hints_pair import HINTS as PAIR_HINTS

LOOP_HINTS: dict[str, dict[str, Any]] = {
    # the plan's keys (SCHEMA.md)
    "plan.seq": H(
        "The sequence's name: the prep folder in/<seq>/ and the renders <seq>/<name>/ take it.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.in": H(
        "The prep folder the render reads k<i>.png from (repo-relative). The studio sets it to this job's prep on every render (--set in=...), so the value in the plan is overridden.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.title": H(
        "One line: what differs from the first candidate (optional). The page shows it beside the name.",
        stage="page",
        source="SCHEMA.md",
    ),
    "plan.gag": H("One line the owner can read as the idea of the clip.", stage="page", source="SCHEMA.md"),
    "plan.timeline": H(
        "The steps in order. The loop is the concatenation, and the last transition lands on the first step's still, which is not repeated: the loop's frame 0 is that still's hold.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.key": H(
        "A hold step: still `key` for `hold` frames at 25 fps, byte-exact pixels.", stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.hold": H(
        "The hold's length in frames at 25 fps. He sets the pace in words ('20 % faster'): apply the percentage to the frame counts.",
        default=1,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.to": H(
        "A transition step: `n` in-betweens from the current still to still `to`.", stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.n": H(
        "The number of in-betweens of the step. RIFE: about 1.3 s each at 1900 px, two calls per frame per `local` box.",
        default=0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.method": H(
        "rife: RIFE v4.26 in-betweens inside the change matte (generated content, the page says so). dissolve: the plain blend. morph: transitions.py's DIS morph. teleport: a region squeezed out and in. cut: no frames. rewind: earlier frames played backward. slices: diagonal cards. sheets: whole pictures sliding across the base. snap: a short blurred jump. slide and rise: one person moved in a matte. repaint: a chain of stills repainted in a per-pixel order, nothing generated.",
        default="rife",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.ease": H(
        "How frame i of N maps to t: linear; smooth (smoothstep); snap (smoothstep twice); accel (t²); accel3 (t³); decel (1 − (1 − t)²); sine (half a cosine). Per-segment eases on a chain stop at every still: use `through` with one profile instead.",
        default="smooth",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.margin": H(
        "rife only: t runs over [margin, 1 − margin], so no in-between hugs a still (an in-between within 4 % of a still reads as a stop). The code's default is 0; the angel plans set 0.04.",
        default=0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.local": H(
        'rife only: [{"box": [x0, y0, x1, y1] (canvas fractions), "ease": "snap", "feather": 0.01}]: inside each box the in-between is RIFE at the box\'s own ease of u, blended over a feathered edge (two RIFE calls per frame per box). A mouth that opens crosses its half-open state in about 3 frames under snap while the lean keeps sine.',
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.through": H(
        "A chain of stills passed under ONE global speed profile (the inner stills never held): the list of the inner stills' indices; `weights` per segment, `soft` slows near a still, `knot_margin` keeps every frame off a still.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.weights": H(
        "One weight per segment of a `through` chain: the share of the profile each leg takes (the motion's size per leg).",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.soft": H(
        "How much a `through` chain slows near each inner still (0 none .. 0.5).",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.knot_margin": H(
        "A `through` chain's margin at each still, as a share of a leg: about half a frame's share so no frame hugs a still.",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects": H(
        "Effects run on the finished frame list; frame 0 is always untouched, so the seam is a still. Kinds: breath, parallax, glow.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.breath": H(
        "A push-in about (cx, cy) (canvas fractions) by 1 + z·sin²(πu) over the loop. Per clip: fine on an idle object, off where the motion is the subject. `depth_k` (0 = off) makes it a dolly: near layers grow more than far ones (needs the depth maps).",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.breath.z": H(
        "The push-in's size as a share of the frame (1.5–2 % reads as a breath).", stage="render", source="SCHEMA.md"
    ),
    "plan.effects.parallax": H(
        "One remap per frame. A pixel at relative depth d moves by amp × W × (d − ref) × wave(u) along `dir` (`shape` sin: a sway; pulse: one excursion), plus amp2 × that along `dir2` with `shape2` (an orbit). The plane at depth `ref` (or the depth read at `ref_at` in frame 0's map) stays put. The maps are blurred `sigma` px and blended per frame by the in-between's t. With a breath present the two compose into one remap.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.parallax.amp": H(
        "The sway's size as a share of the width at depth distance 1 from the reference plane (a2: 0.014).",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.parallax.ref": H(
        "The relative depth (0 far .. 1 near) of the plane that stays put (the halo's plane on the angel pair: 0.15). `ref_at` [fx, fy] reads it from frame 0's map instead.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.glow": H(
        "The frame's pixels above `thr` inside `box` (canvas fractions) are blurred at the `sigma` radii (shares of W), mixed by `mix`, and added back at gain × wave(u): a light source breathing (a bloom); luminance only.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.glow.gain": H("The bloom's strength at its peak (a3: 0.15).", stage="render", source="SCHEMA.md"),
    "plan.matte": H(
        "The change matte of a leg: `thr` the Lab distance above which a pixel counts as changed (on 2 px blurred copies), `grow` the dilation and `feather` the Gaussian feather, both as shares of the width; `min_share` the matte's floor. `all: true` runs a rife leg on the whole frame (a locked or far-field registration leaves the rest of the scene's drift as motion, and RIFE carries it).",
        default={"thr": 14, "grow": 0.015, "feather": 0.01, "min_share": 0.0005},
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.crf": H(
        "The mp4's libx264 quality (lower is larger and truer).", default=14, stage="render", source="SCHEMA.md"
    ),
    "plan.gif_long": H(
        "The gif's long edge in px (a two-pass palette, 40 ms per frame).",
        default=540,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.crop": H(
        "The centre share of the canvas that is output (the seasons plans use 0.75 on a 3600 px prep so a drifting picture never runs out of pixels).",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.provenance": H(
        "Who wrote the plan, what it came from (path and sha256), when, which keys changed, and his words verbatim. The studio writes it; the renderer ignores it (the plan's sha256 in measure.json includes it).",
        stage="plan",
    ),
    # the measures (measure.json; the bars from loops.md §6)
    "measure.steps": H(
        "The mean absolute difference between consecutive decoded frames, one value per step (grey levels). The bar: no run of steps below 0.3 while motion is open (a stall); no step above 3× its neighbours outside a declared cut or snap (a jump).",
        stage="render",
        source="loops.md §6",
    ),
    "measure.step_mean": H("The mean of the step series (grey levels).", stage="render"),
    "measure.step_max": H(
        "The largest step and the index it sits at. Past 3× its neighbours it is a jump unless a cut or a snap is declared there.",
        stage="render",
        source="loops.md §6",
    ),
    "measure.seam_step": H(
        "The difference between the last frame and frame 0: the loop's seam. A still gives about 1–3; anything larger is a visible jump at the seam unless a cut is declared.",
        rng=[0, 3],
        stage="render",
        source="loops.md §6",
    ),
    "measure.faces_per_frame": H(
        "YuNet's face count per decoded frame, against the keyframes' counts; noisy on a group and under a breath. A printed face (a cookie) counts.",
        stage="render",
        source="loops.md §6",
    ),
    "measure.generated_share": H(
        "The share of frames a model drew (RIFE in-betweens). The page says which frames are generated; the strip outlines them violet.",
        stage="render",
    ),
    "measure.dexp_max": H(
        "The largest double-exposure share of a generated frame (the share of pixels where the in-between looks like both stills at once). 3–11 % is the floor on handheld pairs; a doubled prop is found by a crop, not by this number.",
        stage="render",
        source="loops.md §6",
    ),
    "measure.rife_seconds_per_frame": H("The mean wall time of one RIFE in-between on this laptop.", stage="render"),
    "measure.render_s": H("The wall time of the frame pass (before the encode and the measures).", stage="render"),
    "measure.md5_mp4": H(
        "The mp4's md5: a render reproduces it from the same plan, prep and script (a watch, not a hope). The skeptic's verdict is given on one md5; a changed md5 is unjudged.",
        stage="render",
    ),
    "measure.plan_sha256": H("The first 16 hex of the sha256 of the plan as rendered (sorted keys).", stage="render"),
    "measure.script_md5": H(
        "The md5 of scripts/research/loop_seq.py at the render; with the plan's sha256 it names what produced the clip.",
        stage="render",
    ),
    "measure.rife_version": H(
        "The RIFE model the render loaded (from RIFE_MANIFEST.json), null when no leg used it.", stage="render"
    ),
    # the registration record (prep.json)
    "prep.method": H(
        "How the still was registered: sift+magsac (direct), sift+magsac via frame i (a chain), ecc affine, identity (a declared cut or a failed fit, said on the log); '+ lock' when the lock windows shifted it.",
        stage="registration",
    ),
    "prep.inliers": H(
        "The SIFT fit's inlier count on the 1200 px proxy (the floor is --min-inliers). A few dozen inliers on a subject-filled frame can fit a wrong model: look at the overlay.",
        stage="registration",
    ),
    "prep.lock": H(
        "Per lock window: where it sat after the fit (dx, dy in px), the template-match correlation, and the translation applied (the mean offset zeroed).",
        stage="registration",
    ),
    "prep.canvas": H(
        "The reference frame's size and the common valid rectangle after the warps (even sides); every k<i>.png is this crop.",
        stage="registration",
    ),
    "prep.scale_to_canvas": H(
        "The still's scale onto the canvas; below 1 the still was downscaled first (INTER_AREA), nothing is upscaled.",
        stage="registration",
    ),
    # the readers
    "readers.lab_above_14": H(
        "The share of pixels whose Lab distance between two neighbouring stills is above 14 (the change matte's threshold): how much of the frame moves or changes.",
        stage="readers",
    ),
    "readers.laplacian_var": H(
        "The variance of the Laplacian of the grey still: higher is sharper. Two stills that differ by 2× here differ in focus, and the in-betweens will show the shift.",
        stage="readers",
    ),
    "readers.faces": H(
        "YuNet's face boxes on the registered still (x, y, w, h in canvas px and the score).", stage="readers"
    ),
    # the records and the chips
    "chip.running": H(
        "The process runs; the number is its progress from the log (PROGRESS i n: i frames done of a planned total, an estimate; a sheets step plans one frame more than it renders), the lines are the log's tail. Cancel sends SIGTERM to its process group."
    ),
    "chip.done": H(
        "The process exited 0 and its outputs were renamed from the .part folder: an output that exists is one that finished."
    ),
    "chip.failed": H("The process exited with an error; the reason is the log's last line."),
    "chip.refused": H(
        "The script declined the input on purpose (exit 2 with a FAILED: line): the reason names the problem; the fix is in the knobs or the inputs, never in the detector."
    ),
    "chip.lost": H(
        "The server restarted while the stage ran, and no terminal file was found when its process was gone: run it again."
    ),
    "chip.cancelled": H("Cancelled by you; the .part folder was removed."),
    "chip.stale": H(
        "An upstream stage ran again after this one: its outputs may no longer match the inputs. Rerun from here."
    ),
    "chip.draft": H(
        "Rendered at a long edge below the prep canvas: a draft shows the timing, not what a skeptic can judge."
    ),
    "chip.generated": H(
        "A model drew this frame (a RIFE in-between): the violet mark follows it on the strip, the scrubber and the sheet."
    ),
    "chip.unjudged": H(
        "No skeptic verdict exists for this md5 (none yet, or the render changed after the verdict). The page refuses it unless you override, and the override is printed on the page."
    ),
    "chip.READY": H("The skeptic's verdict: no fault found at full size."),
    "chip.READY WITH A NOTE": H("The skeptic's verdict: a fault worth a note on the page, not a block."),
    "chip.NOT READY": H("The skeptic's verdict: a fault he would see; the page refuses it unless you override."),
    "chip.waiting": H(
        "A request file waits for the Claude Code session; the age is since it was written. `reveal-studio requests` lists it at the session's boot."
    ),
    "chip.answered": H("The session wrote its answer into answers/."),
    "chip.ungraded": H("The round's page exists and no grade text is saved."),
    "chip.graded": H("His grade text is saved verbatim with the page md5 it was given on."),
    # ---- the chips whose key had no row (Fable review F2, 2026-11-05): chip() maps a text with a number or a
    # suffix to its state word (core.js chipKey), and a value chip names its key
    "chip.none": H(
        "Nothing yet: the stage has no record and no output in this job. The tile's detail line says what it waits for."
    ),
    "chip.saved": H(
        "The job holds one or more plans saved from the editor under plans/; the frozen plans are only read."
    ),
    "chip.cancelling": H(
        "Cancel was sent: SIGTERM to the stage's process group, then SIGKILL after 5 s; the record then reads cancelled."
    ),
    "chip.ungraded by his word": H(
        "He chose not to grade this round in words. The round gate lets the next round's first full render start."
    ),
    "chip.round": H(
        "The job's latest round: its number, and whether his grade text is saved (graded), absent (ungraded) or waived on his word."
    ),
    "chip.candidates": H(
        "The job's full renders, and how many of them lack a skeptic verdict on their current md5 (unjudged)."
    ),
    "chip.above_6": H(
        "This sequence holds more stills than the longest sequence of the loops work before the studio: 6 (evgen-thug, 2026-10-30). The boxes' seven stills of 2026-11-05 were the first above it, through the studio. No script states a limit, so the import goes ahead."
    ),
    "chip.above_10": H(
        "This sequence holds more stills than the design's range of 2 to 10 per sequence (STUDIO.md §1). No script states a limit, so the import goes ahead."
    ),
    "chip.adopted": H(
        "A run folder made before the studio, opened in place: its prep, renders and page are read where they are, and the studio's records live in the job's own folder."
    ),
    "chip.server unreachable": H(
        "The page's last request to the studio server failed. The page retries every 5 s; if the server stopped, start it again with `reveal-studio serve`."
    ),
    "chip.model_ready": H("The model's manifest reads, so the scripts load the model from disk with no network call."),
    "chip.model_missing": H(
        "The model's manifest is absent or does not read: a stage that needs the model skips it or refuses. Only the tool's warmup, run from the shell, fetches a model."
    ),
    "chip.tag": H(
        "The frame's kind: the loop reads it from frames.json, a pair or a director render tags its frames from its own record. Photo is a still held byte-exact, blend a mix of two stills, snap a blend with motion blur, rewind a stretch of an earlier step played backwards. k is the still's index, t the place between two stills (0 to 1)."
    ),
    "chip.method": H(
        "The method of the transition this frame belongs to (frames.json), for a frame no model drew: dissolve, morph and the other methods mix or move the two stills."
    ),
    "chip.frame": H("The frame under the scrubber: f 0 is the loop's first frame."),
    "chip.dexp": H(
        "The frame's double-exposure share from frames.json (Rule 7): of the pixels inside the leg's matte, the share within 20 levels of the two stills' mean and more than 20 from each. A leg that moves a region records it over the rest of the frame (dexp_rest)."
    ),
    "chip.required": H("The plan schema marks this key required: the render fails without it."),
    # the regions and controls
    "region.rail": H(
        "The jobs (name, flow, the last render's state, the round), the running tasks with their elapsed seconds, the models' readiness. Up and down move the selection, Enter opens."
    ),
    "region.strip": H(
        "The job's stages as tiles, left to right in the flow's order: the thumbnail, the name, the wall time and the state chip; a violet tick where generated content exists; the selected one outlined amber. Left and right move the selection."
    ),
    "region.panel": H("The selected stage's content: its outputs, its history, rerun from here."),
    "region.inspector": H(
        "One row per knob of the selected stage: the literal key, the value, the range, the default and the sentence. Below them sit the provenance (the plan's sha256, the script's md5, the outputs' md5s), the command line that reproduces the stage from the shell, and cancel for a running stage. A director resolve or render shows the knobs its panel sends, read-only."
    ),
    "region.viewer": H(
        "One large picture under judgement: source A (the render's current frame by default), with B beside it as a wipe, a flicker, an onion skin or a difference. The first and the last still sit small beside it. Space plays at the clip's own rate (the loop 25 fps, a director clip 30, a pair its spec's) while the focus is on the picture, the scrubber or no control. Left and right step one frame, shift by ten, and `,` and `.` do the same. m marks the frame as a fault, saved under owner_frames/."
    ),
    "region.axis": H(
        "The shared frame axis: the scrubber, the step series with its stalls (bands) and jumps (ticks), the generated bands, the skeptic's markers and one stability plot per measured window, all at the same x. A click on a plot moves the scrubber. On the loop's step plot the dashed line is the 0.3 stall bar."
    ),
    "control.rerun": H(
        "Runs the stage again with the inspector's knobs into a new record; the stages after it go stale until they run again."
    ),
    "control.cancel": H(
        "SIGTERM to the stage's process group; the record is marked cancelled and its .part folder removed."
    ),
    "control.command": H(
        "The argv that reproduces this record from the shell: the CLI and the studio read and write the same files."
    ),
    "control.save_plan": H(
        "Saves the editor's JSON as a new plan of this job with a provenance block (from which plan, which keys changed, your words); a plan saved from the page is recorded as the owner's. Unknown top-level keys, methods, eases and effect kinds are refused with the known list."
    ),
    "control.render": H(
        "Renders into <seq>/<name>/ (full) or drafts/<seq>/<name>/ (a draft). The loop renders the chosen plan with the job's prep as `in`, a pair its knobs, a director concept its plan under run/. The record shows the progress number and the log."
    ),
    "control.request_skeptic": H(
        "Writes requests/skeptic_<stamp>.json with the candidates' md5s and your brief; the session answers with answers/skeptic_<stamp>.json (a verdict per candidate on the md5 judged) and a report with crops."
    ),
    "control.page": H(
        "Builds the review page over every full render of the sequence by loop_seq.py page, behind the review gate. The gate refuses the page while a candidate is unjudged or NOT READY, unless you override, and the page prints the override. The page's md5 opens a round."
    ),
    "control.grade": H(
        "Saves his words verbatim for the round, with the page md5 they were given on. The next round's first render waits for this text, or for 'ungraded by his word'."
    ),
    "control.adopt": H(
        "Opens a run folder made before the studio existed (benchmarks/runs/<date>/<run>) as a job: its prep, its renders and its page are read in place; the studio's records live in its own folder. The existing page becomes round 1."
    ),
    "control.new_job": H(
        "A new loop job from a folder of developed JPGs (sorted by name = capture order; ARW and XMP ignored): symlinks and sha256s, nothing copied."
    ),
    "control.mark_frame": H("Saves the frame index and your note under owner_frames/ for the next round."),
    # ---- the controls that carried no key of their own (critique A2, P2 11: the "?" leaves the Tab order, so each
    # control names its hint and its focus opens it)
    "control.candidate": H(
        "Opens this render in the viewer: its frames on the scrubber, its measures in the inspector, and the loop's plan as rendered."
    ),
    "control.knob_reset": H("Returns the knob to the last run's value, or to its default when the stage has not run."),
    "control.play": H(
        "Plays the render at 25 fps from the current frame, and pauses it. Space does the same while the focus is on the picture, the scrubber or no control."
    ),
    "control.mp4": H("Opens the render's loop.mp4 in a new tab, as the browser plays it."),
    "control.scrub": H(
        "The frame under judgement on the shared axis: left and right step one frame, shift ten, and the plots below share its x."
    ),
    "control.cmp_ab_flip": H("Flips the picture between A and B; the a key does the same while the A/B mode is on."),
    "control.page_override": H(
        "Builds the page although a listed candidate is unjudged or NOT READY, on his word; the page and the round print the override with the reasons."
    ),
    "control.grade_skip": H(
        "Marks the round ungraded by his word: no grade text is saved, and the next round's first full render may start."
    ),
    # ---- A2: the registration fits, the probe, the measures, the viewer and the graph (agent E)
    "prep.windows": H(
        "Named windows of frame 0 in px before the crop (the px of lock_window), typed as 'name:x0,y0,x1,y1;...'. The prep measures where each window's content sits in every registered frame under each fit and applies none of it. A window named for an object is drawn on the still and looked at before its number is used: the angel sheet's first probe read ring windows that sat 150 px left of the ring.",
        default="",
        stage="registration",
        source="loop_seq.py prep --help; benchmarks/2026-11-04-angel.md",
    ),
    "prep.fits": H(
        "One column group per fit the prep made, in the order all, far, chain, ecc, final. dx and dy are where frame 0's window content sits in frame i after that fit (px, positive right and down); corr is the template match's peak (−1 to 1). all: the SIFT fit on every keypoint. far: the masked fit of bg_depth. chain: the fit through frame i − 1. ecc: the ECC fallback or ecc_refine. final: frame i as the prep writes it, after the lock.",
        stage="registration",
        source="SCHEMA.md 2026-11-05",
    ),
    "prep.edge": H(
        "The match's peak lies on the border of the ±30 px search, so the content sits at or beyond it and the offset is a bound. The lock applies such a value as if it were measured: move or grow the window.",
        stage="registration",
        source="SCHEMA.md 2026-11-05",
    ),
    "prep.largest_offset": H(
        "Per fit, the window that moved most and the length of its offset (px). Under the lock on the angel pair, final held the three ring windows within 2.14 px while the exit sign moved 27 px.",
        stage="registration",
        source="research/2026-11-05/loopseq_a2.md",
    ),
    "prep.windows_jpg": H(
        "windows.jpg: frame 0 at a 960 px long edge with the windows and their names, one panel per registered frame. Each fit draws an arrow from the window's centre at 8 times its offset (all orange, far blue, chain magenta, ecc green, final red). Show sends it to the viewer.",
        stage="registration",
        source="SCHEMA.md 2026-11-05",
    ),
    "measure.probe_dexp": H(
        "Rule 7's double-exposure share of an in-between: the share of pixels within 20 levels of the two stills' mean and more than 20 from each, the pixels that read as both stills at once. inside: within the change matte, where the stills differ; frame: over the whole frame, the value a whole-frame RIFE render records. A high share warns of a ghost: a doubled edge, mouth or prop. On handheld pairs the floor is 3–11 % even where nothing doubles, so the probe has no bar and its table shows no verdict: compare the methods, then read the face crops. The share reads closeness to the mean, so a dissolve away from t 0.5 scores near 0.",
        stage="probe",
        source="loops.md §6; SCHEMA.md 2026-11-05",
    ),
    "measure.probe_step": H(
        "The mean absolute difference between the in-between and still i, and still j (0–255): how far the frame sits from each end.",
        stage="probe",
        source="SCHEMA.md 2026-11-05",
    ),
    "measure.probe_strips": H(
        "Per pair and method, the in-betweens at t 0.25, 0.5 and 0.75 side by side, each labelled with its t. rife: RIFE v4.26 over the whole frame, as a leg with matte all renders it. morph: transitions.py's DIS morph, whose sine ease puts the warp at 0.15, 0.5 and 0.85. dissolve: the plain blend.",
        stage="probe",
        source="SCHEMA.md 2026-11-05",
    ),
    "measure.probe_crops": H(
        "1:1 crops at the YuNet face boxes of the pair, each box grown 25 % on every side: the two stills, then every method at every t. A doubled mouth or prop shows here before any number.",
        stage="probe",
        source="SCHEMA.md 2026-11-05",
    ),
    "chip.rife skipped": H(
        "The probe made no RIFE strip: RIFE_MANIFEST.json is missing or a weight failed its sha256 (the reason is beside the chip). The morph and dissolve strips are there.",
        stage="probe",
    ),
    "chip.edge": H(
        "This offset's peak lies on the border of the search, so the number is a bound: the content sits at least this far.",
        stage="registration",
    ),
    "chip.within": H("The measure is inside its bar."),
    "chip.past bar": H("The measure crosses its bar: look at the frames it names before the page."),
    "chip.not run": H("The stage has no record in this job yet: set its knobs in the inspector and run it."),
    "measure.stability": H(
        "Per window, where frame ref's window content sits in every frame (dx, dy px, sub-pixel by template match over the window grown 30 px; positive right and down): an object's stability under the loop's motion and effects. dx is the solid line in the text colour and dy the dashed line in the muted colour, on the shared frame axis.",
        stage="measure",
        source="loop_seq.py measure --help",
    ),
    "measure.stability_max": H(
        "Per window, the largest |dx| and |dy| with the frame each sits at, the lowest correlation, and the frames whose peak lay on the search's border. No bar is recorded. The angel sheet read the ring's top window at most 1.2 px sideways and 4.2 px up over a1–a3, the vertical at the breath's peak (frames 24–26). A window needs texture in both directions: the right ring window slid along its arc in whole-pixel jumps.",
        stage="measure",
        source="benchmarks/2026-11-04-angel.md; research/2026-11-05/loopseq_a2.md",
    ),
    "measure.stalls": H(
        "Runs of two or more consecutive steps below 0.3 grey levels while motion is open (both frames of each step are in-betweens, neither one a hold): the picture stops mid-motion. Drawn as a band in the failed colour on the shared frame axis.",
        stage="render",
        source="loops.md §6",
    ),
    "measure.jumps": H(
        "Steps above 3× the mean of their two neighbours (the first and the last step: their one neighbour), outside a declared cut or snap: a frame the eye reads as a jump. A step below the 0.3 stall bar reads as a stop and is never a jump, so the encoder's noise in a hold (0.01 against 0.0) stays off the list. Drawn as a tick in the failed colour on the shared frame axis.",
        stage="render",
        source="loops.md §6",
    ),
    "control.measure": H(
        "Runs loop_seq.py measure on the selected render's loop.mp4 with its frames.json and the windows typed here, in px of the mp4 (a draft's px are the canvas px scaled by its long edge). Each run writes a new folder under the render's measures/; the render's own files stay as they are.",
        stage="measure",
    ),
    "control.probe": H(
        "Runs loop_seq.py probe on this job's prep at the long edge of the knobs, into in/<seq>/probe/ (3.1 s for one pair at 960 px with RIFE loaded, measured 2026-11-05); a rerun replaces the folder.",
        stage="probe",
    ),
    "control.show": H(
        "Sends this output to the viewer as A, in the single view: the viewer's A and B lists hold the render's current frame, the registered stills, windows.jpg and the last output shown."
    ),
    "control.zoom_fit": H("The image scaled to fit the viewer; every compare mode keeps the zoom."),
    "control.zoom_1to1": H("One image pixel per screen pixel; scroll the viewer to move around."),
    "control.zoom_2x": H("Two screen pixels per image pixel, drawn without smoothing (image-rendering: pixelated)."),
    "control.cmp_single": H("One image: A (the render's current frame when a render is open)."),
    "control.cmp_wipe": H(
        "Reveal's slider: A left of the split, B right. Drag on the picture, or focus the handle and press left and right (1 %, shift 10 %)."
    ),
    "control.cmp_ab": H(
        "A or B, one at a time: the flip button beside the sources or the a key flips between them, and a flicker shows a shift the eye misses side by side."
    ),
    "control.cmp_onion": H("B over A at the opacity slider's value (0–100 %, default 50)."),
    "control.cmp_diff": H(
        "|A − B| per channel, stretched ×4 and clipped at 255, drawn on a canvas in the browser after B is resampled to A's size. Black is equal; a shift shows as bright edges."
    ),
    "control.cmp_a": H(
        "Source A: the render's current frame (it follows the scrubber), a registered still k<i>.png, windows.jpg, or the last output sent by show."
    ),
    "control.cmp_b": H("Source B: the same list as A; B is drawn at A's size."),
    "control.onion_opacity": H("B's opacity over A in the onion skin, 0–100 % (default 50)."),
    "control.wipe_handle": H(
        "The split's position from the left, 0–100 % of the width (default 50); left and right move it 1 %, shift 10 %."
    ),
    "region.graph": H(
        "The job as a graph: the stages as nodes left to right in the flow's order, an optional stage (readers, probe, measure) in a row under its parent. Each node lists the files its latest record read (left) and wrote (right); a line joins a file one record wrote to the record that read it. Click a node or move with the arrows: the panel beneath and the inspector show it as the strip does."
    ),
    "control.view_strip": H("Shows the job's stages as the strip of tiles."),
    "control.view_graph": H(
        "Shows the job's stages as a graph of nodes with the files they read and write and the lines between them."
    ),
    "control.graph_add": H(
        "Lists the optional stages the registry allows after the selected node (readers and probe after the registration, measure under the render); choosing one adds its node and selects it, so the inspector shows its knobs."
    ),
    # ---- A2: the plan editor, the rulings and the page's variants (agent D)
    # the plan schema's keys without an A1 sentence: SCHEMA.md's words, else loop_seq.py's docstrings (2026-11-05)
    "plan.matte.thr": H(
        "The Lab distance above which a pixel counts as changed, measured on 2 px blurred copies of the two stills.",
        default=14,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.matte.grow": H(
        "The change matte's dilation as a share of the width.", default=0.015, stage="render", source="SCHEMA.md"
    ),
    "plan.matte.feather": H(
        "The change matte's Gaussian feather as a share of the width.", default=0.01, stage="render", source="SCHEMA.md"
    ),
    "plan.matte.min_share": H(
        "Parts of the change matte smaller than this share of the frame are dropped as specks.",
        default=0.0005,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.matte.all": H(
        "true: a rife leg runs RIFE on the whole frame, with no change matte and no plain blend outside it, so the drift a locked or far-field registration leaves rides with the pose change. A through chain, a teleport, a slide and a rise keep the change matte.",
        default=False,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.ease": H(
        "The ease of every sheet's sweep. The code's default is linear; the seasons plans set sine.",
        default="linear",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.local.box": H(
        "The box [x0, y0, x1, y1] in canvas fractions inside which the in-between is RIFE at the box's own ease.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.local.ease": H(
        "The box's own ease of u: under snap a mouth crosses its half-open state in about 3 frames while the leg keeps its ease.",
        default="snap",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.local.feather": H(
        "The feather of the box's edge as a share of the width.", default=0.01, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.morph.preset": H(
        "The transitions.py preset the morph starts from: morph, dissolve, flow-dissolve, snap-morph, iris, wipe or luma.",
        default="morph",
        stage="render",
        source="loop_seq.py, transitions.py",
    ),
    "plan.timeline.morph.anchors": H(
        "Hand anchors 'ax,ay,bx,by;...' in canvas px: each ties a point of the current still to a point of the next one.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.morph.falloff": H(
        "transitions.py's anchor_falloff for this leg, read only with anchors; transitions.py clamps it to 0–0.5.",
        default=0.25,
        stage="render",
        source="loop_seq.py, transitions.py",
    ),
    "plan.timeline.morph.warp": H(
        "transitions.py's warp_amount for this leg: 0 is a plain dissolve on the skeleton; transitions.py clamps it to 0–1.",
        default=1.0,
        stage="render",
        source="loop_seq.py, transitions.py",
    ),
    "plan.timeline.morph.color": H(
        "transitions.py's color_strength for this leg: the colour pull over time; transitions.py clamps it to 0–1.",
        default=0.7,
        stage="render",
        source="loop_seq.py, transitions.py",
    ),
    "plan.timeline.teleport.out_box": H(
        "A box [x0, y0, x1, y1] in canvas fractions around content of the current still that is absent in the next one.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.teleport.in_box": H(
        "A box in canvas fractions around content of the next still that is absent in the current one.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.teleport.mode": H(
        "squeeze: the content squeezes to a bright vertical line and re-opens; fade: the content fades in place. The rest of the changed area goes by RIFE.",
        default="squeeze",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.teleport.span": H(
        "squeeze only: the share of the segment each half takes.", default=0.6, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.teleport.glow": H(
        "squeeze only: the brightness gain at the line.", default=0.6, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.teleport.box_thr": H(
        "The Lab difference above which a pixel inside a box counts as the moved person: higher than the change matte's, so a neighbour's small shift drops out. The group-teleport plan sets 24.",
        default=30.0,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rewind.from": H(
        "The frames rendered so far from this index are played backward.", default=0, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.rewind.stride": H(
        "Every stride-th frame of the backward run is kept.", default=3, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.snap.blur_frac": H(
        "The plain blend blurred along direction by a line whose length is blur_frac of the height times sin(πt): a whip that hides the double exposure of a big move. Nothing is generated; the playbook's snaps use 1.5–2.2 %.",
        default=0.015,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.snap.direction": H(
        "The blur's direction: vertical or horizontal.", default="vertical", stage="render", source="loop_seq.py"
    ),
    "plan.timeline.slide.box_a": H(
        "The moved person's box in the current still, in canvas fractions; her matte is read inside it.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.box_b": H(
        "Her box in the next still, in canvas fractions.", stage="render", source="loop_seq.py"
    ),
    "plan.timeline.slide.matte_a": H(
        'How her matte in the current still is read: {"kind": "box", "thr": 24} thresholds the Lab difference, {"kind": "grabcut"} runs GrabCut; "exclude" lists boxes zeroed afterwards and "erode" shrinks it by a share of the width.',
        default={"kind": "box", "thr": 24},
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.matte_b": H(
        "How her matte in the next still is read, in the shape of matte_a.",
        default={"kind": "grabcut"},
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.mode": H(
        "fly: her cutout travels between her two places with a motion blur over a RIFE base with her removed. dissolve: her old cutout fades out in place and the new one fades in at the destination while the others morph underneath.",
        default="fly",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.window": H(
        "fly only: the part [w0, w1] of the segment in which she travels.",
        default=[0.2, 0.8],
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.window_out": H(
        "dissolve only: the part of the segment over which her old cutout fades out.",
        default=[0.0, 0.55],
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.window_in": H(
        "dissolve only: the part of the segment over which her new cutout fades in.",
        default=[0.45, 1.0],
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.slide_ease": H(
        "fly only: the ease of her travel inside the window.", default="sine", stage="render", source="loop_seq.py"
    ),
    "plan.timeline.slide.blur": H(
        "fly only: a motion blur along her move on the frames where she moves more than 2 px.",
        default=True,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.blur_k": H(
        "fly only: the blur's length in px per px of her speed.", default=0.5, stage="render", source="loop_seq.py"
    ),
    "plan.timeline.slide.fill": H(
        "How her spot in the next still is filled for the base: vertical takes the wall from above and the floor from below. donor+vertical then puts back the current still's own background where it shows one. Any other value takes the current still's background, else the wall extended.",
        default="donor+vertical",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.floor_y": H(
        "The row, as a share of the height, below which the vertical fill takes the floor from below; absent, the wall from above everywhere.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slide.donor_box_b": H(
        "A box of the current still, in canvas fractions, around someone standing at her destination: his matte is kept out of the donor fill.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.ghoul_box": H(
        "The box, in canvas fractions, of the person present in one still only: the one who rises.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.man_box": H(
        "The box, in canvas fractions, of the person in front, whose own GrabCut matte occludes the rise.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.matte_ghoul": H(
        "How the rising person's matte is read, in the slide's matte shape.",
        default={"kind": "grabcut"},
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.matte_man": H(
        "How the front person's matte is read, in the slide's matte shape.",
        default={"kind": "grabcut"},
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.direction": H(
        "up: the person rises (present in the next still); down: the person sinks (present in the current still).",
        default="up",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.start_offset": H(
        "Where the rise starts, as [dx, dy] shares of W and H from the person's place.",
        default=[0, 0.1],
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.window": H(
        "The part [w0, w1] of the segment in which the person rises.",
        default=[0.35, 1.0],
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.rise_ease": H(
        "The rise's ease inside the window.", default="smooth", stage="render", source="loop_seq.py"
    ),
    "plan.timeline.rise.fill": H(
        "How the person's spot is filled for the base: vertical takes the wall from above; any other value takes the other still's background, else the wall extended.",
        default="vertical",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.floor_y": H(
        "The row, as a share of the height, below which the vertical fill takes the floor from below.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.rise.man_box_other": H(
        "A box of the other still, in canvas fractions, around the man where the person stands: his matte is kept out of the fill.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.timeline.slices.through": H(
        "The stills the cells cycle on through after the next one (a wave); n is then computed from the schedule and overwritten in plan.json.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.angle": H(
        "Degrees of the band lines from the horizontal; 62 crosses the wire of the seasons view at about 88°.",
        default=62.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.bands": H(
        "The number of bands across the canvas.", default=12, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.widths": H(
        "Relative band widths; when given they replace bands.", stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.families": H(
        "1: bands; 2: a lattice, a second family along the band axis, width2 px wide, cells indexed i, j.",
        default=1,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.width2": H(
        "families 2: the second family's width in px; 0 takes the mean band width.",
        default=0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.mirror": H(
        "Folds the bands about the centre column into chevrons: each band is a left and a right half-cell with mirrored slide directions.",
        default=False,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.slide": H(
        "across: the card enters from the neighbouring side over the cell's width; along: the whole band's content rolls along the band by travel × the canvas diagonal and locks.",
        default="across",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.travel": H(
        "along only: how far a band's content rolls, as a share of the canvas diagonal.",
        default=0.4,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.wrap": H(
        "along only: true rolls the canvas round instead of mirroring it; the canvas edge then shows as a hard line inside the band.",
        default=False,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.ramp": H(
        "along only: frames of alpha at the start of each band.", default=3, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.dir": H("The entry side, 1 or −1.", default=1, stage="render", source="SCHEMA.md"),
    "plan.timeline.slices.alternate": H(
        "Flips the entry side on odd cells.", default=False, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.lattice_axis": H(
        "families 2: which family's normal the lattice cells slide along: alt by parity, 1 or 2.",
        default="alt",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.order": H(
        "Each cell's rank: up, down, centre, edges, random (with seed), diag or antidiag (families 2).",
        default="up",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.seed": H("The seed of the random order.", default=1, stage="render", source="SCHEMA.md"),
    "plan.timeline.slices.stagger": H(
        "Frames between ranks: a cell starts at rank × stagger.", default=2, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.dur": H(
        "Frames each cell takes under the step's ease.", default=12, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.period": H(
        "With through: frames between a cell's successive transitions; absent, one transition's span, so they do not overlap.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.flip_each": H(
        "Reverses the entry side on every second transition.", default=True, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.reverse_each": H(
        "Reverses the rank order on every second transition.", default=False, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.samples": H(
        "Sub-frames of the motion blur, at least; raised to one per 2 px of the frame's displacement, at most samples_max.",
        default=6,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.samples_max": H(
        "The ceiling of the motion blur's sub-frames.", default=48, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.shutter": H(
        "The share of the frame's motion the blur covers.", default=0.8, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.slices.shadow": H(
        "Darkens the uncovered side of a card's leading edge; 0 is off.",
        default=0.0,
        rng=[0, 1],
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.slices.shadow_px": H("The shadow's width in px.", default=24, stage="render", source="SCHEMA.md"),
    "plan.timeline.sheets.sheets": H(
        "The sheets, back to front: each a band of a listed still that enters from its side over the held base still and leaves at the other. The step's to is the current still, the base.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.angle": H(
        "Degrees of the sheets' edges from the horizontal.", default=62, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.motion": H(
        "normal: the sheets move along the edge's normal; lateral: the edge keeps its slant at angle and the sheet moves along x, side + entering from the right.",
        default="normal",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.feather": H(
        "The softness of a sheet's edge in prep-canvas px.", default=1.5, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.valid_feather": H(
        "Softens a picture's own edge inside a carried sheet, in prep-canvas px.",
        default=1,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.overlap_alpha": H(
        "The front sheet's opacity where it covers a back sheet; 0.5 shows both.",
        default=1.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.shadow": H(
        "The strength of a contact shadow ahead of the front sheet's leading edge onto what lies beneath, faded while the sheet is a sliver.",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.shadow_px": H(
        "The contact shadow's width in prep-canvas px.", default=40, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.shadow_from": H(
        "front: the shadow is cast from the front sheet's leading edge; all: from every sheet's leading edge, which turns the gap between two facing edges into a tube.",
        default="front",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.parallax": H(
        "Scales the content's move by 1 + parallax × (2 depth − 1) from in/<seq>/depth_k<i>.npy, near more than far.",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.edge_depth": H(
        "Bends the wipe edge with the base still's depth map (blurred 8 px): near pixels are reached later than far ones by up to this many px, and the content never moves.",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.layer_soft": H(
        "The softness of a sheet's depth layer at both ends.", default=0.06, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.shutter": H(
        "Motion blur by sub-samples over this share of the frame's edge motion: a forward window, one sample per 2 px.",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.samples_max": H(
        "The ceiling of the motion blur's sub-samples.", default=24, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.objects": H(
        "Objects on the base: per object a GrabCut matte from its box and, per season, the object Poisson-blended into the base once. The plate fades in lead frames before that season's sheet reaches the object's centre and out linger frames after the sheet leaves it.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.object_feather": H(
        "The feather of the object mattes in prep-canvas px.", default=6.0, stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.sheet.key": H("The still this sheet shows.", stage="render", source="SCHEMA.md"),
    "plan.timeline.sheets.sheet.name": H(
        "A label for the sheet that gen_seasons_bands.py writes; the render does not read it.",
        stage="render",
        source="gen_seasons_bands.py",
    ),
    "plan.timeline.sheets.sheet.side": H(
        "+ or −: the side the sheet enters from; it leaves at the other.",
        default="+",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.width": H(
        "The band's width × the canvas extent along the slide normal; photo takes the whole picture behind its leading edge.",
        default=0.8,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.carry": H(
        "How far the content moves with the sheet: 1 the picture slides and is registered with the base only at home; 0 a wipe over the static still; between, a drift behind the edge.",
        default=1.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.lag": H("Frames the sheet starts late.", default=0, stage="render", source="SCHEMA.md"),
    "plan.timeline.sheets.sheet.dur": H(
        "The sheet's own sweep length in frames; absent, the step's remainder after lag.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.scale": H(
        "Enlarges the content about the centre, a depth cue that misregisters the sheet by scale × the half-size at the edges.",
        default=0.0,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.layer": H(
        "[lo, hi]: the sheet applies only where the base still's depth map lies in this range, 0 far .. 1 near (sky about [-1, 0.06], far [0.04, 0.3], mid [0.26, 0.62], near [0.56, 2]).",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.layer_y": H(
        "[y0, y1] in prep-canvas rows: a row bound on the layer, so the sky layer stops above the skyline.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.sheet.shadow": H(
        "This sheet's own contact-shadow strength, 0 for a summer band over summer, which would otherwise show only as its shadow; absent, the step's shadow.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.object.name": H(
        "The object's name on the log; absent, its box.", stage="render", source="loop_seq.py"
    ),
    "plan.timeline.sheets.object.box": H(
        "The object's box [x0, y0, x1, y1] in prep-canvas px; a draft scales it.", stage="render", source="SCHEMA.md"
    ),
    "plan.timeline.sheets.object.lead": H(
        "Frames the plate fades in before that season's sheet reaches the object's centre. The code's default is 6; the seasons plans set 4.",
        default=6,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.object.linger": H(
        "Frames the plate fades out after the sheet leaves the object. The code's default is 10; the seasons plans set 14.",
        default=10,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.sheets.object.seasons": H(
        "The stills whose plate of this object is blended in; absent, every still but the base.",
        stage="render",
        source="SCHEMA.md",
    ),
    # ---- the repaint leg (SCHEMA.md 2026-11-05: chain_luma.py's draw on registered stills; builder L of phase B)
    "plan.timeline.repaint.through": H(
        "The inner stills of the repaint's chain, in order; without it the leg repaints one pair. The inner stills are passed, never held.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.repaint.front": H(
        "The width of a repaint's front in order units (TR14's luma uses 0.15). It must be above 0.",
        default=0.35,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.repaint.overlap": H(
        "A repaint starts this fraction of a step before its turn and ends as late. The first repaint starts on time and the last ends on time, so a single pair ignores it. With 0 the repaint stops at each still.",
        default=0.35,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.timeline.repaint.zone_erode": H(
        "The union changed region eroded this many px is the drawing zone: the change matte of every consecutive pair (the plan's matte keys), eroded, then blurred at sigma 8 px. Outside the zone one dissolve runs from the first still to the last. Prep-canvas px; a draft scales them.",
        default=15,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.kind": H(
        "breath, parallax or glow; each runs on the finished frames with frame 0 untouched.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.breath.cx": H(
        "The push-in's centre x as a share of the width.", default=0.5, stage="render", source="SCHEMA.md"
    ),
    "plan.effects.breath.cy": H(
        "The push-in's centre y as a share of the height.", default=0.5, stage="render", source="SCHEMA.md"
    ),
    "plan.effects.breath.depth_k": H(
        "Above 0 the breath pushes in by depth (a dolly): the zoom at a pixel is z × (1 + depth_k × clip(d − ref, ±depth_clip)), so near content grows more than the reference plane and far content less. It needs the depth maps.",
        default=0.0,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.effects.breath.depth_clip": H(
        "The clip on d − ref in the dolly's zoom.", default=0.6, stage="render", source="loop_seq.py"
    ),
    "plan.effects.breath.ref": H(
        "The dolly's reference depth, 0 far .. 1 near, read when the plan has no parallax (a parallax's ref wins).",
        default=0.0,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.effects.breath.ref_at": H(
        "[fx, fy] in canvas fractions: the dolly reads its reference depth from frame 0's map at this point, when the plan has no parallax.",
        stage="render",
        source="loop_seq.py",
    ),
    "plan.effects.breath.sigma": H(
        "The blur of the depth maps in px for a dolly without a parallax.",
        default=3.0,
        stage="render",
        source="loop_seq.py",
    ),
    "plan.effects.parallax.ref_at": H(
        "[fx, fy] in canvas fractions: the reference depth is read from frame 0's map at this point instead of ref.",
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.parallax.dir": H(
        "The sway's direction [x, y], normalized.", default=[1, 0], stage="render", source="SCHEMA.md"
    ),
    "plan.effects.parallax.shape": H(
        "sin: sin 2πu, a sway; pulse: sin² πu, one excursion.", default="sin", stage="render", source="SCHEMA.md"
    ),
    "plan.effects.parallax.dir2": H(
        "A second axis [x, y], an orbit with dir; absent, none.", stage="render", source="SCHEMA.md"
    ),
    "plan.effects.parallax.shape2": H(
        "The second axis's wave, sin or pulse.", default="pulse", stage="render", source="SCHEMA.md"
    ),
    "plan.effects.parallax.amp2": H(
        "The second axis's size as a share of amp.", default=0.5, stage="render", source="SCHEMA.md"
    ),
    "plan.effects.parallax.sigma": H(
        "The blur of the depth maps in px before the remap.", default=3.0, stage="render", source="SCHEMA.md"
    ),
    "plan.effects.glow.box": H(
        "The box [x0, y0, x1, y1] in canvas fractions whose bright pixels bloom.",
        default=[0, 0, 1, 1],
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.glow.thr": H(
        "The level of a pixel's brightest channel above which it blooms, inside the box.",
        default=235,
        stage="render",
        source="SCHEMA.md",
    ),
    "plan.effects.glow.sigma": H(
        "The two blur radii as shares of the width.", default=[0.012, 0.05], stage="render", source="SCHEMA.md"
    ),
    "plan.effects.glow.mix": H(
        "The shares of the two radii in the bloom.", default=[0.6, 0.4], stage="render", source="SCHEMA.md"
    ),
    "plan.effects.glow.shape": H(
        "The bloom's wave: pulse (sin² πu) or sin.", default="pulse", stage="render", source="SCHEMA.md"
    ),
    # the plan editor's regions and controls, the ruling chip, the page's variants control
    "region.plan_bars": H(
        "The plan's timeline as bars in one row, left to right: a hold's width is its frames, a transition's its n, a cut a thin marker. Each bar prints its method and ease and the still index at its ends; a bar whose frames a model draws is outlined violet. Left and right move between bars, Enter opens the step's form.",
        stage="plan",
    ),
    "region.plan_effects": H(
        "The effects as bars over the whole loop, one per effect, labelled by kind; Enter opens the effect's form.",
        stage="plan",
    ),
    "region.plan_form": H(
        "The selected step's keys, generated from the plan schema: a field per key with its default as the placeholder and its units. An empty field removes the key, so the code's default applies; a key the schema does not list is shown under other keys with its JSON value.",
        stage="plan",
    ),
    "control.plan_load": H(
        "Loads a plan of this job or a frozen plan into the editor without its provenance block; the history and the change count start from it. The frozen plans are never written.",
        stage="plan",
    ),
    "control.plan_undo": H(
        "Steps back one change in the editor's history. Cmd-Z or Ctrl-Z does the same from any control of the editor; in a field with typing not yet committed it undoes the typing first, and in the JSON text it undoes the typing only.",
        stage="plan",
    ),
    "control.plan_redo": H("Steps forward one change after an undo (Shift-Cmd-Z or Shift-Ctrl-Z).", stage="plan"),
    "control.plan_changes": H(
        "The keys that differ from the loaded plan: the list the provenance block records when you save.", stage="plan"
    ),
    "control.plan_faster": H(
        "Multiplies every hold and every transition's n by (100 − p) % and rounds, at least 1; a cut, a rewind and a slices step keep theirs (their counts come from the frames before them or from their schedule). 20 makes the loop 20 % faster, −50 makes it 50 % slower. One change in the history.",
        stage="plan",
    ),
    "control.plan_add_hold": H(
        "Inserts a hold after the selected step, on the still the timeline is at there; its hold takes the code's default of 1 frame until you set it.",
        stage="plan",
    ),
    "control.plan_add_transition": H(
        "Inserts a transition after the selected step, towards the still of the step that follows; set its n and method in the form.",
        stage="plan",
    ),
    "control.plan_move": H("Moves the selected step one place left or right in the timeline.", stage="plan"),
    "control.plan_remove": H("Removes the selected step or effect; undo brings it back.", stage="plan"),
    "control.plan_add_effect": H(
        "Adds an effect of the chosen kind with its required key empty: breath needs z, parallax needs amp.",
        stage="plan",
    ),
    "control.plan_add_item": H(
        "Adds an item to the list (a local box, a sheet, an object plate); its required keys are marked until they are set.",
        stage="plan",
    ),
    "control.plan_clear": H("Removes the key from the plan, so the code's default applies.", stage="plan"),
    "control.plan_json": H(
        "The same plan as JSON text. An edit enters the history when the text field loses the focus; a parse error is shown under it, and the bars keep the last valid plan until the text parses.",
        stage="plan",
    ),
    "chip.ruled_out": H(
        "A value the owner ruled out, with the date and the reason from the DECISIONS line or the playbook. A warning only: the run goes ahead and its record keeps the warning."
    ),
    "control.page_variants": H(
        "The full renders the page lists and their order: untick one to leave it out, and up and down reorder them. Every one in name order passes no flag; anything else passes --variants a,b. The review gate checks the listed candidates only.",
        stage="page",
    ),
}

HINTS: dict[str, dict[str, Any]] = merge_hints(LOOP_HINTS, PAIR_HINTS, DIRECTOR_HINTS)
