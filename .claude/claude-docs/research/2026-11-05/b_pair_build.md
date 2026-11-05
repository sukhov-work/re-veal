<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_pair_build.md (gitignored), the pair transition flow of phase B built on the package by builder P (Opus 5.5, max effort): seven stages, 14 render knobs with the ranges of transitions.py's clamp, the studio-written page, 49 tests, the acceptance on mismatch_3 passed twice; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance tests on the integrated tree before the commit -->

<!-- reader: the main thread, the acceptance driver and the reviewer of phase B, cold. shape: report. Written 2026-11-05 by builder P (Opus 5.5) on the package studio/; the evidence sits beside it in b_pair_build/ (gitignored). -->

## Phase B's pair flow: built and enabled; my files pass every gate

The pair transition flow works end to end and is enabled as of 2026-11-05. `make -k qa` passed every target, with 549 unit tests in 2 min 19 s. On the final tree `make test` passed 573 of 574. The one red test pins the loop hints' digest, which the main thread's edit of `registry/hints.py` moved. The acceptance test passed twice on mismatch_3, in 52 s and 59 s.

The relation (the flow's 480 px, one-second read) reproduced the recorded md5s: mp4 25c0f77ce05ce8ed53580bb36da24acb and strip 8bd77a4dbbd9763ccd1fd95ca9cdddef. The full render at 1920 gave 7262bb06a58194fe7993e01a1eff1eda four times over two jobs.

Asked of the main thread (detail below):
1. Accept one edit outside my files: a four-line dispatch in `views/page.py` that sends a builtin page stage to the pair's writer after the review gate.
2. Add the pair's new modules and tests to `studio/ARCHITECTURE.md`.
3. Optional: merge two lists of fixture pairs.

Done in the tree by the main thread while I wrote this: four shared hints made flow-neutral, reserved pair names refused at creation, the picks file named by flow, the Makefile's acceptance line.

Open: a HEIC pair through the flow is UNVERIFIED (the acceptance pair is JPEG).

| Term | Meaning here |
|---|---|
| the owner, "he" | the person the studio serves; his words grade the rounds |
| the slice, my brief | phase B's generalization slice (wave 1, `b_slice.md` beside this file); the main thread's instructions to builder P |
| builder P, builder D, builder L | the wave-2 Opus subagents that build the pair flow, the director flow and the loop's repaint leg |
| mismatch_3 | the fixture pair `fixtures/mismatch_3_S.jpg` and `_F.jpg`: a crowded bar and a lounge group, which Reveal refuses (`fixtures/MANIFEST.md`) |
| class A, class B | transitions.py's routing: class A has a sane homography with 30 or more SIFT inliers and morphs along a dense flow; class B is any other pair, each photo zooms and pans about its salient blob (method `saliency-panzoom`) |
| relation | the pair flow's first script stage: `transitions.py pair` at 480 px for 1 s, read for the class it reports |
| Reveal's verdict | the optional branch stage under the import, shared with the director flow: `reveal.py align` on the two photos |
| quality basket | the `quality` block of transitions.py's `report.json` (warping error, flicker, goal numbers, endpoints) |
| decoded step series | the studio's per-step mean grey difference on the decoded mp4, the measure `quality.flicker` takes before the encode |
| skeptic, picks | the skeptic: a request file a Claude subagent answers with a verdict per full render's md5; the picks: his grade, a best render and per render acceptable, a note and three boxes |
| builtin page record | the stage record the studio writes when it writes a pair page itself: state done, an empty argv, `builtin: true` |
| review gate, round gate | the page's refusal while a listed render is unjudged or NOT READY, unless the owner overrides; a new round's first full render waits for the previous round's grade |
| wave 3 | the acceptance drive through the served page, a read-only review by a Fable subagent, and the critique with impeccable's anti-pattern detector |

### Files

Paths are under `studio/src/reveal_studio/` unless they start with `tests/`.

| File | What it holds | State |
|---|---|---|
| `registry/pair.py` | the seven stages, the 14 render knobs, `RELATION_LONG` 480, `PRESETS`, `enabled: True` | changed |
| `registry/hints_pair.py` | 67 hint rows | changed |
| `runner/argv_pair.py` | `argv_relation`, `argv_render` (one `--max-long`), `render_name`; `RESERVED`, an alias of `registry/pair.RESERVED_NAMES` since the main thread moved the set | changed |
| `media/pair.py` | `step_series`: the decoded step series and the decode's observables, cached by the mp4's md5 | new |
| `views/pair.py` | 7 tile functions, `relation_view`, `verdict_view`, `extras`, `render_view`, `fixture_pairs`, the basket's bars, `build_pair_page` | changed |
| `views/page.py` | `BUILTIN_PAGES` and the dispatch after the gate; outside my list | changed, request 1 |
| `server/routes_pair.py` | 4 rows: `GET /api/fixtures` and, under `/api/jobs/<id>`, `GET …/relation`, `GET …/relation/frame/<i>`, `GET …/verdict` | changed |
| `web/js/pair.js`, `web/css/pair.css` | the `FLOW_UI.pair` entry; every style rule scoped to a `.pair-` class | changed |
| `tests/fakes/transitions.py` | the real CLI's flags, help sentences and defaults; mp4v mp4, strip, `report.json` last | new |
| `tests/test_pair_flow.py`, `tests/test_server_pair.py` | 34 and 9 unit tests | changed, new |
| `tests/integration/test_transitions_help.py` | 4 tests against the real `transitions.py` | new |
| `tests/acceptance/test_b_pair_flow.py` | 1 test: the whole flow on mismatch_3 | new |

`registry/common.py`, `runner/argv_common.py` and `tests/fakes/reveal.py` are unchanged; the verdict worked as the slice left it.

### The stages as built

Terminal is the file whose presence marks a finished run; identity, the files whose md5s make a rerun say unchanged; stale after, the stages whose later run marks this one stale.

| Stage | Kind | Runs | Knobs | Terminal | Identity | Stale after |
|---|---|---|---|---|---|---|
| import | builtin | links A and B, a sha256 each | — | — | — | — |
| verdict | script, branch under import | `reveal.py align A B --out <job>/verdict.part` | — | `metrics.json` | `metrics.json` | never |
| relation | script | `transitions.py pair A B --out <job>/relation.part --max-long 480 --seconds 1` | — | `report.json` | `transition.mp4`, `strip.jpg` | any earlier script stage (none) |
| render | script | `transitions.py pair A B --out <job>/<pair>/<name>.part --max-long N` and the flags of the 11 knobs that carry one | 14 | `report.json` | `transition.mp4` | never |
| skeptic | request | `requests/skeptic_<stamp>.json` with the pair's crops | — | — | — | — |
| page | builtin | the studio writes `index.html`, `page_A.jpg`, `page_B.jpg` and a builtin page record | 4 | `index.html` | — | a later full render |
| grades | builtin | the picks shape through the slice's writer | — | — | — | — |

The 14 render knobs: `name`, `draft`, `max_long` (1920), `seconds`, `fps`, `preset`, `color`, `warp`, `canvas`, `anchors`, `anchor_falloff`, `force_class`, `camera` and `zoom`. Five carry the ranges `TransitionSpec.clamp` states: seconds [0.1, 10], color and warp [0, 1], anchor_falloff [0, 0.5], zoom [0.02, 0.5]. `name`, `draft` and `max_long` carry no flag, so the argv holds one `--max-long`: the draft when it is above 0, else `max_long`. The `warp` sentence says the CLI's `--warp` overrides every preset's own value; the backlog row T108 asks the owner's word on that. The `max_long` sentence names its source: 1920 is the default of `scripts/bench_transitions.py`, the fixture sweep.

### Decisions I took

| Choice | Why | Revert |
|---|---|---|
| the relation's identity is the mp4 and the strip | `report.json` holds three clock keys, so with it a rerun never says unchanged; my brief named `report.json` | one list in `registry/pair.py` |
| the builtin page writes a stage record | the stale rule, the history, the graph and `post_page`'s answer all read a record; `open_round` gets its id | write none and pass `record=None` |
| render `stale_after: []`, page `["render"]` | a render reads A and B only, so a relation rerun leaves the renders as they are | drop both keys |
| an empty render name becomes `<preset>_<seconds>s` | the sweep's folder names; `morph_1p5s` for 1.5 s | refuse an empty name |
| A and B on the page are copies of the relation's decoded frames, as `page_A.jpg` and `page_B.jpg` | cv2 reads no HEIC; a name with a dot can never be a pair's folder | another source |
| the relation's frame URLs carry `?m=<md5>` | the frame route's answer is cacheable for an hour | drop the query |

### Tests and two mutations shown red

49 tests: 35 in `test_pair_flow.py` (one of them the main thread's, for the creator's refusal of a reserved name), 9 in `test_server_pair.py`, 4 in the integration file and 1 acceptance test. Each docstring names its mutation. After the main thread's edits, `test_pair_flow.py`, `test_server_pair.py` and the integration file passed 48 of 48. `test_server_pair.py` walks the 4 rows with its own spy, as the shared table's test asks.

| Mutation | Red line | After the revert |
|---|---|---|
| the relation's identity set to `["report.json", "transition.mp4"]` | `test_the_relation_runs_and_a_rerun_says_unchanged`: the rerun's `unchanged_from` is None | 2 passed |
| `views/page.py`'s builtin dispatch disabled | `test_the_page_through_the_shared_route_behind_the_gate`: `assert (400 == 202)` | 1 passed |

### Gates

| Gate | Result | Time |
|---|---|---|
| `make -k qa` | ruff clean, 97 files formatted, mypy clean on 55 files, 549 passed, vulture and deptry clean, no known vulnerabilities, 3 contracts kept, prose 0 blocks | 2 min 19 s |
| `make test` | 573 passed (unit and integration) | 2 min 14 s |
| `make test`, final tree | 573 passed, 1 failed: `test_registry.py::test_the_loop_registry_rows_keep_their_digests`, the loop hints' digest that the main thread's edit of `registry/hints.py` moved | 2 min 30 s |
| acceptance, run 1 | passed | 51.8 s |
| acceptance, run 2 on the final tree | passed | 59.2 s |
| radon | my one block at C: `argv_render` C (11); every block of `views/pair.py` at A or B | — |

During the build, `make qa` met three failures. Lint and mypy failed on `media/overlays.py` while builder D wrote it. Two stub tests in `test_director_flow.py` failed while builder D replaced them. My enabling of the pair flow turned `test_server.py::test_post_jobs_refuses_a_bad_folder` red; that test now sets the enabled flows itself, a change made outside my files. All three were green in the final run. In my last gate run, ruff found one line of 129 characters in `views/tiles_loop.py`, a loop module another builder edits now; my 15 files are clean.

### Acceptance values

The test runs a `reveal-studio serve` subprocess on a free port with a tmp lock against the real tree. It skips unless `transitions.py` is at md5 7ef5dcae070c223e360c9c2e533df6c1 and the two photos match their sha256s. To rerun it (about 1 minute): `studio/.venv/bin/pytest tests/acceptance/test_b_pair_flow.py -m acceptance -s -q` from `studio/`.

| Check | Run 1 (`pair_mismatch_3_20261105-182908`) | Run 2 (`pair_mismatch_3_20261105-184450`) |
|---|---|---|
| relation | 2.4 s; class B, `saliency-panzoom`, 0 inliers, 24.71 px, canvas 480×360; mp4 25c0f77c…, strip 8bd77a4d… | the same, 2.4 s |
| relation rerun | 2.3 s; both md5s again; `unchanged_from` the first | the same, 2.3 s |
| verdict (a refusal is the expected outcome on this pair) | refused in 6.8 s: "FAILED: Could not find enough common detail between the two photos. They need to show the same scene from roughly the same spot." | refused in 14.1 s, the same line |
| draft morph480 (480 px, 1 s) | 2.5 s; mp4 25c0f77c… and strip 8bd77a4d…, the relation's own | the same |
| full morph1920 and morph1920b | 7.8 s and 8.1 s; both 7262bb06a58194fe7993e01a1eff1eda; canvas 1920×1440, class B, 6 inliers, 121.92 px | 7.7 s and 7.7 s, the same md5 |
| render view | 30 fps, 30 frames; decoded step max 0.0580 against the report's flicker max 0.0583; edge ratio 0.134 | the same |
| skeptic | request written with the crops, answered by the test with an empty candidates map | the same |
| page | 409 refusing both renders, then 202 on an override; round 1 on md5 56da03ea75848990879aec590b21ea0b | md5 308c4f7ce86d8e1c2eb11aff9e4e0f6b |
| grade | `picks/director_picks_20261105-182940.json`, shape-checked (named before the main thread's rename to `<flow>_picks_`) | `…-184529.json` |
| restart during a 3 s render at 1920 | re-attached by the new server, done in 19.2 s, mp4 d3a476fb6310829037ab8958f75c57fa | 18.9 s, the same md5 |

The page md5 differs between runs because the page prints the time it was written. The 1920 render's 6 inliers and 121.92 px are `fixtures/MANIFEST.md`'s values for mismatch_3. The originals kept their mtimes and sha256s, and `fixtures/` gained no file.

### Requests to the main thread

| Request | File | Why |
|---|---|---|
| accept the dispatch: `BUILTIN_PAGES = {"pair": pair.build_pair_page}`; a builtin page stage goes to its writer after the review gate | `views/page.py` | the shared row `POST /api/jobs/<id>/page` answers before any flow's row, and `start_stage` refuses a builtin stage with a 400 |
| done in the tree: `region.viewer`, `chip.tag`, `control.render` and `control.candidate` now name each flow; the loop hints' digest in `test_registry.py` still pins the old text | `registry/hints.py`, `tests/test_registry.py` | a pair plays at its spec's fps and has neither a plan nor a prep |
| done by the main thread: `create_pair_job` refuses a name in `registry/pair.RESERVED_NAMES` (relation, verdict, drafts, raw, stages, plans, requests, answers, rounds, picks, cache, owner_frames) with a 400 | `jobs/store.py`, `registry/pair.py` | a pair named "relation" would put its full renders inside `relation/`, which a relation rerun deletes; the render keeps its 409 for a job written by hand |
| add `media/pair.py`, the pair's 4 routes and test files to the module map (the Makefile's acceptance line is done) | `studio/ARCHITECTURE.md` | the module map names the loop's modules only |
| optional: merge `GET /api/fixtures` (every fixture pair, 19 on this tree) with builder D's `GET /api/pairs` | `server/routes_*.py` | two lists of the same pairs; the picks file is already named by flow (`pair_picks_<stamp>.json`) |

### Not done

- The drive through the page, the Fable review, the critique and the detector at three viewports: wave 3's. I opened the page in headless Chrome at 1440×900 only. Every pair panel rendered with 0 console errors and every hint key resolved. That check found 4 layout faults, all fixed: a doubled "A:" label, the plot's title over its bar line, a clipped caption and a cramped inspector table. The screenshots are under `b_pair_build/shots/`.
- A HEIC pair through the flow: UNVERIFIED. The acceptance pair is JPEG. For a HEIC original the import tile shows the relation's frame 0, which a unit test pins with a renamed input.
- The no-slop pass: the checker reports 0 blocks; a cold reader with no session context read the report once, and its findings (undefined terms, the unlisted reserved names, the summary's request count) are fixed.

### Appendix: evidence and the final `git status`

`benchmarks/runs/2026-11-05/studio/agents/b_pair_build/` (gitignored, 4.7 MB):
- `logs/`: `make_k_qa.txt`, `make_test.txt`, both acceptance runs, `mutations.txt`, the unit run with builder D's files in progress, and the browser check's server logs;
- `shots/`: 9 screenshots of the relation, render, grades and written-page views at 1440×900.

My servers on port 8391 and my headless Chrome on 9222 are stopped. `scripts/session_sweep.sh` listed 0 session processes at the end. HEAD is 4e2480a. `git status --short` at the end, with every file of mine marked by its name in the files table; the rest belong to builders D and L or to the main thread:

```
 M .claude/skills/reveal/references/tracked-backlog.md
 M scripts/research/loop_seq.py
 M scripts/research/plans/loops/SCHEMA.md
 M studio/Makefile
 M studio/src/reveal_studio/jobs/grades.py
 M studio/src/reveal_studio/jobs/store.py
 M studio/src/reveal_studio/media/pictures.py
 M studio/src/reveal_studio/registry/director.py
 M studio/src/reveal_studio/registry/hints.py
 M studio/src/reveal_studio/registry/hints_director.py
 M studio/src/reveal_studio/registry/hints_pair.py
 M studio/src/reveal_studio/registry/pair.py
 M studio/src/reveal_studio/registry/schema.py
 M studio/src/reveal_studio/runner/argv_director.py
 M studio/src/reveal_studio/runner/argv_pair.py
 M studio/src/reveal_studio/server/routes_director.py
 M studio/src/reveal_studio/server/routes_pair.py
 M studio/src/reveal_studio/views/director.py
 M studio/src/reveal_studio/views/measures.py
 M studio/src/reveal_studio/views/models.py
 M studio/src/reveal_studio/views/page.py
 M studio/src/reveal_studio/views/pair.py
 M studio/src/reveal_studio/views/tiles_loop.py
 M studio/src/reveal_studio/web/css/director.css
 M studio/src/reveal_studio/web/css/pair.css
 M studio/src/reveal_studio/web/js/director.js
 M studio/src/reveal_studio/web/js/pair.js
 M studio/tests/fakes/loop_seq.py
 M studio/tests/test_director_flow.py
 M studio/tests/test_jobs.py
 M studio/tests/test_pair_flow.py
 M studio/tests/test_registry.py
 M studio/tests/test_server.py
 M studio/tests/test_views.py
?? studio/src/reveal_studio/media/overlays.py
?? studio/src/reveal_studio/media/pair.py
?? studio/tests/acceptance/test_b_director_flow.py
?? studio/tests/acceptance/test_b_pair_flow.py
?? studio/tests/fakes/director_page.py
?? studio/tests/fakes/director_render.py
?? studio/tests/fakes/transitions.py
?? studio/tests/integration/test_director_help.py
?? studio/tests/integration/test_transitions_help.py
?? studio/tests/test_repaint.py
?? studio/tests/test_server_director.py
?? studio/tests/test_server_pair.py
```
