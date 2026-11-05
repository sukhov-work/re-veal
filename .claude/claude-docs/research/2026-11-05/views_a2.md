<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/views_a2.md (gitignored), the report of agent E, the views builder (Opus 5.5, max effort) of the 2026-11-05 session; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran the package gates after the copy and ruled on the jump rule's floor (kept) -->

# Studio phase A2, the views: two new stages, the fits table, the comparator, the stability plot and the graph (2026-11-05)

<!-- reader: the main thread of the 2026-11-05 session, which did not watch this work; shape: report; written by agent E (Opus 5.5, max effort), the views builder of studio phase A2 -->

**Built and green.** `make qa` passed in 67.5 s wall (373 unit tests) and `make test` in 64.5 s wall (387 tests), at
02:34 and 02:35 on 2026-11-05. I added 29 tests (28 unit, 1 integration) and 37 hint keys.

Summary:
- The registration stage has a `windows` knob and a table of the named windows under each fit. The probe and measure
  stages run. The render view lists stalls, jumps and the measure runs, and the viewer draws a stability plot.
  The viewer compares two sources in five modes, and a graph view sits beside the strip.
- The proof ran on job `loop_angel_20261104-220719` through my server on 127.0.0.1:8394. 19 of the 20 window cells
  equal the research report's, and the 20th is not in it; the probe's double-exposure shares equal the report's.
- I changed the jump rule as written in one point (a jump must reach 0.3 grey levels; section 6). I edited one test file
  outside both of my file lists and rewrote two A1 hint sentences.
- Asked of you: sync `studio/ARCHITECTURE.md` and `studio/README.md`, which I may not edit (section 5). Copy this report
  to `.claude/claude-docs/research/2026-11-05/` when you commit. The owner's server on 8380 still runs the old code
  (section 7, item 3); a restart, whenever he allows one, gives him A2.
- A question for the owner: the stall rule flags s6, the seasons loop he accepted on 2026-11-01 (section 7, item 1).

## Glossary

| Term | Meaning |
|---|---|
| A1, A2 | the studio's build phases (`STUDIO.md` §9): A1 built the shell, the runner and the loop flow on 2026-11-04; A2 is this session's second phase |
| branch stage | a stage that writes into its own folder, which no other stage reads: the probe and the measure. The strip draws it as a short tile in a second row under its parent, after `STUDIO.md` §2 ("Branches are short second rows under their parent tile") |
| fit | one of the registrations `loop_seq.py prep` made for a frame: `all` (every keypoint), `far` (`--bg-depth`), `chain` (through the previous frame), `ecc`, `final` (the frame as written, after the lock) |
| dexp | the double-exposure share of an in-between frame (rule 7 of the loops playbook, `loops.md` §6) |
| edge | a window whose match peak lies on the border of the ±30 px search; its offset is a bound, not a measurement |
| stale | the A1 tile state: an earlier stage ran again after this one |
| prep | the registration's output folder `in/<seq>/` (the registered stills `k<i>.png`, the depth maps, `prep.json`); "the previous prep" is the folder a registration rerun moves aside |
| lock | `--lock-window`: windows on the gag object (the angel's ring light) whose mean offset the registration zeroes; "after the lock" is the frame as written with that shift applied |
| named windows | the boxes of the new `windows` knob (`--windows "name:x0,y0,x1,y1;…"`), measured under every fit and never applied |
| readers stage | A1's optional stage that reads the depth map, the face boxes and the focus of each registered still |
| RIFE | the frame-interpolation model (v4.26) that draws the in-between frames, loaded offline behind its manifest |
| a2, s6 | the loops the owner accepted: a2, the angel portrait candidate of 2026-11-04 (a full render at 1366×1770), and s6, the seasons loop of 2026-11-01 |
| the brief | the main thread's task message to me: its deliverables, its file lists (mine, shared with agent D, and do-not-edit) |

## 1. The two new stages: argv, folders, records

| Stage | Argv (repo-relative, run by `<root>/.venv/bin/python` from the repo root) | Writes | On a rerun | Identity rule |
|---|---|---|---|---|
| probe | `scripts/research/loop_seq.py probe <root>/in/<seq> --out <root>/in/<seq>/probe.part --long N [--pairs S]` | `<root>/in/<seq>/probe/` (terminal `probe.json`) | the folder is replaced, as the readers stage's folder is (`Runner.finalize` unchanged) | none |
| measure | `scripts/research/loop_seq.py measure <render>/loop.mp4 --out <render>/measures/<stamp>.part [--frames-json <render>/frames.json] [--window S] --ref N` | `<render>/measures/<stamp>/` (terminal `measure.json`); `<stamp>` is the record id without `_measure`, so it never collides | a new folder; the render's own files are never written (a test compares their md5s before and after) | none |

- Knobs: probe `long` (960, `--long`) and `pairs` ("", `--pairs`); measure `render` (`full:<name>` or `draft:<name>`, no
  flag), `windows` ("", `--window`) and `ref` (0, `--ref`). The registration gains `windows` ("", `--windows`) as its
  last knob. Every sentence is the script's `--help` sentence, split where it ran over 60 words.
- A registration rerun stays refused while a probe or a measure runs: the A1 busy rule covers every running record
  (read in `Runner.start_stage`, not tested by me).
  The probe folder lives inside the prep, so it moves aside with the previous prep.
- `IDENTITY` in `runner/process.py` is unchanged: both stages fall to its default, so a rerun never reads "unchanged".
- The stale rule (`views/job.py`, `stage_views`) now skips branch stages as an upstream, so a probe or a measure makes no
  stage stale. A branch goes stale only after the stages its registry field `stale_after` names: the probe after a
  registration, a measure never (it measures a finished mp4).
- The registry gains three fields: `parent` on readers, probe and measure (the graph's layout), and `branch` and
  `stale_after` on probe and measure.

## 2. The JSON shapes

`views/fits.py`, `fits_summary(prep_json)`, served as `job_view.prep.fits` (None without `--windows`):

```
{"windows": {name: [x0, y0, x1, y1]}, "names": [...], "fits": [every fit present, in the order all far chain ecc final],
 "frames": [{"i", "method", "lock_shift": [dx, dy] | null, "fits": [this frame's fits],
             "rows": [{"name", "box", "box_canvas", "cells": {fit: {"dx", "dy", "corr", "edge", "px"} | null}}],
             "largest": {fit: {"name", "dx", "dy", "px", "edge"}}}],
 "unmeasured": [i, ...]}
```
`px` is the length of the offset. `largest` names, per fit, the window whose offset is longest; an edge cell takes part
with its bound. `job_view.prep` also gains `windows` and `windows_jpg` (the file route's URL, or None).

`views/render.py`, `render_view` gains four keys:

```
"measures": [{"record": id | null, "at", "folder", "windows": {name: box}, "ref", "stability_max": {...}}]   oldest first
"stability": {"record", "at", "folder", "ref", "margin", "series": {name: [[dx, dy, corr], ...]}, "max": {...}} | null
"stalls_and_jumps": {"stalls": [[first, last], ...], "jumps": [index, ...]}                                 step indices
"frame_kinds": ["hold" | "generated" | "snap" | "blend" | "morph" | "rewind" | "slices" | "sheets" | "cut", ...]
```
The runs come from the folders under `<render>/measures/`, a `.part` folder skipped, so a run made from the shell is
listed with `record` null. `stability` is the latest run that measured windows.

`views/measures.py`, `stalls_and_jumps(steps, tags)`:
- A stall is a run of two or more consecutive steps below 0.3 whose both frames are in-betweens. A hold or a cut's
  first frame closes motion.
- A jump is a step that reaches 0.3 grey levels and is also more than 3× the mean of its two neighbours. The first and
  the last step are judged against their one neighbour. A step into a cut's first frame, or touching a snap frame, is
  exempt.
- `frame_kinds(rows)` reads frames.json: `none (photo)` is hold and `none (blend + motion blur)` is snap. A cut is
  found where two neighbouring frames belong to different plan steps and the still the first ends on differs from the
  one the next starts from (a cut writes no frames).
- Mutations that turn the tests red, each confirmed by patching the constant in-process: `STALL_BAR` 0.3 to 0.25 or
  to 0.35, `JUMP_RATIO` 3 to 3.5 or to 2.5, and `CLOSED` emptied.

`job_view` gains `probe` (`probe_view`: per pair the strip URLs, the shares per method and t, the steps, the crops as one
row per face and method) and `graph` (`{"ports": {stage: {"in": [{name, path, url?}], "out": [...]}}, "edges": [{"from",
"to", "file"}]}`).

## 3. The page

- **Registration panel.** The A1 lock block is unchanged. Under it sits the table "Windows under each fit", with the
  fit columns side by side. dx, dy and corr are right-aligned in the data mono, with the units in the headers. `edge`
  is a chip in the failed colour, the last row gives the largest offset per fit, and the header carries the hint. Then
  come "show windows.jpg" and a viewer over k0 and k1.
- **Probe panel.** The table of the double-exposure share per method and t (inside the matte and over the frame, in %)
  with the step to each still. Then the three strips with their t and "show", the face crops at 1:1 (one row per face
  and method: k0, t 0.25, 0.5, 0.75, k1), and a "rife skipped" chip with the reason when set.
- **Viewer.** Hosted by the registration, readers, probe, render and measure panels. Two pressed groups: zoom (fit, 1:1,
  2×) and compare (single, wipe, A/B, onion, difference); every mode keeps the zoom. A and B are chosen from the render's
  current frame, `k<i>.png`, `windows.jpg` and the last output shown. B is drawn at A's size. The difference is
  |A − B| × 4 on a canvas in the browser, with the stretch printed. The wipe handle is a focusable slider (1 %, shift
  10 %) that stops the event, so the arrows step frames everywhere else. `a` flips A/B. A generated frame keeps its
  violet outline.
- **Axis.** The step series gains a band per stall and a tick per jump in the failed colour. Under it sits one plot per
  measured window: dx in photo A's blue, dy dashed in photo B's orange, the maxima marked and labelled with px and frame,
  the cursor shared. The measure control and the runs table follow.
- **Inspector.** "stalls" and "jumps" rows with a within or past-bar chip, and a "Stability" section; the measure stage's
  `render` knob is a select of the candidates. The stall and jump chips now come from the server, replacing A1's client
  rules (A1 judged a jump against the larger neighbour), so the axis and the inspector agree.
- **Strip.** The main row is A1's eight tiles. Probe and measure sit in a second row under registration and render.
  Left and right move within a row, up and down between a parent and its branch.
- **Graph.** The layout rule: the required stages in one row in the flow's order; an optional stage in its parent's
  column, in the first free row under it (readers and probe stack under the registration, measure under the render). An
  optional stage without a record appears only after "add". A node shows its thumbnail, name, state chip, input and
  output ports (the latest done record's files, linked ones first, six per side, then "+N more"), "rerun from here"
  (script stages but the page) and "show" (the first image output). Lines are curves left to right; a line into a node
  stacked under its producer runs right, through the gap between the rows, and in from the left. Arrows move between
  nodes, Enter selects. "add" lists the optional stages whose parent is the selected node. No dragging, no drawn edges.

## 4. The proof on the real surface (my server on 127.0.0.1:8394, its lock in my scratchpad)

| Step | Record | Result | Research report (`loopseq_a2.md`) |
|---|---|---|---|
| registration with the lock and the ten windows | `20261105-022318_registration`, 4.4 s | ring top `final` +1.40, −1.09; `all` +6.14, −12.59; lock shift −4.93, +11.48; 19 of the 20 cells equal the report, and the 20th (the mirror box under `all`, +6.96, +2.60) is not in it | §3: +1.40, −1.09 and +6.14, −12.59 |
| | | the previous prep moved to `in/angel_prev_20261105-022322`, as expected; k0, k1 and the depth maps equal it byte for byte (md5 ccdb458c, 558688ea, be5f197b, abc01630), so the tile says unchanged; the renders went stale | §1: the same md5s |
| probe at 960 px | `20261105-022341_probe`, 3.6 s (the script's own 3.1 s) | RIFE 0.0413 / 0.0611 / 0.0341 inside the matte, 0.0203 / 0.0303 / 0.0164 over the frame; morph and dissolve equal too; matte 47.5 %; 740×960 | §4, locked prep: the same |
| measure on `drafts/angel/port_check_20261105-010146` (370×480) | `20261105-022358_measure`, 0.5 s | box `ring_top:107,101,150,120` (the canvas box 393,371,553,441 × 480/1770, rounded); at most 0.37 px sideways at f 15 and 1.03 px up at f 26, corr ≥ 0.968; × 1770/480 that is 1.36 and 3.80 canvas px | §5, a2 at full size: 1.18 at f 13 and 3.96 at f 26 |
| stalls and jumps on that draft | — | none; its steps run 0.42 to 3.57 with no run below 0.3 | — |

Screenshots (headless Chrome 156 at 2560×1440, driven over its DevTools protocol on port 9222), under
`benchmarks/runs/2026-11-05/studio/shots/`:
- `e_fits.png`: the three-fit table;
- `e_probe.png`: the probe panel;
- `e_stability.png`: the stability plot under the step series. This draft has no stall and no jump, so no marker shows;
- `e_markers_injected.png`: the stall band and two jump ticks drawn from values injected into the page only (nothing
  written to disk), to show how the markers look;
- `e_diff.png`: the difference mode, k0 against k1 on the registration panel;
- `e_wipe.png`: the wipe on the render panel, frame 20 (a RIFE frame) against k0;
- `e_graph.png`: the graph with nine nodes and nine lines.

A keyboard drive passed every check. Arrows step frames by 1, shift by 10, and `,` and `.` too. `a` flips A/B. The
handle moved 50 to 39 % without moving the frame. Space plays and pauses in the render viewer only. The strip's and
the graph's arrows move as section 3 says. A graph node's "show" opened k0.png from the registration node and
`sheet.jpg` from the render node, after the render loaded. All five compare modes at 1:1 showed the draft frame at its
370 px, and at 2× at 740 px, with the pixelated class on A, B and the difference canvas. No console error appeared in
any drive.

## 5. Files edited

Mine:
- new: `views/fits.py` (99 lines), `views/measures.py` (217), `tests/test_fits.py`, `tests/test_measures.py`,
  `tests/test_server_views.py`;
- rewritten: `web/js/viewer.js` (142), `web/js/strip.js` (39), `web/js/graph.js` (65), `web/css/viewer.css` (52),
  `web/css/graph.css` (35);
- edited: `tests/test_views.py` (the `job_view` key set gains `probe` and `graph`; one new test on the branch stale rule).

Shared, Edit only:
- `registry/loop.py`: the `windows` knob at line 97, `parent` on readers at line 110, the probe stage at 117, the
  measure stage at 191.
- `registry/hints.py`: my block at lines 339–459; `region.viewer` and `region.axis` rewritten at 302–307, because
  "A (the first still) and B (the last)" no longer held once A and B name the comparator's sources.
- `runner/argv.py`: `import re` and `STILL_RE` (lines 5, 19), `candidate` imported (14), the probe and measure branches
  at 164–199.
- `views/job.py`: imports (13–20), `prep_summary` keys (58–64), `_probe_tile` and `_measure_tile` (84–118), `parent` and
  `branch` (146–147), the two tiles (217–220), the stale rule (277–291), `_port` and `graph_view` (302–364), `job_view`
  (378–379).
- `views/render.py`: the import (12) and six lines at 64–69.
- `web/js/panels.js`: the dispatch (line 6), `fitsTable` and the viewer in the registration panel (13–31), the viewer in
  readers, `panelProbe` (33–50), `wirePanel` (67–69).
- `web/js/inspector.js`: the measure `render` select (line 8), the measures rows and the Stability section (14–15),
  `verdictOf` (25).
- `web/index.html`: the strip and graph switch, an id on the strip wrapper, the graph region (lines 37–39).
- `tests/fakes/loop_seq.py`: `prep --windows`, `probe` and `measure` in the real shapes; under `FAKE_NO_FLAGS` the three
  are absent, as in an older script; `FAKE_NO_RIFE=1` plays the RIFE skip path.

Outside both lists: `tests/integration/test_loopseq_help.py`, two rows of its `ARGV_FLAGS` table (`probe`, `measure`).
`make test` failed with a `KeyError` on my two stages until they were there. The file is on none of the brief's three
lists.

Not edited: `runner/process.py`, `server/routes.py` (no route added: the panels read the new data through `job_view`,
`render_view` and the file route, so the walk stays at 26 and `test_server.py` is unchanged), `core.js`, `boot.js`,
`tests/conftest.py`, `tests/test_runner.py`.

Asked of you, since I may not edit them:
- `studio/ARCHITECTURE.md`: the module map lacks `views.fits` and `views.measures`. It still says "8 stages",
  "HINTS (85 keys)" and "graph.js … placeholders", and its test counts are old.
- `studio/README.md`, "Where state lives": the run folder now also holds `in/<seq>/probe/` and
  `<render>/measures/<stamp>/`.

## 6. Left out, and why

- **The jump rule as written.** "A step above 3× the mean of its two neighbours" listed the encoder's noise. Step 0 is
  0.01 against 0.0 inside a byte-exact hold, and with the stall rule it flagged 110 of the 193 renders on disk that
  have a frames.json. A jump must now also reach the 0.3 stall bar; that is the playbook's own number, so no threshold
  was invented. The hint says so, and a test pins it (the mutation `>=` to `>` turns it red). With the floor, a second
  scan nine minutes later (195 renders by then) flags 76: 69 have stalls and 30 have jumps, 23 of them both. Both scans
  only read.
- **No flag probe for probe and measure.** Adding fields to `ScriptFlags` would change the equality pins in
  `test_views.py`, `test_runner.py` and both integration tests. The commands exist in the script's `--help` (md5
  474d57b3…), and an older script fails the stage with argparse's message in the record.
- **A separate measure panel table.** The measure tile's panel shows the render list and the viewer, with the runs
  table under the plot; I added no fourth view of the same runs.
- **Reconnecting an input from a node** (`STUDIO.md` §3 lists it). The brief's graph deliverable asks for none; the
  measure's input is its `render` knob in the inspector.
- **Complexity.** radon (printed, not gating) grades `graph_view` E (35), `probe_view` and `fits_summary` D, and
  `stage_views` rose from F (74) to F (84). I left them as they are.
- **The acceptance layer.** I wrote no `tests/acceptance/` drive; my drives are the scratchpad scripts named in the
  appendix.

## 7. Found, not changed

1. The stall rule as specified flags the accepted seasons loop s6 at steps 30–49 and 145–162. Each sheets pass opens with
   11 frames identical to the hold (steps 0.0) and eases in and out. The bar was distilled from RIFE legs; a per-method
   bar is the owner's call. The code keeps the rule as written.
2. Before my change, pressing space or `m` while another panel was selected threw a `TypeError` in A1's viewer:
   `$('#play')` is null there, and the stale `S.render` let `m` post a mark. `togglePlay` and `markFrame` now act in
   the render viewer only.
3. The owner's server on 8380 still runs the old modules in memory but reads the page's scripts from disk. On a reload
   it serves the new page over the old API; the new scripts guard every new key, so the page degrades to A1's view. I
   did not touch that server.
4. The scratchpad is shared by every agent of the session. My first `qa2.log` was overwritten by another run, so my logs
   carry an `e_` prefix.
5. `make test`'s integration drive renders a new `port_check_<stamp>` draft into job `loop_angel_20261104-220719` on
   every run (`20261105-023235_render` came from my last run), so that job's draft list grows with each gate.

## Appendix: commands and logs

- Server: `uv run reveal-studio serve --port 8394 --no-browser --lock <scratchpad>/e.lock` (pid 39716), stopped by its
  pid at 02:40; the owner's server on 8380 (pid 51553) was never touched.
- Scratchpad (`/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/d9082b8f-cf5b-4b41-ba3c-c8c2ee5b8bc6/scratchpad/`):
  `cdp.mjs` (the driver), `smoke.mjs`, `shots.mjs`, `markers.mjs`, `keys.mjs`, `e_paths.mjs`, and the gate logs
  `e_qa_final.log` and `e_test_final.log`.
- The scan of the renders on disk read every `benchmarks/runs/**/measure.json` that has a `frames.json` beside it and
  ran `frame_kinds` and `stalls_and_jumps`; it wrote nothing.
