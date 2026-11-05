<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_design.md (gitignored), the phase B design note written by the main thread (Fable 5.1) from the three research reports: 20 decisions, the contracts the builders share, the waves and the ownership; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-verified the mismatch_3 anchors by rendering both argvs (DECISIONS 2026-11-05 eighth and ninth lines) and nothing else -->

<!-- reader: the phase B builders (the generalization slice, then the pair, director and loop builders) and a cold reader of the research copy. shape: report. Written 2026-11-05 by the main thread (Fable 5.1) from the three research reports beside it. -->

## Phase B design: the pair and director flows on the studio's shell

Phase B lands in four waves on the package `studio/`: one generalization slice first, alone and green; then three builders in parallel (the pair flow, the director flow, the loop items of the continued row); then the acceptance drives, a Fable review and a critique; then a fix round. The design of record stays `STUDIO.md` (§2 the registry table, §4 the job folder, §5 the backend contract, §9 the phases); this note fixes the shapes the builders share, so that two of them never edit one file. Every claim below carries its source: the three reports (`b_pair_research.md`, `b_seams_research.md`, `b_director_research.md`, this folder) or a file line.

Asked of nobody: the decisions are taken (the table below). Open items go to the handover (the last section).

### Decisions (2026-11-05, the main thread)

| # | Decision | Why | Source |
|---|---|---|---|
| 1 | The acceptance pins two director argvs: the two-knob argv of `STUDIO.md §9` row B at md5 01b3cf3c769ee45e44a73f1ade36a3b6, and the workbench's four-knob argv at 5b3ee379776ae4e8ce2dec4fa3293740 | both reproduce under renderer 05cd6e1d… on 2026-11-05 (14 s each); the four-knob one proves the studio reproduces the workbench's own record | DECISIONS 2026-11-05 eighth and ninth lines |
| 2 | The plan stage never pre-fills the last round's knobs on its own; a button "load the last round's knobs" does it on request | the pre-fill is what hid two knobs in the workbench's acceptance | `b_director_research.md` key facts 1–2 |
| 3 | Reveal's verdict is an optional branch stage `verdict` under `import`, shared by the pair and director flows, defined once (`registry/common.py`, `runner/argv_common.py`), owned by builder P | one argv per record; a 2–16 s align beside a 1.9 s relation; the workbench showed it beside the class | `b_pair_research.md` Part 1 (the verdict table) |
| 4 | The pair's page is written by the studio (a builtin `page` stage) into `<root>/index.html` and `page.md5`; the round opens through a shared `jobs/rounds.open_round` | no page script exists for a pair; one round shape for every flow | `b_pair_research.md` Part 1 (the page options table) |
| 5 | The director's page runs `director_page.py RUN --notes --title --key [--head] [--keyframes]` in place; the runner copies the previous `run/index.html` beside the record before the run; no flag is added to the script this session | the script has no `--out`; a new flag needs a byte-identity proof | `b_director_research.md` §1, §6 |
| 6 | Every render stage carries an int knob `draft` (0 = full size, else the long edge of a draft) and the two-photo flows an int `max_long` (default 1920) for the full render; a draft goes under `drafts/` | the round rule, `is_draft` and the page's stale rule read `draft` and stay free of new code | `b_seams_research.md` (the `draft` convention) |
| 7 | The director's `--set` overrides ride one knob `set` of the new type `object` (a dict): one `--set k=<json>` per key, in key order; a key is one dotted segment at most | the renderer routes on the first dot (D:883, D:1441) | `b_director_research.md` §2 |
| 8 | A director render folder is `<frozen stem>_<concept>[-<tag>]` under `<job>/run/`; the tag is letters, digits and dashes; the first render of a stem and concept may skip the tag; a plan saved in the job renders under its source's frozen stem | `director_page.py` splits at the last underscore and reads `scripts/research/plans/<stem>.json` | `b_director_research.md` §6 |
| 9 | Every `job.json` carries `seq`: the sequence for a loop, the pair's name for a pair or director job | a `job.json` without `seq` makes `GET /api/jobs` answer 500 | `b_seams_research.md` key fact 1 |
| 10 | The Runner reads the script from the record's own `argv[1]`: `script_md5`, the pid check and cancel | the loop script's path is hard-wired in three places and a live director render would read as gone | `b_seams_research.md` key facts 2–3 |
| 11 | The "unchanged" rule reads `identity` patterns from each stage definition | `loop.mp4` is named for every render stage today | `b_seams_research.md` row 24 |
| 12 | The grades of the two-photo flows take the picks shape `{date, page, best, clips.<render>.{acceptable, note, props{one_picture, transforms, not_invented}, frames?, render?, draft?}}`, shape-checked as the workbench did; his words stay verbatim in `note` and in the round's `text` | `STUDIO.md §3` keeps the picks shape for director rounds; one shape serves both two-photo flows | `b_pair_research.md` Part 1; `director_ui.py:688–707` |
| 13 | The hints split into one module per flow (`hints.py` keeps the loop's 290 keys; `hints_pair.py`, `hints_director.py`), merged into `HINTS` with a disjointness test; flow controls take the prefixes `control.pair_` and `control.director_` | both builders would edit one 1,170-line file | `b_seams_research.md` row 7 |
| 14 | The routes split into the 26 shared rows (`routes.py`, pinned) and one list per flow (`routes_pair.py`, `routes_director.py`) spliced before the two fallback rows | the route-coverage test pins the table's count | `b_seams_research.md` row 43 |
| 15 | The file route serves, read-only, the job folder, its root, `fixtures/`, the layers root, the mattes root, and the helper files a job's plans name (hashed at import) | the overlays and the page's keyframe tiles read them; the workbench served the first three | `b_director_research.md` §6; `director_ui.py:727–741` |
| 16 | Sequences above 6 stills get a hint chip ("above every sequence registered so far: 6"), above 10 a second chip naming the design's 2–10 range; no refusal | no script states a cap; the conventions forbid an invented range | `b_pair_research.md` Part 4(a) |
| 17 | The repaint leg of `loop_seq.py` is built by builder L in wave 2 as a default-off leg method `repaint` (the spec of `b_pair_research.md` Part 4(b)), proved byte-identical on a2 and s6; nothing of the boxes clip is re-rendered for the owner | the continued row of `STUDIO.md §9` names it; his word of 2026-10-17 on the draw ("Do not redraw anything") covers the boxes clips, not the mechanism | `b_pair_research.md` Part 4(b) |
| 18 | The request pickup at boot (T74) is proposed in the handover as the exact hook line; no session edits `.claude/**`; the A1 acceptance test answers its own request from now on | his decision; the seven stale requests were answered on 2026-11-05 | `b_pair_research.md` Part 3 |
| 19 | The viewer plays at the clip's fps (the render view carries `fps`: the loop 25, the director 30, a pair its spec's) | director clips run at 30 fps and the viewer played 25 | `b_director_research.md` key fact 14 |
| 20 | `stage_views` splits into one tile function per stage, in a table per flow, in the slice; `Runner.finalize` stays whole (backlog T96 open) | the builders add tiles without editing `stage_views`; radon F (92) today | `b_seams_research.md` (the radon section) |

### The contracts

**Settings** (`config.py`; every path derived from the root as `loop_seq` is; `reveal-studio check` prints each with its md5 or a count; a missing one prints MISSING and leaves the exit code alone):

| Key | Path | Environment | Note |
|---|---|---|---|
| `transitions` | `transitions.py` | — | the pair's relation and render |
| `reveal` | `reveal.py` | — | the verdict branch (phase C's align flow) |
| `director_render` | `scripts/research/director_render.py` | — | resolve and render |
| `director_page` | `scripts/research/director_page.py` | — | the director's page |
| `director_plans` | `scripts/research/plans` | — | the frozen director plans (19 files); the loop's stay `frozen_plans` = `scripts/research/plans/loops` |
| `fixtures` | `fixtures/` | — | the fixture pairs `<group>_<N>_S.<ext>`, `_F.<ext>` (19 pairs) |
| `layers_dir` | `benchmarks/runs/2026-09-28/layers_v3` | `REVEAL_STUDIO_LAYERS_DIR`, flag `--layers-dir` | the renderer's own default (`director_render.py --help`) |
| `mattes_dir` | `benchmarks/runs/2026-10-17/mattes` | `REVEAL_STUDIO_MATTES_DIR`, flag `--mattes-dir` | the renderer's own default |

**The registry** (`registry/`): `entries.py` holds `K` (a knob) and `H` (a hint); `flows.py` holds `ALL_FLOWS` (loop, pair, director), `FLOWS` (the enabled ones), `stage_def(flow, name)`, `stage_order(flow)` and `STAGE_NAMES` (the union, the loop's ten first). A flow entry: `{title, what, enabled, stages}`. A stage definition gains `script` (the Settings key of the script it runs: `loop_seq`, `transitions`, `reveal`, `director_render`, `director_page`) and `identity` (the file-name patterns of its result files, for the "unchanged" rule). The knob types: `int float str bool list plan object`. The registry view keeps `stage_order` a list (the union).

The pair flow's stages, in order. The full entries with their sentences are in `b_pair_research.md` Part 1.

| Stage | Kind | Backend or action | Knobs | Terminal file |
|---|---|---|---|---|
| import | builtin | links A and B under `raw/<pair>/` with a sha256 each | — | — |
| relation | script | `transitions.py pair A B --out <root>/relation.part --max-long 480 --seconds 1` | — | `report.json` |
| verdict | script, optional branch under import | `reveal.py align A B --out <root>/verdict.part`; exit 2 with `FAILED:` is `refused` | — | `metrics.json` |
| render | script | `transitions.py pair A B --out <root>/<pair>/<name>.part …`; `--max-long` from `draft` when above 0, else `max_long` | `name`, `draft`, `max_long` 1920, `seconds` 1.0 [0.1, 10], `fps` 30.0, `preset` morph (7 choices), `color` 0.7 [0, 1], `warp` 1.0 [0, 1], `canvas` finish or common, `anchors` "", `anchor_falloff` 0.45 [0, 0.5], `force_class` "", A or B, `camera` flat, ramp or model, `zoom` 0.1 [0.02, 0.5] | `report.json` |
| skeptic | request | a request file; the answer in the loop's shape | — | — |
| page | builtin | the studio writes `<root>/index.html` and `page.md5` | `title`, `intro`, `footer`, `variants` | `index.html` |
| grades | builtin | the picks shape | — | — |

A new pair job: `POST /api/jobs {flow: "pair", fixture: "<pair>"}` or `{flow: "pair", a: <path>, b: <path>}`.

The director flow's stages, in order. The full entries are in `b_director_research.md` §1.

| Stage | Kind | Backend or action | Knobs | Output |
|---|---|---|---|---|
| import | builtin | by pair name: a pair that a plan under `scripts/research/plans/` names; `raw/<pair>/A.<ext>`, `B.<ext>` linked as records (the renderer reads `fixtures/<pair>_S` and `_F` from the plan's `pair`); the layer tables and the mattes of both photos located and counted; the helpers the pair's plans name hashed | — | `job.json` |
| verdict | the shared branch | as the pair flow | — | `metrics.json` |
| resolve | script | `director_render.py PLAN OUT --resolve-only [--concept C] [--max-long N] [--set …] --layers-dir L --mattes-dir M` into `<job>/resolve/<stamp>/` | `plan`, `concept`, `max_long` 1920, `set` {} | `anchors.json` (with `canvas_A.png`, `canvas_B.png`, `info.json`) |
| plan | builtin | a plan, a concept and the `set` dict; the timeline bars in clip time with drag, resize, mute and solo; the concept's knob table in both name forms; the 28 global rows with each row's condition; the 8 read-only rows of table D; the extra `key=JSON` lines; the command preview; a button "load the last round's knobs" | — | a job plan under `plans/` only when saved |
| render | script | `director_render.py PLAN OUT --concept C --max-long N --seconds S --fps F --set … --progress --layers-dir L --mattes-dir M`; a full render into `<job>/run/<stem>_<concept>[-<tag>]/`, a draft into `<job>/drafts/<stem>_<concept>[-<tag>]/`; fewer than 3 frames refused | `plan`, `concept`, `name` (the tag), `draft`, `max_long` 1920, `seconds` 3.0, `fps` 30, `set` {} | `info.json` |
| skeptic | request | the answer gains `look` and `faults` per candidate, which the page prints from `notes.json` | — | — |
| page | script | `director_page.py run --notes <rec>/notes.json --title T --key K [--head H] [--keyframes J]`, written in place; the previous page copied to `<rec>/previous_index.html` before the run | `title`, `key`, `head`, `keyframes` | `run/index.html` |
| grades | builtin | the picks shape | — | — |

A new director job: `POST /api/jobs {flow: "director", pair: "<pair>"}`.

**The job folders** (`STUDIO.md §4` kept; the loop's unchanged):

```
pair_<pair>_<stamp>/        job.json {id, flow: "pair", seq: "<pair>", fixture: "<pair>"|null, inputs: [{role: A|B, name, path, sha256, bytes, link}], root: "<this folder>", adopted: false}
  raw/<pair>/A.<ext>, B.<ext>    symlinks (the extension kept: transitions.py picks its reader by suffix)
  relation/                      report.json, strip.jpg, transition.mp4 at 480 px, 1 s; a rerun replaces it
  verdict/                       metrics.json, before.jpg, after_aligned.jpg on success; a refusal leaves the record's reason
  <pair>/<name>/                 a full render: transition.mp4, strip.jpg, report.json; never overwritten
  drafts/<pair>/<name>/          a draft
  index.html, page.md5           the page the studio writes
  stages/ plans/ requests/ answers/ rounds/<n>/ picks/ owner_frames/ cache/    as the loop job
director_<pair>_<stamp>/    job.json {id, flow: "director", seq: "<pair>", pair, inputs (A, B), root: "<this folder>/run", layers_dir, mattes_dir,
                                      tables: {A: {path, sha256, elements}, B}, mattes: {A: {count, missing: [ids]}, B}, helpers: [{path, sha256}], adopted: false}
  raw/<pair>/A.<ext>, B.<ext>    records only
  resolve/<stamp>/               canvas_A.png, canvas_B.png, anchors.json, info.json (outside run/: the page script lists every child of run/ that holds an info.json)
  run/<stem>_<concept>[-<tag>]/  the full renders: transition.mp4, montage.jpg, info.json
  run/index.html, run/notes.json the page and the skeptic's notes; page.md5 beside them
  drafts/<stem>_<concept>[-<tag>]/   the 480 px drafts (outside run/)
  verdict/                       the shared branch's outputs
  stages/ plans/ requests/ answers/ rounds/<n>/ picks/ owner_frames/ cache/    as the loop job
```

**Candidates** (`jobs/candidates.py`): the loop keeps its reader; a spec reader serves the other flows from a per-flow spec `{full: [folders], draft: [folders], terminal, mp4, record_knobs}`. A candidate carries `{name, kind, dir, path, md5_mp4, frames, seconds, canvas, draft, verdict, unjudged, unjudged_reason, mtime}` plus the flow's numbers: a pair's `class, method, sparse_inliers, median_disp_px, mean_certainty, n_frames, preset, quality`; a director's `info.json` scalars (`motion_median_px, motion_pauses, motion_jumps, b_inside_first, residual_edge_max, halo_step_max, halo_ring_max, step_first, step_max, wall_s, renderer_md5, transitions_md5, plan_sha256`, the 16-character one from the file and the full one from the record). `md5_mp4` comes from the record's outputs, else hashed and cached under `cache/` by size and mtime (neither `report.json` nor `info.json` carries it).

**Records**: unchanged shape; `script_md5` is the md5 of `root / argv[1]`; a render record's `outputs` carry the mp4's md5; the director's render record keeps the plan's full sha256 in `inputs`.

**Routes**: the 26 shared rows unchanged. New rows: `GET /api/pairs` (the fixture pairs with their plans, layer and matte status; D), `GET /api/plans/director/<stem>` (D), `GET /api/jobs/<id>/overlay/<A|B>/<kind>.png` with kinds `base elements disparity matte_<id>` (D; cached under `cache/overlays/`; cv2 and numpy in `media/` only), `GET /api/jobs/<id>/relation` (P; the report, the strip url, the 480 mp4's frame urls), `GET /api/jobs/<id>/verdict` (P). `POST /api/jobs` passes `fixture`, `a`, `b`, `pair`. The render view route `GET /api/jobs/<id>/render/<kind>/<name>` dispatches by flow (`views/pair.py`, `views/director.py`) and carries `fps`, `mp4_url`, `frame_url`, `frames_available`, `frames_tags` (the director: a tag per frame from the beats' windows; a pair: photo at 0 and n−1, blend between), the flow's measures and series.

**The job view** keeps the loop's keys; a pair job adds `relation` and `verdict`; a director job adds `director` ({pair, tables, mattes, helpers, plans: the frozen director plans with their concepts}), `resolve` (the latest resolve's anchors, canvases and info) and `verdict`.

**The page** (`web/`): `core.js` declares `FLOW_UI = {}`; each flow script registers `FLOW_UI[flow] = {panels: {stage: fn}, wire: fn, sources: fn, candRow: fn, plots: fn, newJob: fn, inputsWord: str}`; the loop's entries are registered by the existing scripts at load. `panels.js` picks `FLOW_UI[v.job.flow].panels[stage]`, else a plain panel with the stage's sentence. The rail draws one "new job" button per enabled flow that registers `newJob`. The viewer's sources, the candidate row, the plots and the playback fps come from the flow's entry. `plan.js` stays the loop's editor; `director.js` holds the director's plan panel (the bars, the `--set` table, the knob map); `pair.js` the relation and render panels. The hints: every new control carries a key from its flow's module.

**Tests and fakes**: `tests/conftest.py`'s `make_root` copies each fake of a table when its file exists (`tests/fakes/loop_seq.py`, `transitions.py`, `director_render.py`, `director_page.py`), writes the fixture images with cv2 at test time, and a minimal director plan plus a layer table and a matte folder under the tmp root. The count assertions become per flow: the loop's 10 stages, 151 schema rows, 7 rulings, 290 hints; the 26 shared routes; each flow pins its own order, routes and hints in its own test file. The snapshot test of the loop's argv and tiles (`tests/test_loop_snapshot.py`) passes before and after the slice.

**The import contracts** (`.importlinter`): the forbidden names gain `director_render`, `director_page`, `director_ui`, `chain_luma`, `layer_merge`, `matte_source`, `layered_probe`, `nest_probe`; cv2 stays inside `media/`; the layers unchanged.

### Waves, ownership, order

| Wave | Who | Owns | Proof before the report |
|---|---|---|---|
| 1. the slice | one Opus 5.5 builder | the 10 steps of `b_seams_research.md` "The generalization slice" (snapshot tests first; Settings; the registry split with the flow stubs; `seq`; the creators; `open_round` and the picks writer; the argv split; the Runner's `argv[1]` and identity; the tile table; `render_view` by flow; the route split; the file route's bases; the import contract; `FLOW_UI`; the fakes table; the per-flow counts; the still-count chips; the A1 test answering its request) | `make qa`, `make test`; `make acceptance` 2 passed (a2 c302623f…); a Playwright drive of a loop job on a free port; the detector 0 at three viewports |
| 2. P | an Opus 5.5 builder | `registry/pair.py`, `registry/hints_pair.py`, `registry/common.py`, `runner/argv_pair.py`, `runner/argv_common.py`, `views/pair.py`, `server/routes_pair.py`, `web/js/pair.js`, `web/css/pair.css`, `tests/fakes/transitions.py`, `tests/fakes/reveal.py`, `tests/test_pair_flow.py`, `tests/test_server_pair.py`, `tests/integration/test_transitions_help.py`, `tests/acceptance/test_b_pair_flow.py` | its own tests; `make qa`; `make test`; the relation on mismatch_3 twice (mp4 25c0f77ce05ce8ed53580bb36da24acb, strip 8bd77a4dbbd9763ccd1fd95ca9cdddef) |
| 2. D | an Opus 5.5 builder | `registry/director.py`, `registry/hints_director.py`, `runner/argv_director.py`, `views/director.py`, `server/routes_director.py`, `media/overlays.py`, `web/js/director.js`, `web/css/director.css`, `tests/fakes/director_render.py`, `tests/fakes/director_page.py`, `tests/test_director_flow.py`, `tests/test_server_director.py`, `tests/integration/test_director_help.py`, `tests/acceptance/test_b_director_flow.py` | its own tests; `make qa`; `make test`; the two anchors through the package (01b3cf3c…, 5b3ee379…) |
| 2. L | an Opus 5.5 builder | `scripts/research/loop_seq.py` (the `repaint` leg, default-off), `scripts/research/plans/loops/SCHEMA.md`, the loop rows of `registry/schema.py` and `registry/hints.py`, `tests/fakes/loop_seq.py`, `tests/test_registry.py` (the loop counts), `views/measures.py` (Edit-only: `frame_kinds` reads "none (repaint)") | a2 c302623f… and s6 5908af3d… before and after; the four self-checks of `b_pair_research.md` Part 4(b); the seven-still job from `benchmarks/runs/2026-10-09/fabra/draw7_3s/aligned/` registered and rendered at 480 |
| 3 | an Opus driver, a Fable reviewer, an Opus critic | the drives one at a time (the director, then the pair, then the loop acceptance); the review; the critique with the detector at three viewports | the reports under this folder |
| 4 | an Opus fixer | the fix round on its own port and headless Chrome | `make qa`, `make test`, `make acceptance`, the detector, a keyboard drive |

Shared files closed to the wave-2 builders: `server/routes.py`, `registry/hints.py` (except L's loop rows), `web/js/panels.js`, `web/index.html` (the slice adds the two stub script tags), `views/job.py`, `tests/conftest.py`, `runner/process.py`, `jobs/store.py`, `jobs/candidates.py`, `config.py`. A builder that needs a change there reports it as a request; the main thread edits. D's `views/models.py` rows (the layers and the mattes in the models panel) and `media/pictures.py` (a thumbnail from `canvas_A.png`) are Edit-only for D.

### Proofs and risks

| Risk | Check |
|---|---|
| the loop path changes under the slice | the argv and tile snapshots; `test_compat.py`; `make acceptance` (a2 c302623f…, the 960 draft 3d453980…, the 480 draft 2955c25c…) |
| the hints merge drops or doubles a key | `len(HINTS)` 290 right after the slice; the disjointness test; `test_prose.py` |
| the route splice reorders the fallbacks | `len(routes.CORE) == 26`; the route walk per flow |
| the Runner's `argv[1]` rule breaks the re-attach or the stranger-pid rule | `test_runner.py` (24 functions), the acceptance tests' restart checks |
| two drives render at once | one at a time; `wait_quiet` skips a drive while another record runs (T88) |
| a job id collides within one second | each drive uses its own pair |
| the GitHub workflow (unit layer, ubuntu) | the fakes are stdlib plus cv2 and numpy; no new package |

### Deferred to the handover

The request pickup hook line (T74; his decision; the exact line in `b_pair_research.md` Part 3). A `--plans-dir` flag on `director_page.py` so a plan saved in a job gets its own page text (a byte-identity proof needed). The 8 `--set` keys without effect are read-only rows; a backlog row proposes the renderer fix. The warp override of `transitions.py`'s CLI (`--warp` 1.0 overrides every preset's own value) is a backlog row for his word. The disparity overlay against the render's own map is UNVERIFIED.
