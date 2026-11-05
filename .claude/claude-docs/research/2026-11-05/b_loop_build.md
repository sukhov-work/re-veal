<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_loop_build.md (gitignored), the repaint leg of loop_seq.py and the seven-still check of phase B's continued row by builder L (Opus 5.5, max effort): default-off, a2 and s6 byte-identical before and after, four self-checks, the boxes' seven stills through the studio; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance tests on the integrated tree before the commit -->

<!-- reader: the main thread of the 2026-11-05 session, cold, then a cold session reading its copy under .claude/claude-docs/research/2026-11-05/. shape: report. Written 2026-11-05 by builder L (Opus 5.5) of phase B: the loop items of the continued row of STUDIO.md §9. The evidence sits beside it in b_loop_build/ (gitignored). -->

## The repaint leg of phase B: built default-off, a2 and s6 byte-identical, a seven-still draft through the studio

The `repaint` leg is in `scripts/research/loop_seq.py`, default-off: the frozen loop plans a2 and s6 render c302623f293eacd069218fd7518e0967 and 5908af3d5300046579548848679b0cbb before and after. The four self-checks pass. Through the studio's API the boxes' seven photos were registered and a repaint plan drafted at 480 px (job `loop_boxes7_20261105-181906`, md5 3feab96cbb06d3be9ae31972f571d01c). Every check ran on real photos (`loop_seq.py` has no harness). `make qa` passes on HEAD 4e2480a plus my diff; on the shared tree both gates fail only on the other builders' unfinished work.

Asked of the main thread:
1. Rule on two choices that change the brief's counts: a fourth schema entry, `through` (155 entries, not 154), and repaint named in the `plan.timeline.method` hint.
2. Then commit my 8 files ("Files and counts"; one `git revert` undoes them), and rerun both gates on the shared tree once builders P and D finish.
3. Decide whether the import chip's 6 (`SO_FAR`, `views/tiles_loop.py`, closed to me) should read 7, now that seven stills were registered.
4. Sync DECISIONS, `studio/ARCHITECTURE.md`, `STUDIO.md` §9 and `loops.md` §4 from this report.

Open, for the owner's next repaint request: on the boxes the zone covers 0.911 of the canvas, against 0.346 in chain_luma's draw; `matte.thr` 30 gives 0.587.

### Terms

| Term | Meaning here |
|---|---|
| phase B, its continued row | the studio's second build phase (`STUDIO.md` §9); its continued row holds the repaint leg and sequences of up to 10 stills |
| builder L, P, D | the three parallel builders of phase B: L (this report) the loop items, P the pair flow, D the director flow; the brief is L's task file from the main thread |
| the owner | the person whose photos and taste the project serves; he closed the loops work on 2026-11-05 |
| a2, s6 | the frozen plans `angel_a2.json` and `seasons_s6.json` (`scripts/research/plans/loops/`, 48 hand-written plans the studio never writes) and their renders, whose mp4 md5s are the standing byte-identity checks |
| the chip for more than 6 stills | the warning `chip.above_6` on the import stage's tile in the studio page's strip; `SO_FAR` (6) is the count it compares with |
| the leg | the new `repaint` method of a loop plan's transition (a timeline step with `to`) in `loop_seq.py` |
| `through` | a transition's list of inner stills; the chain passes them and holds none |
| a step, the step series | the mean absolute grey difference between two neighbouring frames of the decoded mp4 (0 to 255, `measure.json`'s `steps`); a plan's steps are called timeline steps here |
| the draw | `chain_luma.py --variant draw`, the per-pixel drawing of the boxes clip of 2026-10-09, which the leg ports |
| the zone | where the leg draws; outside it one dissolve runs from the first still of the chain to the last |
| a pair, its first frame | two consecutive stills of the leg's chain (the `segment` of `frames.json`); the first frame whose `segment` names that pair |
| k0 to k6 | the seven registered stills, `k0.png` to `k6.png` of a prep folder, in capture order |
| the copy | HEAD 4e2480a's `studio/` with my diff applied, in the scratchpad, run with the tools of `studio/.venv` |
| the shared tree | the repo's working tree, which builders P (the pair flow) and D (the director flow) edit at the same time |
| the proof renders | a2 and s6 rendered by the script before my first edit and after my last |
| the drive | the API calls of the seven-still check, made by `drive7.py` |
| a stall | a run of two or more steps below 0.3 grey levels between in-betweens, neither frame a hold nor a cut's first frame (the bar of `.claude/skills/reveal/references/loops.md` §6, which the studio's render view applies) |

### The leg as built

- `loop_seq.py:741–825` holds a comment, `rank_order` and `reveal_mix`, and `frames_repaint`. The two helpers are copied from `tr14_variants.py:111–135` (numpy only); the copy of `reveal_mix` drops its `REVEAL_SOFT` default, since the leg always passes `front`. The script imports nothing new.
- The dispatch is `loop_seq.py:1750–1752`, before the `through` branch. The docstring's line 2 now reads "two or more developed stills", and lines 35–37 add `repaint` to the render paragraph.
- The frames follow `b_pair_research.md` Part 4(b): one profile u = ease(j / (n + 1)) over the whole chain, of which each pair's repaint takes an equal share. Inside the zone a repaint spreads in a per-pixel order that runs from 0 to 1: a pixel turns over while a front `front` wide, in those units, passes it. The order weighs the new still's Canny distance by 0.5, the old still's negated grey by 0.3, and noise at sigma 6 and 24 px seeded k + 1 by 0.2, then ranks again. Repaint k starts `overlap` of a share early and ends as late.
- The zone is each pair's `change_matte` at the plan's `matte` keys, binarized at 0.5, the union eroded by an ellipse of `zone_erode` px and blurred at sigma 8 px.
- Each frame writes the row `{"generated": "none (repaint)", "u", "segment", "t"}`, then `step`, `from`, `to` and `method` as every timeline step's rows do, and one `tick` for `--progress`.
- `SCHEMA.md` lines 277–315 hold the dated section: the four keys, their defaults, chain_luma's three help sentences (`chain_luma.py:283–285`) and the measurements below.

### The byte-identity proof

| Render | Before: script 474d57b324c6c7b815aa13c4444862bb | After: script 860aa6ed034f9b98f32db014190cef2e |
|---|---|---|
| a2 `loop.mp4` | c302623f293eacd069218fd7518e0967, 64.6 s | c302623f293eacd069218fd7518e0967, 85.8 s |
| s6 `loop.mp4` | 5908af3d5300046579548848679b0cbb, 90.7 s | 5908af3d5300046579548848679b0cbb, 119.3 s |

The gif, `sheet.jpg` and `plan.json` of both renders, and s6's `frames.json`, are equal byte for byte. a2's `frames.json` is equal without each row's `seconds`. Both `measure.json` files are equal without `render_s`, `rife_seconds_per_frame` and `script_md5`, in the same key order. The commands are the appendix of `.claude/claude-docs/research/2026-11-05/loopseq_a2.md`, with `--out` under the scratchpad. The after renders took 32 to 33 % longer in wall time, and their `render_s` rose 34 to 37 % (a2 59.2 to 79.3 s, s6 68.9 to 94.7 s). The new branch is never reached on these two plans, so I read the slowdown as load from the other builders' test runs [INFERRED].

### The four self-checks

The checks ran on the seven photos, registered by `prep` at its defaults into the scratchpad (canvas 1492×1882). The plan holds k0 for 12 frames, runs the leg to k6 through stills 1 to 5 with `n` 75 and the default keys, holds k6 for 25 frames and cuts back to k0. A test script of mine, `selfcheck.py`, ran `render_plan` in process with the encoder's input teed into per-frame md5s, so checks 1 and 3 compare exact frames, not yuv420p decodes.

| Check | Observed | Result |
|---|---|---|
| a repaint between two identical stills (k3 twice) | 12 of 12 in-betweens equal the still, both from `frames_repaint` and in the frames sent to the encoder; zone 0.0 | pass |
| two renders of one plan | one `loop.mp4` md5, 6af77b0d6591161bd9f46a0a8ed8c42d, over four renders: two from the CLI and two in process; the two CLI runs' gif, sheet, `frames.json` and `plan.json` equal; the run with `--progress --frames` printed 75 frame lines, one per frame of the leg | pass |
| the holds beside the leg | 37 of 37 hold frames sent to the encoder equal `k0.png` (12) or `k6.png` (25) byte for byte | pass |
| no peak at a pair's first frame | the step into the first frame of each of pairs 2 to 6 is 0.998 to 1.073 times its neighbours' mean; the studio's jump bar is 3 times (pair 1 starts the leg, right after the hold) | pass, with a mild hump |

The leg's 75 frames give 69 other in-betweens: all but the leg's first frame and those 5 first frames. At frames 49 and 68 the ratio (1.073 and 1.059) is higher than at 97 % of those 69. I measured the cause on the same plan:

| `overlap` | Ratio at the 5 first frames | The leg's step mean and max |
|---|---|---|
| 0 | 0.185 to 0.493: the repaint stops at each still | 2.003, 7.59 |
| 0.175, half of `front` | 0.91 to 0.975 | 1.997, 5.77 |
| 0.35, the default | 0.998 to 1.073 | 1.937, 5.14 |

Above half the front, two fronts move at once around each boundary. The defaults stay the draw's; the knob is the owner's.

### The seven-still check through the studio

I started the server only when no job had a running record. It ran the copy's package with `--root` the real tree, on port 8391 with its own lock, and I stopped it after the drive, which took 11 s.

| Step | Result |
|---|---|
| `POST /api/jobs` with `benchmarks/runs/2026-10-09/fabra/draw7_3s/aligned/`, seq `boxes7` | job `loop_boxes7_20261105-181906`; the 7 inputs `0_1.jpg` to `6_7.jpg` linked with their sha256 |
| the import tile | "7 stills" and the warning `chip.above_6`, "above every sequence registered so far (6)" |
| the registration at its defaults (`--long 1920 --ref -1 --bg-depth 0.0 --min-inliers 40`) | 2.2 s; the reference and 6 `sift+magsac` fits with 894, 740, 1047, 1037, 960 and 783 inliers; canvas 1492×1882, crop [32, 16, 1524, 1898]; k0 to k6 byte-equal to the shell prep |
| `POST /api/jobs/<id>/plans`, name `repaint7` | `job:repaint7`, sha256 839a8879eef7dc9a…; its provenance block says it was written from scratch (`from` null, 0 changes against a source); the 48 frozen plans unchanged |
| the render, draft 480 | record `20261105-181909_render`, 7.8 s; `loop.mp4` 3feab96cbb06d3be9ae31972f571d01c, the md5 the shell gave for the same plan at 480 |
| the draft's step series | 112 frames at 380×480; mean 1.298, max 5.594 at step 41; on the leg mean 1.895, max 5.59; first-frame ratios 1.009 to 1.122; no jump |
| the render view | tags `photo` and `repaint`; frame kinds hold 37 and blend 75; 0 generated frames; stalls [12, 17] and [79, 85] |

The two stalls are the leg's slow start and end: under the `smooth` ease its first 6 steps and its last 7 stay below 0.3 grey levels. The studio's rule finds the same two runs on the full-size render. A `linear` ease or a shorter `n` would change them; the plan uses `smooth` because the example step of `b_pair_research.md` Part 4(b) does.

### The zone on the boxes

At the matte's defaults the zone covers 0.911 of the canvas (0.8992 in the 480 draft); the draw of the same photos had 0.346. The draw's zone came from the changed-region masks of `reveal.py`, the repo's aligner: 0.06 to 0.25 of the frame per pair (`draw7_3s/report.json`). The leg's zone comes from `change_matte`, a Lab threshold, which marks 0.32 to 0.90 of the frame per pair. The photos in `aligned/` are already light-matched by chain_luma (an L shift of −11.2 to +26.8 levels per still). Even so, k1 to k2 and k2 to k3 differ by a median of 23 and 28 Lab levels, above the threshold of 14. With `matte.thr` 30 the zone falls to 0.587.

I looked only at the 240 px tiles of the full render's contact sheet; no reviewer cropped it at full size. There the pavement shows the noise order between frames 32 and 56. The roller door, open in k2 and k3, draws open and shut as a bright speckle, as in the draw's clip, whose step peak was that door.

### Files and counts

| File | Change |
|---|---|
| `scripts/research/loop_seq.py` | the leg: 94 lines added, 2 changed |
| `scripts/research/plans/loops/SCHEMA.md` | the dated `repaint` section, 39 lines |
| `studio/src/reveal_studio/registry/schema.py` | `METHODS` 11 to 12; `GROUPS` gains `repaint`; 4 entries: `through` (a list of int), `front` 0.35, `overlap` 0.35, `zone_erode` 15 px, each default from "SCHEMA.md", no range; entries 151 to 155 |
| `studio/src/reveal_studio/registry/hints.py` | 4 rows `plan.timeline.repaint.*` with SCHEMA.md's sentences; repaint named in `plan.timeline.method`; loop rows 292 to 296 |
| `studio/src/reveal_studio/views/measures.py` | `_kind` reads "none (repaint)" as a blend |
| `studio/tests/fakes/loop_seq.py` | a repaint step in the real row shape; a frame's level reads `u` when the row has it, so the other rows keep their bytes |
| `studio/tests/test_registry.py` | the methods list; 296 rows; 155 entries; the digests: hints e99abf4035b79528 (294 rows: the loop's rows without the two still-count chips) and schema 28130182bcbb2232; the digests of the loop's stage table and of the rulings table held |
| `studio/tests/test_repaint.py`, new | 5 tests: the editor's schema view and resolver, the step's groups and validation, the method sentence, the frame kind, a seven-still job drafted through the fake |

`tests/test_loop_snapshot.py` is unchanged and passes: its header says the registry digests moved to `test_registry.py`. HEAD's unit count was 459, by the final rerun of the slice report (`b_slice.md`, phase B's first build wave); my 5 tests and 4 parametrized schema-entry cases make 468.

### Gates

| Gate | Where | Result |
|---|---|---|
| `py_compile` of `loop_seq.py` | the tree | pass |
| every step of `make qa` | the copy | pass: ruff check, ruff format (87 files), mypy (53 files), 468 passed and 2 skipped, vulture, deptry, 3 import contracts kept, prose 0 blocks |
| pip-audit | the shared venv | exit 0 |
| `make -C studio qa` | the shared tree | red at lint: ruff would reformat `registry/director.py` and `registry/hints_director.py`, builder D's files; the later steps did not run there (all ran on the copy) |
| `make -C studio test` | the shared tree | 505 passed, 7 failed: 4 in `test_pair_flow.py`, which builder P is editing; 2 in `test_director_flow.py` and 1 in `test_server.py`, files nobody edited, which still expect the director flow disabled (`test_post_jobs_refuses_a_bad_folder` expects the flows ['loop'] and reads ['director', 'loop']) |
| `tests/integration/test_loopseq_help.py` | the shared tree, the final script | 7 passed: the leg adds no flag |
| the integration layer | the copy, linked to the real `.venv`, `scripts` and `benchmarks` | 13 passed, 1 failed: `test_compat` compares a recorded command with the copy's python path; it passes on the shared tree |

### Choices beyond the brief

The first two rows change counts the brief fixed and need a ruling (ask 2). The other rows and the four smaller choices below are details of the implementation, each with its revert.

| Choice | Why | Revert |
|---|---|---|
| a fourth entry, `timeline[method=repaint].through` | the schema group of the `slices` method has its own `through`; without it the editor lists `through` under "other keys: … the schema does not list them", false once SCHEMA.md lists it | drop the entry and its hint row: 154 entries, 295 rows |
| repaint named in `plan.timeline.method` | that hint lists every method, and `test_the_method_sentence_names_every_method` now pins it | drop the clause and the test |
| each pair's matte binarized at 0.5 before the union | the draw's union was of binary masks | a union of the soft mattes |
| `zone_erode` and the sigmas 6, 24 and 8 px scaled by the draft | SCHEMA.md says px knobs are prep-canvas px that a draft scales; at 480 px the zone is 0.8992 against 0.911 | the literal px |
| a malformed `front`, `overlap` or `zone_erode`, or a missing still, prints `FAILED:` and exits 2 | `loop_seq.py`'s `fail()`, its convention since 2026-11-05, which the studio's runner reads as refused; all four refusals ran | the KeyError or ZeroDivisionError they replace |

Four smaller choices:
- The grey comes from `COLOR_BGR2GRAY`, because the stills are `cv2.imread`'s BGR.
- The rows carry `t` as `frames_chain`'s rows do.
- The drive's server ran from the copy, so the other builders' unfinished code could not change its result.
- The `hints.py` module docstring, which counts the loop's rows, now names the four repaint rows.

### Findings and gaps

- The seven-still job is the check the brief required, not a new round. I built no page, wrote no skeptic request and showed the owner nothing: he closed the loops work on 2026-11-05, and his word on the draw was "Do not redraw anything".
- The check's plan carries `"author": "owner"` in its provenance, because `jobs/plans.save_plan` writes that for every API save; its `words` field names builder L.
- `views/render.frame_tag`, closed to me, gives the leg's frames the strip tag `repaint`, a word the viewer has not shown before. Whether the page styles an unknown tag is for the acceptance drive of the next build wave to look at; I opened no browser.
- I edited nothing outside my files: not `transitions.py`, `reveal.py`, the other research scripts, the frozen plans or `.claude/**`. I made no commit.
- The gates on the shared tree stay red until the pair and director builders finish; I touched none of their files.

### Appendix: evidence and the final `git status`

`benchmarks/runs/2026-11-05/studio/agents/b_loop_build/` (gitignored, 1.3 MB) holds the evidence:
- the proof: `run_proof.sh`, `proof_before.txt` and `proof_after.txt`;
- the self-checks: `selfcheck.py` with its output `selfcheck_1_3.json`, `check4.py`, `check4b.py` and their outputs for the three `overlap` values, `refusals.txt`, the plans `plan7*.json`, `sheet_full_n75.jpg` and `stills7.jpg`;
- the studio drive: `drive7.py` and its output `drive7.json`;
- the gates: `qa_iso.txt` (the copy), `qa1.txt` and `test_real1.txt` (the shared tree), and `my_studio.diff`, the diff the copy received.

The renders, the shell prep and the copy stay in the session's scratchpad (`/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/9041ff2b-bcdd-448e-b55d-c8250e7a4b44/scratchpad/L/`), which does not outlive the session. The studio job is `benchmarks/runs/2026-11-05/studio/loop_boxes7_20261105-181906/` (gitignored). At 18:29, `scripts/session_sweep.sh` listed 5 processes, all from builder P's acceptance run (`test_b_pair_flow.py`, its server on port 50175 and a `reveal.py align`). None is mine; my server on port 8391 is stopped.

`git status --short` at the end, on HEAD 4e2480a. My files are the 8 marked "L"; the others belong to builders P and D.

```
 M scripts/research/loop_seq.py                         L
 M scripts/research/plans/loops/SCHEMA.md               L
 M studio/src/reveal_studio/registry/director.py
 M studio/src/reveal_studio/registry/hints.py           L
 M studio/src/reveal_studio/registry/hints_director.py
 M studio/src/reveal_studio/registry/hints_pair.py
 M studio/src/reveal_studio/registry/pair.py
 M studio/src/reveal_studio/registry/schema.py          L
 M studio/src/reveal_studio/runner/argv_director.py
 M studio/src/reveal_studio/runner/argv_pair.py
 M studio/src/reveal_studio/server/routes_pair.py
 M studio/src/reveal_studio/views/measures.py           L
 M studio/src/reveal_studio/views/page.py
 M studio/src/reveal_studio/views/pair.py
 M studio/src/reveal_studio/web/css/pair.css
 M studio/src/reveal_studio/web/js/pair.js
 M studio/tests/fakes/loop_seq.py                       L
 M studio/tests/test_pair_flow.py
 M studio/tests/test_registry.py                        L
?? studio/src/reveal_studio/media/overlays.py
?? studio/src/reveal_studio/media/pair.py
?? studio/tests/fakes/director_page.py
?? studio/tests/fakes/director_render.py
?? studio/tests/fakes/transitions.py
?? studio/tests/test_repaint.py                         L
```
