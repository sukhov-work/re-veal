<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/a2_fixes.md (gitignored), the fix round after the phase A2 review and critique by an Opus 5.5 subagent (max effort) on its own server (port 8396) and headless Chrome (DevTools port 9396); a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa and make test on the final tree (DECISIONS 2026-11-05, fourth line) and did not re-run the keyboard or detector drives; its 53 screenshots stay under benchmarks/runs/2026-11-05/studio/shots/fix_*.png (gitignored) -->

<!-- reader: the main thread of the 2026-11-05 studio session and the owner, both cold. shape: report (the brief's order: the result, the item table, the passes, the screenshots, what was left). Written 2026-11-05 by the fix-round builder (Opus 5.5) against reveal-studio 0.2.0 under studio/. My server: 127.0.0.1:8396 (pid 38485); my headless Chrome: DevTools port 9396 (pid 31328, then pid 2227). -->

# The studio's second-phase fix round: 37 of 39 listed items fixed, every gate green, 0 detector findings

**Result.** I fixed 37 of the 39 items the brief lists and left 2 minor rows. One fixed item, the critique's row on the photo colours, leaves its palette half to a decision. The gates, as of 2026-11-05:

- `make qa` is green in 79.5 s, and `make test` passes 393 tests in 72.9 s. `make acceptance` passes 2 tests in 175.2 s, and `node --check` finds all 9 scripts clean.
- The detector's URL scans print nothing and exit 0 at 2560×1440, 1440×900 and 1280×800. Its scans of 6 chosen screens, the 3 that had findings among them, also find 0 at each of the 3 sizes.
- The keyboard drive passes 34 of 34 checks at each size. The browser counts 0 errors and 0 hint misses over 73 screens.

At 2560×1440 the frame under judgement (the a2 render of the adopted job, at fit) now shows at 46.2 % of its source height, up from 27.1 %. At 1440×900 it stays at 21.2 %, but now sits on screen with its scrubber; before, it started below the window. At 1280×800 it shrinks from 21.2 % to 17.8 % so that it and its scrubber fit the window; before, it sat below the window.

**Asked of the main thread.** Sync the documents in "Documents to sync"; I edited none. File the 7 candidate rows of "What I left". Decide whether the smaller frame at 1280×800 stands.

**Open question for the owner.** `DESIGN.md` gives one blue to both the Info colour and Photo A; should one of them change?

## Names used below

| Name | Meaning |
|---|---|
| the brief | the main thread's task message for this fix round |
| A1, A2 | the studio's first and second build phases (`STUDIO.md` §9); "the A2 page" is the page as phase A2 left it |
| the critique | `benchmarks/runs/2026-11-05/studio/agents/a2_critique.md`, a critique of the A2 page by impeccable's method (28/40) |
| P1, P2 row n, minor row n | the critique's major issue, its 13 issues the owner would notice, and its 15 minor rows, by their table numbers |
| the review, F2, F3, F9, F10 | `a2_review.md`, the read-only review of the package by a Fable model, and its findings by id |
| the acceptance report, T97, T98, T99 | `a2_acceptance.md` and its three defects, filed as backlog rows T97 to T99 |
| impeccable, the detector | the UI design skill under `.claude/skills/impeccable/`, and its anti-pattern scanner (`impeccable detect`) |
| URL scan, CDP scan | the detector loading the page itself (it opens the newest job), or reading a screen I set up in my Chrome through the DevTools protocol (`--cdp 9396`) |
| angel, a2 | the owner's two-still portrait sequence; a2 is one of its loop renders (lower case), never the phase A2 |
| the adopted job | `loop_angel_20261104-220708`, the angel run folder of 2026-11-04 taken in as a job (five full renders) |
| job 220719 | `loop_angel_20261104-220719` (the ten-window registration, the probe, a 480 px draft with a measure) |
| the frame, the box, % of its source | the picture under judgement (`#frameImg`) inside its bordered box (`#frameBox`); the picture's drawn height divided by the image's own height |
| the step plot | the plot under the scrubber of the step series: each frame's mean change from the one before it, in grey levels |
| the side column | the column I added beside the render's frame: its name and chip, the zoom and compare buttons, sources A and B, the list of renders, the first and last stills |
| the host panels | the registration, readers and probe panels, which show the viewer without the frame axis |
| a hint miss | a chip or a `[data-hint]` element whose key has no row in `registry/hints.py` |
| the review gate | the page panel's refusal to build a review page while a listed render is unjudged; distinct from the test gates (`make qa` and the others) |
| other loop words | k0: the first registered still. The prep: the registration's output folder `in/<seq>/`. RIFE: the frame-interpolation model; a rife step's frames are drawn by it. dexp: the double-exposure share. A frozen plan: a plan file the studio only reads. slices: a transition method the owner ruled out. The skeptic: a review pass whose verdict a render needs before the review page |

## The frame before and after

Measured by `measure.mjs` in my Chrome at each window size. "On screen" means the picture's bottom lies inside the window.

| Screen | Size | Before | After |
|---|---|---|---|
| render, the adopted job's a2 (1366×1770) | 2560×1440 | 370×479 px, 27.1 %, box at y 667; on screen with the scrubber and the step plot | 631×817 px, 46.2 %, box at y 370; on screen with the scrubber and the step plot |
| | 1440×900 | 290×376 px, 21.2 %, box at y 1138, below the window | 290×376 px, 21.2 %, box at y 439; on screen with the scrubber; the step plot below the fold |
| | 1280×800 | 290×376 px, 21.2 %, box at y 914, below the window | 243×315 px, 17.8 %, box at y 400; on screen with the scrubber |
| registration, job 220719, windows.jpg (733×960) | 2560×1440 | 287×376 px, 39.2 %, at y 1421, below the window | 733×960 px, 100 %, at y 456, beside the fits table |
| | 1440×900 | 39.2 %, at y 1451, below the window | 301×394 px, 41.0 %, at y 486, on screen; the tables under it |
| | 1280×800 | 39.2 %, at y 1451, below the window | 224×294 px, 30.6 %, at y 486, on screen |
| probe, job 220719, k0 in the viewer (1366×1770) | 2560×1440 | 21.2 %, at y 3860 | 54.5 %, at y 456, beside the tables |
| | 1440×900 | 21.2 %, at y 3942 | 22.3 %, at y 486 |
| | 1280×800 | 21.2 %, at y 3890 | 16.6 %, at y 486 |

At 2560×1440 the frame is now the largest element on screen: 515,131 px² against the step plot's 327,936. Before, the plot was the larger, against the frame's 177,065.

How `viewer.js` `sizeFrame` sets the height: the window's height, less the box's top (with the work area scrolled to its start), less the axis under the box. The axis is the scrubber plus the step plot when the frame keeps at least 480 px after both (`FRAME_FULL`). Otherwise the axis is the scrubber alone, and the plots go below the fold. The floor is 240 px (`FRAME_MIN`, was 380). In the new layout with the old 380 px floor, the registration's frame ended at y 866 at 1280×800, and the render's scrubber at y 853: both past the 800 px window.

## The gates

| Gate | Command (from `studio/` unless named) | Result | Wall time |
|---|---|---|---|
| qa | `make qa` (ruff check and format, mypy strict over 34 files, 379 unit tests, vulture, deptry, pip-audit, 3 import contracts, the prose checker) | exit 0 | 79.5 s |
| test | `make test` | 393 passed, 3 deselected | 72.9 s |
| acceptance | `make acceptance` (it made jobs `loop_angel_20261105-045220` and `-045354`) | 2 passed. The a2 render's md5 is `c302623f…`, and the measure stage reads 1.18 px at f 13 and 3.96 px at f 26: both the values of the acceptance report. Neither job holds a running record | 175.2 s |
| syntax | `node --check` on the 9 scripts of `web/js/` | 9 clean | not timed |
| URL scans | the three commands below, from the repo root | 0 findings each | not timed |
| CDP scans | `detect --json --no-advisory --cdp 9396 --target 127.0.0.1:8396`, 6 screens at 3 sizes | 0 findings each | not timed |

`make acceptance` ran once, before my last page-only edits (the quiet focus, the side column's 300 px floor, the two form labels); it drives the server's routes, not the page. Every other gate ran on the final tree.

The URL scans on the final code, verbatim; no `.impeccable/` folder exists after them:

```
detect --no-advisory --viewport 2560x1440 http://127.0.0.1:8396/ -> exit 0, output: ''
detect --no-advisory --viewport 1440x900 http://127.0.0.1:8396/ -> exit 0, output: ''
detect --no-advisory --viewport 1280x800 http://127.0.0.1:8396/ -> exit 0, output: ''
```

The CDP scans, verbatim:

```
plan_ruled 2560x1440: exit 0 []      page_adopted 2560x1440: exit 0 []      graph_220719 2560x1440: exit 0 []
plan_ruled 1440x900: exit 0 []       page_adopted 1440x900: exit 0 []       graph_220719 1440x900: exit 0 []
plan_ruled 1280x800: exit 0 []       page_adopted 1280x800: exit 0 []       graph_220719 1280x800: exit 0 []
render_a2_wipe_f20 2560x1440: exit 0 []   registration_windows 2560x1440: exit 0 []   probe_220719 2560x1440: exit 0 []
render_a2_wipe_f20 1440x900: exit 0 []    registration_windows 1440x900: exit 0 []    probe_220719 1440x900: exit 0 []
render_a2_wipe_f20 1280x800: exit 0 []    registration_windows 1280x800: exit 0 []    probe_220719 1280x800: exit 0 []
```

`plan_ruled` is the plan editor on the frozen plan `angel_a2` with step 1's method set to `slices`. `page_adopted` is the adopted job's page panel, and `graph_220719` is job 220719's graph. The last change touching layout, the side column's 300 px floor, acts at 1280 only, so the six 1280 scans were rerun after it.

One finding appeared midway and is fixed: the plan editor's new two columns (P2 row 10) raised `first-viewport-column-overflow` on `div.pe-main` at 1440 and 1280. The 32-key slices form ran 252 % of the window's height beside bars that fit in 36 %. The bars column is now sticky beside the form, which the rule exempts.

## Every item

| From | State | File and change | Test or check |
|---|---|---|---|
| P1 | fixed | `viewer.js` `renderViewer`, `sizeFrame`; `panels.js` `panelRender`, `hostGrid`; `studio.css`, `viewer.css`. The render list, the render's name, the modes and the sources moved into the side column (300 to 400 px wide). The frame's height comes from the window. From a 1800 px window the host panels put their tables beside a sticky viewer; below that, under the viewer | the frame table above |
| P2 row 1, Space on a focused button | fixed | `boot.js`: the frame keys act only while a render's scrubber is on the page and no Cmd, Ctrl or Alt is held. Space plays only from the picture, the scrubber or no control | keyboard checks 2, 5, 6, 22 |
| P2 row 2, the focus after a mode switch | fixed | `core.js` `focusKey`, `restoreFocus`; `viewer.js` puts the focus back on the control with the same data attributes after each rebuild, and opens no hint for it | keyboard checks 1, 3, 4 |
| P2 row 3, Cmd-Z on a bar | fixed | `plan.js`: a bar keeps the arrows, Home and End only, so Cmd-Z reaches the editor's undo. `hints.py` `control.plan_undo` says when it undoes the typing first | keyboard checks 20, 21 |
| P2 row 4, state words that disagree | fixed | `views/job.py` `attempt_note`: a render or measure tile done by its contents prints "last attempt: cancelled by you" in the head. `job_row` reads done when any candidate exists, drafts included. `readers_moved` finds the folder a later registration moved, and `panels.js` prints it in place of "Not run." | three tests: `test_a_failed_attempt_beside_finished_renders_keeps_the_tile_done` (extended; mutation: dropping `attempt_note`); `test_the_rail_row_says_done_when_only_a_draft_stands_beside_a_failed_render` (mutation: `if full and`); `test_the_readers_tile_names_the_folder_a_later_registration_moved` (mutation: dropping the lookup). Keyboard check 34 |
| P2 row 5, the graph's one-click rerun | fixed | `graph.js`: the first click turns "rerun from here" into "Rerun registration with the inspector's knobs? The prep moves aside and the stages after it go stale." with "yes, rerun" and "no", the focus on "no". "no" or Escape closes it | keyboard checks 28 to 30; no record was started |
| P2 row 6, the tag and the violet mark at 1:1 and 2× | fixed | `viewer.js`, `viewer.css`: the tag sits over the box's corner in a wrapper that does not scroll. The violet outline marks the picture at fit and the box at 1:1 and 2× | keyboard checks 8, 10 |
| P2 row 7, the probe's violet mark | fixed | `panels.js` `panelProbe`: the rife strip and the rife crops at t carry class `gen` and a "generated" chip; `viewer.css` outlines them | keyboard check 32 |
| P2 row 8, the rail's Running list | fixed | `views/job.py` `running_entry` returns `{id, stage, name, elapsed_s, progress}`; `rail.js` prints "render · a2 · 12/50 · 38 s", the job and record id in its title. The `running` field of `GET /api/jobs` now holds these objects, not record ids | `test_the_rail_row_names_a_running_record` (mutation: listing the ids alone); the injected row of the miss count |
| P2 row 9, a line behind the plan node | fixed | `graph.js` `drawEdges`: a line within one row that skips a column runs through the gap under the row | keyboard check 31: the registration → render line runs at y 249, under the plan node's bottom at y 159 |
| P2 row 10, the plan editor at 1440×900 | fixed | `plan.css`: the form in a 360 px column beside the bars from 1181 to 1700 px (440 px above), one column below 1181 | the first field at y 715 at 1440×900 (before: y 949) and at y 675 at 1280×800 |
| P2 row 11, 74 of 131 Tab stops were "?" and chips | fixed | `core.js` `hintBtn`: `tabindex="-1"`; chips lose `tabindex`. Every control carries `data-hint`: tiles, nodes, rail rows, the editor, the inspector's fields, the panels' forms. A "?" or a chip opens its hint on hover at once. A control opens it after 600 ms of hover, or at once on the owner's own keyboard focus; any key but Tab hides it | the render view: 62 Tab stops, none a "?" or a chip. From "start from" to the form's first field: 17 stops (was 31). 0 controls without a key. The cost is in "What I left" |
| P2 row 12, one blue for three things | fixed, the palette part left | `viewer.css`: sources A and B and the picture's A and B labels in the text and muted colours. `viewer.js`: dx solid in the text colour, dy dashed in the muted colour; `hints.py` `measure.stability` reworded. The stills k0 and the last keep the photo colours | keyboard check 14 |
| P2 row 13, unnamed fields and 47 "hint" buttons | fixed | `inspector.js`: `aria-label` with the key on each knob field and its "?". `core.js`: each "?" is named "about <key>". `index.html`: the form labels point at their fields, with each "?" outside its label | keyboard check 15 |
| minor row 1, the request chip cut in the rail | fixed | `studio.css` `.rail .kv{flex-wrap:wrap}` | 5 of 5 request chips inside the rail at 3 sizes |
| minor row 2, the review gate's message | fixed | `panels.js` `gateMessage`: the candidates grouped by reason; `studio.css` `.msg{max-width:75ch}` | CDP scan `page_adopted` 0; the message 661 px wide at 2560 |
| minor row 3, the ruled chip's padding | fixed | `plan.css` `.chip.ruled{padding:6px 8px}`; 4 px 8 px in the inspector | CDP scan `plan_ruled` 0 |
| minor row 4, "% faster" with an empty field | fixed | `plan.js` `peFaster`: "type a percentage first: …"; the placeholder "20" dropped | keyboard check 23 |
| minor row 5, "1 a local box" | fixed | `plan.js` `peNoun`, `pePlural`: "1 local box", "local box 0"; the add button keeps "add a local box" | keyboard check 25 |
| minor row 6, the message after an undo | fixed | `plan.js`: "4 frame counts × 0.80 (one undo step)"; undo and redo clear the message | keyboard check 24 |
| minor row 7, "Failed to fetch" | fixed | `core.js` `api`: "the studio server at 127.0.0.1:<port> does not answer: start it again with reveal-studio serve". The port is the one the page came from: 8396 on my server, 8380 on the owner's | a fetch made to fail in the page |
| minor row 8, two hints that contradict their control | fixed | `hints.py`: `control.page_variants` says "up and down reorder them"; `control.cmp_ab` names the flip button; a new `control.cmp_ab_flip` sits on that button | `tests/test_prose.py` |
| minor row 9, a tile's "?" passed the arrows on | fixed | `strip.js`: a key on a tile or on its "?" stops there | the "?" also left the Tab order |
| minor row 10, "range none stated" on 22 knobs | left | see "What I left" | none |
| minor row 11, long "last run" values | fixed | `studio.css` `.knob .def{overflow-wrap:anywhere}` | 0 values past the inspector's edge at 3 sizes |
| minor row 12, the stills' legend cut, a 150×483 focus ring | fixed with P1 | the stills and the legend sit in the side column, which holds controls, so the browser never makes it a Tab stop | the Tab walk of keyboard check 17 |
| minor row 13, 2× off-centre | fixed with P1 | `viewer.js` `sizeBase` centres a zoom on the next frame once the picture has its size; `.frame` aligns with `safe center` | keyboard check 9: scroll (599, 1361) equals the centre |
| minor row 14, angel numbers in five hints | left, one of five changed | see "What I left" | none |
| minor row 15, the probe's share hint | fixed | `hints.py` `measure.probe_dexp`: a high share warns of a ghost; the probe has no bar, which is why its table shows no verdict | `tests/test_prose.py` |
| detector: `cramped-padding` on the ruled chip | fixed | minor row 3 | CDP scan 0 |
| detector: `line-length` on the review gate's message | fixed | minor row 2 | CDP scan 0 |
| detector: `edge-flush-cards` on the graph at 1280 | fixed | `graph.js` `graphWidth`: the node width (176 to 240 px) makes whole columns fill the scroller at rest, and the next column starts past its edge; at 1280, four 196 px columns | CDP scan 0 |
| F2, chips whose key had no row | fixed | `core.js` `chipKey`: a parenthesis and a progress fraction dropped; a leading state word (stale, draft, round, waiting, running, generated) kept alone. A value chip names its key: `chip.frame`, `chip.tag`, `chip.method`, `chip.dexp`, `control.cmp_a`. `hints.py` gains 15 chip rows and 8 control rows: 290 rows (was 267) | `test_every_chip_text_of_the_page_resolves_to_a_hint_row` (mutation: deleting `chip.adopted`); 0 misses in the browser |
| F3, a rebuild dropped the focus | fixed | `core.js` `focusKey`, `restoreFocus`, `focusQuiet`, used by `renderPanel`, `renderInspector`, `renderViewer` and `renderGraph`. An element the viewer draws after its fetch gets the focus within 5 s. A focus the page restores opens no hint; the strip, the rail and the plan editor restore theirs the same way | keyboard checks 4, 11 to 13 |
| F9, the rail listed dead records as running | fixed | `views/job.py` `job_row(settings, d, runner=None)` reconciles through the Runner; `server/routes.py` `get_jobs` passes `app.runner`. The rail now reconciles on every poll (5 s, 1 s while busy), so a live record of a second server is also re-attached from the rail: backlog row T88's surface widens | `test_the_rail_row_reconciles_a_record_whose_process_is_gone` (mutation: dropping the reconcile) |
| F10, dead code | fixed | `core.js` `stateClass` without `queued`. `runner/lock.py` `release` deleted: only tests called it, and `serve` closes the handle, as the tests now do. `CODE_ONLY_KNOBS` moved into `tests/test_registry.py` | the lock and rulings tests |
| T97, the inspector missed the Stability section | fixed | `viewer.js` `loadRender` ends with `syncInspector`: the inspector is redrawn when the fetched render's measures differ from those it drew, unless a field there has the focus | keyboard check 33: the section absent, then present after the fetch, with no click |
| T98, a draft made the page stale | fixed | `views/job.py`: the page's upstream render is the latest full render's record (`is_draft`) | `test_a_draft_leaves_the_page_fresh_and_a_full_render_makes_it_stale` (mutation: the latest render record as the upstream) |
| T99, the A1 test's cleanup left a record running | fixed | `tests/acceptance/test_a1_loop_flow.py`: the cleanup cancels each running record through `POST …/cancel` first; the kill is the fallback, as in the A2 test | `make acceptance` passed; both jobs hold no running record |

I ran every mutation named above. All seven tests turned red, and green again on the restored files.

## The keyboard pass

`keys.mjs` sends real key and mouse events through DevTools. It ran at 2560×1440, 1440×900 and 1280×800, and all 34 checks passed at each size.

| # | Check |
|---|---|
| 1 to 4 | Enter on "1:1" keeps the focus there (1). Space on "fit" presses it and does not play (2). Enter on "wipe" keeps the focus there (3), and the hint stays closed (4) |
| 5 to 7 | Space on a render in the list opens it. With no control focused, Space plays and pauses. On the scrubber, right steps 1 frame and Shift+right steps 10 |
| 8 to 10 | at 2× on the generated frame 20, the tag "f 20 generated t 0.5554 dexp 0.0294" stays on screen and the box carries the violet mark (8); the view opens at the centre (9); at fit the mark is back on the picture (10) |
| 11 to 13 | a panel rebuild returns the focus to the "onion" button; an inspector rebuild returns it to the run button and to the `name` field |
| 14 to 17 | the source labels in the text and muted colours; every knob field named; no "?" and no chip among the Tab stops; 52 stops from the first rail row to the scrubber |
| 18 to 26 | the bars: right moves between bars, and Enter opens the form. Cmd-Z and Shift-Cmd-Z on a focused bar undo and redo. Space on "add a hold after" adds a hold. Then the "% faster" messages, "1 local box", and 17 stops from "start from" to the form's first field |
| 27 to 31 | the graph: right from import reaches registration; the confirmation opens with "no" focused, and Enter on "no" or Escape closes it; the routed line runs under the plan node |
| 32 to 34 | the probe's violet marks; the inspector's Stability section after a fetch (T97); the heads and the rail agree with the tiles on jobs `loop_angel_20261105-024930`, `-031000` and `loop_angel_20261104-223204` |

The hint rules held in `pop.mjs`, `pop2.mjs` and check 4. A mouse click on a bar opened no hint, and Tab onto the scrubber opened `control.scrub`. Right on the scrubber then stepped the frame from 0 to 1 and closed the hint. A control hovered for 750 ms showed its own hint.

## The console pass

Every drive saw 0 page errors and 0 uncaught exceptions. The final miss count covered 73 screens: 60 stage panels (6 jobs × 10 stages), 4 compare modes, 3 frames of a2, 3 plan-editor states, the graph, and 2 injected rail states. It found 5,338 chips and 11,861 elements with a hint key, and 0 misses.

An estimate of the state before this round: the A2 key rule and table, applied to today's chip texts, leave 17 distinct chip keys without a row. The fix needed fewer than 17 new rows because the new key rule maps several of those texts to existing rows: "draft 480" to `chip.draft`, "stale after registration" to `chip.stale`, "A: …" to `control.cmp_a`.

## Screenshots

53 files under `benchmarks/runs/2026-11-05/studio/shots/`, each at the size in its name:

- the frame before and after: `fix_before_{render,registration,probe}_{2560,1440,1280}.png`, and `fix_after_…` the same 9 names;
- the viewer at 2×: `fix_render_2x_tag_{2560,1440,1280}.png`;
- the graph and its confirmation: `fix_graph_{2560,1440,1280}.png`, `fix_graph_confirm_{2560,1440,1280}.png`;
- the plan editor, the review gate and the inspector: `fix_plan_{2560,1440,1280}.png`, `fix_page_gate_2560.png`, `fix_registration_inspector_2560.png`;
- the readers' moved folder: `fix_readers_moved_{2560,1440,1280}.png`;
- the scanned screens: `fix_scan_{plan_ruled,page_adopted,graph_220719,render_a2_wipe_f20,registration_windows,probe_220719}_{2560,1440,1280}.png`.

## What I left, and why (candidate backlog rows)

The two minor rows left (10 and 14) are the first two rows below; the other five come from this round's findings.

| Source | What | Why it is left |
|---|---|---|
| minor row 10 | 22 of 22 stage knobs read "range none stated" | a range has to be read from each flag's `loop_seq.py --help` line into `registry/loop.py`; the registry copies ranges and never invents them, and that reading is a registry task beyond this round |
| minor row 14 | 4 hints still quote the angel pair's numbers as their example: `prep.windows`, `prep.largest_offset`, `measure.stability_max` and the `ecc_refine` knob | which example a universal hint keeps is a content decision (`PRODUCT.md`: "Universal, never overfit"); `measure.probe_dexp` lost its example with minor row 15 |
| P2 row 12 | Info and Photo A share `#6aa9f0`, so the "unjudged" and "draft 480" chips share k0's blue | a palette change is a `DESIGN.md` amendment, which the critique names as such |
| P2 row 11, its cost | a hint attached only to a region or a table heading (`region.strip`, `measure.steps`, `prep.fits`) has no control to focus; with the "?" out of the Tab order, a keyboard user cannot open it | the critique proposed the trade for the 74 Tab stops; a keyboard path to these hints (a key that opens the hints of the focused region, say) is a design choice |
| the review gate's wording | grouped, the reason reads "a1, a2, a3, a4, a5: no skeptic verdict for this candidate in the studio" | the reason string comes from `views/page.py`, and a view test pins its exact text; rewording it is a small server change for the next round |
| the frame at 1280×800 | 17.8 % on screen, where it was 21.2 % below the window | the brief asks for the height the window leaves; raising `FRAME_MIN` back to 380 restores the larger frame and puts the scrubber 53 px below the fold |
| not in this round | the critique's hardening rows: save, build and grade stay clickable while their request runs; the wipe drag has no `pointercancel`; the m key marks a fault that no route removes; a probe of many pairs runs to 4,264 px | outside the brief's list; untouched |

Two observations, not defects of this round. First, while the selected stage runs, the poll redraws its panel every 1 s, and the render panel fetches the render each time. This predates this round (read in `strip.js`, not driven). Second, on the final code `radon` grades `job_row` D (24) and `stage_views` F (92); the backlog row on complexity grades (T96) tracks them.

## Documents to sync

I edited none of these; the brief reserves them for the main thread.

| Document | What changed in the code |
|---|---|
| `studio/ARCHITECTURE.md` | `views.job`: `attempt_note`, `is_draft`, `readers_moved`, `running_entry`, and `job_row(settings, d, runner=None)`. `runner.lock` without `release`; `registry.rulings` without `CODE_ONLY_KNOBS`; `registry.hints` 290 keys. Test counts: 379 unit plus 14 integration, 393 in `make test`. The web row: the side column, the host panels' grid, and `core.js` `chipKey`, `focusKey`, `restoreFocus`, `focusQuiet` |
| `.claude/conventions/contracts.md` | the `running` field of each `GET /api/jobs` row is a list of `{id, stage, name, elapsed_s, progress}` (was a list of record ids) |
| `.claude/conventions/studio.md` | the panel, the inspector, the viewer and the graph now restore the focus by data attribute too, and a restored focus opens no hint; the "?" is no Tab stop, and a control's keyboard focus opens its hint |
| `DESIGN.md`, if the owner accepts | the viewer's side column; the violet mark on the box at 1:1 and 2×; the Info and Photo A question |
| `.claude/skills/reveal/references/tracked-backlog.md` | T97, T98, T99 fixed; F2, F3, F9, F10 fixed; the 7 rows above to file |

## Appendix: what I ran and what I wrote

- My server: `uv run reveal-studio serve --port 8396 --no-browser --lock <scratchpad>/fix.lock`. It ran as pid 31325 for the "before" measurements, then as pid 38485 after the Python changes. The owner's server (pid 51553, port 8380) was never touched.
- My Chrome: headless on DevTools port 9396, pid 31328. Late in the round a second studio tab appeared in it, from a cause I did not find; no drive presses Enter on a link. I closed one tab, and the next CDP scan closed the last one, which ends a headless browser. Pid 2227 replaced it for the final 1280 scans and the final miss count. In one long command, two keyboard runs stopped mid-way when the DevTools socket closed; I did not find the cause. Rerun alone, each size passed 34 of 34.
- Stages run: none on the owner's jobs or on the jobs other agents made today. The running record, the failed poll, the T97 state and the plan edits were injected into the page's copy only and never saved. `make acceptance` made its two jobs under `benchmarks/runs/2026-11-05/studio/`.
- Files changed, under `studio/src/reveal_studio/`: `views/job.py`, `jobs/records.py`, `server/routes.py`, `runner/lock.py`, `registry/rulings.py`, `registry/hints.py`, `web/index.html`, and the 9 scripts and 4 style sheets of `web/`. Under `studio/tests/`: `test_views.py`, `test_registry.py`, `test_runner.py`, `test_cli.py`, `acceptance/test_a1_loop_flow.py`.
- The drive scripts and their JSON results: `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/d9082b8f-cf5b-4b41-ba3c-c8c2ee5b8bc6/scratchpad/fix/` (`measure.mjs`, `misses.mjs`, `keys.mjs`, `scan.mjs`, `layout.mjs`, `pop.mjs`, `pop2.mjs`, `adv.mjs`; results under `out/`).
- The no-slop pass: the checker, and a cold read by a context-free subagent. The first save of this file came before the cold read returned; this version applies its findings.
