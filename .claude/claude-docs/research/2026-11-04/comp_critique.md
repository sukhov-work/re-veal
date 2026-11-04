<!-- Provenance: written by an Opus 5.5 subagent (impeccable's critique run by hand, the engine not installed, on the comp of the studio's render stage) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/comp_critique.md (sha256 61ae005fb6db4cda) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Score 24/40; the one change before the build: one large viewer for the frame under judgement with playback, A and B small; the knob table with ranges, defaults and descriptions; the measures with limits and verdict chips; the missing states; a fluid layout. Keep: the shared frame axis, the stage strip, the violet mark. STUDIO.md §12 and DESIGN.md record what changed. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

⚠️ DEGRADED: single-context (run by hand inside one sub-agent; the impeccable engine is not installed, so neither the detector scan nor the overlay ran)

## Findings: comp critique (impeccable critique by hand)

<!-- reader: the parent session and the build session (cold); shape: report; written 2026-11-04 by the comp-critique agent from comp/index.html, my screenshots crit_2560.png, crit_1440.png and crit_1440_noautofocus.png (all in this folder), DESIGN.md, PRODUCT.md, STUDIO.md §1, §3, §6 and §12, comp_build.md and the two incumbent screenshots -->

Verdict: 24/40 (Acceptable). The comp is a sound light table with one strong idea, the shared frame axis. It misses its main job: the frame under judgement is not the dominant thing on screen. Fix the viewer before the build. Keep the shared frame axis, the stage strip and the violet rule for generated frames. The comp is a fixed 2560 × 1440 canvas, so at 1440 × 900 the inspector and the axis are cut off with no way to scroll to them.

### Scores

| # | Heuristic | Score | Reason (where on the screen) |
|---|---|---|---|
| 1 | Visibility of system status | 2 | The strip's chips and the rail's models and box read at a glance. Two things are not drawn at all: a running stage (progress number plus log lines, STUDIO §1) and the request state. The viewer's compare buttons are all unpressed, so the mode on screen is unknown. The gating measures carry no verdict. |
| 2 | Match with the real world | 3 | It uses his words: k0, leg, hold, round, candidates, skeptic. Three phrases leak working shorthand: "467 inl" (registration tile), "dexp max" (inspector) and "5 candidates, unjudged after a fix: 0" (the angel row in the rail). |
| 3 | User control and freedom | 2 | It has "rerun from here", "mark f 25 as a fault" and "copy command". It has no cancel for a task and no way back to a knob's default. The incumbent workbench has "clear all knobs" and "reset to last round" (workbench_plan.png). |
| 4 | Consistency and standards | 3 | One visual world. Same state, two treatments: angel's chip is info blue, seasons' "ungraded" is grey. Models read "ready, offline" next to "ready". The rail shows port 8379, which §12 gives to the workbench; the studio's port is 8380. |
| 5 | Error prevention | 2 | The inspector's knobs show no range or default. "render full" is the primary action while "full" is already pressed and the render is done, so a click repeats a 56 s render. The review rules from §12 (the page refuses unjudged candidates) have no visible trace. |
| 6 | Recognition rather than recall | 3 | The keyboard hint sits by the scrubber, and provenance and the command are on screen. The workbench's per-knob "what" column is gone, so he must remember what "local box ease" does. |
| 7 | Flexibility and efficiency | 3 | Keyboard stepping, the copyable command and rerun from a stage are all here. There is no playback at 25 fps (§12 lens 2, C5), and no keyboard path along the strip is drawn. |
| 8 | Aesthetic and minimalist design | 3 | Quiet and dense as intended. The loudest element on screen is the scrubber's focus ring, an amber rectangle 1832 px wide, not a photograph. The "every 5th frame" row repeats what the scrubber already shows. |
| 9 | Error recognition and recovery | 1 | No failed, refused, lost or error state is drawn anywhere. DESIGN.md's rule (name the problem and the fix) exists on paper only. |
| 10 | Help and documentation | 2 | Help exists as the keyboard hint and the frame note ("The last generated frame of the first leg…"). Knobs and measures carry no explanation. |
| **Total** | | **24/40** | **Acceptable** |

### Cognitive load

Three of eight checklist items fail, so the load is moderate.

- **Single focus: fail.** Three photographs at the same size (417 × 540 px each), a frame table, three plots and a frame row all compete for attention.
- **Visual hierarchy: fail.** On a first look the eye lands on the three photographs, then jumps to the amber scrubber ring in the middle of the screen. A violet outline is the only thing that sets apart the frame under judgement, and violet means "generated", not "this one".
- **Minimal choices: fail.** The panel header holds 8 options in one row: wipe, A/B, onion, difference, fit, 1:1, 2× and "show in viewer", none of them pressed.
- **Pass:** chunking (the inspector's five groups of 3–5 rows), grouping, one thing at a time, working memory (the frame table repeats the leg and t), progressive disclosure (a stage opens its own panel).

The 10 stage tiles are navigation for an expert and acceptable as they are. The step plot, the ring plot, the generated lane, the skeptic lane and the frame row read as one axis. The amber cursor line runs through all five, sits under the scrubber thumb at f 25, and the skeptic's markers sit at the right x (f 19 at x 808, which is 104 + 19 × 37.06).

### Priority issues

1. **[P1] The viewer: the frame under judgement is small, not set apart, and cannot play.** Where: the render panel, the three photographs below the panel header. Why: each frame shows at 540 px tall from a 1366 × 1770 px source, about 30 % scale. The skeptic's faults (teeth fade at f 19 and f 43, hair lock at f 44–46) cannot be judged at that size. A and B get the same weight as the frame, and there is no play control. Fix: one large viewer for the current frame (the area between the strip and the axis is about 2000 × 700 px), with the current mode shown pressed. Show A and B as small references or as the wipe's two ends. Put play/pause at 25 fps beside the scrubber. Clicking a skeptic marker opens a 1:1 crop. Add the three-up view to DESIGN.md as a named mode if it stays. Commands: /impeccable layout, then /impeccable shape.
2. **[P1] The inspector dropped the incumbent's knob table.** Where: the right inspector, the "render" and "Plan keys changed" sections. Why: STUDIO §3 asks for each knob's range, default and a changed-from-default weight. The workbench shows knob · range · default · value · what (workbench_plan.png). The comp shows four bold rows with no default, and they cannot be edited. The keys are set in monospace but written with spaces ("breath z"), so a reader cannot tell a literal plan key from a label. Fix: one row per knob with the literal key, a value input, the range, the default and a one-line "what". Weight the changed rows, and add a ghost "reset to default" action. Command: /impeccable clarify.
3. **[P1] The measures that gate show no bar and no verdict.** Where: the inspector's "Measures that gate" section and the step plot. Why: PRODUCT.md principle 1 says measures gate. "step max 4.09 px at f 43" says nothing on whether it passed. The step plot draws only the 0.3 px stall bar. Fix: give each row its bar and a word chip ("within" in OK green, "past bar" in the failed colour). Draw the step-max bar dashed on the step plot. Command: /impeccable clarify.
4. **[P2] The states the brief names are missing.** Where: the rail's "Running tasks: idle", the "send to the skeptic" button, the empty grades tile. Why: STUDIO §1 lists running, failed or refused, lost, waiting for the session and graded as states. None are drawn, the grade form has no shape on screen, and DESIGN.md's "working…" loading label and the disabled state are absent. Amber marks both "selected" and "running", and no screen yet shows the two together. Fix: draw a second comp frame with four states. Show a running stage with its progress number and last log lines, and a refused registration tile with its reason. Show the "waiting for the session" chip with the request's age, and the grades panel with its verbatim text field. Command: /impeccable harden.
5. **[P2] Fixed canvas.** Where: `body{width:2560px;height:1440px;overflow:hidden}`, `.shell` set to 240px 2000px 320px, the SVG plots fixed at 1952 px. Why: DESIGN.md targets "1440 px and wider". See the next section. Fix: `grid-template-columns:240px minmax(0,1fr) 320px`, plots at 100 % width, the viewer's height taken from the viewport, and no `overflow:hidden` on body. Command: /impeccable adapt.

Minor:
- **Data Mono Rule.** Prose is set in monospace in the stage detail lines ("RIFE / morph / dissolve", "5 candidates on the page") and in the frame table ("generated (RIFE)", "k0 → k1 · leg 1 of 2").
- **Off-scale type.** The tick labels and the "generated" tag are 11 px, a size the type scale does not have.
- **Stale tokens.** The comp's CSS keeps the old `--faint:#6c737a` and `--failed:#e5655a`. DESIGN.md's amendment changed them to #8a9198 and #e8706a.
- **Skeptic chip.** "READY WITH A NOTE" is in green capitals, and the note itself cannot be reached from the tile.
- **Wall times.** Five of the ten tiles show "—" (a known gap per comp_build.md).

### Keep

1. **The shared frame axis.** One amber cursor runs through the step plot, the ring plot, the generated bands, the skeptic's markers and the frame row, all at measured x positions under the scrubber thumb. This is the design's distinct contribution.
2. **The stage strip.** Real thumbnails, a name, a detail line, the wall time and a word chip per tile. Nine "done/saved" chips and one grey "none yet" tell where the job stands in one look.
3. **The violet rule for generated frames.** One violet mark is used the same way on the render tile's tag, the viewer frame's outline, the generated bands and the frame-row outlines. A frame that is both selected and generated gets violet inside and an amber ring outside.

Also kept by the craft-floor check, which found nothing to refuse:
- no kicker above a heading, no section numbers, no nested cards;
- no sparkline without axes (both plots have y ticks and a baseline);
- no coloured side border above 2 px (the rail's 2 px amber edge is the one DESIGN.md allows);
- no emoji or glyph used as an icon, no gradient text.

### What breaks at 1440 × 900

- **The canvas is clipped.** The page is a fixed 2560 × 1440 canvas with `overflow:hidden`, so a 1440 × 900 window shows only the top-left crop: the rail and 1200 px of the work area (crit_1440_noautofocus.png).
- **Parts are unreachable.** The inspector, the scrubber, the plots, the frame row, B's caption and stage tiles 7–10 cannot be reached, because the page does not scroll.
- **Autofocus scrolls the page.** With `autofocus` on the scrubber, headless Chrome scrolled to it and painted the top 520 px blank (crit_1440.png). Whether a real window does the same is UNVERIFIED.
- **A correct shell would still be cramped.** DESIGN.md's shell at 1440 px leaves a work area of 880 px. That gives about 80 px per stage tile, and the detail lines already truncate at 192 px. A three-up view gets about 285 px per photograph. The strip then needs horizontal scroll or a smaller tile, and the viewer needs one frame, not three.

### Confidence: 75%

The scores rest on screenshots and the source, checked against the brief. I recomputed the builder's contrast numbers with the WCAG formula. They match: muted text on the raised face 5.68:1, the old failed colour on the raised face 4.48:1, the new one 4.92:1, amber ink on amber 8.64:1. Body text on the violet band is 8.83:1.

### Gaps

- **No engine output.** impeccable's detector and overlay did not run (the engine binary is not installed), and Assessments A and B were not isolated.
- **Hover and keyboard untested.** Only static screenshots were taken. Hover, real `:focus-visible` and keyboard stepping are untested.
- **Plan-key names unchecked.** I did not compare the inspector's key names against `scripts/research/plans/loops/SCHEMA.md`.
- **Port drift unexplained.** The 8379 versus 8380 finding rests on STUDIO §12; I did not check which port the comp builder meant.
- **Skipped steps.** The no-slop cold read by a context-free reader was skipped, and the critique's closing questions to the owner are left to the parent session.
