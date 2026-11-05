"""The pair flow's hints (builder P, phase B). Merged into registry.hints.HINTS; a key here must be in no other flow's
table (the merge raises on a duplicate). The prefixes: `control.pair_` for the flow's controls, `report.` for the
numbers of transitions.py's report.json and the studio's decode of the mp4, `relation.` for the relation panel and
`verdict.` for Reveal's verdict. The meanings are transitions.py's own (b_pair_research.md Part 1, the report table
and the bars table, with the lines it cites); a bar is named only where a harness check or TRANSITIONS.md states it.
"""

from __future__ import annotations

from typing import Any

from reveal_studio.registry.entries import H

T = "transitions.py report.json"
B = "b_pair_research.md Part 1"

HINTS: dict[str, dict[str, Any]] = {
    # the new-job form in the rail
    "control.pair_new_job": H(
        "Opens the form for a new pair job: a fixture pair by name, or two photo paths, A the start and B the finish. Each photo is linked under raw/<pair>/ with its sha256; nothing is copied."
    ),
    "control.pair_fixture": H(
        "A pair from fixtures/: <name>_S.<ext> is A and <name>_F.<ext> is B, the first file of each in name order. The pair's name becomes the job's name.",
        source="jobs/store.py fixture_photos",
    ),
    "control.pair_photo_a": H(
        "Photo A, the start (BEFORE): a path, absolute or relative to the repo root. transitions.py reads JPEG, PNG, WebP, TIFF, BMP, HEIC and the camera raws DNG and ARW.",
        source="transitions.py:269-323",
    ),
    "control.pair_photo_b": H(
        "Photo B, the finish (AFTER): a path, absolute or relative to the repo root. The canvas takes B's aspect by default (the render's canvas knob).",
        source="transitions.py:269-323",
    ),
    "control.pair_name": H(
        "The pair's name: letters, digits, dash and underscore. Empty takes the fixture's name, or the two file names joined. The renders go under <name>/ and drafts/<name>/."
    ),
    "control.pair_create": H("Makes the job: links the two photos, hashes them, and opens the job on its import."),
    # the panels' controls
    "control.pair_relation_run": H(
        "Runs transitions.py pair on A and B at 480 px for one second (about 2 s on this laptop): the class, the method and the correspondence it reports. A rerun replaces relation/.",
        stage="relation",
        source=B,
    ),
    "control.pair_verdict_run": H(
        "Runs reveal.py align on A and B, the strict reshot profile (2 to 16 s per pair). It writes metrics.json and two aligned stills, or exits 2 with a FAILED: line when the photos share too little detail.",
        stage="verdict",
        source=B,
    ),
    "control.pair_show": H(
        "Puts this picture in the viewer as source A, at fit; the compare modes then set it against B.",
        stage="relation",
    ),
    "control.pair_skeptic": H(
        "Writes requests/skeptic_<stamp>.json over the checked full renders, with the crops a pair needs: frame 1 against A, frame n-2 against B, the mid frame and the two endpoint steps behind the edge ratio.",
        stage="skeptic",
        source="TRANSITIONS.md §12.13",
    ),
    "control.pair_page": H(
        "The studio writes index.html over the listed full renders, behind the review gate: refused while a listed render is unjudged or NOT READY unless you override. The page's md5 opens a round.",
        stage="page",
    ),
    "control.pair_page_override": H(
        "Builds the page over unjudged or NOT READY renders on his word; the override's text goes into the page's footer and into the round.",
        stage="page",
    ),
    "control.pair_page_note": H(
        "One line under this render on the page: what to look at.",
        stage="page",
    ),
    "control.pair_best": H(
        "His pick for the round: the best render of the pair, or none usable. Saved in the picks file as best.<pair>.",
        stage="grades",
        source="director_picks_11.json",
    ),
    "control.pair_acceptable": H(
        "Whether he would accept this render as it is (clips.<render>.acceptable).",
        stage="grades",
    ),
    "control.pair_clip_note": H(
        "His note on this render, verbatim (clips.<render>.note).",
        stage="grades",
    ),
    "control.pair_one_picture": H(
        "The mid frame is one coherent picture, with no two photos superimposed (props.one_picture).",
        stage="grades",
        source="scripts/bench_transitions.py",
    ),
    "control.pair_transforms": H(
        "Details move and change, rather than the frame panning or fading (props.transforms).",
        stage="grades",
        source="scripts/bench_transitions.py",
    ),
    "control.pair_not_invented": H(
        "No content appears that is in neither photo (props.not_invented).",
        stage="grades",
        source="scripts/bench_transitions.py",
    ),
    "control.pair_words": H(
        "His words for the round, verbatim, saved beside the picks with the page md5 they were given on.",
        stage="grades",
    ),
    "control.pair_grade_save": H(
        "Saves the picks file (picks/director_picks_<stamp>.json, the director rounds' shape) and the round's grade. The next round's first full render waits for it.",
        stage="grades",
    ),
    "control.pair_grade_skip": H(
        "Marks the round ungraded by his word, so the next round's first full render may start without picks.",
        stage="grades",
    ),
    # the relation panel
    "relation.class_at_480": H(
        "The class the relation measured on its own 480 px canvas. Class A needs 30 or more SIFT and MAGSAC++ inliers on a sane homography; at 480 px mismatch_3 found 0, against 6 at 1920. A render's report gives the class of record.",
        stage="relation",
        source="transitions.py:834-835; fixtures/MANIFEST.md",
    ),
    "relation.class_differs": H(
        "This render's report reads another class than the relation at 480 px: a pair near the 30-inlier floor routes by the canvas it runs on. Look at the render's own class and method.",
        stage="render",
        source=B,
    ),
    "relation.frames": H(
        "A and B as the relation decoded them: frames 0 and n-1 of its 480 px mp4, on the cover-cropped canvas. cv2 reads no HEIC, so the studio shows the photos through the relation.",
        stage="relation",
        source=B,
    ),
    "relation.strip": H(
        "strip.jpg: up to 8 tiles 160 px tall at evenly spaced frames, the first tile A on the canvas and the last tile B.",
        stage="relation",
        source="transitions.py:1273-1300",
    ),
    "relation.wall": H(
        "The record's wall time: 1.89 s on mismatch_3 on 2026-11-05, 1.6 to 2.4 s on 2026-10-21. transitions.py prints no progress, so the tile shows the elapsed time.",
        stage="relation",
        source=B,
    ),
    "relation.md5": H(
        "The md5s of the relation's transition.mp4 and strip.jpg, the two files a rerun is compared by (report.json holds three clock keys and changes on every run).",
        stage="relation",
        source=B,
    ),
    # Reveal's verdict
    "verdict.refused": H(
        "reveal.py exited 2 with this FAILED: line and wrote no metrics.json. A refusal usually means the photos share too little detail to align; a decode failure also exits 2, and the line's text tells the two apart.",
        stage="verdict",
        source="reveal.py:2517-2534; STUDIO.md §7",
    ),
    "verdict.method": H(
        "The estimator that won Reveal's alignment of B onto A (for example sift, or phase+ecc).",
        stage="verdict",
        source="reveal.py metrics.json",
    ),
    "verdict.inliers": H(
        "The matches the homography kept. Inlier counts do not compare across matchers.",
        stage="verdict",
        source="reveal.py metrics.json; HANDOFF.md §5b",
    ),
    "verdict.rmse_px": H(
        "The inliers' reprojection error in px on the work image.",
        stage="verdict",
        source="reveal.py metrics.json",
    ),
    "verdict.confidence": H(
        "Reveal's confidence score, 0 to 100, from the inlier statistics only (never from pixel similarity).",
        stage="verdict",
        source="reveal.py confidence_score; HANDOFF.md §3.4",
    ),
    "verdict.passed": H(
        "Whether the strict profile's bars held: enough inliers and an rmse within the profile's good_rmse.",
        stage="verdict",
        source="reveal.py:1332",
    ),
    "verdict.stills": H(
        "before.jpg (A) and after_aligned.jpg (B warped onto A) at full resolution, the align flow's outputs.",
        stage="verdict",
        source="reveal.py:1406",
    ),
    # report.json's numbers
    "report.class": H(
        "A: a sane homography from SIFT and MAGSAC++ with 30 or more inliers, so the photos morph along a dense flow. B: any other pair; each photo zooms and pans about its salient blob. --class forces either.",
        source=T + "; transitions.py:834-835",
    ),
    "report.method": H(
        "Class A: homography+dis, or dis-only when forced without a sane homography, with +anchors and +falloff suffixes. Class B: saliency-panzoom with +ramp or +model, or mls-anchors with anchors.",
        source=T + "; transitions.py:852-896",
    ),
    "report.sparse_inliers": H(
        "The SIFT and MAGSAC++ inliers between A and B on the run's own canvas (0 when none).",
        source=T + "; transitions.py:836-837",
    ),
    "report.sparse_rmse": H(
        "The sparse inliers' rmse in px; null when there are none.",
        source=T + "; transitions.py:836-837",
    ),
    "report.median_disp_px": H(
        "The median displacement from A to B in canvas px: 24.71 px for the relation of mismatch_3 at 480 px.",
        source=T + "; transitions.py:903-905",
    ),
    "report.mean_certainty": H(
        "The mean splat weight. Class A: the forward-backward consistency, 1 when every pixel agrees both ways. Class B: a fixed 0.5.",
        source=T + "; transitions.py:886, 903",
    ),
    "report.pan_fraction": H(
        "Class B without anchors: the share of the distance between the two salient centres that A and B each pan.",
        source=T + "; transitions.py:882",
    ),
    "report.camera": H(
        "Class B's camera move (flat, ramp or model) and its zoom fraction per frame, as rendered.",
        source=T + "; transitions.py:883",
    ),
    "report.canvas": H(
        "The canvas in px, even sides, and its policy: finish takes B's aspect, common the smaller width and height of the two.",
        source=T + "; transitions.py:356-380",
    ),
    "report.n_frames": H(
        "The frames written: round(seconds × fps), at least 2.",
        source=T + "; transitions.py:202-203",
    ),
    "report.timing": H(
        "Clock seconds of the run: correspondence_s, render_s and total_s; the decode of the two photos sits outside total_s. They change on every run.",
        source=T + "; transitions.py:1326, 1442, 1451",
    ),
    "report.preset": H(
        "The preset the record ran with. report.json keeps the expanded style only, so the name comes from the record's knobs.",
        source=B,
    ),
    "report.basket": H(
        "The quality basket of report.json: several numbers on 480 px proxies of the frames before the encode, each beside its bar where a harness check or TRANSITIONS.md records one. A number means nothing across pairs: compare a pair against itself.",
        source=T + "; transitions.py:1114-1136",
    ),
    "report.first_vs_A": H(
        "Frame 0 against A on the 480 px proxies before the encode, mean absolute difference in levels. The bar is 0: frames 0 and n-1 are the photos byte for byte (invariant 4).",
        source="harness checks 21 and 31; TRANSITIONS.md §1",
    ),
    "report.last_vs_B": H(
        "The last frame against B on the 480 px proxies before the encode. The bar is 0, as for frame 0.",
        source="harness checks 21 and 31; TRANSITIONS.md §1",
    ),
    "report.edge_ratio": H(
        "The larger endpoint step over the interior mean step: the hidden-cut detector. The bar is below 1.5 for every preset; real pairs read at most 0.79 on the smooth presets and 0.13 to 0.66 on morph 1 s class B. snap-morph inflates it by design.",
        source="harness checks 21 and 31; TRANSITIONS.md:241, 247",
    ),
    "report.flicker_max": H(
        "The largest adjacent-frame change on 0..1 grey over the 480 px proxies. The bar is below 0.12, about 31 grey levels.",
        source="harness check 21",
    ),
    "report.flicker_mean": H(
        "The mean adjacent-frame change on 0..1 grey over the 480 px proxies, before the encode. No bar is recorded.",
        source=T + "; transitions.py:1156-1164",
    ),
    "report.spikiness": H(
        "The largest adjacent-frame change over the mean one. No bar is recorded.",
        source=T + "; transitions.py:1156-1164",
    ),
    "report.warping_error": H(
        "The mean absolute difference after warping each next frame back by DIS flow, 0..1 grey. No fixed bar: a coherent pan reads below 0.03 and unrelated frames above 0.1. Compare a pair against itself.",
        source="harness check 26; transitions.py:1116, 1134",
    ),
    "report.feat_floor": H(
        "The least, over the interior frames, of the share of A's SIFT keypoints matched plus the share of B's: details of A or B must survive. No bar; references sit in the goal table of TRANSITIONS.md §6.",
        source="transitions.py:1114-1136",
    ),
    "report.laplace_floor": H(
        "The least Laplacian variance over the interior frames against the endpoints' interpolated value: the sharpness kept. No bar is recorded.",
        source="transitions.py:1114-1136",
    ),
    "report.contrast_floor": H(
        "The least median patch contrast over the interior frames against the endpoints' interpolated value: the local contrast kept. No bar is recorded.",
        source="transitions.py:1114-1136",
    ),
    "report.dissolve_fit": H(
        "The share of the change a plain crossfade explains, mean R² of each step against B − A (a dissolve reads about 1). No bar is recorded.",
        source="transitions.py:1114-1136",
    ),
    "report.motion_share": H(
        "The share of the change that motion explains, by DIS warp (a crossfade reads about 0). No bar is recorded; the basket did not separate his crossfade verdicts from his closest picks (AUC 0.46 to 0.48).",
        source="transitions.py:1114-1136; TRANSITIONS.md §11",
    ),
    "report.no_bar": H(
        "No harness check or document records a bar for this measure: read it against the same pair's other renders.",
        source=B,
    ),
    "report.steps": H(
        "The decoded step series: per pair of adjacent frames of the mp4 as a player shows it, the mean absolute grey difference on 0..1 over a 480 px proxy. The report's flicker numbers take the same measure before the encode: on mismatch_3's 1920 morph the largest step read 0.0580 decoded and 0.0583 in the report.",
        source="media/pair.py; transitions.py:1156-1164",
    ),
    "report.decode_frames": H(
        "The frames the studio decoded from the mp4 against the report's n_frames (harness check 28).",
        source="transitions_harness.py check 28",
    ),
    "report.decode_size": H(
        "The decoded frame size against the report's canvas (harness check 28).",
        source="transitions_harness.py check 28",
    ),
    "report.decode_fps": H(
        "The mp4's frame rate against the spec's fps; the viewer plays at the spec's fps.",
        source="transitions_harness.py check 28",
    ),
    "report.decode_darkest": H(
        "The darkest decoded frame's mean over every channel, 0..255. The bar is above 5: no all-black frame.",
        source="transitions_harness.py check 30",
    ),
    "report.md5_mp4": H(
        "The md5 of the render's transition.mp4, from its record's outputs: the skeptic judges this md5, and two CLI runs of one argv give the same one (harness check 33).",
        source="transitions_harness.py check 33",
    ),
}
