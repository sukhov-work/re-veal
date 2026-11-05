<!-- provenance: copied verbatim on 2026-11-06 from benchmarks/runs/2026-11-05/studio/agents/b_docsync.md (gitignored), the doc-sync of phase B by an Opus 5.5 subagent: eight documents synced from the code and the reports, the review's 42 wrong statements fixed, make -C studio prose green; a second pass after the fix round; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance drives on the final tree before the commit -->

8 documents synced · 42 of 42 review statements fixed, and the Layout block · `make -C studio prose` exit 0 · `director_ui.py` stays (retirement row 22 fails). 2026-11-06: row 22 passed, the file is removed; see the second pass.

<!-- reader: the main thread of the 2026-11-05 studio session, cold. shape: report. Written 2026-11-05 between 21:38 and 22:30 by the phase B doc-sync subagent (Opus 5.5), from the brief brief_docsync.md in the session's scratchpad. Documents only: no code edited, no server started, no commit. -->

# Phase B doc-sync: 8 documents synced, the review's 42 statements and the Layout block fixed, `make -C studio prose` green

The four documents of the Fable review's list and four design records now describe the tree of commit 0a5a260. All 42 statements of the review's last section are fixed, and so is the Layout block of `.claude/conventions/studio.md`. `make -C studio prose` exits 0 with 0 blocks. Every count I measured comes from a command run on 2026-11-05 between 21:42 and 22:24; the appendix lists them. The other numbers cite the report or commit message they come from.

Asked of the main thread:
1. Decide `scripts/research/director_ui.py`. Three notes say it stays until row 22 of the retirement checklist passes, as the drive asks. If you remove it, amend them and the drive's bullet in `STUDIO.md §13` (named below "What each document says now").
2. Fix four stale statements in code and config files, which my brief kept closed to me (the table "Outside my files").
3. Copy `b_review.md`, `b_critique.md`, `b_acceptance.md` and this report to `.claude/claude-docs/research/2026-11-05/` with their provenance headers: `STUDIO.md §13` and three notes cite them there.
4. Write the phase B line of `.claude/claude-docs/DECISIONS.md` with the four deviations from the design note that the review kept; `STUDIO.md §13` lists them.

Open: none for the owner.

## Terms

| Term | Meaning |
|---|---|
| the review, the Fable review | the read-only review of phase B by a Fable 5.1 subagent, `benchmarks/runs/2026-11-05/studio/agents/b_review.md`. It checks 13 constraints (12 PASS); its last section lists 42 doc statements the diff made wrong |
| F1 to F10 | the review's findings by number (F5: an in-place page record reads `lost` after a restart; F7: `director_ui.py` still in the tree; F10: the sentence of `STUDIO.md §5` on cv2). "The a2 review's finding F6" is the earlier review of phase A2 |
| phase B, the slice, the builders | phase B: the pair and director flows on the studio's shell, with the loop's repaint leg. The slice: its first wave, which made the package flow-neutral (`b_slice.md`). The builders: the three subagents of its second wave, whose reports are `b_pair_build.md`, `b_director_build.md` and `b_loop_build.md` |
| an anchor | a recorded md5 that a render must reproduce, such as the director's two-knob draft 01b3cf3c… |
| the drive | the acceptance driver's report, `b_acceptance.md` in the same folder (written 22:11; 54 of 61 checks PASS) |
| the critique | the critic's report, `b_critique.md` in the same folder (written 22:06; impeccable's score, 26 of 40) |
| the checker | the no-slop checker, `python3 -I .claude/skills/no-slop/scripts/slop-check.py --profile file <path>` |
| a block | a BLOCK finding of the checker (a sentence over 60 words, two negation openers, a hedge, a filler); a block fails `make prose`. Radon's "blocks" are code blocks (functions, methods, classes), a different thing |
| cell prose | the text of a table cell I wrote, run through the checker as a paragraph, because the checker skips table rows |
| the retirement checklist | `b_director_research.md` §8: each function of the workbench `director_ui.py` and where the studio does it. Its rows are numbered 1 to 23; the drive counted 16 of them, passed 15 and failed row 22 (the grade form pre-filled from the last picks file) |

## What each document says now

| Document | Sections edited | Lines (+/−) | Counts written, with their source |
|---|---|---|---|
| `studio/ARCHITECTURE.md` | The intro's date. A new section, "Phase B (2026-11-05)": a lead paragraph in the shape of the A2 paragraph and a table of what each part adds. The module map, one row per module (49 rows, 21 of them new), each with its imports. The load order. The data flow, with the argv by flow as a table, the in-place rule and the round opening. The import contracts and the configuration. The test layers, with a table of the five fakes. The hard constraints, with two new rows: the Runner on `argv[1]` and the file route's bases. "Changed from the research script" is untouched. | 141/61 | 550 unit, 24 integration and 5 acceptance tests collected, 579 in all (`pytest --collect-only`). 555 hint rows: the loop's 296, the pair's 67, the director's 192. 155 schema entries in 22 groups; 12 methods; 13 stage names (registry introspection). 35 routes: 26 shared, 4 of the pair, 5 of the director. 112 `--set` rows in the renderer's four tables: 26 top-level, 18 sky, 60 transform, 8 read-only. 6 style sheets and 11 scripts (`ls`). 16 forbidden names (`.importlinter`). 82 files and 441 dependencies, 3 contracts kept (`make -C studio audit`). 55 files and 11,785 lines, against 34 and 5,450 at 4f564b5 (`wc -l`). Every import cell comes from an AST pass over `src/`. |
| `studio/README.md` | The opening (three flows) and the history (phase B). The `check` sentence. "Where state lives": a table of the run folder by flow, and `picks/`. The settings table: 6 rows added for the derived paths. The 2 rows of `--layers-dir` and `--mattes-dir` came with the slice (commit 0eb09d8), so the table now holds all 8 paths. The gates table (`make test-fast`, `make acceptance`) and the paragraph after it. | 34/20 | 4 drives in about 8 minutes (the Makefile's help line). 4 jobs per `make acceptance`. |
| `studio/GUIDE.md` | The opening, and the loop's steps 1 and 2. Two new sections, "One pair transition, start to finish" and "One director plan, start to finish": 31 lines together. The Space row, and a row for the director's timeline bar. "Where things are". | 45/6 | The playback rates: `LOOP_FPS` 25 in `views/render.py`, `DEFAULT_FPS` 30 in `views/pair.py` and `views/director.py`. The bar's step of 0.01 (`dBarKey` in `web/js/director.js`). |
| `.claude/conventions/contracts.md` | The studio section. The shared routes row, rewritten in shorter sentences, gains the three new `POST /api/jobs` bodies and the file route's read-only bases. Five rows are new: the pair's routes, the director's routes, the two-photo job folders, the picks body and file, and the candidate shapes. The record, registry, `GET /api/registry`, `round.json`, `job_view`, CLI and probe rows gain "since phase B" notes. | 14/9 | 35 routes, 555 hints, 155 entries, 13 stage names. The 13 director candidate fields and the 7 pair fields (the specs in `registry/director.py` and `registry/pair.py`). |
| `.claude/conventions/studio.md` | The Layout block: the 21 phase B modules marked "(B)", `GUIDE.md`, the five fakes. Beyond it, four dated notes. The tests table's unit row: five fakes, and 550 tests in 120.8 s (the review's run). Its integration row: the three new scripts whose `--help` the tests read. Its acceptance row: four drives in about 8 minutes. The gates line: the prose target covers `GUIDE.md` too. | 22/14 | 21 modules (`comm` over `git ls-tree` of 4f564b5 and HEAD). |
| `.claude/claude-docs/STUDIO.md` | §13 gains the paragraph "What phase B built on the package (2026-11-05)", in the shape of the A2 paragraph. It covers the slice, the three flows, the counts, the four kept deviations, the review, the critique and the drive. §2: five rows gain dated "As built on 2026-11-05" notes. The notes cover the verdict as a shared branch, the relation's knobs, the resolve outside `run/`, the `--set` table as data with its button, the director's run folder, and the pair's page written by the studio. §9: rows B and B (continued) are marked BUILT, each with a status note. §5, beyond the brief: one dated amendment for the review's finding F10, which says the server also reads a clip's step series with cv2. | 19/8 | The counts above. The anchors 01b3cf3c…, 5b3ee379…, 25c0f77c…, 8bd77a4d…, 7262bb06…, c302623f…, 5908af3d… and 3feab96c… (the builders' reports and the drive). Radon's average grade B (5.97) over 378 code blocks, the worst `Runner.finalize` at F (63). |
| `.claude/claude-docs/EXPLORATION_PLAN.md` | Dated notes on five rows. UI1: superseded; `director_ui.py` stays until row 22 passes. UI2: partly in the studio; the import into `fixtures/` stays phase C. UI3: phase D. UI4: phases C and D. UI5: phase B built, with its numbers. | 5/5 | The review 12 of 13, the critique 26 of 40, the drive 54 of 61. |
| `.claude/claude-docs/research/director-tooling.md` | The workbench row (line 110) gains a dated note: superseded by the studio's director flow, the file kept until row 22 passes. | 1/1 | — |

Three notes say `director_ui.py` stays until row 22 passes: `STUDIO.md §9` row B, `EXPLORATION_PLAN.md` UI1 and `director-tooling.md` line 110. The drive's bullet in `STUDIO.md §13` reports row 22 failing. My brief asked for "retired" in two of the notes; the file is in the tree (73,236 bytes, last commit 226cbb5), so I wrote what holds.

## The review's 42 statements

Each statement is fixed in the document's current text; the right column says where.

| Document, the review's line | The statement it made wrong | Where it is fixed |
|---|---|---|
| ARCHITECTURE 3 | "after phase A2 and its fix round" | the intro: "after phase B (the tree of commit 0a5a260)" |
| ARCHITECTURE 25 | `registry.loop` owns `FLOWS`, `stage_def`, `K` | `registry.loop`, `registry.flows` and `registry.entries` rows |
| ARCHITECTURE 26 | `registry.hints` "290 keys", "imports nothing" | its row: 296 loop rows, 555 in `HINTS`, three imports |
| ARCHITECTURE 27 | 151 entries in 21 groups | `registry.schema` row: 155 in 22, `METHODS` 12, `NAME_RE` 60 characters |
| ARCHITECTURE 28 | `registry.rulings` imports `registry.loop` | its row: `registry.flows`, `registry.schema` |
| ARCHITECTURE 29 | `jobs.store` owns `create_job` only | its row: the three creators, the adoption, `fixture_photos`; imports `registry.pair` |
| ARCHITECTURE 31 | `jobs.candidates` owns `candidates` | its row: `spec_candidates`, `loop_candidates`, `cached_md5` |
| ARCHITECTURE 33 | `jobs.grades` owns four functions | its row: `check_picks`, `save_picks` added |
| ARCHITECTURE 34 | `runner.argv` is the loop's builder | its row: the dispatcher, `builder_of`, `SCRIPTS`, `as_object`, `script_rel`; four `runner.argv_*` rows |
| ARCHITECTURE 35 | `runner.process` imports `runner.argv` and `jobs` | its row: `jobs.rounds`, `registry.flows`; the in-place rule |
| ARCHITECTURE 37 | `media.pictures` holds "the one cv2 import" | its row; the `media.pair` and `media.overlays` rows; the cv2 contract row |
| ARCHITECTURE 38 | `views.job` owns the stale rule and the summaries | `views.job`, `views.base` (`mark_stale`) and `views.tiles_loop` rows |
| ARCHITECTURE 39 | `views.render` owns the loop's view | its row: `RENDER_VIEWS` by flow and its imports |
| ARCHITECTURE 42 | `views.models` imports `registry` (the loop) | its row: `registry.flows`, `director_inputs` |
| ARCHITECTURE 43 | `views.page` imports six modules | its row: seven, with `views.pair` and `registry.flows`; `BUILTIN_PAGES` |
| ARCHITECTURE 46 | `server.routes` "26 rows" | its row: `CORE` 26, `ROUTES` 35; the `server.route`, `routes_pair`, `routes_director` rows |
| ARCHITECTURE 47 | 4 style sheets, 9 scripts | the `web/` row: 6 and 11, `FLOW_UI`, `chipKey` |
| ARCHITECTURE 49-52 | the load order | the load-order paragraph: `pair`, `director` before `boot`; the `flowEntry` registrations |
| ARCHITECTURE 61 | the child is `loop_seq.py` | data-flow step 3 and the table "The argv by flow" |
| ARCHITECTURE 78 | the forbidden names | the contracts table: 16 names, the 8 of the slice marked |
| ARCHITECTURE 99-103 | tests 381 / 14 / 3 and the files | the test layers table: 550 / 24 / 5 collected, the six integration files and tests, the four drives |
| ARCHITECTURE 105-108 | "The fake script" | the fakes table: five fakes, `FAKE_TABLE` |
| ARCHITECTURE, missing modules | 21 modules without a row | 21 rows added; 49 of 49 modules have a row (checked by script) |
| README 3-4 | "over the loop flow" | the opening: three flows with their scripts |
| README 6-9 | the history stops at A2's fix round | the history: a phase B sentence |
| README 51-53 | "the symlinked stills under `raw/<seq>/`" | "the symlinked inputs"; the flows table's inputs column; the director's `job.json` |
| README 54-56 | the run folder is the loop's | the table of the run folder by flow |
| README 90 | `make acceptance`: two drives, about 3 minutes | the gates table: four drives, about 8 minutes, one at a time |
| README 95-97 | `make acceptance` makes one new job | the paragraph: four jobs, by flow |
| README 45 | `check` lacks the MISSING rule | the sentence names it and points at the settings section |
| GUIDE 3 | "one local page over the loop flow" | the opening: three flows, one job of each |
| GUIDE 19 | "press new loop job…" only | the loop's step 1 says the rail has one button per flow; the two new sections press "new pair job…" and "new director job…" |
| GUIDE 22-23 | the strip's stages are the loop's | "A loop job's strip"; each new section lists its flow's stages |
| GUIDE 47 | Space plays at 25 fps | the Space row: the clip's own rate |
| contracts 50 | 26 routes, the loop's `POST /api/jobs` bodies, the file route | the shared routes row; the pair's and the director's route rows |
| contracts 52 | the layout | the row "The two-photo job folders"; the picks row; `seq` in every `job.json` |
| contracts 53 | the record rules | the record row: `in_place`, `previous`, the builtin page record, `script_md5` of `argv[1]`, `identity` |
| contracts 54 | "The stage registry of the loop flow" | the stage registry row: three flows, `script`, `identity`, `object`, 555 hints, 155 entries, 12 methods, 60 characters |
| contracts 55 | `stage_order` the loop's ten | the `GET /api/registry` row: the union, 13; `flows` the enabled flows with `enabled` |
| contracts 56 | `round.json` | the round row: `record` (an adopted round has none); the picks row: the grade `{at, page_md5, picks, text}` |
| contracts 57 | `job_view` | the `job_view` row: each flow's keys and each render view's keys |
| contracts 60 | the CLI and the environment | the CLI row: the two flags, the two names, the eight Settings keys, `check`'s rows |
| conventions 11-25 | the Layout block (the a2 review's finding F6) | the Layout block |

Two counts in the review differ from what I measured. Its finding F1 says 19 modules were added; its own list, and `comm` over the two trees, give 21. Its contracts line 56 says an adopted round's `record` is None; `jobs/store.adopt_loop_job` writes no `record` key at all, so I wrote "has no `record` key".

## The prose checks

| Document | Blocks at HEAD, then now | Note |
|---|---|---|
| `studio/README.md`, `ARCHITECTURE.md`, `GUIDE.md` | 0, then 0 (`make -C studio prose`, exit 0) | advisories now 1 in `README.md`, 2 in `ARCHITECTURE.md`, 1 in `GUIDE.md`: sentences over 25 words in each, and in `ARCHITECTURE.md` three codes (A1, A2, F5) |
| the new table cells of those three, as cell prose | ARCHITECTURE's old cells 3 blocks; the new cells 0 | the two cells over 60 words (the `web/` row, the acceptance row) were split |
| `.claude/conventions/contracts.md` | 0, then 0; as cell prose the old studio rows 2 blocks, the new rows 0 | 124 sentences, none over 40 words |
| `.claude/conventions/studio.md` | 0, then 0 | — |
| `.claude/claude-docs/STUDIO.md` | 14, then 14, the same 14 sentences | inherited text; the paragraph I added holds 0 blocks and no sentence over 40 words |
| `.claude/claude-docs/EXPLORATION_PLAN.md` | 28, then 28 | inherited; my five notes as cell prose: 0 blocks, 0 sentences over 40 words |
| `.claude/claude-docs/research/director-tooling.md` | 0, then 0 | my note: 0 blocks |

I loaded the `no-slop` skill and ran its pass on every edit: the checker, then a read for codes in place of names, unintroduced referents and sentences over 40 words. A cold reader (an Explore subagent given this report alone, 22:15 to 22:25) found 12 terms it could not resolve and 7 sentences it read twice; I defined the terms above and rewrote those sentences.

## Outside my files

These statements are wrong on the tree of 0a5a260. My brief closed code and config to me, so I left them.

| File | Statement | What the code does |
|---|---|---|
| `studio/pyproject.toml`, `description` | "one local page over the loop flow" | the package serves three flows |
| `studio/src/reveal_studio/__init__.py`, docstring | "one local page over the loop flow" | the same |
| `studio/pyproject.toml`, the comment on deptry's `DEP002` | "the package never imports it" (numpy) | `media/pair.py` and `media/overlays.py` import numpy inside their functions |
| `studio/src/reveal_studio/jobs/rounds.py`, `open_round` docstring | `record` is "None for a page the studio wrote" | `views/pair.build_pair_page` passes its builtin record's id |

The drive also edited two acceptance test files during my run (`studio/tests/acceptance/test_b_director_flow.py`, `test_b_pair_flow.py`; the drive's third ask is to commit them). They are its changes, not mine; the collected count stayed at 5 acceptance tests (22:13).

## `git status` at the end

```
 M .claude/claude-docs/EXPLORATION_PLAN.md
 M .claude/claude-docs/STUDIO.md
 M .claude/claude-docs/research/director-tooling.md
 M .claude/conventions/contracts.md
 M .claude/conventions/studio.md
 M .claude/skills/reveal/references/tracked-backlog.md
 M studio/ARCHITECTURE.md
 M studio/GUIDE.md
 M studio/README.md
 M studio/tests/acceptance/test_b_director_flow.py
 M studio/tests/acceptance/test_b_pair_flow.py
```

Eight are mine. The two test files are the drive's, and `tracked-backlog.md` changed during my run by another hand (my brief closed the backlog to me). This report sits under `benchmarks/runs/` (gitignored). A revert of my part is `git checkout` of the eight documents.

## Appendix: the commands behind the counts

All from the repo root or `studio/`, on 2026-11-05.

| Time | Command | Output used |
|---|---|---|
| 21:42 | `studio/.venv/bin/python` over `registry.hints`, `schema`, `flows`, `rulings`, `director`, `pair` and `server.routes*` | 555, 296, 67 and 192 hints. 155 entries in 22 groups, 12 methods, `NAME_RE` 60, 7 rulings. 3 flows enabled, 13 stage names, 35 routes (26, 4, 5). 112 `--set` rows (A 26, B 18, C 60, D 8), 8 read-only; 12 reserved names. |
| 21:43 | `pytest tests --collect-only -q -m "not integration and not acceptance"`, `-m integration`, `-m acceptance` | 550, 24, 5 (579 in all); rerun at 22:13 after the drive's edits: the same |
| 21:43 | `make -C studio audit` | exit 0; deptry 55 files clean; pip-audit no known vulnerabilities; lint-imports 82 files, 441 dependencies, 3 kept |
| 21:44 | `radon cc src -a -s`; `-n D`; `-n E` | 378 code blocks, average B (5.97); 11 code blocks at D or worse; `Runner.finalize` F (63), `graph_view` E (35) |
| 21:44 | `reveal-studio check` | 8 flow rows; 19 director plans, 19 fixture pairs, 24 layer folders, 14 matte folders; the script md5s 7ef5dcae…, d859dfb4…, 05cd6e1d…, dcf393a8… |
| 21:45 | `git ls-tree` of 4f564b5 and HEAD, `comm`; `wc -l` over `src/` | 21 Python modules and 4 web files added; 55 files, 11,785 lines; 34 files, 5,450 lines at 4f564b5 |
| 21:46 | an AST pass over `src/` (the package's own imports, lazy and typing-only marked) | every cell of the module map's Imports column; 3 differences on recheck, all deliberate wording |
| 21:50 | a `Counter` over the hint keys' prefixes | the pair's 22 / 32 / 6 / 7 and the director's 26 / 10 / 9 / 9 / 26 / 112 |
| 22:00 | `awk` over `GUIDE.md` | the two new sections: 31 lines |
| 22:24 | `make -C studio prose`, the last run | exit 0; 0 blocks in the three files |

## Second pass (2026-11-06, 00:25 to 00:40): the fix round synced, the workbench removed

The first pass's four asks are closed: the main thread removed `director_ui.py`, copied the reports to the research folder and wrote the phase B DECISIONS line (2026-11-05, eleventh), and another hand fixed the four stale statements at 22:27. The five documents of the "Documents to sync" list in the fix round's report (`b_fixes.md`) now describe the fix round's tree. No sentence of mine says `director_ui.py` stays: the main thread removed it from the tree, and `git status` shows the staged deletion. `make -C studio prose` exits 0 with 0 blocks (00:36): `README.md` 41 sentences, `ARCHITECTURE.md` 70, `GUIDE.md` 74.

| Document | What this pass changed | Counts and their source |
|---|---|---|
| `.claude/conventions/contracts.md` | The `job_view` row: a stage view's `chip_key` (the director's plan tile with `director.plans`), the two-photo skeptic tile's "answered (0 verdicts)", and a refused verdict's tile with `reason: null`. Beyond the list: the record row's note on a refused record's `.part` folder and the in-place restart rule, the hint count, and the workbench's citation marked as removed. | 559 hint rows: the loop's 296, the pair's 67, the director's 196 (registry introspection, 00:28) |
| `.claude/claude-docs/STUDIO.md` | §4 gains a dated amendment with the three runner rules: the in-place record judged by its file's mtime, the record another server finalizes, the refused stage's `.part` folder. In §9 row B my sentence "stays in the tree until that row passes" now reads "stayed … and was removed on 2026-11-06". In §13 the review bullet says the file was removed and that F5 is fixed; the drive bullet's 43-word sentence is split. Beyond the list, §13 gains a fix-round bullet in the shape of the A2 paragraph's, with the numbers of `b_fixes.md`, and its report list names `b_fixes.md`. | the same 14 blocks and 35 sentences over 40 words as at HEAD |
| `.claude/conventions/studio.md` | The State rule gains the three runner rules, the page rule gains `busy`, and the Sentences rule names the 60-word and 40-word checks. The tests table gives the new unit count. | 555 unit tests (`pytest --collect-only`, 00:28) |
| `studio/ARCHITECTURE.md` | The intro's date and a fix-round row in the phase B table. The `runner.process` row (`_written_since`, `Runner._finished_elsewhere`, the refused `.part` folder) and the `views.base` row (`skeptic_state`, the new import `registry.schema`). The hint counts; the `web/` row (`busy`, `closeForms`, five `FLOW_UI` hooks); data-flow steps 4, 5 and 8. The test counts, the prose test's two checks, and a hard-constraint row for a second server. | 555, 24 and 5 tests collected, 584 in all, 579 in `make test` (00:28); 55 files and 11,875 lines (`wc -l`); the Imports column matches an AST pass with 0 differences |
| `studio/GUIDE.md` | The director's steps 3 to 6: the inspector's read-only knobs for the resolve and the render, "clear all knobs" asking first, the next render's controls in the side column, one grade form per round started from the newest picks file. The keys table gains Alt and Page Up, Page Down on a bar, and Cmd-Z for the director's knobs. | the two flow sections now hold 35 lines (`awk`) |
| `.claude/claude-docs/EXPLORATION_PLAN.md` | UI5's note: the fix round fixed 49 of the 50 items. | — |

I read the four notes the main thread amended: `STUDIO.md §9` row B and §13, `EXPLORATION_PLAN.md` UI1, and `director-tooling.md` line 110. Only §9 row B and the §13 review bullet still held a sentence of mine on the workbench staying, and both now say it was removed. Every new sentence went through the checker, the table cells as cell prose: 0 blocks, 0 sentences over 40 words.

The four stale statements of "Outside my files" were fixed at 22:27 on 2026-11-05 by another hand; the fix report credits that edit to the doc-sync writer, and I made none of it. The research copy `.claude/claude-docs/research/2026-11-05/b_docsync.md` predates this section, so it needs a re-copy.

`git status --short` at 00:35, the documents and the deletion only (the fix round's `studio/src/` and `studio/tests/` files stand as its report lists them):

```
 M .claude/claude-docs/DECISIONS.md
 M .claude/claude-docs/EXPLORATION_PLAN.md
 M .claude/claude-docs/STUDIO.md
 M .claude/claude-docs/research/2026-11-05/README.md
 M .claude/claude-docs/research/director-tooling.md
 M .claude/conventions/contracts.md
 M .claude/conventions/studio.md
 M .claude/skills/reveal/references/studio.md
 M .claude/skills/reveal/references/tracked-backlog.md
D  scripts/research/director_ui.py
 M studio/ARCHITECTURE.md
 M studio/GUIDE.md
 M studio/README.md
?? .claude/claude-docs/research/2026-11-05/b_acceptance.md
?? .claude/claude-docs/research/2026-11-05/b_critique.md
?? .claude/claude-docs/research/2026-11-05/b_docsync.md
?? .claude/claude-docs/research/2026-11-05/b_fixes.md
?? .claude/claude-docs/research/2026-11-05/b_review.md
```

This pass edited six documents: `contracts.md`, `STUDIO.md`, `conventions/studio.md`, `ARCHITECTURE.md`, `GUIDE.md` and `EXPLORATION_PLAN.md`. `DECISIONS.md`, both reveal-skill references, the research folder's README and copies, and the deletion are the main thread's.
