<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/a2_critique.md (gitignored), the critique of the phase A2 page by an Opus 5.5 subagent (max effort) with impeccable's method and the engine's detector (a DEGRADED run by its own first line: one agent did the design review and the detector); a research artifact whose claims carry the author's own confidence and gaps; its 39 screenshots stay under benchmarks/runs/2026-11-05/studio/shots/crit2_*.png (gitignored); a fix round followed the same session (a2_fixes.md) -->

DEGRADED: single-context (one sub-agent ran both the design review and the detector scan; the review was saved before the scan ran; the in-page overlay did not run)

<!-- reader: the main thread of the 2026-11-05 studio session and the owner, both cold. shape: report. Written 2026-11-05 from 02:56 to 03:44 EET by the critic sub-agent (Opus 5.5). Source: my own server on 127.0.0.1:8397 (reveal-studio 0.2.0, pid 68931). Driver: my own headless Chrome 156 on DevTools port 9397 (pid 69209), with the DOM read by script. Code read: studio/src/reveal_studio/web/ and registry/hints.py. -->

# Critique of the studio's second-phase page: 28/40, one major issue

**Score: 28/40 (Good, the 28–35 band).** The first build phase's page (A1) scored 26; the static mock-up of 2026-11-04 scored 24. Keyboard focus now survives the refresh, knobs start from the last run, and ruled values warn before a run.

Summary:
- **One major issue (P1).** The frame under judgement shows at 27 % of its source on the render panel (A1: 38 %). In the registration panel, windows.jpg and the k0 − k1 difference are 376 px tall, below 1,026 px of tables.
- **Thirteen issues he would notice (P2).** The top three: Space plays the render from any focused button; the focus falls to the page body after each zoom or compare switch; Cmd-Z does nothing on a focused plan bar.
- **The detector (impeccable's scanner).** URL scans: 0 anti-patterns at 2560×1440, 1440×900 and 1280×800. Scans of chosen screens: 3 distinct findings (the plan form, the page panel, the graph at 1280).
- **Console:** 0 errors from the page's scripts. **Contrast:** 4.92:1 or more for every enabled text colour.
- **Asked of the main thread:** fix the P1 and P2 rows 1 to 4 before the owner sees the page; decide P2 row 5, the graph's one-click rerun.

## Names used below

| Name | Meaning |
|---|---|
| the owner, he | The repo's one user, who grades the clips by eye. |
| the main thread, the brief | The session that launched this critic, and its task message of 2026-11-05. |
| A1, A2 | The studio's first and second build phases (`STUDIO.md` §9). A1's critique is `.claude/claude-docs/research/2026-11-04/a1_critique.md` (26/40); "A1's P2 #4" means its issue 4. |
| the comp | The static mock-up of 2026-11-04, critiqued at 24/40 (`comp_critique.md`, same folder). |
| impeccable, DEGRADED | The design skill under `.claude/skills/impeccable/`. Its critique wants a design review and a detector scan in two separate sub-agents; a run in one context must say DEGRADED on its first line. The in-page overlay is its script injected into a tab to outline findings. |
| the detector | impeccable's scanner, `impeccable detect`, version 0.1.18+engine, run from the repo root. |
| URL scan, CDP scan | The detector loading the page in its own browser (it opens the newest job), or reading a page I set up in my Chrome through the DevTools protocol (`--cdp 9397`). |
| the build routine | The UI checks of `.claude/skills/reveal/references/studio.md`, which include a detector run at 0 findings before the owner sees a change. |
| the studio page, the review page | The web page under critique; and the HTML for his grades that the page stage builds. |
| job 220719 | `loop_angel_20261104-220719`: the ten-window registration, the probe, and a 480 px draft with a stability measure. |
| the adopted job | `loop_angel_20261104-220708`: an older run folder taken in as a job, with five full renders; round 1 is graded by the owner, while all five still lack a skeptic verdict made in the studio. |
| a2, a2cancel | Candidate plans and renders of the angel portrait loop; the owner accepted a2 on 2026-11-04. a2cancel is a cancelled draft. |
| k0, k1, the fits | The registered stills `k0.png` and `k1.png`; the fits are the registrations computed for each still (all keypoints, the final frame after the lock, and others when enabled). |
| windows, lock windows, windows.jpg | Named boxes on frame 0 measured under each fit; lock windows are the boxes the registration holds in place (the angel's ring light); windows.jpg draws them on frame 0. |
| the probe | The stage that compares three in-between methods (RIFE, morph, dissolve) on a pair of stills before a plan is written. |
| RIFE, generated, t | The frame-interpolation model; a frame it drew is "generated" and marked violet; t is its place between the two stills (0 to 1). |
| hold, leg, seam step | A still held for some frames; a transition between two stills; the step from the loop's last frame back to its first. |
| frozen plan, slices | A plan file the studio reads and never writes; a transition method the owner ruled out on 2026-11-01. |
| the skeptic, unjudged | A review pass by the session before the review page; "unjudged" means no skeptic verdict in the studio, and NOT READY is one verdict. |
| P1, P2, minor | impeccable's severities as the brief defines them: P1 he would stumble, P2 he would notice, minor the rest. |
| hint, "?" | The 14 px button that opens a hint popover from `registry/hints.py`. |
| the gate | The page panel's review gate: it refuses a review page while a listed candidate is unjudged or NOT READY. |
| ruled value | A knob value the owner ruled out on a dated line; the studio page shows a red chip, and the run still goes ahead. |
| the poll | The studio page's refresh of the open job, every 5 s (1 s while a stage runs). |
| page-only injection | Values changed in the browser's copy of a job to draw a state, then discarded by a reload; nothing written to disk. |

## Scores

The rubric is impeccable's heuristics scoring guide (`.claude/skills/impeccable/reference/critique.md`), as A1 used it. Each row quotes the guide's line for the score given.

| # | Heuristic | A1 | A2 | The guide's line | Why (where) |
|---|---|---|---|---|---|
| 1 | Visibility of system status | 2 | 3 | "Good; most operations give clear feedback, minor gaps" | Render tiles now read their contents; a failed fetch shows "server unreachable, retrying"; the plan editor counts changes. Gaps: three state contradictions (P2 row 4) and a Running row without elapsed time (P2 row 8). One of A1's three causes for its 2, the readers' stale / "Not run." / done, is unchanged; I judge the rest of the status feedback good enough for a 3. |
| 2 | Match between system and real world | 3 | 3 | "Mostly natural; occasional term needs context" | His words throughout (round, candidate, draft, hold, leg). Leaks: "1 a local box", "passes --variants a2,a3,a4,a5", "Rule 7's double-exposure share". |
| 3 | User control and freedom | 3 | 3 | "Good control; users can exit and undo most actions" | 300-state undo and redo, reset per knob, "discard the text" for bad JSON. Missing: a way back from the graph's one-click rerun and from the m key's fault mark. |
| 4 | Consistency and standards | 2 | 2 | "Partially consistent; main flows match, details diverge" | Space presses tiles and bars but plays the render on buttons. Cmd-Z works in an unchanged text field and fails on a bar. Photo A's blue means k0, source A and dx on one screen. |
| 5 | Error prevention | 2 | 3 | "Good prevention; most error paths blocked proactively" | The registration's knobs now show the last run (ref 0, depth maps, three lock windows); ruled values warn in four places before a run (the form, the bar, a summary box above the bars, the inspector). The graph's rerun is one click away beside "show". |
| 6 | Recognition rather than recall | 3 | 3 | "Good recognition; most things discoverable, few memory demands" | Forms show each key's default, units and source. Lock windows are still typed numbers; windows.jpg is too small to read; graph ports truncate to identical names. |
| 7 | Flexibility and efficiency of use | 2 | 3 | "Good accelerators; keyboard nav, some customization" | Focus survives the poll (6.5 s held on a tile, a rail row, a graph node and a bar); roving tab order on bars with Home and End. Costs: 31 Tab stops to the first form field. |
| 8 | Aesthetic and minimalist design | 3 | 2 | "Some clutter; main content clear, periphery noisy" | The frame is 27 % of its source in a 1786 px box that is 79 % empty ground. 44 "?" marks on the first screen, 63 on the plan editor. |
| 9 | Help users recognize, diagnose and recover from errors | 3 | 3 | "Clear with suggestions; identifies problem and offers next steps" | "a new job needs a folder of developed JPGs, or a run folder to adopt"; "takes a whole number" under the field. Raw "Failed to fetch" when the server is down. |
| 10 | Help and documentation | 3 | 3 | "Good documentation; searchable, mostly task-focused" | 267 hint keys; 3 of 14 hints read contradict their control; 22 of 22 stage knobs read "range none stated". |
| | **Total** | **26** | **28** | "28–35 Good: Address weak areas, solid foundation" | |

## The detector

The three lines the brief asks for, verbatim. Each URL scan printed nothing in text mode, printed `[]` with `--json`, and exited 0. A run with advisories at 2560×1440 also printed nothing and exited 0.

```
detect --no-advisory --viewport 2560x1440 http://127.0.0.1:8397/   -> (no output), exit 0; --json: []
detect --no-advisory --viewport 1440x900 http://127.0.0.1:8397/    -> (no output), exit 0; --json: []
detect --no-advisory --viewport 1280x800 http://127.0.0.1:8397/    -> (no output), exit 0; --json: []
```

The URL scan sees one screen: the newest job, opened by `boot.js` because the detector's browser has no stored job. The newest job changed during my run (another agent created jobs 030326 and 031000), so which job it saw is unknown. To scan chosen screens, I set each one up in my Chrome and ran `detect --json --no-advisory --cdp 9397 --target 127.0.0.1:8397`:

| Screen | 2560×1440 | 1440×900 | 1280×800 |
|---|---|---|---|
| render, adopted job, a2, wipe, f 20 | 0 | 0 | 0 |
| registration, job 220719, fits table, windows.jpg shown | 0 | not run | not run |
| probe, job 220719 | 0 | not run | not run |
| plan, frozen angel_a2, step 1 set to slices | 1: `cramped-padding` | 1: same | 1: same |
| graph, job 220719 | 0 | 0 | 1: `edge-flush-cards` |
| page, adopted job | 1: `line-length` | 0 | 0 |

The findings, verbatim from the JSON (each checked on the screen):
- `cramped-padding` at `div.pe-row:nth-of-type(3) > span.chip.bad`: "2.5px of space above and below the text (need ≥4.0px for 12px text)". The ruled chip under the method field is four lines of red text with 1 px of vertical padding. Real.
- `line-length` at `div.msg.bad`: "~151 chars on 4 of 5 rendered lines (aim for <80)". The gate's refusal on the page panel. Real.
- `edge-flush-cards` at `#graph`: "1 card flush against the right edge of div.graph at rest (-23px gap, e.g. div.gthumb)". A node cut by the graph's horizontal scroller at 1280 px. Real, though a scroller cuts something by design; the fix is an inset or a fade.

The bar the build routine sets is 0 anti-patterns. The URL scans meet it; three chosen screens do not. The detector runs wrote nothing under the repo: no `.impeccable/` folder exists after them.

## What A2 fixed from A1's priority issues

| A1 issue | Now | Measured |
|---|---|---|
| A1's P1 #1: the refresh takes the keyboard focus | fixed | Focus held 6.5 s, across a poll, on the probe tile, a rail row, a graph node and a plan bar. |
| A1's P1 #2: the inspector shows defaults | fixed | Registration rows read "default −1 · last run 0"; the button reads "rerun registration with the last run's knobs". |
| A1's P1 #3: the frame and its axis do not share the screen | traded | Scrubber at y 1198 and step plot at 1224–1392 are on screen; the frame shrank from 38 % to 27 % of its source. |
| A1's P2 #4: a chip shows its last record | partly | Render tiles read contents ("1 full, 2 drafts; unjudged: a2 · last attempt cancelled: a2cancel"); this report's P2 row 4 lists what remains. |
| A1's P2 #5: 1440 and 1280 break | partly | At 1440 no chip is cut on job 220708's tiles, but job 220719's "done (unchanged)" shows as "done (unc…"; the render frame box starts at y 1138 in a 900 px window. |
| A1's P2 #6: scrubber and plot on two x scales | mostly | The thumb's centre sits 4 px right of the cursor at f 0 and 9 px left at f 49 (one frame is 38.8 px). |

Four of A1's minor issues are fixed. The popover's key line is no longer amber, and the new-job refusal sits under its form. The gate's message is no longer a box inside a box, and a failed refresh shows a chip. Three stay open. The adopted job's five candidates still read "unjudged", though the gate's message now names the two skeptic reports written before the studio existed ("judged before it: skeptic1.md, skeptic2.md"). 2× opens off-centre. 14 of the 15 rail rows read "angel angel-portrait" at 03:37 EET; only the job id under each name tells them apart.

## P1

| # | Screen | What I measured | Rule broken | Fix (file, change) |
|---|---|---|---|---|
| 1 | Render panel, adopted job, a2; registration and probe panels of job 220719 | Render at 2560×1440: frame box 1786×482 at y 668, picture 369×478 of 1366×1770 (27 %). Above it: the strip 263 px, the row of render tiles 185 px (193 px with its gap), the viewer head 28 px, the source row 27 px. Registration: viewer at y 1347, box 1952×380 (the 380 px floor of `sizeFrame`), windows.jpg 287×376 of 733×960, the k0 − k1 difference 290×376 (21 %); at 1:1 the box shows 378 of 1770 rows. Probe: viewer at y 3785 of a 4264 px panel. At 1440×900 the render's frame box starts at y 1138, below the window. | `DESIGN.md` §The viewer: "One large frame under judgement fills the space between the strip and the axis (sized from the window)"; `STUDIO.md` §9 A2 acceptance: "compares the three fits on the ring windows". | (a) `panels.js` `panelRender`: list the renders in the 150 px column under the two reference stills, or as a select beside source A, freeing the 193 px row. (b) `viewer.js` `renderViewer`: put the viewer head and the source selects on one row (frees 39 px). (c) `panels.js`: in registration, readers and probe, put `#viewerWrap` in a column beside the tables (the fits table is 612 px wide in a 1952 px panel). (d) `viewer.js` `sizeFrame`: size the box from the window, `innerHeight - 160`, not from its current top. Estimate, not driven: the render box grows to about 714 px (40 %); a side-column registration viewer to about 1,280 px. |

## P2

Ranked by how often he would meet them.

| # | Screen | Quote or measured value | Rule broken | Fix (file, change) |
|---|---|---|---|---|
| 1 | Every panel once a render was opened | Space on the focused "1:1" button started playback (f 10 to f 44 before I stopped it) and left the zoom at fit. Space on "add a hold after" did nothing (4 steps stayed 4); Enter added the hold. | `DESIGN.md` Overview: "Everything is a standard web control"; a button answers Space. | `boot.js` keydown: handle Space only when the target is the body, `#scrub` or inside `#frameBox`, and only when `#scrub` exists; otherwise leave the event alone. |
| 2 | Viewer, every host | Enter on "wipe" or "2×" switched the mode and moved the focus to `<body>`. | `PRODUCT.md` Accessibility: "visible focus are required for the review loop". | `viewer.js` `wireViewer`: after `renderViewer()`, focus the pressed button of the same group (`[data-mode="…"]` or `[data-cmp="…"]`). |
| 3 | Plan editor | Cmd-Z on a focused bar did nothing (1 change stayed 1). Cmd-Z in the unchanged n field undid the plan (1 change to 0). The hint says "Cmd-Z or Ctrl-Z when the focus is not in a text field". | The hint contradicts the control (brief, item 9). | `plan.js` panel keydown: stop propagation only for the arrows, Home and End, so Cmd-Z reaches the document. `hints.py` `control.plan_undo`: "Cmd-Z or Ctrl-Z undoes the last change; in a text field with typing not yet committed, it undoes the typing first." |
| 4 | Panel head, rail, readers panel | Job 024930's render head: chip "done" beside "cancelled by you". Job 031000: render head "done" beside "the server restarted while the stage ran and no terminal file was found: run it again"; rail chip "lost" while the tile says "done". Job 223204: readers tile "stale", panel "Not run.", inspector "done 20261104-223316_readers". | `DESIGN.md` Chips: "a chip names a state in a word"; A1's P2 #4. | `views/job.py` line 234 sets a stage to "done" from its contents: there, clear `reason` and show the attempt as "last attempt: cancelled by you" in muted text. `views/job.py` line 402: override `last_render` when any candidate exists (`if cands`), as the tile rule does with `full or drafts`. `panels.js` `panelReaders`: under the stale message, replace "Not run." with the path of the moved readers folder. |
| 5 | Graph view | 4 of job 220719's 9 nodes (registration, probe, render, measure) carry "rerun from here", a ghost button beside "show"; one click posts the run (`graphRerun`, `graph.js` line 35). On the registration node this moves the prep aside and makes the renders stale unless the new prep is byte-identical. | `clarify.md`: "For destructive actions, name the object and consequence". | `graph.js`: make the first click turn the button into "rerun registration with the last run's knobs? the renders go stale · yes · no", focus on "no"; or keep reruns in the inspector only. |
| 6 | Viewer at 1:1 and 2× | At 2× the box scrolls to (0, 647); the tag "generated t 0.5554" sits at the box's top-left and the violet outline at the picture's edge, so neither is on screen. | `DESIGN.md` Generated Violet Rule: "Every model-made pixel on screen carries the violet mark where it is shown". | `viewer.css`: move `#frameTag` out of the scrolling `#frameBox` (into the source row) and draw the violet outline on `#frameBox` while a generated frame is shown. |
| 7 | Probe panel | The rife strip (568×276 px) and the rife face crops at t 0.25, 0.5, 0.75 carry no violet mark. | Generated Violet Rule: "a strip, a scrubber and a sheet all mark it the same way". | `panels.js` `panelProbe`: add `class="gen"` to the rife figure and its crop cells; `viewer.css`: `figure.gen img{outline:2px solid var(--gen);outline-offset:-2px}`. |
| 8 | Rail, Running | During another agent's render the row read "20261105-030817_render" and a "running" chip: no stage name, candidate name or elapsed time. | `DESIGN.md` Navigation: "the running tasks with their elapsed seconds"; `STUDIO.md` §3 Rail: "elapsed seconds and the expected wall time". | `views/job.py` job summary: running entries as `{id, stage, name, elapsed_s, progress}`; `rail.js`: print "render · a2 · 12/50 · 38 s". |
| 9 | Graph view, job 220719 | The `prep.json` line from registration (canvas x 488) to render (x 808) passes behind the plan node (x 544–752), so it reads as registration → plan. | `STUDIO.md` §3 Graph: "the edges the files between stages". | `graph.js` `drawEdges`: route a line that skips a column through the gap under the row, as the branch rule already does. |
| 10 | Plan editor at 1440×900 | The step form starts at y 900 (first field y 949), below the window; the inspector beside it holds only "plan ?". | `DESIGN.md` Layout: "a fixed three-region shell … 1440 px and wider". | `plan.css`: keep two columns down to 1280 (`grid-template-columns:minmax(0,1fr) 360px`), or render the form in the empty inspector on the plan stage. |
| 11 | Every view | The adopted job's render view: 131 Tab stops, 47 of them "?" buttons and 27 chips. Plan editor: 31 stops from "start from" to the step's first field, 16 of them "?". | impeccable's heuristic 7 (flexibility and efficiency): 74 of the 131 stops (56 %) are "?" buttons and chips, not controls. | `core.js` `hintBtn`: `tabindex="-1"`; `chip()`: drop `tabindex="0"`. The focus handler already opens the hint of any focused `[data-hint]` control, so give each control its `data-hint`. |
| 12 | Render panel | Refs: k0 blue, k1 orange. Source labels: A blue, B orange, and B defaults to k0. Stability plot: dx blue, dy orange. The same blue marks three things on one screen: the still k0 in the reference column, source A in the comparator, and dx in the stability plot. | `DESIGN.md` Photo A and Photo B: "the two photographs' identities". | `viewer.css` `.srcpick` labels and `viewer.js` stability lines: use the text colour and the muted colour (solid and dashed); keep the photo colours for k0 and the last still. `DESIGN.md` also gives `#6aa9f0` to both Info and Photo A, so the "unjudged" and "draft 480" chips share the blue; that part needs a `DESIGN.md` amendment (a separate Info or Photo A colour). |
| 13 | Inspector, every "?" | The knob inputs (name, draft, fps on the render) have no accessible name; 47 "?" buttons share the name "hint". | WCAG 4.1.2 Name, Role, Value. | `inspector.js`: `aria-label` with the knob's key on each input; `core.js` `hintBtn`: `aria-label="about <key>"`. |

## Minor

| # | Screen | Quote or measured value | Fix (file, change) |
|---|---|---|---|
| 1 | Rail, Requests | The chip spans x 157–273 in a 240 px rail; "waiting 1 h 7 min" showed as "waiting 1 h 7". | `studio.css`: `.rail .kv{flex-wrap:wrap}`. |
| 2 | Page panel, the gate | "(no skeptic verdict for this candidate in the studio (judged before it: skeptic1.md, skeptic2.md))" repeats for a2, a3, a4 and a5: 4 lines of about 151 characters. | `panels.js` `panelPage`: group the candidates by reason; `studio.css`: `.msg{max-width:75ch}`. |
| 3 | Plan form, ruled chip | 2.5 px above and below four lines of text (the detector). | `plan.css`: `.chip.ruled{padding:6px 8px}`. |
| 4 | Plan editor, "% faster" | Empty field with the placeholder "20", then apply: "the percentage is a number below 100: 20 makes the loop 20 % faster, −50 makes it 50 % slower". The field is empty, not out of range. | `plan.js` `peFaster`: "type a percentage first"; drop the placeholder that reads as a value. |
| 5 | Plan form, local boxes | "1 a local box"; the item reads "a local box 0". | `plan.js` `peItems`: a group title without the article. |
| 6 | Plan editor | "4 frame counts × 0.80 as one change" beside "4 changes from frozen:angel_a2"; the message stays after the undo. | `plan.js`: "(one undo step)"; clear the message on undo and redo. |
| 7 | Any request while the server is down | "Failed to fetch". | `core.js` `api()`: catch the TypeError and name the server, its port and `reveal-studio serve`. |
| 8 | Hints | `control.page_variants`: "the arrows reorder" (the buttons read "up" and "down"). `control.cmp_ab` on the A/B mode button: "this button or the a key flips between them". | `hints.py`: "up and down reorder"; a separate hint for the mode button. |
| 9 | Strip | With a tile's "?" focused, ArrowRight stepped the frame 10 to 11 and Shift+ArrowRight to 21. | `strip.js`: stop the arrows' propagation before the early return for `.hint`. |
| 10 | Inspector | 22 of 22 stage knobs read "range none stated". | `registry/`: state a range where the script's argparse states one; leave the rest. |
| 11 | Inspector | The "last run" value of `lock_window` and `windows` runs past the 320 px column's right edge. | `studio.css`: `.knob .def{overflow-wrap:anywhere}`. |
| 12 | Render viewer | The key legend under the last still is cut (`.refs` content 493 px in 482 px), and `.refs` takes the Tab focus with a 150×483 amber ring. | `studio.css`: let `.refs` grow (`height:auto`), so it is not a scroll container. |
| 13 | Render viewer, 2× | Opens at scroll (0, 647), not the centre (474, 1532); at 1:1 the 1366 px frame hugs the left of a 1784 px box. | `viewer.js`: centre after `sizeBase()` on the next animation frame; centre the picture when narrower than the box. |
| 14 | Five new hints | `prep.windows`, `prep.largest_offset`, `measure.stability_max`, `measure.probe_dexp` and the `ecc_refine` knob quote the angel pair's numbers as the example. | `hints.py`: keep the rule, cite the angel sheet as the source. `PRODUCT.md` principle 4: "Universal, never overfit". |
| 15 | Probe panel | `measure.probe_dexp`: "Rule 7's double-exposure share … 3–11 % is the floor on handheld pairs". A cold reader cannot tell whether 6.11 % passes. | `hints.py`: say what a high share warns of, and that the probe has no bar, which is why its table shows no verdict. |

## Keyboard pass

| Area | Check | Result |
|---|---|---|
| Strip | Focus held across a poll | Pass: the probe tile kept the focus for 6.5 s. |
| Strip | A tile's "?" and the arrows | Fail: the frame stepped (minor row 9). |
| Rail | Focus held across a poll | Pass: 6.5 s on a job row. |
| Graph | Tab into the graph, arrows, Enter | Pass: right to registration, down to probe, up back; Enter selected it, the rebuild restored the focus, and it held 6.5 s. Each node adds 3 to 5 Tab stops (node, "?", chip, buttons). |
| Plan editor | Bars and effects | Pass: one Tab stop each (roving tab order), arrows move, Home and End jump, Enter opens the form, focus returns after a rebuild. |
| Plan editor | Undo and redo | Pass from a button (Cmd-Z: 4 changes to 0; Shift-Cmd-Z: back to 4). Fail from a bar (P2 row 3). |
| Plan editor | Space on a button | Fail (P2 row 1). |
| Viewer | Zoom and compare buttons | Enter works; the focus then falls to the body (P2 row 2). |
| Viewer | Wipe handle | Pass: reached by one Tab from source B, 2 px amber ring on the 28 px handle (`crit2_wipe_handle_focus_2560.png`), ← and → move 1 %, Shift 10 %, and the frame stayed at f 31. The handle's hint opens on focus and covers the picture under it. |
| Viewer | Scrubber | Pass: the ring sits on the thumb only (`crit2_scrub_focus_2560.png`), ← → step 1, Shift 10 (31 to 41 to 42 to 32). |
| Viewer | The arrows never leave a control that owns them | Pass for the bars, the graph, the handle and the scrubber; fail for a tile's "?". |

Every Tab stop I visited showed a 2 px amber outline (buttons, tiles, nodes, bars, chips, "?") or an amber border (inputs, by `DESIGN.md`'s input rule).

## Console pass

- 0 exceptions and 0 console errors from the page's scripts from 02:57 to 03:41 EET, over every screen named in the brief. A second DevTools client attached to my tab logged every error, warning and failed response.
- Network: 1 HTTP 400 from my deliberate empty new-job submit, which Chrome also logs as "Failed to load resource". 0 HTTP 404.
- I made every fetch fail inside the page, so no request left it. The Running list showed "server unreachable, retrying" within 6.5 s, and "idle" 6.5 s after I lifted the block.

## Accessibility pass

Contrast, measured with the WCAG formula on the effective background (the lowest per colour):

| Text | Face | Ratio |
|---|---|---|
| failed `#e8706a` (chips "lost", "past bar", ruled chip) | raised `#24282c` | 4.92:1 |
| faint `#8a9198` (knob default lines) | panel `#1c1f22` | 5.19:1 |
| faint `#8a9198` (form default lines, plot ticks) | ground `#141618` | 5.69:1 |
| muted `#9aa1a8` (grey chips) | raised | 5.68:1 |
| info `#6aa9f0` ("unjudged", "draft 480") | raised | 6.04:1 |
| ok `#5cc48a` ("done", "within") | raised | 6.87:1 |
| amber `#e0a65a` ("running", "waiting") | raised | 6.91:1 |
| photo B `#f0a06a` (label B, dy) | ground | 8.59:1 |
| amber ink on amber (primary buttons) | amber | 8.64:1 |
| disabled "redo" at 40 % opacity | raised | 3.19:1 (exempt) |
| disabled graph "show" at 40 % opacity | panel | 2.13:1 (exempt) |

- The 12 px floor: chips, tags, plot ticks and labels compute to 12 px. Below it: the "?" glyph (10 px; 49 on job 220719's render view with the stability plot, 63 on the plan editor) and the wipe handle's "◂▸" (10 px). Both sit inside a larger control.
- Focus rings: the scrubber's ring sits on its thumb and never on the 1918 px track; the wipe handle has its own ring.
- Names and announcements: P2 row 13. A field error sets no `aria-invalid` or `aria-describedby`; `#msg` is not a live region. The strip's tiles are `role="tab"` with no `tabpanel`.
- Passes: the landmarks `nav`, `main` and `aside`, and one `h1` per screen.

## The states

| State | Where I saw it | How it is drawn | Shown as a word |
|---|---|---|---|
| running | Rail, during another agent's render (job 030326) | amber chip "running" on the job row; Running row with the record id | yes; no elapsed time (P2 row 8) |
| running, tile | page-only injection (nothing written) | amber chip "running 12/50 rife", amber tile border | yes; the selected tile is also amber |
| failed, refused | page-only injection; the empty new-job form, live | red chip and red tile border; the head prints the reason; the form prints "a new job needs a folder of developed JPGs, or a run folder to adopt" | yes; a selected failed tile shows only amber |
| lost | job 031000's rail row; job 223204's render history | red chip "lost" | yes; contradicts the tile (P2 row 4) |
| cancelled | job 031000's registration tile and head | red chip "cancelled", "cancelled by you" | yes, in the failed colour |
| stale | job 223204's readers and page tiles | blue chip "stale"; head "stale after registration" | yes; the panel adds "Not run." (P2 row 4) |
| draft | render tiles and viewer head | blue chip "draft 480", "draft 960" | yes |
| generated | frame tag, axis, tiles | violet chip "generated t 0.5554", violet bands under the step plot, violet bars; the tile's 10 px violet square has a title only | yes, except the square |
| unjudged | render tiles, viewer head, rail | blue chip "unjudged" | yes |
| waiting | skeptic tile and the Requests list | amber chip "waiting 30 min" | yes |

The disk holds no failed or refused record. I drew those tiles by changing the page's own copy of the job (`crit2_states_injected_2560.png`), then reloaded.

Stall bands and jump ticks: a2 in the adopted job and the measured draft in job 220719 both have 0 stalls and 0 jumps, so neither mark shows. I did not inject them; the views report's `e_markers_injected.png` shows them drawn from injected values.

## impeccable audit

| # | Dimension | Score | Key finding |
|---|---|---|---|
| 1 | Accessibility | 2 | Contrast passes everywhere; 47 identical "hint" names, unnamed knob inputs, no live region, Space taken from buttons. |
| 2 | Performance | 3 | The poll rebuilds only on change. In difference mode a frame's diff can run twice, on the step and again when the picture loads: 80 diffs in 2 s of playback over 50 frames, 22 ms each at 1366×1770. |
| 3 | Theming | 3 | Tokens in `:root`; `viewer.js` repeats the palette as JS constants, and the page panel's iframe sets `background:#fff`. |
| 4 | Responsive design | 2 | At 1440 the frame and the plan form start below the window; at 1280 the inspector sits under an 800 px work area with its own scroll; the graph shows 3.5 of 7 columns at 1440. |
| 5 | Implementation integrity | 3 | A product-specific system (strip, shared axis, violet mark, fits table); the detector's 3 findings on chosen screens are real; drift in the reused photo colours. |
| | **Total** | **13/20** | "10-13 Acceptable (significant work needed)" |

Verdict on integrity: pass; the Keep list below names the parts no other product would have.

## impeccable harden (by hand)

| Case | Result | Fix |
|---|---|---|
| Long values | The last-run lock windows overflow the inspector; graph ports truncate two different files to the same "PXL_2026110…"; long render names wrap beside their chip. | `overflow-wrap:anywhere`; ports keep the distinguishing tail ("…103732636"). |
| Many candidates | 8 render tiles fill one row at 2560 and three rows (554 px) at 1440; a row is 185 px plus an 8 px gap. The Halloween round's 24 candidates would take three rows at 2560, about 580 px (projected, not driven). | P1 fix (a). |
| Many pairs | The probe panel is 4,264 px for one pair with two faces; a 10-still sequence has 9 pairs. | Collapse each pair after the first; show its table row only. |
| Server down | The rail reports it and recovers (console pass); a button's request shows "Failed to fetch". | Minor row 7. |
| Double submit | "save as a new plan", "build the page" and "save the grade" stay enabled while their request runs (`plan.js` `peSave`, `panels.js`; code read, not driven); run and measure show "working…". | Disable them and show "working…", as `DESIGN.md` Buttons says. |
| Interrupted drag | The wipe drag ends only on `pointerup` (`viewer.js`); no `pointercancel` or `lostpointercapture` handler (code read, not driven). | Clear the drag on both. |
| Stray key | `m` writes a fault mark under `owner_frames/` from anywhere in the render viewer; the server has no route to remove one (`server/routes.py`: POST `/frames/mark` only; code read, not driven). | Confirm in the note field, or add an unmark beside the mark. |
| Languages | Not tested: the studio has one English-speaking user. | None. |
| Empty states | Each names the next action ("No render yet. Pick a plan and a name in the inspector…"; "Load a plan to edit it as bars and forms"). | Keep. |

## impeccable clarify (by hand)

The clarify rows are minor rows 2, 4 to 8, 14 and 15, and P2 rows 3, 4 and 8. Two more:
- "within" on step max, stalls and jumps names no bar; only the seam step's chip names one, and only when past ("past bar (3)"). Print the bar in both cases.
- The registration panel shows each lock window's offset twice: "(6.14, −12.59)" in A1's lock column and "+6.14 −12.59" in the fits table. Keep the fits table.

I opened 5 hints as popovers (`prep.fits`, `control.page_variants`, `control.wipe_handle`, `control.cmp_ab`, `stage.plan`) and read 14 of the 267 cold from the table the popovers draw from. Ten explain their control: `prep.fits`, `chip.edge`, `prep.largest_offset`, `measure.stability_max`, `measure.jumps`, `control.cmp_diff`, `control.plan_faster`, `region.plan_form`, `chip.ruled_out` and `control.graph_add`. Three contradict it: `control.cmp_ab`, `control.plan_undo` and `control.page_variants`. `measure.probe_dexp` leaves the reader unable to act. The ranges the hints give match their controls: correlation −1 to 1, wipe and onion 0–100 %, the probe step 0–255.

## Cognitive load

4 of 8 checklist items fail, which the guide calls high load (A1: 3, moderate).

| Item | Verdict | Where |
|---|---|---|
| Single focus | fail | The 27 % frame competes with 10 stage tiles, 8 render tiles, two reference stills and 13 measure rows. |
| Chunking | fail | The slices form lists 32 keys in one column; the editor's top row holds 7 controls and 5 "?". |
| Grouping | pass | Rail sections, inspector sections, one box per round or request. |
| Visual hierarchy | pass on the render panel | The frame is the largest saturated object there, though many items compete for focus. The registration and probe panels put the picture last. |
| One thing at a time | pass | One stage per panel. |
| Minimal choices | fail | The viewer head holds 3 zooms, 5 compare modes, "mp4" and two source selects. |
| Working memory | fail | The grade form still shows neither the page nor the candidates. |
| Progressive disclosure | pass | Hints on demand; one form per bar. |

Personas. A power user (impeccable's "Alex") loses the focus after each mode switch, cannot use Space on buttons, and Tabs 31 times to reach a form field. A keyboard and screen-reader user ("Sam") hears 47 buttons named "hint" and unnamed inputs, and errors are not announced. The owner at his 27-inch display judges a 369×478 px frame, and at 2× loses the tag that says the frame is generated.

## Keep

1. The plan editor. Each bar's width is its frame count, and the rife bars are outlined violet. The forms come from the schema, with each key's default, units and source. Undo keeps 300 steps, "% faster" is one step, and the JSON tab keeps text that does not parse.
2. The rulings. A red chip with the date and the reason shows in the form, on the bar, in a summary box and in the inspector, before a run. Example: "ruled out 2026-11-04: Measured on the angel pair: the masked ECC on the far field left the far field 2–9 px worse."
3. The fits table and the probe's crops. The table lists ten windows under each fit, with units in the headers and a largest-offset row. The 1:1 face crops show the doubled hair at t 0.25 to 0.75.
4. The shared axis: the stability plot under the step series with one cursor, its maxima labelled with px and frame.

## Screenshots

All under `benchmarks/runs/2026-11-05/studio/shots/`, PNG at CSS scale; each is the full window at the size in its name, or a crop of it. The finding each one supports is in brackets.
- First screen: `crit2_first_2560.png` (P1; P2 row 4, "done" beside "cancelled by you"; minor rows 1 and 12).
- Registration: `crit2_reg_top_2560.png` (the fits table; minor row 11), `crit2_reg_windows_2560.png` and `crit2_reg_diff_2560.png` (P1), `crit2_reg_diff_1to1_2560.png` (P1, 378 of 1770 rows), `crit2_hint_fits_2560.png` (a hint popover).
- Probe: `crit2_probe_2560.png`, `crit2_probe_crops_2560.png` (P2 row 7; Keep 3).
- Plan: `crit2_plan_form_2560.png` (minor row 5), `crit2_plan_faster_2560.png` (minor row 6), `crit2_plan_ruled_2560.png` (minor row 3), `crit2_plan_json_2560.png`, `crit2_plan_fielderr_2560.png`, `crit2_plan_1440.png` (P2 row 10).
- Render: `crit2_render_fit_2560.png` (P1), `crit2_render_1to1_2560.png` and `crit2_render_2x_2560.png` (P2 row 6; minor row 13), the crops `crit2_render_wipe_2560.png`, `crit2_render_ab_2560.png`, `crit2_render_onion_2560.png`, `crit2_render_diff_2560.png` (P2 row 12), `crit2_render_stability_2560.png` (Keep 4), `crit2_render_1440.png` (P1 at 1440), `crit2_render_1280.png`.
- Inspector, page, graph: `crit2_inspector_ruled_2560.png` (a ruled knob), `crit2_page_variants_2560.png` (minor rows 2 and 8), `crit2_graph_2560.png` (P2 rows 5 and 9), `crit2_graph_1440.png` (the graph cut at 1440).
- Focus rings (crops): `crit2_scrub_focus_2560.png`, `crit2_wipe_handle_focus_2560.png` (keyboard pass).
- States: `crit2_states_running_rail_2560.png` (P2 row 8), `crit2_states_injected_2560.png`, `crit2_states_refused_newjob_2560.png`, `crit2_states_lost_2560.png`, `crit2_states_lost_cancelled_2560.png` and `crit2_states_done_lost_reason_2560.png` (P2 row 4), `crit2_states_stale_2560.png` (P2 row 4), `crit2_states_waiting_2560.png`, `crit2_harden_offline_2560.png` (console pass).

## Gaps

- One context ran both halves; the design review was saved first (`scratchpad/crit2/assessment_A.md`, session scratch). The in-page overlay did not run. I skipped the snapshot under `.impeccable/critique/` and the closing questions to the owner, because the brief allows only this report and the shots.
- A running tile, the inspector's progress line and cancel were not seen live; my server started no stage. The running tile, failed and refused were drawn by page-only injection.
- Playback at 25 fps was not judged by eye. The 24-candidate layout is a projection.
- A1's fix-table rows 10a (the import panel's first sentence) and 13 (every saved plan's author recorded as "owner") were not re-checked: I saved no plan.
- My server was a second server on the tree. At 03:22 it re-attached two running records of another agent's job `loop_angel_20261105-032226` (registration pid 4160, probe pid 4256), during its run and not only at start: backlog row T88 also fires at runtime. Both records ended done.
- Another agent's server (8398) made jobs 030326 and 031000 during my run; I read them and clicked nothing that runs.
- The prose pass: the no-slop checker (0 blocks, 0 sentences over 40 words) and one cold read by a context-free sub-agent; the terms it could not resolve went into the glossary, and its contradictions were fixed.
- My writes: one empty new-job submit (HTTP 400; a listing of `2026-11-05/studio/` before and after showed no new folder), these 39 screenshots, and this report. Plan edits, ticked knobs and the variants control stayed in the browser and were undone.
