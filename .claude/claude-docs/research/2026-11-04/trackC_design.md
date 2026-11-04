<!-- Provenance: written by an Opus 5.5 subagent (Track C, the impeccable method and the UI patterns for a pipeline workbench) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/trackC_design.md (sha256 1b7b146159da73d9) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). impeccable's workflow, commands and detector rules read from the clone at commit 695cea5; the recommendations: a stage strip over a node graph, canvas overlays in image pixels, a hand-written schema-to-form generator, polling over SSE, a remote queue with a pre-flight; the direction as Operate and Restrained. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

---
reader: the design-session lead (cold), then the build session
shape: report
---
## Findings: Track C (design method)

Summary (2026-11-04). Impeccable (github.com/pbakaus/impeccable, a design skill plus a rule-based UI scanner) can run here without its npm hook. Its state in this repo:
- **Already done.** The skill folder is already copied to `.claude/skills/impeccable/` and a `PRODUCT.md` exists at the repo root. Both are untracked; another session wrote them at 14:45–14:46 today.
- **Engine not installed.** The skill's engine binary is absent from this laptop, and its first run downloads it from GitHub, so every `impeccable <verb>`, `detect` included, is UNVERIFIED as run here.
- **Detector blind to Reveal's page.** The page in `reveal.py` is a Python string, so the scanner applies only its text-pattern rules to it. The rendered rules (contrast, text size, padding) need the page served and scanned as a URL.

For the UI, I recommend:
- a linear **stage strip** with thumbnails, timings and "rerun from here", not a free node graph;
- canvas overlays that store shapes in image pixels;
- a hand-written schema-to-form generator;
- polling the job folder's JSON files for progress, not SSE.

Asked of the owner: (1) allow or refuse the engine download from GitHub; (2) answer the three `init` questions in 4; (3) choose which of the repo's three visual styles `DESIGN.md` records, or rule that a new style starts.

Glossary. *Impeccable*: the skill under review; *PRODUCT.md* and *DESIGN.md* are its product and visual records at the repo root. *Workbench*: the director's page in `scripts/research/director_ui.py` and the UI now being designed. *Operate*, *Restrained*: impeccable's names for a task surface and for a palette of tinted neutrals plus one accent. *craft-floor*: impeccable's quality checklist, `reference/craft-floor.md`. *The box*: the remote Strix Halo machine (`ssh strix`) that renders keyframes. *Stage strip*: a horizontal row of pipeline stages, one tile each, as in a CI run view. *Operate mode*: impeccable's name for app and tool surfaces where the user completes a task. *Detector*: `impeccable detect`, impeccable's rule-based scanner (no LLM). *Engine*: the self-contained binary that the skill's `scripts/impeccable` launcher runs.

Paths: `IMP` = `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/impeccable/src` (clone at commit `695cea5`). `SK` = `IMP/plugin/skills/impeccable`.

### 1–4 impeccable

**1. What SKILL.md tells an agent to do** (`SK/SKILL.md`, version 4.8.0, engine pin 0.1.18 in `SK/scripts/VERSION`)
- Before: run `scripts/impeccable context` once per session. It loads PRODUCT.md, DESIGN.md, the surface brief and platform guidance (line 19). Then load the command's reference file, or `reference/new-work.md` for a new surface, and inspect the incumbent visual state first (line 20). If the launcher fails, say so and read PRODUCT.md and DESIGN.md directly (line 23).
- During: read `reference/craft-floor.md` immediately before any UI edit (line 21). Choose the mode from the surface (Persuade, Operate, Read, Experience; lines 32–41). "The brief wins" (line 27). "Refinement preserves; redesign replaces" (line 28).
- After: "Verify by looking at the rendered result at the sizes it ships at" (line 15). `new-work.md §7` adds a batched screenshot round, the `impeccable-finish-reviewer` subagent, and the documenter subagent that writes DESIGN.md from the built result.
- AI-slop tells named in the skill: `craft-floor.md` lines 23–42. Page scaffolds: same-size icon+heading+text cards, nested cards ("always wrong"), the hero-metric template, a kicker above a heading (banned outright), section numbers. Surface habits: gradient text, decorative glass, a colored side border over 1px, hard offset shadows. Stand-ins: sparklines and progress rings in place of content, monospace as a costume, emoji in place of icons. Theme: light or dark picked by category instead of by use scene. The README adds Inter everywhere, purple-to-blue gradients, gray text on colored backgrounds and the rounded icon tile (`IMP/README.md` "Why").
- Direction catalog: for a new visual world the skill runs `impeccable concept-seed`. It fetches a "roll" of catalog worlds from `https://impeccable.style/api/roll` (`IMP/crates/context/src/concept_seed.rs` lines 120–160; `telemetry.rs` line 44). A local catalog can replace it through `IMPECCABLE_CATALOG_DIR` (`concept_seed.rs` line 502). The catalog lives only on impeccable.style; its schema, from the test fixture `IMP/tests/fixtures/concept-catalog/concept-ingredients.json`, is: wells (tiers such as graphic, interaction) → families → concepts. Each concept has `form`, `lineage` and a five-row `system`: Palette/material, Type/composition, Topology/navigation, Controls/state, Responsive/motion. Color strategies are Restrained, Committed, Full palette and Drenched (`new-work.md §4`). For Operate surfaces a world may lend only "type, palette, density, and one signature move" (`reference/mode-operate.md` line 7).

**2. Commands** (`SK/scripts/command-metadata.json`, `SK/reference/*.md`; "reads" means PRODUCT.md and DESIGN.md through `context` unless noted)

| Command | Input | Output | Files written |
|---|---|---|---|
| `shape` | a feature or surface | an interview of 2–3 questions per round, then a confirmed design brief of 3–7 blocks; "never writes code" (`shape.md` lines 3, 57) | none |
| `init` | the repo plus up to 3 questions per round | `PRODUCT.md` in a fixed schema: Platform, Stack, Users, Purpose, Positioning, Operating Context, Capabilities, Evidence, Principles, Accessibility (`init.md` Step 4); never DESIGN.md | `PRODUCT.md`, `.impeccable/config.json` (`buildPath`), optionally `.impeccable/live/config.json` |
| `document` | CSS custom properties, the global stylesheet, components, the rendered page (`document.md` Step 1) | `DESIGN.md` in Google Stitch format: YAML tokens plus 8 sections (Overview … Do's and Don'ts); asks before overwriting (line 71); seed mode before code | `DESIGN.md`, `.impeccable/design.json` sidecar |
| `critique` | one file or URL | Nielsen heuristics scored 0–4 ×10, cognitive load, persona red flags, 3–5 priority issues. A design review and a detector run go to two isolated subagents (`critique.md` lines 5–16) | `.impeccable/critique/<slug>*.md` and a trend line |
| `audit` | an area | 5 dimensions scored 0–4 (accessibility, performance, theming, responsive, implementation integrity), total /20, findings P0–P3; "Don't fix issues" (`audit.md` line 1) | none |
| `polish` | a target | fixes in triage order: broken tasks → missing states → drift → visuals → cleanup (`polish.md §3`); reads the latest critique snapshot | source edits; closes the critique snapshot |
| `clarify` | an interaction path | rewritten labels, errors, empty and loading text (`clarify.md`) | source edits |
| `onboard` | a target | first-run flow and empty states that "teach the interface" (`onboard.md`) | source edits |
| `harden` | a target | handling for long and empty text, 1000+ items, errors, i18n, overflow (`harden.md`) | source edits |
| `distill` | a target | removed elements, plus a record of what was removed (`distill.md`, "Document Removed Complexity") | source edits |
| `layout` / `typeset` / `colorize` | a target | structure, type or color changed inside the existing world. Operate rules: predictable density; one family and a fixed scale; color for action, selection and status (each file's "Visitor mode") | source edits. I did not read their "Two isolated assessments" and "Live-mode signature params" sections. |
| `detect` | an engine verb, not a skill command; see 3 | findings; exit 2 = findings, 1 = could not scan | none |

**3. The detector**
- How it runs: `SK/scripts/impeccable detect <file|dir|url>`, a POSIX launcher that needs no Node. The launcher looks for a sibling `bin/`, then `~/.impeccable/bin/<version>/`, then downloads from `https://github.com/pbakaus/impeccable/releases/download` with a checksum check (launcher lines 19–22, 44, 129–141). Neither location exists on this laptop, so the first run makes a network call. The download happens when a developer runs the tool. The offline contract in `AGENTS.md` covers the runtime and is not crossed, but the owner should know the call happens. `npx impeccable detect` is the npm route.
- Targets: `.html` files get a static HTML/CSS scan, other files get regex matching, and `http(s)://` and `file://` URLs get a full render in the installed Chrome or Edge (`IMP/crates/detect/src/cli.rs` lines 100–103). Consequence here: `reveal.py`'s page is a Python string, so only the regex rules reach it. The contrast, tiny-text and padding rules fire only when the page is scanned as a URL: start `./run.sh`, then run `detect http://127.0.0.1:8378` (or the workbench's port, 8379 by default). The loop review pages are real `.html` files: `detect benchmarks/runs/2026-11-04/angel/index.html`, or the `file://` URL for the rendered rules. Useful flags: `--json`, `--viewport 2560x1440` (a 27-inch window), `--list-rules`.
- Rule count: 62 built-in rules in `IMP/crates/foundation/src/registry.rs` (rows 63–65 are test-pack fixtures). The rules that apply to a dense workbench:

| Rule id | Category | What it flags |
|---|---|---|
| `low-contrast` | quality | text below WCAG AA (4.5:1 body, 3:1 large) |
| `gray-on-color` | quality | gray text on a colored ground |
| `tiny-text` | quality | body text under 12px |
| `undersized-ui-text` | quality | labels, buttons, table cells, timecodes under 11px |
| `cramped-padding` | quality | text too close to its container edge |
| `tight-leading` | quality | line height under 1.3× |
| `skipped-heading` | quality | h1 then h3 with no h2 |
| `heading-rhythm` | quality | less space above a heading than below it |
| `flat-type-hierarchy` | slop | heading and body sizes less than 1.25× apart |
| `overused-font` | slop | Inter, Roboto, Geist, Space Grotesk and similar |
| `nested-cards` | slop | cards inside cards |
| `icon-tile-stack` | slop | a rounded icon tile above a heading |
| `gradient-text`, `ai-color-palette` | slop | gradient text; purple/violet gradients, cyan on dark |
| `side-tab` | slop | a thick colored border on one side of a card |
| `pulsing-dot` | slop | a pulsing status dot not tied to live data |
| `kicker-above-heading` | slop | a small tracked label above a heading |
| `monotonous-spacing` | slop | one spacing value used everywhere |
| `text-overflow`, `clipped-overflow-container` | quality | content spilling out; popovers clipped by `overflow:hidden` |
| `repeated-container-text` | quality | the same label 3+ times in one panel |
| `design-system-font/-color/-radius/-font-size` | quality | values outside DESIGN.md; active only once DESIGN.md exists |

The other rules mostly target landing pages: `hero-eyebrow-chip`, `oversized-h1`, `marquee`, `radial-halo` and others. Run `detect --list-rules` to get the full list.

**4. Applying it with the least intrusion**
- Copy: done. `.claude/skills/impeccable/` matches `IMP/plugin/skills/impeccable` byte for byte. That build keeps the `<skill-base-dir>` placeholder. The repo's `IMP/.claude/skills/impeccable` build, which the README's "Manual copy" names, has the paths already resolved. Both work, because SKILL.md line 19 says to substitute the placeholder. A manual copy has no hook and no subagents (README "Manual copy"). The hook is what runs the detector after each edit, so here someone must run the detector by hand.
- Still missing: `.impeccable/config.json` and the README's `.gitignore` block (README "Project files and git"). Before any `concept-seed` run, set `DO_NOT_TRACK=1`, or `"telemetry": false` in `.impeccable/config.json`. The direction fetch still goes out unless `IMPECCABLE_CATALOG_DIR` points at a local catalog (README "Telemetry").
- PRODUCT.md: the existing file follows `init.md`'s schema and holds what `init` would write for this workbench. One user on a 27-inch display; a stdlib server on 127.0.0.1 with no build step; principles such as "his eye grades; measures gate". It departs from the method in one way. Its header says it was written from the decision log "not from an interview", while `init.md` Step 3 requires one real answer round and says to "probe once" before concluding no one can answer. The owner should answer the three init questions (`init.md` Step 3):
  1. Who is the primary user, in what situation, doing what job?
  2. What does the product make possible that a neighbour could not claim?
  3. Which constraints, assets or facts must future work preserve?
  The file also marks "Users" and "Accessibility" as `[inferred]`.
- DESIGN.md: `document` scan mode assumes one coherent world. The repo has three:
  - `reveal.py` line 1765: dark warm `--bg:#191210`, amber accent, an italic serif wordmark, system sans at 15px, `max-width:1100px`;
  - `scripts/research/director_ui.py` line 910: `13px Menlo` on `#fafafa`, unstyled buttons;
  - the loop review pages (`benchmarks/runs/2026-11-04/angel/index.html`): `--bg:#fafaf8`, `--line:#ddd`.

  The owner has two choices:
  - Record Reveal's page as DESIGN.md and name the other two as drift.
  - Run `document` in seed mode for the new workbench. Seed mode runs the new-world flow (`new-work.md`), whose `concept-seed` step fetches directions from impeccable.style.

  I make no recommendation between them. Either way DESIGN.md is what turns on the four `design-system-*` detector rules.
- Order of commands. In the design session, before code: `shape` (the brief), then `critique` on the incumbent pages (Reveal served, the workbench served, one loop page) to rank what to keep, then `document` once the owner picks a world. In the build session, after code: `detect` on the served URL at `--viewport 2560x1440`, `audit`, `harden` (1000+ frames, long plan names, the remote box offline), `clarify` (error and refusal text), `polish` last. `distill` fits if the stage panels grow. `onboard` matters little for one expert user, except for empty states.

### 5–8 pipeline view, comparison, plan editor, long jobs

**5. Pipeline view.** Recommendation: a stage strip, not a free node graph.
- Evidence. Graph tools give every node a status and a viewer link:
  - ComfyUI emits `executing`, `progress` (value and max), `executed` and `execution_cached` per node, and queue state in `status` (docs.comfy.org, comms_messages). Its partial execution "only runs the branch … from the starting node to the output node" (docs.comfy.org, partial-execution).
  - Houdini's display flag "marks the node whose geometry appears in the 3D viewer", and its bypass flag passes input through unchanged (sidefx.com, network/flags).
  - GitHub Actions' run graph shows each job with a status icon, dependency lines, and the job's log on click (docs.github.com, visualization graph).
  - Blender's Viewer node and DaVinci Resolve's node tree: two fetches of the Blender manual returned navigation only, and Resolve was not fetched. Both UNVERIFIED.
- Why a strip fits. The align, transition and loop flows are linear with at most two branches (the depth camera beside the morph; probes beside the plan). A strip encodes order by position. A free graph needs pan, zoom, edge routing and hit-testing, maybe 1,500–3,000 lines of plain JS plus SVG, and the user would gain nothing from rearranging nodes. A strip is CSS grid plus one `<details>` per stage, maybe 300–500 lines (both estimates UNVERIFIED). Show a branch as a second short row under its parent tile.
- Per stage tile: name and status (queued, running, done, cached, failed, refused). Next, elapsed time and the last wall time; one thumbnail of the stage's main output (matches drawn over A, the warped B, the residual field, the mask, depth); the key measure (inliers, rmse px, confidence). Expanded: inputs and outputs as file links with sha256 prefixes, the knobs that apply to this stage, the stage's log tail, and "rerun from here". Rerun invalidates the downstream tiles and keeps the upstream ones, as ComfyUI's `execution_cached` does. Borrow Houdini's display flag as "show in viewer": any stage's output can be sent to the comparison area.

**6. Comparing images and frames**
- Modes in one viewer, chosen by key: the slider Reveal already has (a wipe), A/B toggle, onion skin with an opacity control, and difference. Nuke's Viewer picks A and B inputs and offers wipe with a draggable handle (learn.foundry.com, viewer composite modes, Nuke 8.0, and "Comparing Media"). OpenRV-web documents onion skin as "B over A with adjustable opacity" and lists a difference matte (lifeart.github.io/openrv-web docs; a port, not the original RV docs).
- Frame scrubber: decode to a frame strip on disk (the renderers already write `frames/`). Scrub by index over JPEGs, not by `video.currentTime`, so frame N is exact. Under the scrubber, one shared x-axis with small plots of the per-frame measures (step series, stall and jump markers, object stability). A vertical line marks the current frame across all plots. These plots are content, so the craft-floor ban on "sparklines standing in for content" does not apply. `requestVideoFrameCallback` gives `mediaTime` and `presentedFrames` for checking a playing mp4 (MDN; Baseline 2024).
- Skeptic crops: 1:1 and 2× crops drawn to canvas with `imageSmoothingEnabled=false`, or `<img>` with `image-rendering: pixelated` ("nearest neighbor … to the nearest integer multiple", MDN). The 2× view does not blur, so it shows real pixels.
- Contact sheet: a grid of frames at a fixed step with the frame index under each; click a frame to jump the scrubber.
- Drawing boxes, points and polygons: one `<canvas>` absolutely positioned over the `<img>`, using Pointer Events with `setPointerCapture`. Convert to image pixels on every event as `x_img = (clientX - rect.left) * naturalWidth / rect.width`, store only image coordinates, and redraw on resize. Save as JSON beside the plan: `{kind, pts:[[x,y]...], image:{path, sha256, w, h}, author:"owner"|"session", ts, note}`. The image sha256 is the provenance: a shape whose image hash changed is shown as stale. No library is needed (cost UNVERIFIED, roughly 200–300 lines).

**7. Plan and timeline editor**
- Holds and legs as absolutely positioned bars on a time ruler. Drag a bar's edge to change its duration, using the same Pointer Events code as item 6. Snap to frames at the plan's fps. Click a leg to open its panel: method (a select), ease (a select plus a small curve preview drawn on canvas), box. Keyboard: the selected bar's edge moves ±1 frame on arrow keys and ±10 frames with Shift.
- Knob panels from a schema: a hand-written generator for `number` (with `minimum`, `maximum`, `step` → a range plus a number input), `enum` → a select, `boolean` → a checkbox, and `description` → a help line. The plan schemas are small enough. `json-editor` is the reference pattern: one script file, no dependencies, JSON Schema drafts 3 and 4 (github.com/json-editor/json-editor). Adding it would be a new dependency, which `AGENTS.md` says needs a decision. Show a knob that differs from its default in a different weight, so hidden defaults stay visible (PRODUCT.md principle 2).
- Undo: an array of immutable plan snapshots with an index; Cmd+Z and Shift+Cmd+Z. Do not write the open plan file in place. "Save as new plan" writes `plans/<name>_r<N>.json` with `{parent: <path>, parent_md5, author, ts, changed_keys:[...]}`. That record matches the repo's plan-plus-md5 reproducibility rule.

**8. Long-running jobs**
- Progress: keep polling. `director_ui.py` already writes `tasks/<tid>.json` and a `.log` for each subprocess and parses progress from the log (lines 14, 325–396), so the job folder is already the source of truth. SSE gains little here:
  - `http.server` serves one request at a time unless it is `ThreadingHTTPServer` (Python 3.7+; docs.python.org), and an open event stream needs a thread of its own.
  - Over HTTP/1.1, browsers allow about 6 connections per domain (MDN, "Using server-sent events"), and two tabs plus video range requests reach that limit.

  Polling every 1 s while a task runs, and every 5 s when idle, costs nothing on localhost.
- Cancel: SIGTERM to the recorded pid, then mark the task file `cancelled`. The workbench already offers cancel (line 965).
- Resume after a server restart: on start, scan `tasks/*.json`. A task marked `running` whose pid is gone becomes `lost`, and its partial outputs stay on disk. Each stage writes its outputs to a temp name and renames on success, so "rerun from here" can trust that a stage's output exists only if the stage finished.
- Remote box queue: one queue file per job (`remote_queue.json`: items with prompt, seed, state). Before each item, a pre-flight check confirms `ssh strix` answers, that `~/halo-hold` is absent, and that free memory is above the floor. If the hold file exists, the queue shows "held by the box owner", does not start, and keeps polling. Show each item's expected duration from past wall times (40 s to 30 min). `~/halo-hold` and the pre-flight probe come from `.claude/claude-docs/DECISIONS.md` (2026-09-26 lines) and `.claude/claude-docs/research/2026-10-17/flux3_run.md` line 309.

### 9–10 direction, accessibility, performance

**9. Direction.** In impeccable's terms this is an Operate surface with a Restrained color strategy (`mode-operate.md`; `new-work.md §4`; `operate.md` "Color": "Product defaults to Restrained"). From `operate.md`:
- one family, with system fonts allowed;
- a fixed rem scale at a 1.125–1.2 ratio;
- density allowed: "tables at 120ch+ are fine";
- motion of 150–250 ms, and only to show state;
- color for action, selection and status only, with a second neutral layer for panels.

Two `craft-floor.md` items apply directly: tabular numerals for measures (line 15), and "Light or dark picked … from the use scene", not by category (line 42).

The use scene is one person at a desk grading photographs. The page chrome should stay neutral and must not tint the photos under review. A mid-dark neutral gray is one answer; Reveal's warm brown shifts how colors read (UNVERIFIED as a measured effect; this is an argument, not a test). The "signature move" impeccable asks for could be the shared frame axis under the viewer, which ties measures to frames. Use the full width of a 27-inch display: Reveal's `max-width:1100px` wastes it.

Slop tells to avoid on this surface:
- pulsing status dots (`pulsing-dot`); a running task shows its progress number instead;
- cards nested in stage panels (`nested-cards`);
- icon tiles above stage names (`icon-tile-stack`);
- kicker labels and 01/02/03 stage numbers, unless order carries information (`kicker-above-heading`, `craft-floor.md` line 28);
- colored side borders as status (`side-tab`);
- monospace for everything, as `director_ui.py` does (`craft-floor.md` line 38); keep mono for paths, hashes and numbers;
- an italic serif wordmark (Reveal's page; `new-work.md §4` lists "italic display serif" among the AI-look clusters);
- labels under 11px (`undersized-ui-text`).

**10. Accessibility and performance minima**
- Scrubber and wipe handle: use the APG slider pattern (w3.org/WAI/ARIA/apg/patterns/slider). It means `role="slider"`, `aria-valuenow`/`min`/`max`, `aria-valuetext` such as "frame 41 of 120, 1.71 s", arrows step 1, Page Up and Page Down step 10, Home and End. Add `,` and `.` for frame steps, as video tools do (UNVERIFIED as a standard).
- Focus order matches the strip's order. The focus ring is visible and uses the palette (`craft-floor.md` line 15). Overlays use `<dialog>` or popover so they escape `overflow:hidden` (`operate.md` "Components").
- Images: serve thumbnails at the displayed size (for example 320 px long side) and the full image only in the 1:1 crop. Set `width` and `height`, or `aspect-ratio`, on every `<img>` and `<video>` so nothing shifts while loading. Use `loading="lazy"` on below-the-fold images.
- Video: the angel review page has 5 `<video autoplay>` tags. MDN says "the autoplay attribute has precedence over preload", so all 5 start downloading at once. Fix: `preload="metadata"` with no autoplay, and an IntersectionObserver that plays a clip when it is visible and pauses it when it leaves. MDN also documents `loading="lazy"` on `<video>` (browser support UNVERIFIED).
- `prefers-reduced-motion` keeps state changes visible (`audit.md` "Motion sensitivity"). Reveal's page kills all transitions with `!important` (line 1789), which `audit.md` flags.

### Confidence: Part 1 85%, Part 2 65%
Part 1 rests on primary sources read in this clone; the engine was not run. Part 2 combines documentation with my own synthesis. The cost estimates and the neutral-ground argument are unmeasured.

### Gaps
- Not run: the impeccable engine (`context`, `detect`, `critique-storage`). No binary is on this laptop, and getting one requires a GitHub download.
- Not read: the full catalog of directions. It lives on impeccable.style and is not in the repo; only the fixture schema was read.
- Failed fetches: Blender's compositor Viewer page (two attempts returned navigation only). Not fetched: DaVinci Resolve's node docs or a current Nuke viewer page (the Nuke 8.0 page found by search was not opened).
- Not read in full: `critique.md` (819 lines; top, setup and snapshot read), `harden.md` and `onboard.md` (headings read), the "Two isolated assessments" sections of `layout.md`, `typeset.md` and `colorize.md`.
- No `critique` or `audit` was run on the incumbent pages. That is design-session work, after the owner settles the engine download.
