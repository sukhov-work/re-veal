"""The director flow's hints (builder D). Merged into registry.hints.HINTS; a key here must be in no other flow's
table (the merge raises on a duplicate). The prefixes: `control.director_` the page's controls, `director.` the flow's
regions and tables, `resolve.` the resolve panel, `anchors.` the keys of anchors.json, `info.` the measures and keys
of a render's info.json (b_director_research.md §3), and `set.` one row per key of the renderer's `--set` table
(registry/director.SET_KEYS: `set.<key>`, `set.sky.<key>`, `set.tr.<key>`), its sentence the table's own.

A sentence copied from SCHEMA.md or a script's --help names its source in `source`; D:n is director_render.py's line.
"""

from __future__ import annotations

from typing import Any

from reveal_studio.registry.director import SET_KEYS
from reveal_studio.registry.entries import H


def _set_hint(row: dict[str, Any]) -> dict[str, Any]:
    """A `--set` row's hint: its sentence, then the condition the renderer reads it under, or why it is read-only."""
    if row["readonly"]:
        what = f"{row['what']} Read-only: {row['readonly']}."
    elif row["when"] == "always":
        what = f"{row['what']} Read on every render."
    else:
        what = f"{row['what']} Read only when {row['when']}."
    return H(what, default=row["default"], rng=row["range"], stage="render", source=row["source"])


SET_HINTS: dict[str, dict[str, Any]] = {row["hint"]: _set_hint(row) for row in SET_KEYS}

CONTROL_HINTS: dict[str, dict[str, Any]] = {
    "control.director_new_job": H(
        "Makes a director job from a fixture pair that a plan under scripts/research/plans/ names: the two photos linked as records, the layer tables and the mattes of both photos counted, the helper pictures the plans name hashed."
    ),
    "control.director_pair": H(
        "The fixture pairs some director plan names, with each photo's layer table and matte count; a pair without a plan has no director job (mismatch_7, the match and fabra pairs)."
    ),
    "control.director_resolve": H(
        "Runs director_render.py --resolve-only on the plan and concept chosen here: the canvases, the anchors, the camera and every layer's resolved numbers, in about 10 to 14 s at 1920 px. The resolve writes into resolve/<stamp>/ beside run/.",
        stage="resolve",
        source="b_director_research.md §1",
    ),
    "control.director_plan": H(
        "The plan the timeline, the knob tables and the next resolve and render read: a frozen plan of this pair (frozen:<stem>) or a plan saved in this job (job:<name>)."
    ),
    "control.director_concept": H(
        "The concept of the plan: its idea, its beats, its knobs and the renderer's keys with this concept's defaults. The studio checks the name before a run, since director_render.py renders the first concept for an unknown one.",
        source="director_render.py:2095",
    ),
    "control.director_timeline": H(
        "One bar per beat in clip time, 0 the first frame and 1 the last, and one for the end effect. Drag a bar to move its window, or within 6 px of an end to resize it; the window is rounded to 0.01, at least 0.02 wide and kept inside 0 to 1. A dragged bar becomes <name>.window or end_window in the set dict.",
        source="scripts/research/director_ui.py:1042-1059",
    ),
    "control.director_mute": H(
        "Mute sets <name>.skip=true: the renderer leaves the transform out and records it under unplaced.",
        source="director_render.py:891",
    ),
    "control.director_solo": H("Solo mutes every other beat of the concept, so this beat renders alone."),
    "control.director_knob": H(
        "A knob the planner named for this concept, shown in both name forms: the plan's path and the --set key it becomes. Its value replaces the key's value in the set dict; a read-only knob names the reason."
    ),
    "control.director_set": H(
        "A key of the renderer's --set table: tick it to send it, then type its value as JSON. The default shown is this concept's, from the plan or the code."
    ),
    "control.director_extra": H(
        "Extra --set lines, one key=JSON value per line, for a transform param the tables do not list. A key that reaches no frame is refused before the run, with the reason."
    ),
    "control.director_command": H(
        "The command the next render runs, from the plan, the concept, the size and the set dict: one --set per key, in key order."
    ),
    "control.director_last_round": H(
        "Loads the knobs of the newest round render of this plan and concept (benchmarks/runs/*/director_r*/<stem>_<concept>/info.json) into the set dict. Off until pressed: the plan stage never pre-fills them, because the pre-fill hid two knobs in the workbench's acceptance.",
        source="b_design.md decision 2",
    ),
    "control.director_clear": H("Empties the set dict: the next render reads the plan as written."),
    "control.director_draft": H(
        "Renders a draft at 480 px under drafts/<stem>_<concept>[-<tag>]/, outside run/, so the page never lists it; about 10 to 14 s for 90 frames.",
        stage="render",
    ),
    "control.director_full": H(
        "Renders the full size under run/<stem>_<concept>[-<tag>]/, a candidate for the page; 33 to 66 s at 1920 px. A new round's first full render waits for the previous round's grade.",
        stage="render",
    ),
    "control.director_tag": H(
        "The variant's tag, letters, digits and dashes: the folder is <stem>_<concept>-<tag>. Empty names the first render of a stem and concept; a folder that exists is refused, because a finished render is never overwritten.",
        stage="render",
    ),
    "control.director_seconds": H(
        "The clip's length in seconds; seconds times fps is the frame count, 3 or more.", stage="render"
    ),
    "control.director_fps": H("Frames per second of the mp4; the viewer plays the clip at this rate.", stage="render"),
    "control.director_overlay": H(
        "An overlay of the layer table on the photo: the elements in their group's colour with white borders, the disparity in the TURBO colour map, or one element's matte in magenta with a yellow outline.",
        source="scripts/research/director_ui.py:526-579",
    ),
    "control.director_both": H("Turns an overlay on or off on both photos at once."),
    "control.director_opacity": H("The overlays' opacity over the photo, 0 to 100 %."),
    "control.director_element": H(
        "An element of the layer table. A click shows its matte: the matting model's el_<id>.png, or the hard element mask when the file is missing, named as a fallback."
    ),
    "control.director_page": H(
        "Builds the page with director_page.py over the run folder, behind the review gate; the notes come from the skeptic's look and faults per clip. The page is written in place and the previous one is kept beside the record.",
        stage="page",
    ),
    "control.director_grade": H(
        "His grade per clip in the picks shape: one picture, content transforms, nothing invented, acceptable as-is and a note, with the marked frames; the best clip per plan; his words verbatim beside them.",
        stage="grades",
        source="director_page.py:155-160",
    ),
    "control.director_best": H(
        "The best clip of a plan, as <concept>[-<tag>], or none.", stage="grades", source="director_page.py:159"
    ),
}

DIRECTOR_HINTS: dict[str, dict[str, Any]] = {
    "director.photos": H(
        "The pair's two photos: A is fixtures/<pair>_S.*, B is fixtures/<pair>_F.*, each with its sha256, its layer table's element count and its matte files. The renderer reads them by the plan's pair, so the job's links are records.",
        source="director_render.py:420-421",
    ),
    "director.elements": H(
        "The layer table of a photo: per element its id, label, group, share of the canvas, depth rank (1 nearest) and median disparity, and whether its soft matte exists.",
        source="layers.json of benchmarks/runs/2026-09-28/layers_v3",
    ),
    "director.overlap": H("The labels found in both photos, with the share of each photo's canvas they cover."),
    "director.plan_identity": H(
        "The plan's file, its sha256, the pair's relation and the planner that wrote it. A frozen plan is a tracked input and is never written."
    ),
    "director.idea": H("The planner's own sentence: what the viewer sees.", source="SCHEMA.md:15"),
    "director.risk": H("The planner's own risk note: where the concept can fail.", source="SCHEMA.md:23"),
    "director.readonly": H(
        "A key the renderer reads too early or never: setting it changes no frame, so the studio refuses it before a run and names where to make the change."
    ),
    "director.condition": H(
        "The condition under which the renderer reads the key at all. A row whose condition this concept's container rules out is shown faint; its value would change nothing."
    ),
    "director.motion_note": H(
        "Under the motion model the renderer may move a beat earlier to overlap the one before; the resolve's motion.adjusted lists where.",
        source="SCHEMA.md:184-190",
    ),
    "director.verdict": H(
        "Reveal's strict alignment of B onto A, run on demand as the shared branch under the import; on mismatch_3 it refuses, since the photos are unrelated."
    ),
}

RESOLVE_HINTS: dict[str, dict[str, Any]] = {
    "resolve.canvas_A": H(
        "A's crop as the render uses it: the layer table's centred cover crop, re-cropped round the anchor under a disc container.",
        stage="resolve",
        source="director_render.py:587-611",
    ),
    "resolve.canvas_B": H("B covered to the canvas.", stage="resolve", source="director_render.py:426"),
    "resolve.quad": H(
        "The quad or rect container in B's canvas px: A's whole frame maps onto it by a homography or a similarity.",
        stage="resolve",
        source="SCHEMA.md:28-31",
    ),
    "resolve.camera": H(
        "The camera the renderer derives from the container and the first anchor: sim, one similarity, or homog, one homography; S_A3 maps A's canvas into B's.",
        stage="resolve",
        source="director_render.py:349-355",
    ),
    "resolve.layers": H(
        "Every layer the concept places, with its kind, its window in clip time and its depth; recede and line_to layers add their resolved centres, radii and angles.",
        stage="resolve",
        source="director_render.py:1802",
    ),
    "resolve.adjusted": H(
        "motion.adjusted: a beat moved earlier to overlap the one before, from its plan window to the moved one.",
        stage="resolve",
        source="SCHEMA.md:188-190",
    ),
    "resolve.held": H(
        "motion.held: a layer's end held until the guard releases its target, the window's end moved to the guard's arrival.",
        stage="resolve",
        source="SCHEMA.md:224-227",
    ),
    "resolve.front_elements": H(
        "B's front: the elements nearer than the container, each with its median disparity; forced marks the plan's front_ids.",
        stage="resolve",
    ),
    "resolve.matte_fallbacks": H(
        "photo:id of each element drawn with its hard mask, because its el_<id>.png is missing.",
        stage="resolve",
        source="SCHEMA.md:93-96",
    ),
}

ANCHORS_HINTS: dict[str, dict[str, Any]] = {
    "anchors.pair": H("The pair the plan names.", stage="resolve", source="director_render.py:1802"),
    "anchors.concept": H("The concept the resolve built.", stage="resolve", source="director_render.py:1802"),
    "anchors.canvas": H("The canvas in px, width and height.", stage="resolve", source="director_render.py:1802"),
    "anchors.frames": H(
        "The frame count, seconds times fps; the resolve takes the CLI's 3 s and 30 fps.",
        stage="resolve",
        source="director_render.py:1795",
    ),
    "anchors.anchors": H(
        "The resolved anchors, a0 in A and b0 in B with a centre and a radius, under a disc container only; empty for a quad.",
        stage="resolve",
        source="director_render.py:611, 1801",
    ),
    "anchors.layers": H(
        "Every placed layer's name, kind, window and depth, with the numbers the kind resolves.",
        stage="resolve",
        source="director_render.py:1802",
    ),
    "anchors.info": H(
        "The scene's info, the same object a render's info.json opens with: the container, the camera, the parallax, B's front, the motion and the matte fallbacks.",
        stage="resolve",
        source="director_render.py:1803",
    ),
    "anchors.camera": H("The camera's kind and its matrix S_A3.", stage="resolve", source="director_render.py:1804"),
    "anchors.renderer_md5": H(
        "The md5 of director_render.py at the resolve.", stage="resolve", source="director_render.py:1805"
    ),
}

INFO_HINTS: dict[str, dict[str, Any]] = {
    "info.motion_px": H(
        "The mean DIS flow between consecutive decoded frames, computed at 480 px or less and scaled to frame px: entry j is frames j to j + 1. No bar is stated for the whole frame.",
        stage="render",
        source="director_render.py:2038-2045; SCHEMA.md:191-193",
    ),
    "info.motion_median_px": H(
        "The median of motion_px from 10 % to 90 % of the list, in px.",
        stage="render",
        source="director_render.py:2048-2049",
    ),
    "info.motion_pauses": H(
        "The entries from 10 % to 90 % of motion_px under a fifth of the median: the renderer's pauses.",
        stage="render",
        source="director_render.py:2050; SCHEMA.md:193-194",
    ),
    "info.motion_jumps": H(
        "Consecutive motion_px entries that differ by more than the larger of 1 px and half the median, over the whole list.",
        stage="render",
        source="director_render.py:2051",
    ),
    "info.b_inside": H(
        "On every third frame and the last, the share of A's region inside the camera's view where B shows, read after the guard, as [frame, share] pairs.",
        stage="render",
        source="director_render.py:1936-1942; SCHEMA.md:207-208",
    ),
    "info.b_inside_first": H(
        "The first sampled frame where B shows over 1 % of A's region. Rule 1's bar: at or after the first beat's start, unless the plan declares an early region.",
        stage="render",
        source="director_render.py:2055; retrospective.md §4 rule 1",
    ),
    "info.residual_edges": H(
        "On every third interior frame, the share of pixels at 720 px or less that are Canny edges of the frame and lie more than 3 px from every edge of A and of B through the camera.",
        stage="render",
        source="director_render.py:1985-1995",
    ),
    "info.residual_edge_max": H(
        "The largest residual_edges value. Rule 5's bar: 0.2 % of the pixels; a ring or a band the photos lack raises it.",
        stage="render",
        source="director_render.py:2056; retrospective.md §4 rule 5",
    ),
    "info.halo": H(
        "On every third interior frame under a disc with a recede layer: the frame, the largest step between 10 px radial bins round the brightest blob's core, the deepest ring and the blob's radius; null on other pairs.",
        stage="render",
        source="director_render.py:2002-2036; SCHEMA.md:265-269",
    ),
    "info.halo_step_max": H("The largest halo step, in levels.", stage="render", source="director_render.py:2057"),
    "info.halo_ring_max": H("The deepest halo ring, in levels.", stage="render", source="director_render.py:2058"),
    "info.guard": H(
        "The guarded targets: the transform's name, the beat progress at which B's target may show and the share of B the grown target covers.",
        stage="render",
        source="director_render.py:1348",
    ),
    "info.guard_share_max": H(
        "The largest share of the frame where the guard held A's base.",
        stage="render",
        source="director_render.py:1935, 2054",
    ),
    "info.step_first": H(
        "The mean absolute difference over three channels between decoded frames 0 and 1, in levels.",
        stage="render",
        source="director_render.py:2014, 2052",
    ),
    "info.step_second": H("The step between decoded frames 1 and 2, in levels.", stage="render"),
    "info.step_last": H("The step between the last two decoded frames, in levels.", stage="render"),
    "info.step_max": H("The largest step between consecutive decoded frames, in levels.", stage="render"),
    "info.steps_decoded": H(
        "The whole step series, decoded from transition.mp4 by the studio with the renderer's own rule and cached under cache/steps/; info.json keeps four values of it.",
        stage="render",
        source="director_render.py:2014",
    ),
    "info.plate_A_share": H(
        "The share of A's canvas filled under its lifted layers, by pull-push.",
        stage="render",
        source="director_render.py:1393-1398",
    ),
    "info.matte_fallbacks": H(
        "photo:id of each element drawn with its hard mask because its el_<id>.png is missing; rule 5 names a fallback as a source of hard edges.",
        stage="render",
        source="director_render.py:224-230; SCHEMA.md:93-96",
    ),
    "info.unplaced": H(
        "Each transform left out, with the reason: an empty a-mask, the operator's skip or no keyframes.",
        stage="render",
        source="director_render.py:891-893, 925-928, 1179-1180",
    ),
    "info.wall_s": H(
        "Seconds from the scene's start to the end of the measures; the montage and the JSON come after.",
        stage="render",
        source="director_render.py:1791, 2053",
    ),
    "info.renderer_md5": H(
        "The md5 of director_render.py at the run; a reproduction carries the recorded one.",
        stage="render",
        source="director_render.py:2100",
    ),
    "info.transitions_md5": H(
        "The md5 of transitions.py, which the renderer imports for its encoder and its morph.",
        stage="render",
        source="director_render.py:2101",
    ),
    "info.plan_sha256": H(
        "The plan's sha256, its first 16 hex characters; the render's record keeps the full one.",
        stage="render",
        source="director_render.py:2099",
    ),
    "info.knobs": H(
        "The --set knobs of the run, as the renderer parsed them.", stage="render", source="director_render.py:2053"
    ),
}

HINTS: dict[str, dict[str, Any]] = {
    **CONTROL_HINTS,
    **DIRECTOR_HINTS,
    **RESOLVE_HINTS,
    **ANCHORS_HINTS,
    **INFO_HINTS,
    **SET_HINTS,
}
