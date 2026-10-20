<!-- Provenance: written by an Opus 5.5 subagent (the UI design track, 2026-10-20 about 23:35) of the Claude Code session of 2026-10-20 (the round-12 session; DECISIONS 2026-10-20), copied verbatim from benchmarks/runs/2026-10-20/agents/ui_design.md (sha256 b9b932a2d52d96af) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"); folded into `EXPLORATION_PLAN.md` slices UI1–UI4, backlog T52, the questions for the owner in the handover. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# The director's workbench: a local web UI for the grade → plan → render → grade loop (design, Deep tier, 2026-10-20)

Recommendation: build a fourth research script, `scripts/research/director_ui.py`: one file, the
standard library's `ThreadingHTTPServer` bound to 127.0.0.1, one embedded vanilla-JS page, every
existing script called as a subprocess, and the job folder on disk as the only state. Phase 1 fits
in one session and covers the owner's acceptance loop on the three director pairs. The owner must
decide where the tool lives (here, or a third root tool `director.py`) and how the UI reaches the
planner (§9 Q1–Q2). Nothing below was built or run; every timing is UNVERIFIED unless it cites a
measured file.

Evidence labels follow `core-disciplines.md §1`: `[CODE file:line]`, `[DOC file]`, `[ASSUMPTION]`,
`[OPEN]`. Line anchors in `scripts/research/director_render.py` are as of md5 `6961a726…` (1,935
lines, read 2026-10-20 ~23:00). The file is being edited tonight and moved by 38 lines while I read
it, so re-grep before building.

## 1. Triage and intent

Triage: this is a design problem. There are three viable shapes (§6), a new surface whose location
is an owner decision, a cross-process contract (UI ↔ renderer ↔ planner ↔ box), and a data-model
change (an edited plan with provenance, an annotation file, a sequence manifest).

Intent: the owner opens one page on 127.0.0.1, picks or loads a pair (later a sequence or a clip),
sees what the readers found and how far apart the photos are, turns the plan's knobs and drags its
beats, gets a 480 px draft with a progress line in seconds, scrubs and grades it, and the grade
lands in the picks file the planner reads next. The CLI and the UI read and write the same files.

## 2. Neighbour read: what the UI reuses or copies

| Neighbour | What it shows | Reuse in the UI |
|---|---|---|
| `reveal.py` HTTP section | stdlib only, `ThreadingHTTPServer(("127.0.0.1", port), Handler)` [CODE reveal.py:1741]; one `_send` with `Cache-Control: no-store` [CODE reveal.py:1585-1599]; a job id regex [CODE reveal.py:1525]; a capped body read [CODE reveal.py:1609-1623]; routes by `re.match` [CODE reveal.py:1626-1659]; background work on a `threading.Thread` [CODE reveal.py:1704]; the page as one embedded string [CODE reveal.py:1753-2404]; port 8378, beside `viewer.py`'s 8377 [CODE reveal.py:92] | copy the pattern: the same `Handler` shape, the id regex, the size cap, 127.0.0.1 hard-coded, port 8379 |
| `reveal.py` `Job` | state lives in memory (`JOBS` dict [CODE reveal.py:1522]); `status()` returns state, note, error, metrics, params [CODE reveal.py:1215-1226] | copy the `status` JSON shape; do not copy the in-memory store. The UI's state is files, so a restart or a CLI run sees the same jobs |
| `reveal.py align` | headless: writes `metrics.json` (method, inliers, rmse_px, ecc_rho, changed_pct, passed, confidence) and exits 0, or prints `FAILED:` and exits 2 on a refused pair [CODE reveal.py:2517-2534, 1311-1338] | the relation reader, as a subprocess |
| `transitions.py pair` | writes `report.json` with `class`, `method`, the correspondence diagnostics, canvas and quality [CODE transitions.py:1447-1453] | the class A/B reader, as a subprocess at `--max-long 480` |
| `director_render.py` | `PLAN OUT [--concept] [--seconds] [--fps] [--max-long] [--set knob=value]` [CODE director_render.py:1920-1935]; a dotted knob `<transform>.<param>` overrides a transform's params, `.window` its window [CODE director_render.py:880-887]; `<name>.skip=true` drops a beat [CODE director_render.py:889]; writes `transition.mp4`, `montage.jpg`, `info.json` with steps, layers, `motion_px`, `motion_pauses`, `motion_jumps`, `guard_share_max`, `b_inside`, `residual_edges` [CODE director_render.py:1897-1901] | the render backend, as a subprocess; the review charts read `info.json` |
| `director_page.py` | per clip: the planner's reading and idea, resolved numbers, the knobs with range and default, generated keyframes and filled shares, three checkboxes, "acceptable as-is", a note, "best" per pair; state in `localStorage`, exported by a download [CODE director_page.py:46-136] | copy the grading form and the `director_picks.json` shape field for field; replace the download with a POST that writes the file into the job folder |
| `director_picks_11.json` | `{date, page, best: {pair: concept}, clips: {tag: {acceptable, note, props: {one_picture, transforms, not_invented}}}}`; the owner's note refers to an attached frame (`owner_frames/mismatch_2_r11_tear.png`) [DOC benchmarks/runs/2026-10-17/director_r11/director_picks_11.json] | the picks file stays in this shape; frames he marks are saved under `owner_frames/` as today, and a `frames` list is added to each clip as an optional extra key |
| `notes.json` beside the page | per clip `look` and `faults` (the skeptic's text) [DOC director_r11/notes.json] | the review panel shows it; faults with frame numbers become markers on the scrubber |

What the neighbours do not have, and phase 1 needs: (1) progress. The render loop writes frames to
the encoder and prints nothing per frame [CODE director_render.py:1692-1860]; only `INFO` lines go
to stderr. (2) Per-job input folders. The renderer reads the layer tables and mattes from two fixed
paths [CODE director_render.py:35-36] and finds the photos under `fixtures/` by pair id
[CODE layered_probe.py:152-157 via director_render.py:421]. (3) A renderer version: `info.json` keeps
a 16-hex prefix of the plan's sha256 [CODE director_render.py:1932] and nothing about the
renderer's own code; the sheets record its md5 by hand (§13.19 "md5 c7924d3e…").

## 3. Information architecture

One page, a left rail with the job list, five panels in tabs. The canvas of every overlay and
annotation is the layer source's canvas, which is also the plan's coordinate system
[DOC scripts/research/plans/SCHEMA.md lines 6-9].

| Panel | Shows | The owner can |
|---|---|---|
| Inputs | the fixture pairs that have a layer table, mattes and a plan; a sequence's items in order; for a clip, its first and last frame and a frame picker | pick a pair; import two new photos (a background job, phase 2); build a sequence; pick a clip frame as an endpoint (phase 4) |
| Analysis | relation (aligned / themed / unrelated; Reveal's verdict and its numbers; the transitions class); A and B side by side with toggles: element map coloured by group, one element's soft matte, the disparity map, faces, bright discs, fitted lines; a table of elements per photo (id, label, group, area share, depth rank, median disparity); the label overlap table (labels in both photos with their area shares) | toggle overlays; click an element to see its matte and id; copy an id into a knob or an annotation |
| Plan | the plan's reading, relation, the concept's idea, risk, the planner block (model, prompt sha256, brief); every knob of the concept with range, default and its sentence; a timeline with one bar per transform window, the end-effect window, the guard's arrival per beat, and the motion model's edge; the layer list (phase 3) | edit a knob; drag a bar (it becomes a `<name>.window` knob); mute a beat (`<name>.skip=true`), solo a beat (skip every other); "save as plan" writes a new plan file with provenance; "ask the planner" writes a request with his notes as the brief |
| Render and review | the task's progress line and log tail; the clip with a frame scrubber; under it the `motion_px` profile and the step profile with pauses and jumps marked, the `b_inside` series; a three-up compare (A, frame, B) at the scrubber's frame; generated keyframes beside the clip; the skeptic's faults as markers | render a 480 px draft or a full render; step frame by frame; mark a frame as a fault (it saves the PNG under `owner_frames/`) |
| Grade | the director page's form per render: three boxes, acceptable as-is, the note, best per pair; the history of his grades for this pair | save the picks file into the job folder (and to the round folder when he says it is a round) |
| Jobs (rail) | every background task: kind, state, progress, wall time, the log's last 20 lines | cancel a task; open its folder path |

## 4. Backend contract

Every heavy call is a subprocess with its stdout and stderr in a log file under the job folder; the
UI never imports `reveal`, `transitions` or another research script. The server process itself
uses numpy and cv2 from `.venv` only to turn `layers.npz` and mattes into overlay PNGs.

| Endpoint | Input | Output | Backend call | Reads / writes under the job folder | Today |
|---|---|---|---|---|---|
| `GET /` | — | the page | embedded string | — | new (copy of reveal.py:1628) |
| `GET /api/pairs` | — | pairs with flags: layers, mattes, plans | glob `fixtures/*_S.*`, `layers_v3/<photo>/layers.json`, `mattes/<photo>/`, `scripts/research/plans/<pair>*.json` | reads only | new |
| `POST /api/jobs` | `{pair}` or `{sequence}` | `{id}` | — | writes `job.json` | new |
| `GET /api/jobs/<id>` | — | `job.json` + every task's state | — | reads `job.json`, `tasks/*.json` | new |
| `POST /api/jobs/<id>/analyze` | — | task ids | `.venv/bin/python reveal.py align S F --out analysis/reveal`; `.venv/bin/python transitions.py pair S F --out analysis/transitions --max-long 480 --seconds 1`; `director_render.py PLAN analysis/resolve --resolve-only` | writes `analysis/` | reveal and transitions calls exist; `--resolve-only` is new |
| `GET /api/jobs/<id>/overlay/<A|B>/<kind>.png` | kind: elements, disparity, matte_<id>, faces, discs, lines | PNG on the layer source's canvas | server code over `layers.npz` (`element`, `disparity` arrays [DOC layer_source.py lines 13-15]), `mattes/<photo>/el_<id>.png`, `analysis/resolve/anchors.json` | writes `analysis/overlays/` (cache) | new |
| `GET /api/jobs/<id>/file/<path>` | a path inside the job folder | the file | — | reads; paths outside the job folder, `fixtures/`, `layers_v3/` and `mattes/` are refused | new |
| `POST /api/jobs/<id>/render` | `{plan, concept, knobs, max_long: 480 or 1920, seconds, fps}` | task id | `.venv/bin/python scripts/research/director_render.py PLAN renders/<rid> --concept C --max-long N --set k=v … --progress` | writes `renders/<rid>/{transition.mp4, montage.jpg, info.json, render.json, log.txt}` | the render exists; `--progress` is new |
| `GET /api/jobs/<id>/tasks/<tid>` | — | `{state, progress: [i, n], wall_s, log_tail}` | — | reads `tasks/<tid>.json`, `tasks/<tid>.log` | new |
| `POST /api/jobs/<id>/tasks/<tid>/cancel` | — | ok | SIGTERM to the pid | writes the task state | new |
| `POST /api/jobs/<id>/frame` | `{rid, index}` | PNG path | cv2.VideoCapture seek (the renderer already decodes its own mp4 this way [CODE director_render.py:1875]) | writes `renders/<rid>/frames/<i>.png`, `owner_frames/` when marked | new |
| `POST /api/jobs/<id>/plan` | `{from, concept, changes}` | new plan path | — | writes `plans/<pair>_<stamp>_owner.json` (never the frozen plan) | new |
| `POST /api/jobs/<id>/annotations` | the annotation list | ok | — | writes `annotations.json` | new |
| `POST /api/jobs/<id>/picks` | the picks object | path | — | writes `picks/director_picks_<stamp>.json` | new (shape from director_page.py:127-136) |
| `POST /api/jobs/<id>/request/plan` | `{notes, annotations, picks}` | request id | none: the Claude Code session picks the request up (§9 Q2) | writes `requests/plan_<stamp>.json`; the session writes the plan into `plans/` | new |
| `POST /api/jobs/<id>/request/keyframe` | `{prompt, refs, region}` | request id | none: a session subagent runs `strix_keyframe.sh` on the box by SSH [DOC scripts/research/strix_keyframe.sh lines 14-25] | writes `requests/keyframe_<stamp>.json`; the subagent writes `helpers/` | new |
| `POST /api/import` (phase 2) | two photos (multipart, parser copied from reveal.py:1529-1554) | fixture id | copy into `fixtures/<group>_<N>_S/F.<ext>`; then `layer_merge.py` in its scratch venv [DOC layer_merge.py lines 13-18] and `matte_source.py run` | writes `fixtures/` (gitignored), `layers_v3/<photo>/`, `mattes/<photo>/`, `job.json`'s draft MANIFEST row | new; the scripts exist |
| `POST /api/sequences/<id>/stitch` (phase 4) | the sequence manifest | task id | a new `scripts/research/director_stitch.py` (one canvas, endpoints asserted byte-equal, the shape of `loop/work/build_loop.py` [DOC benchmarks/runs/2026-10-20/loop/report.md]) | writes `sequence/final.mp4` | new |

Three changes to `director_render.py` (a research script, not either tool; each default-off, each
verified by rendering a round-11 plan twice and comparing the md5 with and without the flag):

1. `--progress`: print `PROGRESS i n` to stderr every 5 frames. The UI parses it from the log.
   Without it, phase 1 shows elapsed time against the last `wall_s` of the same plan and size.
2. `--resolve-only`: build the scene, write `canvas_A.png`, `canvas_B.png` and `anchors.json` (the
   resolved anchors, the fitted circle, lines, face boxes, the camera, the guard's arrival per
   beat), and stop before the frame loop. One code path then decides both what the overlay shows
   and what the render uses.
3. `--layers-dir`, `--mattes-dir`, and a renderer stamp in `info.json` (md5 of
   `director_render.py` and of `transitions.py`). The stamp makes "reproducible from plan + knobs +
   renderer version" checkable from the file instead of from the sheet.

Knob names: the plan's knob list and the renderer's `--set` keys do not always match. Plan
`mismatch_2_r11.json` names `end_effect.window`; the renderer reads `end_window`
[CODE director_render.py:1688-1689]. A dotted name whose prefix is a transform name works
[CODE director_render.py:880]. The UI keeps a small table from plan knob names to `--set` keys and
shows a knob it cannot map as read-only with the reason, instead of passing it on and having the
renderer ignore it silently.

## 5. Data model

Job folder: `benchmarks/runs/<date>/workbench/<job_id>/` (gitignored under `/benchmarks/runs/`
[CODE .gitignore:18]). The job folder is the source of truth: the UI rebuilds its state from it on
restart, and a render the agent runs from the CLI into the same folder appears in the UI.

```
<job_id>/
  job.json            {id, kind: pair|sequence, pair, inputs: [{path, sha256}], created, ui_version}
  analysis/           reveal/ (metrics.json or failed.txt), transitions/ (report.json, strip.jpg),
                      resolve/ (canvas_A.png, canvas_B.png, anchors.json), overlays/, analysis.json
  plans/              copies of the frozen plans used (byte-identical) and the owner's edited plans
  annotations.json
  renders/<rid>/      transition.mp4, montage.jpg, info.json, render.json, log.txt, frames/
  tasks/<tid>.json    {kind, argv, pid, state, progress, started, ended, exit_code} + <tid>.log
  requests/           plan_<stamp>.json, keyframe_<stamp>.json (read by the session)
  helpers/            generated keyframes + keyframes.json (model, seed, steps, cfg)
  picks/              director_picks_<stamp>.json
  owner_frames/       PNGs he marked
  notes.json          the skeptic's look/faults per render (written by the session)
```

`render.json`: `{argv, plan_path, plan_sha256 (full), concept, knobs, max_long, seconds, fps,
renderer_md5, transitions_md5, started, wall_s, md5_mp4}`. Two renders with equal plan sha256,
knobs, size and renderer md5 must give the same `md5_mp4`, which the round-11 sheet already shows
by rendering each clip twice (§13.19 "Deterministic").

The owner's edited plan: a new file `plans/<pair>_<stamp>_owner.json`. It keeps the source plan's
`planner` block unchanged and adds a top-level `edited` block:
`{"by": "owner", "from": "<path>", "from_sha256": "…", "at": "<ISO time>", "changes":
[{"path": "/concepts/0/transforms/2/window", "old": [0.1, 0.92], "new": [0.15, 0.9]}]}`. The
renderer reads only `plan["pair"]` and `plan["concepts"]` [CODE director_render.py:420, 1927], so
the new key changes no render. The frozen plan under `scripts/research/plans/` is never written.
Knob changes alone do not need a new plan: they ride `render.json` and `info.json["knobs"]`
[CODE director_render.py:1898]. "Save as plan" folds the current knobs into a new plan when he
wants them to become the default.

`annotations.json`: a list of `{id, photo: "A"|"B", shape: box|point|stroke|polygon, coords
(layer-source canvas px), role: anchor|lift|protect|target, label, ids_hit (element ids under the
shape), note, by: "owner", at}`. A box maps to the schema's `box` anchor and a point to its `point`
anchor [DOC SCHEMA.md "Anchor kinds"]. A stroke or a polygon has no schema kind today. It travels
to the planner as part of the brief, and a `mask` anchor kind (a PNG on the canvas) is a schema
addition for phase 3. A `protect` region would also be a schema addition: a `reveal.protect` list
that the round-12 guard [CODE director_render.py:449, 1345] treats like a layer's b-mask.

Picks: the shape of `director_picks_11.json` unchanged, plus two optional keys per clip, `frames`
(paths under `owner_frames/`) and `render` (the `rid`), and a per-beat note list in phase 3 (the
retrospective's item 5(ii) [DOC benchmarks/runs/2026-10-20/agents/retrospective.md:152]).

Sequence manifest `sequence.json`: `{items: [{kind: photo|clip, path, sha256, in, out}], joins:
[{from: 0, to: 1, job: "<pair job id>", plan, concept, knobs, seconds}], canvas: [w, h], hold_s}`.
Each join is a pair job, so every panel above works on one join at a time.

## 6. Alternatives

| | A1 `scripts/research/director_ui.py` (stdlib server, vanilla JS) | A2 root `director.py` (same code, a third tool) | B Streamlit or Gradio app | C static page per run + a watcher |
|---|---|---|---|---|
| Single-file rule | one file; research scripts carry no rule beyond their own | one file; a new root tool is a DECISIONS line (`AGENTS.md` "a new dependency is a decision"; the 2026-09-13 two-tool decision [DOC .claude/conventions/architecture.md]) | one app file, but the framework is a package tree in the shared venv | the page generator exists; a second script for the watcher |
| Offline, 127.0.0.1 | by construction (copied bind) | same | depends on the framework's config: bind address, usage statistics, share links are settings to pin [ASSUMPTION: read their docs before relying on this] | no server; `file://` blocks fetching some files in some browsers [ASSUMPTION] |
| Owner's rulings (no tool edits, frozen plans, planner path) | yes; touches neither tool | yes; needs his yes on a third tool | yes, if pinned | yes |
| Build cost | phase 1: one session (4–6 h) best case, 2 sessions worst (overlay canvas and timeline drag take longer); all four phases 5–8 days | as A1 + a harness of its own (~1 day) | phase 1: 1–2 days best; worst adds a dependency review and version pins | 0.5 day |
| Risk to the no-regression roster | none: no import into either tool, both harnesses untouched | small: a third module the harness check 1–2 pattern would have to cover | a new package in the shared `.venv` can move numpy, Pillow or OpenCV pins under harness checks 1–82 | none |
| What it cannot do | nothing in the list; the cost is JavaScript for the canvas, the timeline and charts (reveal.py's page is 650 lines [CODE reveal.py:1753-2404]) | as A1 | custom drag on a timeline and drawing on an image need custom components; per-frame scrubbing with overlays is awkward | start a render, show progress, edit a knob: the page is static and the picks leave by download [CODE director_page.py:127-136] |

Recommendation: A1. Feasibility, best case: phase 1 is usable on mismatch_2/3/5 in one session,
because every backend call exists except two default-off flags. Worst case: the 480 px draft is not
"seconds" on the window pair (61 s at full size [DOC retrospective.md:152]; the frame loop scales
with pixels but the scene build, the mattes and the plate fill may not), and drafts take 15–30 s.
The loop still runs, with a progress line. Promote A1 to A2 when he says the UI is the operator
surface he wants to keep. The move is a rename plus a harness. C is the fallback if the session
runs out: `director_page.py` with a POST target would take an hour, but it does not render.

Rollout and reversibility: the UI is a new file and a new port. It is turned off by not running it,
and reverted by deleting the file in one commit. The three renderer flags are default-off and
md5-checked. `[revert: commit]`. Nothing in the default path of either tool changes.

## 7. Phased plan

Phase 1, one session: the smallest thing he can start playing with.
- Panels: Inputs (the fixture pairs that have a plan: mismatch_2, mismatch_3, mismatch_5), Analysis
  (Reveal's verdict and numbers, the transitions class and median displacement, element map,
  disparity and per-element matte overlays from files, the element tables, the label overlap
  table), Plan (the concept's knobs with range and default, the timeline with draggable windows
  that become `<name>.window` knobs, mute and solo by `skip`), Render and review (draft 480 /
  full, the progress line, the log tail, the scrubber, the `motion_px` and step profiles with
  pauses and jumps marked, the A | frame | B compare), Grade (the picks form, saved to the job
  folder).
- Endpoints: `/`, `/api/pairs`, `/api/jobs`, `/api/jobs/<id>`, `/analyze`, `/overlay`, `/file`,
  `/render`, `/tasks/<tid>`, `/frame`, `/picks`.
- Wrapped scripts: `reveal.py align`, `transitions.py pair`, `director_render.py` (+ `--progress`,
  `--resolve-only`, the renderer stamp).
- Acceptance check: he runs `.venv/bin/python scripts/research/director_ui.py`, the browser opens
  127.0.0.1:8379; he picks mismatch_3; within 30 s the analysis shows "unrelated (Reveal refused,
  class B)" with the numbers, and the element and depth overlays toggle on both photos; he changes
  two knobs (`parallax_push` 1.5 → 2.0 and one transform's window by dragging); he presses "draft"
  and sees a progress line move to done; he scrubs the clip frame by frame with the motion profile
  under it; he ticks the boxes, writes a note, picks best; `picks/director_picks_<stamp>.json`
  exists and has exactly the keys of `director_picks_11.json`; `render.json` lists both knobs, and
  re-rendering from it gives the same mp4 md5.

Phase 2, "UI with all tweaks and all the tools for director, loading progress":
- every schema key editable with its range: the concept's knobs, plus the global ones the renderer
  reads (`front_ids`, `parallax_*`, `plate`, `plate_fill`, `front_per_element`, `motion`, `guard`,
  `end_*`), from a range table kept beside SCHEMA.md;
- "save as plan" with provenance;
- importing a new pair: copy into `fixtures/`, then the layer source (minutes, scratch venv) and
  the mattes (2–25 s per photo [DOC director-tooling.md §1]) as background tasks with progress and
  log tail;
- the jobs rail with cancel.

Phase 3, "annotate part of pics, play with layering and other sub-tools":
- box, point, stroke and polygon tools on either photo, snapped to element ids;
- the layer list (order, inside or front, soft or hard matte, solo, mute, the plate under a lifted
  layer shown as its own overlay);
- faces, discs and lines from `--resolve-only` as overlays, and the guard's arrival per beat on
  the timeline;
- the skeptic's faults as scrubber markers, and the helpers beside the clip;
- "ask the planner" and "ask for a keyframe" as request files;
- the suggestions panel: the tooling list's rows (`director-tooling.md` §2–§5) filtered by the
  relation, each with his last verdict quoted, beside the plan's own concepts.

Phase 4, "both match and mismatch pairs … sequences, and mix photo to video and vice versa":
- match pairs through the same panels (Reveal's aligned stills and changed-region mask as
  overlays);
- sequences as a list of joins with the stitch task;
- clips as endpoints.

What "mix photo to video and vice versa" can mean, ranked:

| Option | What happens | Cost and status | Recommend |
|---|---|---|---|
| V1 a clip's first or last frame as an endpoint | extract the frame (cv2.VideoCapture, already in the repo [CODE director_render.py:1875]) and treat it as a photo; the transition ends on the clip's first frame and the clip plays on (or starts from its last frame) | the extraction is hours; the join needs the stitch task and one canvas | first |
| V2 a still becomes a clip | the depth camera move `transitions.py --camera` [DOC director-tooling.md §2] on one photo, before or after a transition | exists for pairs; a single-photo mode is UNVERIFIED | second |
| V3 a transition that lands on a moving clip | B changes every frame during the transition; the layer source and mattes per frame | the renderer reads one B [CODE director_render.py:420-425]; the plan's TR4 (video I/O, PyAV decision T8) is OPEN [DOC EXPLORATION_PLAN.md:429] | after TR4 |
| V4 a clip → a photo | V1 mirrored | same as V1 | with V1 |

Sequences: a sequence of related photos already has a chain renderer (`chain_luma.py`, the fabra
seven [DOC .claude/claude-docs/benchmarks/2026-10-09-fabra-boxes.md, Stage 4b]). A sequence of
unrelated photos is N−1 pair jobs plus the stitch. The renderer sizes each pair's canvas by the
`finish` policy [CODE director_render.py:424], so consecutive joins can differ in size. The loop
track hit this on 2026-10-20 and fixed it with `--canvas common` [DOC loop/report.md]. The stitch
task must render every join on the sequence's canvas, which is a fourth renderer flag.

## 8. Skeptic pass (my own; five objections)

1. "The slow part is his calendar, not the render." The retrospective shows three rounds in under
   five hours on 2026-10-17/18 and two days before the round-11 grade [DOC retrospective.md:76].
   Conceded in part. The UI removes the agent's turnaround for knob-level changes (12 hand-set knobs
   per round) and lets him try them himself. It does not make him available. Structural changes
   still go through the planner and the session.
2. "Knobs turned by hand bypass the planner and the skeptic, and the rounds become hand-tuned."
   Answered: every render records its knobs, a saved plan records what changed, and the planner's
   request carries his knob history as the brief. The skeptic pass stays a session step before a
   round's page. The UI does not replace it.
3. "A 480 px draft hides the faults he grades: hard edges, ghosts, a 4-frame overlap." Answered by
   labelling, not by a fix. Drafts are for timing and motion. `render.json` records the size, the
   picks file records the `rid`, and a grade on a draft is marked as one. Whether he may grade
   drafts is §9 Q5.
4. "Annotations on the layer-source canvas break when the renderer re-crops A for an anchored
   crop." The renderer shifts element masks by `shiftA` [CODE director_render.py:186-205, element_mask_ids]. Answered
   for element-snapped shapes, which carry ids. Conceded for free shapes: the UI must apply the
   same shift, and phase 3 tests it on mismatch_5, whose crop is anchored (§13.2).
5. "The renderer changes every night and the UI's knob table will drift." It moved 38 lines during
   this read. Conceded. The knob table is read from the plan plus a range table beside SCHEMA.md
   that the round's author updates, and an unknown knob is shown read-only. The renderer stamp
   makes a drift visible in `render.json`.

Feedback not applied: a framework (B) for speed of the first screen. A new package in the shared
`.venv` is a decision with a roster risk, and phase 1 needs custom drag and canvas work either way.

## 9. Open questions for the owner (each with my recommended answer)

1. Where does the UI live? Recommended: `scripts/research/director_ui.py` now (no tool decision,
   both harnesses untouched); a root `director.py` with its own harness once you call it the
   surface you keep.
2. How does the UI reach the planner? Recommended: it writes `requests/plan_<stamp>.json` with your
   notes, annotations and picks. The Claude Code session you run beside it (the Opus 5.5 subagent
   you approved, T36) writes the plan into the job's `plans/`, and the UI shows "waiting for the
   planner" until the file appears. The UI itself never opens a network connection. The
   alternative is the UI starting a headless Claude Code process as a subprocess. That is a second
   egress path, so it needs your yes and a DECISIONS line [OPEN: its flags are not verified here].
3. Port 8379? Recommended yes (Reveal 8378, viewer 8377 [CODE reveal.py:92]).
4. May the UI copy new photos into `fixtures/` and run the layer source and mattes on them?
   Recommended yes. The originals are never touched, and the session appends the MANIFEST row
   (a tracked file).
5. May you grade 480 px drafts? Recommended yes, marked as drafts in the picks file; a round's
   page stays full size.
6. Which video option first? Recommended V1 (a clip's end frame as an endpoint, plus the stitch).
   V3 waits for TR4 and the PyAV decision.

## 10. Confidence and gaps

### Confidence
- 90 % that A1 with the contract in §4 covers items 1–8 of the brief without touching either tool:
  every heavy call exists as a CLI today except the three default-off flags [CODE cited in §2, §4].
- 75 % that phase 1 fits one session. The overlay canvas, the draggable timeline and the scrubber
  charts are new JavaScript of roughly reveal.py's page size, and that is the variable.
- 60 % that a 480 px draft finishes in under 10 s on the window pair. Unmeasured: the scene build
  (mattes, plate fills) is not proportional to the output size.

### Gaps
- No render was run at `--max-long 480`. Whether the anchors, the face guide and the mattes
  resolve at that size is UNVERIFIED (`ls_scale` handles the scale [CODE director_render.py:432],
  and the YuNet input size is fixed at 320 [CODE director_render.py:284]).
- The planner request path depends on the session watching the folder (Monitor or the owner's
  word). How the session is told is not designed here.
- The knob-name map (plan name → `--set` key) was checked on one plan only (`end_effect.window`).
  The rest are unenumerated.
- Streamlit and Gradio claims (bind address, usage statistics) were not checked against their docs.
- V2 (a single still becoming a clip with `--camera`) assumes `transitions.py pair` accepts the same
  photo twice; not checked.
- The box keyframe path (SSH via the prod box as a jump host [DOC strix_keyframe.sh lines 14-17])
  stays a session subagent's job. The UI only writes the request and shows the result.
