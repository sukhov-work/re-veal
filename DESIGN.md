---
name: Reveal studio
description: One dark light-table for aligning, transitioning and looping the owner's photographs, every stage shown as a strip of frames
colors:
  ground: "#141618"
  panel: "#1c1f22"
  panel-raised: "#24282c"
  line: "#30353a"
  line-strong: "#454b52"
  text: "#e8e8e6"
  text-muted: "#9aa1a8"
  text-faint: "#8a9198"
  amber: "#e0a65a"
  amber-deep: "#c78a3b"
  amber-ink: "#1a1200"
  ok: "#5cc48a"
  running: "#e0a65a"
  failed: "#e8706a"
  info: "#6aa9f0"
  generated: "#b48ef0"
  photo-a: "#6aa9f0"
  photo-b: "#f0a06a"
typography:
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0em"
  heading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0em"
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0em"
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.01em"
  data:
    fontFamily: "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0em"
rounded:
  sm: "3px"
  md: "6px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.amber-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "6px 14px"
  button-primary-hover:
    backgroundColor: "{colors.amber-deep}"
  button-secondary:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "6px 14px"
  chip-state:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "1px 6px"
  input:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.text}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  frame-tile:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-muted}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "0px"
---

# Design System: Reveal studio

<!-- Written 2026-11-04 by the Claude Code session as the committed visual world for the UI rebuild; amended the same day after the comp build (`research/2026-11-04/comp_build.md`: the strip's height, the faint and failed colours' contrast, the selected-and-generated rule) and its critique (`comp_critique.md`: the viewer's hierarchy, the tick floor, the focus ring on the thumb) (the "replace" path of impeccable's new-work: the incumbent pages are evidence, not the system). The build session applies it; the owner's eye on the first screens may amend it (a dated note here). -->

## Overview

**Creative North Star: "The light table"**

The studio is where one photographer judges his own pictures and the clips made from them, so the surface is a dark, colour-neutral light table: the photographs and the rendered frames are the only saturated things on screen, and every control sits in quiet greys around them. The one brand colour is the amber of the Reveal wordmark, used for the primary action, the current selection and anything "running"; green, red and blue carry states and the two photographs' identities and nothing else.

The density is that of an editing tool, not a website: tables of numbers, a strip of frames across the top, knobs with their ranges, measures with axes. Everything is a standard web control the owner already knows (buttons, inputs, selects, tabs, tables with sortable headers, a range slider); the world lends only its type, palette, density and one signature move.

The signature move: **every process is a strip of frames.** The pipeline of a job reads left to right as a contact sheet, one frame per stage (its thumbnail, its name, its wall time, its state chip), and each stage opens into its own panel beneath the strip. A render is a strip of its frames with the generated ones marked; a candidate page is a strip of candidates. Nothing in the studio is a step the owner cannot see as a picture.

**Key Characteristics:**
- Dark neutral surfaces, one amber accent, state colours only where they carry meaning.
- One sans family for the interface; a monospace only for numbers, hashes, paths and plan keys.
- Strips of frames as the structure of every process; tables for every measure; no cards.
- Flat regions separated by 1 px lines; depth only on overlays that must float.
- Motion only as state feedback, 150–200 ms, no entrances.

## Colors

A neutral grey ramp that does not tint the photographs, one warm accent, and five meanings.

### Primary
- **Amber** (#e0a65a): the primary action (render, save, open), the current selection in a strip or a list, the "running" state, the focus ring. On at most a tenth of any screen.
- **Amber deep** (#c78a3b): the amber control's hover and active face.

### Neutral
- **Ground** (#141618): the page.
- **Panel** (#1c1f22): the rail, the inspector, a stage's panel.
- **Panel raised** (#24282c): a control's resting face, a chip, a table header row, a hovered row.
- **Line** (#30353a) and **Line strong** (#454b52): separators and borders; the strong one on focused or selected regions and table outlines.
- **Text** (#e8e8e6), **Text muted** (#9aa1a8), **Text faint** (#8a9198): primary copy; labels, units and secondary cells; placeholder text (4.65:1 on the raised face; the earlier #6c737a measured 3.09:1 there and is kept only for disabled text at 40 % opacity).

### Meaning colours
- **OK** (#5cc48a): a task done, a measure within its bar, READY.
- **Running** (the amber): a task running or queued.
- **Failed** (#e8706a): a task failed, a refusal, NOT READY, a measure past its bar, a marked fault frame (4.92:1 on the raised face; #e5655a measured 4.48:1 there).
- **Info** (#6aa9f0): a note, a link, an UNVERIFIED tag.
- **Generated** (#b48ef0): any frame or pixel a model produced (RIFE in-betweens, a keyframe): the badge, the tick on a strip, the outline of the frame.
- **Photo A** (#6aa9f0) and **Photo B** (#f0a06a): the two photographs' identities in overlays, the blend slider's ends, the timeline's ends.
- Open since 2026-11-05 (backlog row T102): Info and Photo A share #6aa9f0, so an "unjudged" chip and a "draft 480" chip wear k0's blue; the owner decides which of the two changes.

### Named Rules
**The Neutral Ground Rule.** Nothing behind or beside a photograph is tinted: the greys are neutral to 2 units of chroma. A photograph's colour is judged against grey.
**The One Amber Rule.** Amber marks the action, the selection and the running task. It never decorates; a heading, a border or an icon is never amber.
**The Generated Violet Rule.** Every model-made pixel on screen carries the violet mark where it is shown; a strip, a scrubber and a sheet all mark it the same way.

## Typography

**Display Font:** none; the interface has no display voice.
**Body Font:** the system sans (system-ui, SF Pro on the Mac)
**Label/Mono Font:** the system monospace (ui-monospace, SF Mono) for numbers, md5s, paths, plan keys and log lines

**Character:** quiet and exact; the type never competes with a photograph. Hierarchy comes from weight and size steps at a 1.14 ratio, not from a second family.

### Hierarchy
- **Title** (600, 1.25rem, 1.25): the job's name at the top of the work area; one per screen.
- **Heading** (600, 1rem, 1.3): a stage's or a panel's name.
- **Body** (400, 0.875rem, 1.45): notes, the skeptic's text, help lines; 65–75ch measure in prose panels.
- **Label** (500, 0.75rem, 1.3, 0.01em): control labels, chips, table headers, the frame numbers under a strip; also the floor for axis ticks and tags (12 px; the comp's 11 px ticks were off the scale).
- **Data** (mono 400, 0.8125rem, 1.4): every number, hash, path and key; tabular numerals on; right-aligned in tables.

### Named Rules
**The Data Mono Rule.** Monospace carries data, never prose. A sentence is set in the sans even inside a table.
**The Units Rule.** Every number shows its unit or its frame index beside it in the muted colour ("4.1 px", "f 25", "63 s").

## Layout

A fixed three-region shell on a 27-inch display, 1440 px and wider: a 240 px left rail (jobs, tasks, models), the work area (the stage strip across the top at 168 px (a tile holds a 96 px thumbnail, the name, a detail line, the wall time and a chip; the comp of 2026-11-04 measured 160 px), the stage's panel beneath), and a 320 px right inspector (the selected thing's knobs, measures and provenance). Below 1280 px the inspector collapses under the panel; the rail collapses to icons below 1100 px. The spacing unit is 8 px: 4 inside controls, 8 between related controls, 16 between groups, 24 between regions, 40 around the work area. Tables run at 13 px with 4 px cell padding and may exceed 120ch. The strip's frames are 96 px tall thumbnails with the label beneath; a selected frame has a 2 px amber outline.

## Elevation & Depth

Tonal layering, no shadows at rest: the ground, the panel and the raised face are three greys, and regions are separated by 1 px lines. A shadow appears only on an overlay that must float over a photograph (a popover, a dropdown, a dragged timeline bar): `box-shadow: 0 8px 24px rgba(0,0,0,0.45)`, with an offset and a soft blur.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat; a line, not a shadow, separates them. Depth is reserved for things that are literally above the page.

## Shapes

Right angles softened to 3 px on controls and 6 px on floating overlays; 1 px borders in the line colour; frames and photographs are never rounded or clipped; thumbnails keep their aspect inside a fixed-height tile with a ground-coloured letterbox. No pill shapes, no circles standing in for a status (a chip with a word carries a state).

## Components

### Buttons
- **Shape:** 3 px radius, 1 px border in the line colour on the secondary face.
- **Primary:** amber face, amber-ink text, label type, 6 × 14 px padding; one primary per panel (render, save, open).
- **Hover / Focus:** the deep amber face; a 2 px amber focus ring offset 2 px; 150 ms background transition.
- **Secondary:** the raised panel face with light text; **Ghost:** no face, muted text, for cancel and "show".
- **Disabled:** 40 % opacity, no hover; **Loading:** the label replaced by "working…" and the button inert, never a spinner beside it.

### Chips (state)
- **Style:** the raised face, label type, 1 × 6 px padding, 3 px radius; the text in the meaning colour (OK, running, failed, info, generated), the face unchanged.
- **State:** a chip names a state in a word (done, running, failed, lost, draft, generated, READY, NOT READY); it is never only a colour.

### Containers
- **Corner Style:** none for regions; 3 px for a stage panel's inner boxes only where a border is needed.
- **Background:** the panel grey; a raised face only for controls and table headers.
- **Shadow Strategy:** none (see Elevation).
- **Border:** 1 px lines between regions; never a card inside a card.
- **Internal Padding:** 16 px; 8 px in dense tables.

### Inputs / Fields
- **Style:** the ground colour inside a 1 px line border, 3 px radius, data type, 4 × 8 px padding; a unit label to the right in the muted colour; a range slider beside a number for any knob with a stated range.
- **Focus:** the border turns amber; no glow.
- **Error / Disabled:** a failed-colour border and a message beneath naming the problem and the fix; disabled at 40 % opacity.

### Navigation
- The rail lists jobs (name, pair or sequence, the last render's state chip), then the running tasks with their elapsed seconds, then the models with their readiness. The current job's row has the amber selection bar on its left edge at 2 px (the one place a coloured edge is allowed, and only at 2 px). Keyboard: up and down move the selection, Enter opens.

### The stage strip (signature)
One tile per stage of the job's pipeline, left to right: the thumbnail of the stage's output (or the ground grey with the stage's name when it has none yet), the name in label type, the wall time and the state chip beneath. The selected stage has the amber outline; a failed stage the failed outline; a stage with generated content the violet tick. A frame that is both selected and generated carries the violet outline inside the frame and the amber ring outside it (the comp's rule, kept). Clicking a tile opens the stage's panel; "rerun from here" lives in the panel, not on the tile. The same component shows a render's frames (every frame or every Nth, generated frames outlined violet) and a round's candidates.

### Measure plots
SVG line plots with axes, a baseline, the bar as a dashed line, markers for the frames the skeptic named; the step series, the seam, an object's stability per frame. Never a sparkline without axes.

### The viewer and the scrubber
One large frame under judgement fills the space between the strip and the axis (sized from the window); A and B are small beside it or the two ends of the wipe; the active comparator mode is drawn pressed; play and pause at 25 fps sit beside the scrubber. The scrubber is a range input over the render's frames, keyboard-steppable (left and right by one frame, shift by ten), the frame index and its t in data type, the plots beneath aligned to the same x; its focus ring sits on the thumb, never on the whole track (the comp's 1,832 px amber rectangle was the loudest thing on the screen, the critique of 2026-11-04). Since the fix round of 2026-11-05: the render's name, its modes, the sources A and B and the list of renders sit in a column of 300 to 400 px beside the frame. The frame's height comes from the window with a 240 px floor, so at 1280×800 the frame and its scrubber fit the window (backlog row T105 holds the trade: 17.8 % of the source on screen against 21.2 % below the fold). The violet outline marks the picture at fit and the box at 1:1 and 2×.

## Do's and Don'ts

### Do:
- **Do** set every number in the monospace with its unit, right-aligned in tables (tabular numerals).
- **Do** mark every generated frame with the violet outline wherever it appears.
- **Do** keep the ground and panels neutral grey; judge photographs against grey.
- **Do** use one primary amber control per panel and standard web controls everywhere.
- **Do** theme the browser's own surfaces: the focus ring amber, the selection highlight amber at 30 %, the scrollbar thin in the line colour, the caret amber.

### Don't:
- **Don't** nest cards, add a kicker above a heading, or number sections.
- **Don't** use a second type family, a display face, gradient text or an icon tile above a heading.
- **Don't** animate an entrance; the page loads into the task (Reveal's current fade-in is dropped).
- **Don't** use colour as the only carrier of a state; the chip's word carries it.
- **Don't** put a sparkline, a progress ring or a rounded placeholder where content belongs; a measure gets axes, a pending stage gets its name on the grey tile.
