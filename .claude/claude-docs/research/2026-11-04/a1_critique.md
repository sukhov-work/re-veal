<!-- Provenance: written by an Opus 5.5 subagent (impeccable's critique of the studio's phase A1 page, served live, with the engine's detector run; 23:00–23:40) of the Claude Code session of 2026-11-04 (the studio phase A1 build; DECISIONS 2026-11-04 sixth line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/a1_critique.md (sha256 7acf537935321991) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Score 26/40 (acceptable; the static comp scored 24). Its three P1 issues (the refresh stealing the keyboard focus, the inspector showing defaults instead of the last run's knobs, the frame and its axis not sharing the screen), the three P2 issues and the minor ones were fixed by the main thread at 23:50, except the plan's author (every plan saved from the page is recorded as the owner's, by design, said in the hint). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

DEGRADED: single-context (one sub-agent ran both assessments; Assessment A was saved to the scratchpad before the detector ran; the detector ran by its CLI, and the in-page overlay did not run)

## Findings: critique of the studio A1 (impeccable critique, the engine's detector run)

<!-- reader: the main thread and the owner, both cold. shape: a report in the brief's template. Written 2026-11-04, 23:00 to 23:33, by an Opus 5.5 subagent. Sources: a drive of http://127.0.0.1:8380/ in headless Chrome at three viewports, with the DOM read by script. The server was pid 29844 on studio.py md5 dd2e170be599eb718f6e3cc5413860b8. Also read: studio.py at the cited lines, and four detector runs. -->

Verdict: 26/40 (Acceptable) — the build answers in part the three major issues of the comp critique, but the 5-second refresh drops keyboard focus, a rerun ignores the last run's knobs, and the scrubber starts below the screen.

Names used below:

| name | meaning |
|---|---|
| the studio A1 | Phase A1 of `scripts/research/studio.py`, the local page at http://127.0.0.1:8380/ (`.claude/claude-docs/STUDIO.md` section 9). |
| the test job | `loop_angel_20261104-223204`: full renders a1 and a2, drafts a1d, a2d and a2r, rounds 1 and 2. |
| the adopted job | `loop_angel_20261104-220708`: five candidates, round 1 graded. |
| the refresh | The page's poll of the open job, every 5 s, or every 1 s while a stage runs. |
| the comp critique | `.claude/claude-docs/research/2026-11-04/comp_critique.md`, which scored the static mock-up (the comp) 24/40. |
| the acceptance drive | `benchmarks/runs/2026-11-04/studio/agents/a1_acceptance.md`, with checks 1 to 15 and defects 1 to 14. Letters (a) to (h) are the checks in this critique's brief. |
| Assessment A and B | The two halves of impeccable's critique method: A is the design review, B the detector run. |
| P1, P2, minor | Impeccable's severity tags: P1 is major, P2 an annoyance with a workaround. Names such as /impeccable harden are impeccable's sub-commands. |
| the strip, the violet tick | The row of stage tiles across the top; a tile's violet square marks model-made frames. |
| lock windows, ref | Rectangles on the reference still that registration holds in place; ref is the reference still's index. |
| the review gate, "ungraded by his word" | The page panel's refusal of unjudged candidates; the chip of a round he chose to leave ungraded. |
| the readers stage | The optional stage that reads faces, focus, grey level and depth per still. |

The comp critique's three major issues, as built:
- The viewer: one frame with its mode drawn pressed, A and B at 200 px, play at 25 fps. The frame still shows at 38 % of its source.
- The knob rows: each shows its key, value, sentence, default and a reset. All 12 rows of registration and render read "range none stated".
- The gating measures: 3 of 11 rows carry a verdict chip ("no stall", "within"). The step plot draws only the 0.3 stall bar.

### Fix verification

FAIL means the defect still shows on the surface. UNVERIFIED means the new code exists, no drive exercised it, and the surface shows nothing of the defect.

| # | defect (acceptance drive) | verdict | the number read |
|---|---|---|---|
| 1 | `.part` folders listed as renders; console errors (a) | PASS | Renders listed: a1, a2, a1d, a2d, a2r; `drafts/angel/a2l.part` sits on disk, unlisted. 0 console errors at load and over 39.6 s of refresh (26 requests, none to a `.part`). |
| 2 | 1:1 hides the frame's top (b) | PASS | At 1:1 the image renders 1366 px wide, natural width 1366. At scrollTop 0 its top sits 1 px (the border) below the box top. |
| 3 | 2× renders at 1.269× (b; acceptance check 8) | PASS | Rendered width 2732 px, ratio 2.0000, `image-rendering: pixelated`. The top sits 1 px below the box top; the bottom is reached at scrollTop 2862. |
| 4 | one failed fetch ends the refresh (a) | PASS | I injected two "Failed to fetch" rejections, at 1.5 s and 6.5 s. The job's request then succeeded at 11.5 s and 16.6 s. |
| 5 | a registration rerun breaks the pages' keyframe image | FAIL | The code now copies keys.jpg (studio.py:654–655). The test job still lacks `in/angel/keys.jpg`: 6 HTTP 404s in my tab, and the page frame shows a broken image. |
| 6 | placeholder contrast (d; acceptance check 14) | PASS | `::placeholder` computes rgb(138, 145, 152) at opacity 1 on rgb(20, 22, 24): 5.69:1, the same on all 5 placeholders. |
| 7 | step-plot caption over the ticks; stretched text (c) | PASS | viewBox width 1952 = CSS width 1952 (scale 1.0000), and the SVG has no `preserveAspectRatio`. The ticks span y 133–147, the caption y 152–167: a 5 px gap. |
| 8 | scrubber and plot off-screen (e) | FAIL | The 5 renders share one row at y 417. The frame box ends at y 1459, the scrubber starts at y 1507 and the plot ends at y 1706, in a 1440 px viewport. |
| 9 | one panel's message shows on another (f) | PASS | The empty-folder refusal showed at y 294 in the render panel. After a click on the plan tile, and after opening the adopted job, `#msg` computed `display: none`. |
| 10a | import copy says "under in/raw" (g) | FAIL | The last line names "raw/angel/", but the first sentence (studio.py:149) still says "one symlink per still under in/raw". |
| 10b | mark button reads "mark f as a fault" | PASS | It reads "mark this frame as a fault". |
| 10c | rail round chip differs from the strip (h) | PASS (simulated) | Both read "round 2 ungraded". With `ungraded_by_his_word` forced true in the API reply, the rail read "round 2 ungraded by his word"; the strip reads the same flag (studio.py:1121). |
| 10d | a job opens on the stage used last | PASS | I left the test job on its plan stage; the adopted job opened on render. |
| 11 | whole-second wall times | UNVERIFIED (code present) | `now_iso` now writes milliseconds (studio.py:82). The existing records keep whole seconds, so the readers and page tiles still read "0.0 s". |
| 12 | an identical rerun says nothing | UNVERIFIED (code present) | `finalize` writes `unchanged_from`, and the tile prints "(unchanged)". A rerun was outside the brief. |
| 13 | every saved plan's author is "owner" | FAIL | studio.py:1002 still writes `"author": "owner"` on every save. |
| 14 | a lost record leaves its `.part` folder | UNVERIFIED (code present) | The lost path now deletes the `.part` (studio.py:672–676). `drafts/angel/a2l.part` from 22:46, with a 265,655-byte loop.mp4, is still on disk, unlisted. |
| check 8 | acceptance check 8 (2× only) | PASS | See row 3. |
| check 14 | acceptance check 14 (the detector) | PASS | 0 findings at 2560×1440 and at 1440×900, exit 0, with and without advisories. |

My tab logged 8 console errors in all. Two are HTTP 400s from my empty-folder probes. Six are row 5's 404s, from five openings of the page panel.

### Scores

| # | heuristic | score | reason (where) |
|---|---|---|---|
| 1 | Visibility of system status | 2 | Chips name every state, and a running stage shows its frame count (acceptance check 6). Yet the test job reads "lost" on the rail, the render tile and the panel header while 2 full renders and 3 drafts are done. The readers stage reads "stale" on its tile, "Not run." in its panel and "done" in the inspector. Two failed refreshes showed nothing. |
| 2 | Match between system and real world | 3 | The copy uses his words: round, candidate, draft, skeptic, "his words, verbatim", "ungraded by his word". Internal keys head the hint popovers ("chip.running"), log tails print raw JSON, and one line shows literal backticks ("the plan's \`in\`"). |
| 3 | User control and freedom | 3 | By the code, a running stage gets a cancel button in the inspector; I did not drive one. Each changed knob has "reset", and a saved plan or a finished render is never overwritten. A registration rerun has no undo in the page; the old prep only moves to `in/angel_prev_<stamp>`. |
| 4 | Consistency and standards | 2 | One visual world, but the keys act differently by place. ArrowRight on a strip tile moves the focus and also steps the frame (f 5 to f 6). Shift+ArrowRight steps 10 from the page body and 1 on the focused scrubber. A knob typed in one job shows, marked changed, in another job. |
| 5 | Error prevention | 2 | The review gate names each unjudged candidate before the click; the round gate and the never-overwrite rule answer HTTP 409. The registration inspector shows ref −1, depth_maps off and no lock windows, while the last run used ref 0, depth maps and three windows. Its amber "rerun registration" button runs with the values shown, not the last run's. |
| 6 | Recognition rather than recall | 3 | All 85 hint keys carry text; the keyboard legend sits beside the viewer; each record shows its command and md5s. The lock windows are typed numbers, never drawn on the still. The plan panel's 30 key sentences open one hover at a time. The rail's three rows all read "angel loop". |
| 7 | Flexibility and efficiency of use | 2 | Space, the arrows, `,`, `.` and m work from the page body; playback runs at 25 fps; every command line can be copied. The refresh rebuilds the strip and the rail: a focused tile lost focus after 2977 ms, a focused rail row within 6.5 s. |
| 8 | Aesthetic and minimalist design | 3 | The grey light table keeps the photographs as the only saturated objects, with at most one amber button per stage view (8 of 8). Clutter: 14 to 46 visible hint marks per view (40 on the render view), and the inspector stacks the next run's knobs and a lost draft's log above the selected render's measures. |
| 9 | Help users recognize, diagnose and recover from errors | 3 | Refusals name the problem and the fix: "choose another name", "save his words, or mark the round ungraded", "Request the skeptic, or override below". The new-job refusal lands in the work area at y 294, while its form sits in the rail at y 467. |
| 10 | Help and documentation | 3 | Each panel opens with its stage's sentence, and each knob row shows its sentence, default and range. All 12 knob rows of registration and render read "range none stated". Help opens on hover or focus only, and no line names the next stage of the flow. |
| | **Total** | **26/40** | **Acceptable** (the 20–27 band) |

The comp critique scored the same heuristics 2, 3, 2, 3, 2, 3, 3, 3, 1, 2. The build gained on control (2 to 3), error recovery (1 to 3) and help (2 to 3). It lost on consistency (3 to 2) and flexibility (3 to 2) through the keyboard faults, which a static comp could not show.

### Cognitive load

Three of the eight checklist items fail: moderate load.

| item | verdict | where |
|---|---|---|
| Single focus | fail | The render panel stacks a 4-line stage sentence, 5 render tiles (193 px), a 7-line plan title (142 px), then the frame. The inspector beside it shows a lost draft's log. |
| Chunking | fail | The plan panel lists 30 key hints in one paragraph. |
| Grouping | pass | Rail sections, inspector sections, one box per request or round. |
| Visual hierarchy | pass | The frame is the largest saturated object; A and B are 200 px wide. The inspector's order belongs to priority issue 3 below. |
| One thing at a time | pass | One stage per panel. |
| Minimal choices | pass | The viewer head holds 4 controls (fit, 1:1, 2×, mp4); each stage view has at most one primary button. |
| Working memory | fail | The grade form shows neither the page nor the candidates, which open in another tab. A registration rerun needs the last windows recalled from the panel text. |
| Progressive disclosure | pass | Hints open on hover or focus; each stage opens its own panel. |

### Priority issues

1. **[P1] The refresh takes the keyboard focus.** Where: the strip and the rail. `openJob(id,true)` calls `renderStrip()` on every refresh, and `loadJobs()` rebuilds `#jobs`. Why: a Tab-focused import tile fell to `<body>` after 2977 ms, and a focused rail row within 6.5 s. PRODUCT.md requires keyboard scrubbing and visible focus; DESIGN.md makes the strip arrow-steppable. Two more keyboard faults: ArrowRight on a tile also steps the frame (f 5 to f 6), and Shift+ArrowRight on the focused scrubber steps 1, not 10. Fix (JS): rebuild the strip only when `JSON.stringify(v.stages)` changes, then restore the focus by `data-stage`; treat `#jobs` the same way by `data-id`. Add `e.stopPropagation()` to the tile's `onkeydown`. In the document key handler, skip inputs except the scrubber, `e.target.matches('input:not(#scrub),textarea,select')`; its `preventDefault()` then stops the native one-frame step. Command: /impeccable harden.

2. **[P1] The inspector shows defaults, not the last run's knobs.** Where: the knob rows of every script stage. Registration shows ref −1, depth_maps off and an empty lock_window. Its latest record (`20261104-224913_registration`) ran with ref 0, depth maps on and `422,371,582,441;248,478,318,618;757,458,827,538`. Why: "rerun registration" is the primary button. One click replaces the locked prep, moves the old one to `in/angel_prev_<stamp>` and leaves both full renders stale. `S.knobs` is also one object for all jobs: "zz_probe", typed as the render name in the test job, showed marked changed in the adopted job. Fix (JS): key the state by job and stage, and seed it from the record: `const K=(S.knobs[v.job.id+'/'+s.name] ||= {}); const val = K[k.key] ?? latest?.knobs?.[k.key] ?? k.default;`. Mark "changed from the last run" apart from "changed from default". Label the button "rerun with the last knobs" or "run with 2 changes". Command: /impeccable harden, then /impeccable clarify for the label.

3. **[P1] The frame and its axis do not share the screen.** Where: the render panel on a2 at 2560×1440. The frame box spans y 779–1459, the scrubber starts at y 1507 and the plot ends at y 1706. The frame shows at 523 × 678 px of its 1366 × 1770 source (38 %) inside a 1736 px wide box. The Measures section, which holds the gating measures, starts 1485 px down an inspector 1440 px tall. Why: `.frame{height:calc(100vh - 760px)}` budgets 760 px for everything else, but 779 px sits above the box, and 247 px of axis (y 1459 to 1706) plus 24 px of padding below it. The viewer head alone is 145 px, because the plan title wraps to 7 lines. Fix (CSS/JS): clamp the title to one line (`.panel .head .muted{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}`) and put the full text in its hint. Move the stage sentence into its `?`, and the 5 render tiles into the 200 px column under A and B. Then size the box in JS, `Math.max(380, innerHeight - box.getBoundingClientRect().top - 271)`: about 830 px, or 47 % scale, with the axis on screen (an estimate from the measured heights). Show Measures first in the inspector while a render is selected. Command: /impeccable layout.

4. **[P2] A stage chip shows its last record, not its contents.** Where: the test job's render tile, panel header and rail chip all read "lost" in red, after the a2l draft died in the acceptance drive's restart test. Two full renders and three drafts are done. The readers stage reads "stale", "Not run." and "done" in its three places. Why: the strip exists to show where the job stands, and 2 of its 8 tiles answer wrongly. Fix (JS and server): in `stage_views`, set the render chip from the candidates ("2 full · 3 drafts") and show the last attempt as a second chip ("last attempt lost: a2l"). Make the readers panel say "stale: read on the previous prep" and link `in/angel_prev_…/readers`. Command: /impeccable clarify.

5. **[P2] The 1440 and 1280 layouts break.** Where: at 1440×900 the 8 tiles shrink to 96 px, 3 state chips cut to "do…", "st…" and "do…", and the frame box starts at y 1027, below the 900 px viewport. At 1280×800 the media query splits the window into rows of 399.5 and 400.5 px. Why: DESIGN.md targets "1440 px and wider" and puts the inspector under the panel below 1280 px. Fix (CSS): `.strip{grid-template-columns:repeat(8,minmax(120px,1fr));overflow-x:auto}` and `.stage .ft .chip{overflow:visible}`. Inside `@media (max-width:1280px)`, add `.shell{height:auto;grid-template-rows:100vh auto}`. Command: /impeccable adapt.

6. **[P2] The scrubber and the plot use two x scales.** Where: the axis under the viewer. The range track spans x 264–2216 (1952 px), while the plot maps f 0 to x 304 and f 49 to x 2206 (1902 px). Why: STUDIO.md section 1 makes the shared frame axis the signature, with the scrubber and every per-frame plot on one x. The thumb and the cursor line drift apart toward f 0 (crit_axis_focus.jpg). Fix (CSS): inset the track to the plot's span, for example `#scrub{margin-left:32px;width:calc(100% - 34px)}` for a 16 px thumb (the thumb width is UNVERIFIED). Drawing the thumb inside the SVG also works. Command: /impeccable layout.

Minor issues:

| where | why | fix | command |
|---|---|---|---|
| `.cand .dt`, `.stage .dt`, `#frameTag .chip` | Numbers such as "step max 4.006 · seam 1.312" and "467 inl." compute to system-ui without tabular numerals (DESIGN.md's Data Mono Rule: numbers, hashes and paths in the monospace) | Wrap each number in `<span class="data">` | /impeccable typeset |
| the step plot and the Measures table | The y ticks (0.0, 2.0, 4.1) carry no unit; "4.091 at f 43 levels" puts the unit after the frame index | Label the axis "levels"; print "4.091 levels at f 43" | /impeccable clarify |
| `#pop .k` | The hint popover's key line is amber, a label and not an action (DESIGN.md's One Amber Rule) | `#pop .k{color:var(--text)}` | /impeccable polish |
| `alertMsg()` | The new-job refusal lands in the work area at (264, 294); its form sits in the rail at (0, 467) | Write the message under `#newForm` | /impeccable clarify |
| the page panel | `.msg.bad` (1 px border, 3 px radius) sits inside `.box`, the one card in a card across 8 stage views | `.box .msg{border:0;padding:0;color:var(--failed)}` | /impeccable polish |
| `schedulePoll()` | Two injected fetch failures left the page unchanged | A rail chip "server unreachable, retrying", set in the catch | /impeccable harden |
| the adopted job | Five candidates read "unjudged" after two skeptic passes before the studio (commit a13cc88); `verdicts()` reads only `answers/skeptic_*.json` | A chip "judged before the studio" that links `agents/` | /impeccable clarify |
| the rail | All three job rows read "angel loop"; only the id line differs | Put the source folder or "adopted" on the first line | /impeccable clarify |
| the viewer's 1:1 and 2× | Both open at the frame's top-left corner; at 2× the box shows the ceiling, and the faces need a long scroll (crit_render_2x.jpg) | After a mode switch, scroll to the frame's centre: `box.scrollTo((box.scrollWidth-box.clientWidth)/2,(box.scrollHeight-box.clientHeight)/2)` | /impeccable polish |
| the test job's page (fix table row 5) | `in/angel/keys.jpg` is missing since the rerun under the old code, so the page shows a broken image and logs a 404 on each opening | Copy `in/angel_prev_20261104-224918/keys.jpg` (37,958 bytes) into `in/angel/`, or rebuild the page | /impeccable harden |
| the import panel's first sentence (row 10a) | studio.py:149 says "under in/raw"; the links sit under raw/angel/ | Change the sentence to "under raw/<seq>/" | /impeccable clarify |
| `save_plan()` (row 13) | studio.py:1002 writes `"author": "owner"` on every save, the session's saves included | Add an author choice (owner or session) to the save form and record it | /impeccable harden |

### Keep

1. The review gates on screen. The page panel names each unjudged candidate and the way out before any click, and the round gate's refusal says "save his words, or mark the round ungraded". PRODUCT.md's first principle is visible.
2. The viewer's exact modes. 1:1 shows 1366 px and 2× shows 2732 px pixelated, with both ends of the frame reachable. The active mode is drawn pressed, the frame tag names the frame (photo, or generated with its t), playback runs at 25 fps, and the focus ring sits on the thumb.
3. The strip and the hints: 8 tiles with thumbnails, word chips and the violet tick, one amber button per stage view, and 85 hint keys with text.

### What breaks at 1440×900 and 1280×800

- 1440×900 (crit_1440_render.jpg): the shell keeps 240 + 880 + 320 px. The 8 tiles shrink to 96 px; 5 detail lines and 3 state chips truncate ("do…", "st…", "do…"), and "5.0 s" wraps. The renders wrap to two rows (386 px). The frame box starts at y 1027, below the 900 px viewport, at 616 × 380 px; the image is 292 × 378 (21 %). The scrubber sits at y 1680. The inspector keeps its 320 px.
- 1280×800 (crit_1280_render.jpg): the media query fires, and the shell becomes two rows of 399.5 and 400.5 px. The rail (785 px of content) and the work area (1848 px) share the top 400 px. The inspector spans the full 1280 px in the bottom 400 px (2060 px of content). The frame box sits at y 973 inside the 400 px work window.

### Detector

The engine's binary (version 0.1.18+engine, 62 rules) ran the brief's command from the repository root. It found 0 findings at 2560×1440 and 0 at 1440×900, exit 0 both times. Runs with `--json` and with advisories returned `[]` at both viewports. The acceptance drive's one finding, the placeholder at 3.9:1, is gone. The detector caught none of the issues above: they live in behaviour and layout, outside its rules. By the page's boot code, each scan sees one state: the test job's render panel on its newest full render, a1. This critique's screenshots show a2, selected by hand. The runs wrote no file under the repository (checked with `find -newer` after them).

### Craft floor

| ban | verdict | evidence |
|---|---|---|
| a kicker above a heading | kept | Each panel and section starts at its heading; small labels sit above inputs only. |
| section numbers | kept | 0 found. |
| nested cards | broken once | `.msg.bad` inside `.box` on the page panel; the other 7 stage views nest nothing. |
| a sparkline without axes | kept | The step plot has y ticks, 17 frame ticks, a baseline and the dashed 0.3 bar. |
| a coloured side border above 2 px | kept | Only the current job row's 2 px amber edge, the one DESIGN.md allows. |
| an emoji or glyph as an icon | kept, with a note | 0 emoji. The hint is an ASCII "?" in a bordered box, as STUDIO.md section 3 specifies. |
| gradient text | kept | 0 elements with `background-clip: text`. |
| every number in the monospace with its unit | broken | Render and stage tile details and the frame tag compute to system-ui; the plot's y ticks carry no unit. |
| every state as a word chip | kept at 2560, broken at 1440 | At 1440 three chips cut to "do…" and "st…". The violet tick is a 10 px square with only a `title`. |
| one primary control per panel | kept | 8 of 8 stage views hold at most one amber button. |
| the focus ring on keyboard focus | kept, briefly | A 2 px amber outline at 2 px offset on a tile and on the scrubber's thumb; the refresh removes a focused tile after 2977 ms. |
| amber only for the action, the selection and the running state | broken once | The hint popover's key line. |
| placeholder contrast of 4.5:1 or more | kept | 5.69:1. |

### Screenshots

All in `benchmarks/runs/2026-11-04/studio/shots/`, JPEG at CSS scale, 2560×1440 unless marked.
- The render panel on a2: crit_render_fit.jpg, crit_render_1to1.jpg, crit_render_2x.jpg. The inspector scrolled to Measures: crit_inspector_render.jpg. The axis with the scrubber focused (element shot): crit_axis_focus.jpg.
- The test job's panels: crit_import.jpg, crit_registration.jpg, crit_readers.jpg, crit_plan.jpg (angel_a2 loaded, unsaved), crit_skeptic.jpg, crit_page.jpg, crit_grades_test.jpg.
- The adopted job's graded round: crit_grades_adopted.jpg. The rail with a hint open: crit_rail_hint.jpg. The empty-folder refusal: crit_error_newjob.jpg.
- Smaller viewports: crit_1440_render.jpg (1440×900), crit_1280_render.jpg (1280×800).

### Confidence: 80%

Every number comes from the DOM, a command or a cited line of studio.py. The doubt: rows 11, 12 and 14 rest on code alone, row 10c on a simulated API reply, and the scores on one reviewer's judgement.

### Gaps

- One context ran both assessments. Assessment A was saved to `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/assessment_A.txt` (session scratch, temporary) before the detector ran. The in-page overlay was skipped, because the brief barred a second server.
- Left undriven: a running stage, a failed or refused stage, cancel, adoption, and a skeptic answer with its verdict chips. The brief barred renders, registrations, page builds and grade saves.
- Another actor emptied the test job's `requests/` folder at 23:03, before my skeptic screenshot. The waiting state appears in the acceptance drive's acc_12_request.jpg.
- Playback at 25 fps was not judged by eye, and the scrubber thumb's width was not measured.
- The detector saw one state per viewport, the test job's render panel on a1.
- Skipped from the impeccable method: the snapshot under `.impeccable/critique/` (the brief allows writes only to this report and the shots) and the closing questions to the owner, which the parent session asks.
- The no-slop pass ran: the checker (0 blocks, 0 sentences over 40 words) and a cold read by a context-free subagent. I fixed the terms it could not resolve, the sentences it re-read and the four contradictions it found.
- My probes: two refused `POST /api/jobs` with an empty folder (HTTP 400, nothing written), one knob typed and cleared, frames stepped, and a plan loaded into the editor without a save. The Playwright MCP writes its own logs to `.playwright-mcp/` (gitignored).
