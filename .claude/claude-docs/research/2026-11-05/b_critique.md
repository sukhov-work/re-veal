<!-- provenance: copied verbatim on 2026-11-06 from benchmarks/runs/2026-11-05/studio/agents/b_critique.md (gitignored), the critique of phase B's screens by an Opus 5.5 subagent with impeccable's method and detector (a DEGRADED single-context run): 26 of 40, the detector 0 on the URL scans and 2 line-length findings by CDP, 1 P1, 9 P2, 17 minor, 0 hint misses over 277 keys; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-ran make qa, make test and the acceptance drives on the final tree before the commit -->

Score 26/40 (A2 28, A1 26). Detector: 0 findings in the 3 URL scans; 2 findings, both line-length on the director plan panel, at each of 3 viewports in the scans of 6 chosen screens. DEGRADED: single-context (one subagent ran the design review and the detector; the review was saved at 21:47:24, the first scan ran at 21:47:55).

<!-- reader: the main thread of the 2026-11-05 studio session and the phase B fix-round builder, both cold. shape: report. Written 2026-11-05 from 21:10 to 22:11 EET by the critic subagent (Opus 5.5), read-only on studio/. Source: my own server on 127.0.0.1:8394 (reveal-studio 0.2.0). Browser: my own headless Chrome 156 on DevTools port 9394, the DOM read by script. Code read: studio/src/reveal_studio/web/ (director.js, pair.js and the shared scripts), runner/process.py, views/page.py, jobs/rounds.py. -->

# Critique of the studio's phase B screens: 26/40, one major issue

**Score: 26/40 (Acceptable, the 20–27 band).** The A2 page scored 28 before its fix round, A1 26. At 2560×1440 the new flows draw the frame under judgement at 51 to 57 % of its source's height (A2's render: 27 %).

Summary:
- **One major issue (P1).** The director's render stage holds its knobs in two places that disagree. Each place has its own amber run button: a 480 px draft with no `--set` key, or a full 1920 px render with the last run's two keys.
- **Nine issues he would notice (P2).** The top three: the director's measures are cut on the plots and in the inspector; checkboxes show no focus ring; 10 of 14 new action buttons fire twice while their request runs.
- **Hints:** 0 misses over 277 keys. **Console:** 0 exceptions from the page's scripts; the only failed requests were the 404s of P2 row 6. **Contrast:** 5.19:1 or more for every new colour pair.
- **Asked of the main thread:** a fix round on the P1 and the nine P2 rows; a choice of the P1's direction (the options are below); one question for the owner (the director's measure names).

## Names used below

| Name | Meaning |
|---|---|
| the owner, he | The repo's one user, who grades the clips by eye. |
| the main thread, the fix-round builder | The session that launched this critic; the subagent that will fix the findings. |
| A1, A2, phase B | The studio's build phases (`STUDIO.md` §9). A2's critique (`a2_critique.md`, 28/40) is this report's shape. Phase B adds the pair and director flows. |
| the pair flow, the director flow, the loop flow | A transition between two photos (`transitions.py`); a planned clip from a pair (`director_render.py`); a looped clip from stills (`loop_seq.py`). |
| the director job, the pair job, the loop job | `director_mismatch_3_20261105-202914`, `pair_mismatch_3_20261105-203244`, `loop_angel_20261105-202715`: the newest of each flow when I started. The acceptance driver made newer jobs during my run. |
| the driver, the review, my design review | Two other subagents of this step of phase B: the acceptance driver (its report `b_acceptance.md` was not written when I finished) and a read-only review by a Fable model (`b_review.md`). My design review is `b_critique/review_A.md`. |
| impeccable, the detector, DEGRADED | The design skill under `.claude/skills/impeccable/`; its scanner `impeccable detect` (0.1.18+engine). Its critique wants two separate subagents; a run in one context says DEGRADED on its first line. |
| URL scan, CDP scan | The detector loading the page itself (it opens the newest job), or reading a screen I set up in my Chrome through the DevTools protocol (`--cdp 9394`). |
| P1, P2, minor | impeccable's severities as the A2 critique used them: P1 he would stumble, P2 he would notice, minor the rest. "P2 row 3" is row 3 of the P2 table. |
| a hint, "?" | The popover a control or a "?" button opens, from the hints table; a miss is a key with no row. |
| page-held | A request answered inside the page by a promise that never settles: the button's handler runs and nothing reaches the server. |
| the poll | The page's refresh of the open job: every 5 s, every 1 s while one of its stages runs. |
| the set dict, a `--set` key | The director render's renderer overrides, one `--set key=JSON` each; the plan panel holds them. |
| the timeline, a bar | The director plan panel's beats in clip time (t from 0 to 1); a bar is one beat's window. |
| a round, the review gate | One built review page and his grade on it; the gate refuses a page while a listed render is unjudged, unless overridden. |
| the rail, the strip, a panel, the inspector | The page's regions (`STUDIO.md` §3): the left column of jobs and new-job forms; the row of stage tiles; the selected stage's area under the strip; the right column with the stage's knobs, measures and latest record. |
| a knob, the side column | One input of a stage: a script flag or a renderer key. The side column is the viewer's column beside the frame: the render's name, the comparison modes, the sources and the list of renders. |
| a plan, a concept, frozen plans, the planner, the resolve | A director plan is one JSON file per photo pair; a concept is one of its alternative clips (c1); frozen plans are the plan files under `scripts/research/plans/`, which the studio never writes; the planner is the model that wrote a plan's idea and risk; the resolve stage builds the scene without rendering frames. |
| the workbench | `scripts/research/director_ui.py`, the director's earlier page, which the studio replaces. |
| the skeptic, a picks file | A request file the Claude Code session answers with a verdict per full render; his grade per clip in the workbench's shape (`picks/<flow>_picks_<stamp>.json`). |
| a2, a2copy | The angel loop's accepted render (md5 c302623f…); a2copy is the loop job's copy of it. |
| the build routine, the prose test, the handover | `.claude/skills/reveal/references/studio.md`, the steps a studio change follows; `studio/tests/test_prose.py`, which runs the checker over the hints with a 60-word limit; the session's note to the next session, which carries questions for the owner. |
| the quality basket, the in-page overlay | The quality block of `transitions.py`'s report (warping error, flicker, the endpoints), drawn with a bar and a reading per row; impeccable's script injected into a tab to outline its findings. |
| file paths | `*.js` names are under `studio/src/reveal_studio/web/js/`, `*.css` under `web/css/`; `views/`, `jobs/`, `runner/` and `registry/` are under `studio/src/reveal_studio/`. |
| backlog rows T88, T106, T107 | Open rows of `references/tracked-backlog.md`: a second server re-attaching another server's records; A2's hardening rows (buttons clickable twice, the wipe drag); the 1 s redraw while a stage runs. |

## The detector

The three URL scans, verbatim, run from `studio/` at 21:47:55. Each printed nothing in text mode and `[]` with `--json`; each exited 0.

```
detect --no-advisory --viewport 2560x1440 http://127.0.0.1:8394/   -> (no output), exit 0; --json: []
detect --no-advisory --viewport 1440x900 http://127.0.0.1:8394/    -> (no output), exit 0; --json: []
detect --no-advisory --viewport 1280x800 http://127.0.0.1:8394/    -> (no output), exit 0; --json: []
```

A URL scan opens the newest job. At 21:47:55 that was the driver's running loop job `loop_angel_20261105-214751`, so the URL scans saw a loop screen, not a phase B one. The scans of chosen screens ran `detect --json --no-advisory --cdp 9394 --target 127.0.0.1:8394` while my session held the viewport:

| Screen | 2560×1440 | 1440×900 | 1280×800 |
|---|---|---|---|
| director plan panel, the director job | 2: `line-length` ×2 | 2: the same | 2: the same |
| director render panel with its plots | 0 | 0 | 0 |
| pair relation panel, the pair job | 0 | 0 | 0 |
| pair render panel | 0 | 0 | 0 |
| the rail with the three new-job forms open | 0 | 0 | 0 |
| the graph view of the director job | 0 | 0 | 0 |

The rail's buttons open at most two forms at once (minor row 1), so the loop's form was shown by setting its style. The findings, verbatim, each checked on the screen:
- `line-length` at `p.d-prose:nth-of-type(3)`: "~105 chars on 5 of 6 rendered lines (aim for <80)". This is the planner's Idea paragraph. `.d-prose{max-width:75ch}` counts in widths of the digit 0, wider than an average letter. Real. Fix: `director.css` `.d-prose{max-width:56ch}` (75ch measured 105 characters, so 56ch gives about 78).
- `line-length` at `p.d-prose.muted`: "~86 chars on 2 of 12 rendered lines (aim for <80)". The Risk paragraph, the same rule. Real.

The bar the build routine sets is 0 anti-patterns. The URL scans meet it; the director plan panel does not, at every viewport. My design review had placed the same two paragraphs above the timeline (P2 row 7) but had not measured their line length; the detector added that. The detector does not test what the P1 and the nine P2 rows describe. No `.impeccable/` folder exists after the scans.

## Scores

The rubric is impeccable's heuristics scoring guide (`.claude/skills/impeccable/reference/critique.md`), as A1 and A2 used it. Each row quotes the guide's line for the score given.

| # | Heuristic | A1 | A2 | B | The guide's line | Why (where) |
|---|---|---|---|---|---|---|
| 1 | Visibility of system status | 2 | 3 | 3 | "Good; most operations give clear feedback, minor gaps" | The strip's chips, "unchanged from …", the rail's "render · two · 6 s". Gaps: 10 buttons show no "working…" (P2 row 3); the plan tile reads "none"; the poll's late answer (P2 row 6). |
| 2 | Match between system and real world | 3 | 3 | 2 | "Mixed; some plain language, some jargon leaks through" | His words for the flow (pair, relation, class, round, best, acceptable). Leaks: 16 director measures named by their file keys, 12 top-level `--set` rows citing script lines, "Exit 2 with a FAILED: line", "(backlog T108)". |
| 3 | User control and freedom | 3 | 3 | 3 | "Good control; users can exit and undo most actions" | Unticking a `--set` key resets it; the graph's rerun asks first; cancel. Gaps: no undo in the director's editor; "clear all knobs" acts in one click (P2 row 8). |
| 4 | Consistency and standards | 2 | 2 | 2 | "Partially consistent; main flows match, details diverge" | The P1; the shared verdict stage has a run button in the pair's panel only; the two grade forms differ (P2 row 5); source B defaults differ. |
| 5 | Error prevention | 2 | 3 | 2 | "Partial prevention; common errors caught, edge cases slip" | The command preview equals the record's command. Against: the P1, which sits on the render action itself; a doubled page build opens two rounds (P2 row 3). |
| 6 | Recognition rather than recall | 3 | 3 | 3 | "Good recognition; most things discoverable, few memory demands" | 277 hint keys resolve; the knob map gives each knob's plan name and `--set` key; each `--set` row's condition. Gap: the timeline counts t from 0 to 1, the scrubber counts frames. |
| 7 | Flexibility and efficiency of use | 2 | 3 | 3 | "Good accelerators; keyboard nav, some customization" | Bars by arrows with the focus kept; rows by Enter and Space. Costs: 137 Tab stops on the director import (P2 row 9); no start-only move on a bar. |
| 8 | Aesthetic and minimalist design | 3 | 2 | 2 | "Some clutter; main content clear, periphery noisy" | The frame leads at 2560. The director plan screen is 2,905 px tall at 2560, with its timeline under the planner's prose; its inspector is empty; 85 "?" on that panel with its sections open. |
| 9 | Help users recognize, diagnose and recover from errors | 3 | 3 | 3 | "Clear with suggestions; identifies problem and offers next steps" | Five of six refused new-job requests named the problem and the fix; the sixth names the allowed characters (clarify). By the code, a doubled draft shows a red 409 after a good start. |
| 10 | Help and documentation | 3 | 3 | 3 | "Good documentation; searchable, mostly task-focused" | 0 hint misses; 5 hint and stage sentences over 40 words; 3 of 18 hints read state times the records contradict; four unlabelled "?" in a row under the director plots. |
| | **Total** | **26** | **28** | **26** | "20–27 Acceptable: significant improvements needed before users are happy" | |

## P1

| # | Screen | What I measured | Rule broken | Fix (file, change) |
|---|---|---|---|---|
| 1 | Director render, every viewport; the resolve stage's two knob sets | The panel prints "No --set key: the plan as written." Its amber "render a 480 draft" posts `{"draft":480,…,"set":{}}`. The inspector's `set` field holds the last run's `{"parallax_push":2,"pane_becomes_view.window":[0.35,0.97]}` with `draft` 0. Its amber "rerun render with the last run's knobs" posts a full 1920 px render with those two keys. Both requests were page-held (`drive/results.txt`). On the resolve stage the panel's plan, concept and long side sit beside the inspector's plan, concept, max_long and set, each with an amber button; they agreed in this job, and nothing keeps them in step. Shot `critB_P1_two_render_paths_2560.png`. | `DESIGN.md` Buttons: "one primary per panel". The shared inspector pre-fills the last run's knobs, A2's fix for the loop; the director adds a second knob store in its panel, and the two disagree on one screen. `b_design.md` decision 2 names the same risk: "the pre-fill is what hid two knobs in the workbench's acceptance". `PRODUCT.md` principle 2: every knob rides the plan or the record. | Option (a): for the director's resolve and render only (the loop's inspector keeps A2's pre-fill), the inspector shows the knobs the panel will send, read-only (the plan panel's set dict and the command preview), with no run button. Option (b): the inspector's rows write the plan panel's state and the panel's run row goes. Either way one amber button per screen. Under (a) the panel's "render a 480 draft" and "render full" stay the run buttons. `FLOW_UI` is the per-flow table in `core.js`; a hook there lets `inspector.js` draw the director's rows. |

## P2

Ranked by how often he would meet them.

| # | Screen | What I measured | Rule broken | Fix (file, change) |
|---|---|---|---|---|
| 1 | Director render, every viewport | The measures are cut in both places. Three of four plots draw their y labels left of the SVG (x −7 to −22 px): 17.6 px reads ".6 px", 8.32 % ".32 %", 100.00 % ".00 %". The inspector's measures table is 351 px wide in a 319 px column at 2560 and 1440: "past bar" shows "pa", and each bar's sentence loses its right half. Shots `critB_dir_render_plotaxis_2560.png`, `critB_dir_render_inspector_2560.png`. | `DESIGN.md` Measure plots: "SVG line plots with axes"; the Units Rule. | `director.js` `dPlot`: tick labels of at most 5 characters without the unit ("17.6", "100"), the unit in the plot's title; `xOf` keeps its 40 px gutter, so the axis still matches the scrubber. `dMeasures`: the verdict chip and the bar's sentence on a second row under the value. |
| 2 | Every checkbox: the director plan (26 "send" boxes, mute, solo), grades (16), import overlays (5); the pair skeptic (3), page (4) | A Tab-focused checkbox matches `:focus-visible` and draws no ring: `studio.css` sets `outline:none` on every focused input, and a checkbox draws no border. Shot `critB_dir_grades_checkbox_focus_2560.png`. | `PRODUCT.md` Accessibility: "visible focus are required for the review loop"; `DESIGN.md`: "a 2 px amber focus ring offset 2 px". | `studio.css`: `input[type=checkbox]:focus-visible,input[type=radio]:focus-visible{outline:2px solid var(--amber);outline-offset:2px}`. |
| 3 | Ten buttons: director resolve, "render a 480 draft", re-render, skeptic request, grade; pair skeptic request, page build, grade; the rail's two "create" | Each posted twice when pressed twice 80 ms apart with its first request page-held (`drive/results.txt`; a double press leaves no picture). Server effects, read in the code: a doubled pair page build opens two rounds on one page (`jobs/rounds.open_round` numbers rounds by count); a doubled grade writes a `_2` picks file. A doubled create or skeptic request fails or rewrites its file within one second (one-second names: `jobs/store._new_dir`, `jobs/grades.write_request`), and makes two jobs or two requests across a second. By the code, a doubled draft would get a red 409 ("… is still running into …") right after "started". Guarded: the inspector's rerun, the director's page build, the pair's relation and verdict. | `DESIGN.md` Buttons: "Loading: the label replaced by 'working…' and the button inert"; extends backlog row T106. | `core.js`: one helper that sets "working…" and `disabled` until the request settles, the director page build's pattern; used by `dPost`, `#skGo`, `#dgSave`, `#pairSkGo`, `#pairPgGo`, `.pairGrSave`, `.pairGrSkip`, `#pairGo`, `#dNewGo`. |
| 4 | Director render at 1440×900 and 1280×800 | At 1440 the frame box is 283 px tall (the loop's 419, the pair's 434; all 514 px wide), 19.4 % of the source. At 1280 the box sits on its 240 px floor and the scrubber is at y 825 in an 800 px window; the loop's and the pair's are at y 766. Above the viewer sit the panel's control row (66 px when it wraps), the `--set` line and the re-render button, about 150 px. Shots `critB_dir_render_1440.png`, `critB_dir_render_1280.png`. | `DESIGN.md` The viewer: "at 1280×800 the frame and its scrubber fit the window". | `director.js` `dRender`: move the control row, the `--set` line and the re-render button into the side column under "Renders" (with the P1's option (a)), or into the inspector (with option (b)). |
| 5 | Director grades | Round 2's page lists one render; the form lists four (the full render and three drafts), so the picks file would grade three drafts he never saw on that page. Only the last round shows, so round 1's grade text ("the drive") appears nowhere. The pair's form grades the round's own renders and lists every round. Shot `critB_dir_grades_2560.png`. | `STUDIO.md` §3: "The grade form keeps the shape of the picks file"; heuristic 4. | `director.js` `dGrades`: iterate the round's `candidates`; list every round, newest first, a graded round read-only, as `pairGrades` does. |
| 6 | Any job switch while a poll's request is out | A poll answer that lands after a job switch wins, and polling stops until the next click: the late answer re-arms the poll's timer for the old job, which then does nothing. Unprovoked, once, on my drive's own `openJob` call (the code path of a rail click): the director's render panel showed "no full render a2copy" over an empty viewer, and its inspector printed the loop's a2 md5 c302623f… as its own mp4 md5 (`critB_dir_graph_2560.png`). Reproduced with the loop's answer held 1.5 s inside the page: the rail marked the director job while the work area showed "angel · loop" and the loop's strip, and the viewer asked the loop job for the director's render (`critB_race_poll_after_switch_2560.png`, `drive/results.txt`). The driver's console log of 21:50 holds two 404s of the same kind: `render/full/morph1920` asked of director job 212526. | Heuristic 1; `PRODUCT.md` principle 2: the provenance printed belonged to another render. | `strip.js` `openJob`: after the job view arrives, return when `S.jid` is no longer `id`. `viewer.js` `loadRender`: drop an answer whose job or candidate changed while it was out. The code is shared, so the loop flow has the same window; job views answered in 0.03 s here, so it is narrow. |
| 7 | Director plan | The timeline, the panel's editing surface, starts at y 1065 at 2560 and at y 1079 at 1440 and 1280, below the window at both. Above it sit the plan's identity line and the planner's Idea and Risk paragraphs. The inspector beside it is empty. The command preview sits about 2,700 px down at 2560, near the panel's end. Shots `critB_dir_plan_2560.png`, `critB_dir_plan_1280.png`. | `STUDIO.md` §2, the plan stage: "the beats on a timeline (draggable windows …)" | `director.js` `dPlan`: the timeline and the knob table first, the command preview right under them; the Idea and Risk in a closed `<details>` below. |
| 8 | Director plan, the timeline by keyboard | The arrows move a whole window by 0.01; Shift with the arrows moves its end. A window's start cannot move alone. Home, End, Enter, Space and Cmd-Z do nothing. "clear all knobs" wipes every knob and the extra lines in one click, with no undo; the loop's editor keeps 300 undo steps. Shot `critB_dir_plan_2560.png`; the key log in `drive/results.txt`. | Heuristic 3; the loop editor's own keys (`plan.js`). | `director.js` `dBarKey`: Alt with the arrows moves the start by 0.01; Page Up and Page Down move the window by 0.1. An undo stack over the set dict (Cmd-Z, Shift-Cmd-Z). "clear all knobs" asks first. |
| 9 | Director import | Each of the 131 element rows (75 in A, 56 in B) is a Tab stop, so the panel holds 137 stops before the inspector. Shot `critB_dir_import_2560.png`; the walk in `drive/tabwalk_director_2560.json`. | Heuristic 7; A2's P2 row 11 took chips and "?" out of the Tab order for the same cost. | A roving tab order per table: one stop, up and down move, Enter toggles the matte, as `plan.js` does for the loop's bars. |

## Minor

| # | Screen | Quote or measured value | Fix (file, change) |
|---|---|---|---|
| 1 | Rail, the new-job forms | Opening the director's form, then the pair's, shows both with two amber "create" buttons. The loop's button closes the pair's form only. The director's form names no flow ("a fixture pair with a plan"). Shot `critB_rail_forms_order3_2560.png`. | `rail.js`: one `closeForms()` that every opener calls; a heading per form. |
| 2 | Director plan, a bar's drag | After a pointer cancel dispatched inside the page and a button-up away from the bar, the bar follows a hovering mouse: 0.36–0.98 to 0.38–1.00 with no button held, while the set dict stays empty (`drive/results.txt`). Backlog row T106 holds the wipe drag's same gap. | `dDragStart`: clear the drag and redraw on `pointercancel` and `lostpointercapture`. |
| 3 | Director skeptic | The skeptic form's brief field (what to look at) shows the angel loop's example as its placeholder: "the left mouth at mid-leg; the ring's top arc; the couch texture under the breath". | `panels.js` `panelSkeptic`: a placeholder per flow, or none (`PRODUCT.md` principle 4). |
| 4 | Pair page | "Every full render in name order (3), no flag.": the loop's `--variants` wording, while the pair's page runs no script. | `plan.js` `variantsControl`: "every full render, in name order (3)" for a page the studio writes. |
| 5 | Pair verdict | The refusal sentence shows three times: the panel head, a red box with a "refused" chip, then "Reveal refused this pair". | `pairVerdict`: keep the box only. |
| 6 | Director verdict | "Not run: it is optional, and the inspector runs it." The same shared stage has a run button in the pair's panel. | `dVerdict`: the pair's button and wording. |
| 7 | Pair viewer | Source B defaults to frame 0 (photo A), so a wipe at f 0 compares A with A; the director's defaults to its last frame. | `pair.js`: default B to the last frame. |
| 8 | Pair page, after a poll redraw | A title he emptied came back as "mismatch_3: round 2"; typed text in every other field survived (`restoreForms` skips an empty string). | `panels.js` `restoreForms`: restore an empty value the owner typed. |
| 9 | Director page | The review page's iframe has an inline `background:#fff`; the pair's uses the ground colour. | `dPage`: the pair's `.pair-frame` class. |
| 10 | Director render, under the plots | Four "?" in a row, each for a different plot, with no label between them. | `director.js` `dPlots`: one "?" in each plot's title line. |
| 11 | Director render rows | No generated share, while 55 of the full render's 90 frames are generated; the loop's rows print "N% generated". | `dCandRow`: the share from the frame tags. |
| 12 | Pair skeptic tile | "answered" in green over three unjudged renders: the answer held no verdict. | `views/pair.py`, the skeptic's tile: "answered, 0 verdicts" when the answer names none. |
| 13 | Director plan tile | The chip reads "none" while five frozen plans exist and the panel shows one. | `views/director.py`, the plan's tile: the chip "5 plans". |
| 14 | Rail rows, every flow | "1 candidates". | `rail.js`: the singular for 1. |
| 15 | Director plan, boolean `--set` rows | Two checkboxes with different meanings in one row: an unticked "send" box beside a ticked value box (`guard`, `front_per_element`, `plate`). | `director.js` `dSetInput`: a true or false select for a boolean value. |
| 16 | Pair render, empty | "render a draft (draft 480) or the full size (draft 0 at max_long 1920)": knob keys inside the sentence. | `pair.js` `pairRender`: "a 480 px draft, or the full size at 1920 px". |
| 17 | Director import, a selected element row | `director.css:26` draws a 2 px amber left edge (`box-shadow:inset 2px 0 0 var(--amber)`). `DESIGN.md` Navigation calls the rail's job row "the one place a coloured edge is allowed". | The raised face alone marks the row; or a dated amendment to `DESIGN.md`. |

## Hint misses

0 misses over 277 distinct hint keys, read with the sections open and the forms shown. The director's eight stages and its graph use 216 keys, the pair's seven stages and its graph 122; 62 keys appear in both, and 1 only in the rail's two new forms. Every visible chip maps to a key. Two controls open no hint, the two `<summary>` rows of the `--set` sections. A Tab stop inside a review page's iframe opens none either; those are the page's links, not studio controls.

## Keyboard pass

Tab stops per panel at 2560×1440, from a real Tab walk that starts at the strip's last tile:

| Flow | import | verdict | resolve or relation | plan | render | skeptic | page | grades |
|---|---|---|---|---|---|---|---|---|
| director | 137 | 0 | 6 | 66 | 28 (9 panel, 19 viewer) | 3 | 22 (12 inside the iframe) | 23 |
| pair | 0 | 1 | 12 (2 panel, 10 viewer) | — | 19 (viewer) | 5 | 26 (10 inside the iframe) | 0 (the round is graded) |

The director plan's 66 counts its two `--set` sections closed; opened, they add about 74.

| Check | Result |
|---|---|
| Chips and "?" out of the Tab order (the A2 ruling) | Pass: neither walk stopped on one. |
| Enter and Space on "render a 480 draft" (page-held) | Each posted; Space started no playback. |
| Space on a render row | Pass: it selected the row. |
| Timeline bars | Arrows and Shift work; the focus stays on the bar across each redraw and a forced poll (P2 row 8 lists what is missing). |
| Element rows | Pass: Enter and Space toggle the matte, the focus stays. |
| Wipe handle | Pass: → moved it 1 %, Shift+→ 10 % (50 to 61), the frame stayed at f 0, the ring showed. |
| Graph, "rerun from here" | Pass: one click turned it into "Rerun render with the inspector's knobs? …", 0 requests. |
| Focus ring | Fail for every checkbox (P2 row 2); every other stop showed the amber outline or border. |

## Copy pass

The checker (`slop-check.py --profile file --max-sentence 40`) ran over three files I extracted: the director screens (230 sentences), the pair screens (144) and the 277 hint texts (429 sentences).
- Five studio sentences run over 40 words: `region.viewer` 54, `region.axis` 48, `region.inspector` 45, the director skeptic stage's sentence 44 (`registry/director.py:142`), `control.render` 43. The prose test passes at 60, so `make qa` let them through.
- Three more come from the plan file itself (the planner's Idea and Risk: 111, 66 and 51 words); they are data, and the detector's `line-length` covers their measure.
- Codes in place of names: the director inspector names its 16 measures by their `info.json` keys (`motion_median_px`, `b_inside_first`, `residual_edge_max`, …), and three plot titles open with a key; the pair names its measures in words.
- More codes: 12 of the 28 top-level `--set` rows cite script lines in their condition or reason ("(director_render.py:674-676)"); 18 of all 112 rows do. The verdict stage's sentence says "Exit 2 with a FAILED: line is a refusal". Hints cite sources inline: `knob.render.warp` "(backlog T108)", `chip.within` and `chip.past bar` "(loops.md §6)", three pair knobs "(TRANSITIONS.md §3; --help gives no sentence)". The pair's decoded rows read "= n_frames 90" and "0..1 grey".
- The review's finding F6 already holds that the 150 condition and read-only texts of the `--set` table pass no prose test; the line citations are this report's addition.

## impeccable audit

| # | Dimension | Score | Key finding |
|---|---|---|---|
| 1 | Accessibility | 2 | Checkbox focus invisible (P2 row 2); 131 row stops (P2 row 9). Contrast passes: violet chip 5.70:1, amber value on the panel 7.70:1, photo A 6.74:1, photo B 7.84:1, faint 5.19:1, failed 5.48:1. The 12 px floor holds; only the 10 px "?" glyph sits below it, inside its 14 px button. |
| 2 | Performance | 3 | Job views answered in 0.03 s; the poll redraws a panel only when its data changed. Not measured: the 1 s redraws during a running director render (backlog row T107). |
| 3 | Theming | 3 | Tokens throughout; the director page iframe's inline `#fff`; plot colours repeated as script constants (A2's note). |
| 4 | Responsive design | 2 | P2 rows 4 and 7; the inspector's measures cut at 2560 and 1440; the graph at 1280 shows 4 of 7 nodes and scrolls (no detector finding). |
| 5 | Implementation integrity | 3 | A product of its own: the timeline in clip time with the generated beat outlined violet, the knob map in both name forms, the command preview equal to the record. The P1 is the integrity fault. |
| | **Total** | **13/20** | "10–13 Acceptable (significant work needed)" |

## impeccable harden (by hand)

| Case | Result | Fix |
|---|---|---|
| A button clickable twice while its request runs | 10 of 14 (P2 row 3). | P2 row 3. |
| A drag without `pointercancel` | The director's bars: minor row 2. The wipe drag: backlog row T106, unchanged. | Minor row 2. |
| A form the poll rewrites while typed into | Typed text survived a forced redraw in four cases: the pair page's footer and note; the director page's head, look and faults; a director knob typed without a change event; the director render's tag. An emptied title came back (minor row 8). | Minor row 8. |
| The poll's late answer | P2 row 6. | P2 row 6. |
| Long values | The inspector's measures table overflows (P2 row 1). The A photo's 32 element ids without a matte sit in one table cell. The inspector's plan select cuts "frozen:mismatch_". | Wrap; a title on the select. |
| Many renders | The director grade form grows by one box per draft (P2 row 5). | P2 row 5. |
| New-job refusals | Six bodies sent through the API, each answered 400 or 404, five naming the problem and the fix; the job folder count stayed 40. | None. |
| Empty states | Each names the next action; two use knob keys (minor row 16). | Minor row 16. |
| Server down | Not re-tested; `core.js` `api()` still names the server and `reveal-studio serve`. | None. |

## impeccable clarify (by hand)

The clarify rows are the copy pass above, minor rows 3 to 6, 12, 13 and 16, and P2 row 5.

I read 18 hints of the controls I drove against what they did and what the records hold (`drive/results.txt`). Three state times the records contradict:
- `control.director_full` says "33 to 66 s at 1920 px"; this job's full render took 147.7 s, and the builder measured 147.1 and 152.6 s.
- `control.director_draft` says "about 10 to 14 s for 90 frames"; this job's three drafts took 14.8 to 18.0 s.
- `control.pair_verdict_run` says "2 to 16 s per pair"; this pair's refusal took 17.5 s.

Two leave out part of what the control does. `control.director_timeline` describes the drag and not the arrow keys. `control.director_clear` does not say it also empties the extra `--set` lines. The other 13 match what I saw or read in the code.

One more: the director job's refusal for an empty pair reads "a director job names its pair: letters, digits, dash and underscore". It describes the allowed characters, not the missing choice; "choose a pair" would say it.

## Cognitive load and personas

4 of 8 checklist items fail, which the guide calls high load (A2: 4).

| Item | Verdict | Where |
|---|---|---|
| Single focus | fail | The director plan: the timeline under the planner's prose and 66 to 140 controls. |
| Chunking | fail | 28 top-level `--set` rows in one table. |
| Grouping | pass | Panels, `<details>` sections, the inspector's sections. |
| Visual hierarchy | pass at 2560 | The frame is the largest object on both render screens; at 1440 the director's is not (P2 row 4). |
| One thing at a time | pass | One stage per panel. |
| Minimal choices | fail | The director render: two amber buttons over two knob sets (the P1). |
| Working memory | fail | The timeline in t, the scrubber in frames (t 0.35 is f 31 of 90); the grade form against the page (P2 row 5). |
| Progressive disclosure | pass | The `--set` sections collapse; hints on demand. |

Personas. A power user (impeccable's "Alex") meets two run buttons with different knobs, 137 Tab stops on the import and no undo in the director's editor. A keyboard user ("Sam") cannot see which checkbox holds the focus. The owner at his 27-inch display reads ".32 %" for 8.32 % on the residual-edge plot and "pa" for "past bar" in the inspector.

## Keep

1. The command preview. For the 480 px draft tagged "two", it matches the record's command in every argument after the interpreter, the `--set` order and the JSON form included. The interpreter's path is relative in the preview and absolute in the record.
2. The `--set` table. Each key shows its default for this concept and the condition under which the renderer reads it. Read-only rows give their reason, and the knob map shows both name forms.
3. The relation panel: the class chip, the facts with units, the strip, "unchanged from …" with both md5s, and a bar and a reading for each row of the quality basket.
4. The frame and the violet. At 2560 the frame takes 51.3 % (director) and 56.7 % (pair) of its source. A generated frame carries the "generated t 0.663" tag, the violet outline round the picture and the band under the plots; the keyframed beat's bar is outlined violet.
5. The refusals: five of the six new-job errors I sent name the problem and its fix.

## Asked of the main thread

These are the critique's closing questions; the brief keeps them in this report.
1. Run a fix round on the P1, the nine P2 rows and the detector's line-length fix before the owner sees phase B; the minor rows are the builder's choice or backlog rows. The build routine (step 6) calls for a fix round after a critique of more than a few items.
2. Choose the P1's direction. Option (a): the inspector shows the director's next-render knobs read-only and loses its run button. Option (b): the inspector's rows write the plan panel's state and the panel's run row goes. I would take (a): the panel's run buttons already read the plan panel's knobs, and (a) leaves one amber button.
3. For the owner, through the handover: should the director's 16 measures read as words with the file key in parentheses, or keep the keys as the renderer writes them?

Outside the critique: seven job folders hold a `verdict.part/jobs/<id>/` left by a refused verdict (`reveal.py align` writes its work folder under `--out`), and the review does not list it. The Runner could remove a refused record's `.part` folder (`runner/process.py`); the main thread decides between the fix round and a backlog row.

## Gaps

- One context ran both halves (DEGRADED). The design review, `b_critique/review_A.md`, was saved at 21:47:24, before the detector's first run at 21:47:55. The in-page overlay did not run. I wrote no snapshot under `.impeccable/critique/`, since the brief allows only this report and its evidence.
- I started no stage and no render. My writes are six refused new-job requests (0 folders) and the studio's own frame caches of the two renders I opened. Every page-held request, drawn state and pointer event lived in my tab and went with its reload.
- Not seen live in my tab: a running pair or director stage (the driver's showed in the rail as "render · two · 6 s"), the 1 s redraws of backlog row T107, playback at 30 fps by eye.
- The loop job was read on its render, plan and page panels only, as the A2 baseline.
- My server was a second server on the tree. It re-attached 35 running records of the driver's and the reviewer's jobs (backlog row T88 at runtime); every one ended done or refused, none lost.
- One Tab walk ran past the page's end into the headless browser's own interface, and a key then opened a chrome://settings tab. I closed it before any detector scan, which needs a single page.
- My server's log holds 18 "Connection reset by peer" tracebacks from requests a reload or the detector's browser abandoned; the page logged no error for them.
- The review page's own keyframe tile, inside the director page's iframe (written by `director_page.py`), was not judged for the violet mark.
- The appendix's JSON covers the screens, the Tab walks and the hints; the console output of the page-only drives is in `drive/results.txt`.
- `review_A.md` stays as saved before the detector, with three dated corrections appended. It holds 7 sentences over 40 words, which this report rewrites.
- The prose pass: the checker on this report, and one cold read by a subagent with no session context.

## Appendix: evidence and processes

`benchmarks/runs/2026-11-05/studio/agents/b_critique/` (gitignored, 32 MB):
- `shots/`: 51 PNGs at CSS scale, named `critB_<flow>_<stage>_<width>.png` with crops by name (the P1 and P2 shots are named in their rows).
- `detector/`: the three URL scans (text, JSON, stderr), 18 CDP scans as JSON, `cdp_summary.json`.
- `drive/`: 24 Node scripts over a DevTools client that attaches to the running Chrome (`ccdp.mjs`), their JSON (`screens_*`, `tabwalk_*`, `hints_audit.json`) and `results.txt`, the console output of the page-only drives.
- `copy/`: the extracted sentences of each flow and the hints, with the checker's output beside each.
- `logs/server_8394.log`; `review_A.md`, the design review saved before the detector.

My processes: the server `reveal-studio serve --port 8394` (pid 23063) under `caffeinate -i -s` (pid 23066), and headless Chrome on DevTools 9394 (pid 23214). All three stopped at 21:54:12; ports 8394 and 9394 no longer listen. `scripts/session_sweep.sh` then listed 10 processes, all the driver's (its server on 8417, its Chrome on 9417, its pytest acceptance run and children). I left them running.
