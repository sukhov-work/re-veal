<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/b_director_research.md (gitignored), the director plan flow as studio stages, the --set key table (104 effective keys, 8 without effect), the info.json measures and their bars, the workbench's panels, the overlays, the job folder, the acceptance checks and the retirement checklist by an Opus 5.5 research subagent (max effort), read-only on the repo; a research artifact whose claims carry the author's own confidence and gaps; the main thread re-verified the mismatch_3 anchors by rendering both argvs (DECISIONS 2026-11-05 eighth and ninth lines) and nothing else -->

<!-- reader: the phase-B main thread and the director-flow builder, cold on this track. shape: report. author: an Opus 5.5 research subagent, read-only on the repo except this file. -->

## Findings: director-flow

The director flow fits the studio as 7 stages over 104 renderer keys that change a render. These findings change the build:

1. The acceptance anchor is two different renders. The workbench's md5 5b3ee379… came from four knobs: two pre-filled from the round-12 render (`cont_feather=14`, `front_margin=0.3`), plus `parallax_push=2` and the window. The md5 re-recorded today, 01b3cf3c… (DECISIONS 2026-11-05, eighth line), comes from the last two knobs only. That line's "the anchor moved with round 13 and not since" is therefore not established.
2. Eight `--set` keys change nothing in the render (section 2, table D). SCHEMA.md round 12 names two of them, `name.edge` and `name.rate`, as working knobs.
3. The page script fixes the run folder's layout: render folders named `<frozen plan stem>_<concept>[-<tag>]`, the resolve output outside, plans read from `scripts/research/plans/` only.

Actions asked of the main thread:
- Render the four-knob argv once under renderer 05cd6e1d… (about 14 s; section 7) and record its md5.
- Choose the argv the acceptance pins.
- Decide whether the plan stage pre-fills the last round's knobs; default off is proposed.

Glossary:

| Term | Meaning |
|---|---|
| the renderer, D | `scripts/research/director_render.py` (md5 05cd6e1d95adbb3c83313b98b3f43815); D:n is its line n |
| the workbench, U | `scripts/research/director_ui.py`, the director's web page on 127.0.0.1:8379 that phase B retires; U:n is its line n |
| the page script, P | `scripts/research/director_page.py`, the review page over a folder of renders; P:n is its line n |
| the run folder | the folder the page script reads: one child folder per render |
| the loop script | `scripts/research/loop_seq.py`, the backend of the studio's loop flow |
| DECISIONS | `.claude/claude-docs/DECISIONS.md`; "the eighth line" is its eighth entry dated 2026-11-05 |
| T60, T62 | rows of the backlog `.claude/skills/reveal/references/tracked-backlog.md` |
| a round | one planner → render → grade cycle of the director work; rounds 8 to 13 ran from 2026-10-17 to 2026-10-21, and SCHEMA.md has a section per round |
| A, B | the pair's first and last photo, `fixtures/<pair>_S.*` and `fixtures/<pair>_F.*` |
| container, disc, quad, rect | SCHEMA.md's region of B that holds A: a disc (a luminary), a quad or rect (a window, a screen) |
| beat | one transform's time window in the plan (`retrospective.md` §4) |
| recede, line_to, morph_to, move_to, exit, colour, hold, keyframe_chain | SCHEMA.md's transform kinds |
| guard | the round-12 rule that keeps a transform's target in B hidden until the transform delivers it (SCHEMA.md:199–206) |
| c1 | concept c1 of `scripts/research/plans/mismatch_3_r12.json` |
| a key without effect | a `--set` key whose value never reaches a frame: stored and never read, or read and never used |
| the strip, terminal, rng | the studio's row of stage tiles; the file whose presence marks a stage's run finished; a knob's range (`registry/loop.py`) |
| the round gate, the review gate | the studio's rules that a new round's first full render waits for the previous round's grade text, and that a page refuses an unjudged candidate unless he overrides (`STUDIO.md §4`) |
| `contracts.md` | `.claude/conventions/contracts.md`, whose studio section lists the routes and the job folder's shapes |

### Key facts

| # | Fact | Source |
|---|---|---|
| 1 | The workbench's acceptance render carried four knobs: `cont_feather` 14, `front_margin` 0.3, `parallax_push` 2, `pane_becomes_view.window` [0.35, 0.97]. All five renders at md5 5b3ee379… carry the same four, under the pre-round-13 renderers d8a5f732…, 52630887… and a1ec3245…. | `benchmarks/runs/2026-10-21/workbench/mismatch_3_20261021-015336_10e3/renders/r20261021-015422_480_483d/render.json`; `research/2026-10-21/ui1_build.md` acceptance step 8 |
| 2 | The workbench pre-fills the plan form from the newest round render of the same plan and concept: `director_r12/mismatch_3_r12_c1/info.json` holds `cont_feather` 14, `front_margin` 0.3, `parallax_push` 1.5. | U:270–280, U:1004; `benchmarks/runs/2026-10-20/director_r12/knobs.txt` |
| 3 | The eighth line's two renders hold two knobs. Against the four-knob renders at 5b3ee379… they keep 44 front layers instead of 25, step 0 → 1 reads 0.27 instead of 0.69, and `b_inside_first` reads 84 instead of 21. | DECISIONS 2026-11-05 eighth line; read today from `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/9041ff2b-bcdd-448e-b55d-c8250e7a4b44/scratchpad/m3probe/info.json` and `m3probe2/info.json` (a scratch folder a later session will not find); `info.json` of `r20261021-015422_480_483d` and `r20261021-015939_480_bf15` |
| 4 | The eighth line's sentence "the anchor moved with round 13 and not since" is not established: the knob set changed too. One shell render of the four knobs decides it. 5b3ee379… means the knobs alone moved the anchor; any other md5 means both changed. The line sits in the uncommitted working tree (`git status`: DECISIONS.md modified), so correcting it or superseding it is the main thread's call under the append-only rule. | the two rows above; `git status` at boot |
| 5 | The eighth line counts "53 matte files" for mismatch_3_F. The folder holds 51 `el_*.png` among 53 entries (with `mattes.json` and `sheet.jpg`); elements 9, 19, 24, 26 and 32 have no matte. | `ls benchmarks/runs/2026-10-17/mattes/mismatch_3_F`; `layers.json` of mismatch_3_F |
| 4 | `--set k=v` splits at the first `=` and decodes the value as JSON, keeping the raw string when decoding fails; a repeated key keeps its last value. | D:2068–2074, D:2097; help text D:2081 |
| 5 | A key that starts with a transform's name and a dot goes to that transform: `window` and `mix` to the layer, any other suffix into its params. A key that starts with `sky.` goes into the sky dict. | D:881–889, D:1439–1441 |
| 6 | A layer's ease, edge and rate are read from the plan at D:878–880, one line before the knob loop at D:881, so `--set <name>.ease`, `.edge` and `.rate` land in params where nothing reads them. | D:877–890; scan of every params read in D:862–1780 |
| 7 | `hole_reveal_from` and `hole_reveal_over` are fallbacks that never fire: every layer with a footprint also gets its own `hole_from` and `hole_over`. | D:1399–1432, D:1477, D:1485 |
| 8 | The renderer reads `key_end` from the concept's `params`, never from the sky dict, and only when the sky lacks `key_window`. All five disc concepts with a sky set `key_window`: `mismatch_5_r9` to `_r12` and `mismatch_4_r12`. | D:1437, D:1450; the frozen plans |
| 9 | An unknown `--concept` renders the first concept without a message, and fewer than 3 frames crash the measures. | D:2095; D:1795, D:2052 (`steps[1]`) |
| 10 | `--resolve-only` writes `canvas_A.png`, `canvas_B.png`, `anchors.json` and an `info.json` without the measures. The workbench's resolves took 8.8, 9.5 and 13.9 s at the default 1920 px. | D:1796–1807, D:2102–2105; `benchmarks/runs/2026-10-21/workbench/*/tasks/resolve_*.json`, `benchmarks/runs/2026-11-04/workbench/*/tasks/resolve_*.json` |
| 11 | The page script lists every child folder of the run folder that holds an `info.json`, then indexes `info['step_first']`; a resolve folder there raises KeyError. | P:41, P:87–91 |
| 12 | The page script reads a folder's plan from `scripts/research/plans/<stem>.json` only. A stem with `_r` and no file falls back to the newest frozen plan of the pair; a stem without `_r` and no file raises FileNotFoundError. | P:18, P:58–65 |
| 13 | One measure has a numeric bar: `residual_edge_max` against 0.2 % of pixels (retrospective rule 5). The two-knob c1 draft reads 9.6 %. | `research/2026-10-20/retrospective.md` §4 rule 5; the m3probe `info.json` |
| 14 | The studio assumes the loop script in four places: the record's script md5, the pid check, the frame decode and the playback rate. Director clips run at 30 fps; the viewer plays 25. | `studio/src/reveal_studio/runner/process.py:136`, `:324`; `media/pictures.py:53`; `web/js/viewer.js:52`, `:169` |

### 1. The director stages for the studio registry

Seven stages, in the order the strip shows them. The shape is `registry/loop.py`'s `K(key, typ, default, what, flag, choices, rng)`. Each `what` and each knob sentence names its source in the comment above it. A sentence marked "studio" is new and states facts from the cited lines. Every range is `None`, because neither the renderer's `--help` nor SCHEMA.md states one for these knobs.

```python
# registry/director.py (proposal): the director flow, in the shape of registry/loop.py.
# The CLI's defaults: D:2077-2087. The settings carry layers_dir and mattes_dir (below the block).
DIRECTOR_STAGES = [
    {
        "name": "import", "title": "import", "kind": "builtin", "optional": False, "terminal": None,
        # studio; facts: layered_probe.py:152-157 (find_pair), D:420-423, SCHEMA.md:6-8 and 92-96
        "what": "The pair's two photos as the renderer reads them: the first fixtures/<pair>_S.* and fixtures/<pair>_F.* "
                "in name order, linked under raw/<pair>/ with a sha256 each. The layer tables and the mattes of both "
                "photos are located and counted.",
        "knobs": [
            # studio; the pairs some file under scripts/research/plans/ names (U:126-147 lists them the same way)
            K("pair", "str", "", "the pair: one that a plan under scripts/research/plans/ names",
              choices=["mismatch_1", "mismatch_2", "mismatch_3", "mismatch_4", "mismatch_5", "mismatch_6"]),
        ],
    },
    {
        "name": "resolve", "title": "resolve", "kind": "script", "optional": False,
        "backend": "director_render.py --resolve-only", "terminal": "anchors.json",
        # D:2085 (--help) and SCHEMA.md:271-273
        "what": "Builds the scene, writes canvas_A.png, canvas_B.png and anchors.json into OUT, and stops before the "
                "frame loop: the resolved anchors, the camera, every layer's resolved numbers and the scene's info.",
        "knobs": [
            K("plan", "plan", "", "the plan: a plan saved in this job (job:<name>) or a frozen plan (frozen:<stem>)"),
            # studio; D:2095 falls back to the first concept for an unknown name, so the studio checks the name
            K("concept", "str", "", "the concept to resolve; empty takes the plan's first", "--concept"),
            # D:2080 default 1920; the workbench allowed 480 and 1920 only (U:593)
            K("max_long", "int", 1920, "the canvas's long side in px", "--max-long", choices=["480", "1920"]),
            # D:2081 (--help)
            K("set", "object", {}, "knob=value (JSON value); 'name.param' targets a transform's params", "--set"),
        ],
    },
    {
        "name": "plan", "title": "plan", "kind": "builtin", "optional": False, "terminal": None,
        # SCHEMA.md:3-4, then studio; facts: the renderer reads only the plan's pair and concepts (D:420, D:2094)
        "what": "A plan is one JSON file per pair, frozen as a tracked input. Here: one plan, one concept and the "
                "--set overrides as a dict; a frozen plan is copied into plans/ with a provenance block and never written.",
        "knobs": [
            K("plan", "plan", "", "the plan: a plan saved in this job (job:<name>) or a frozen plan (frozen:<stem>)"),
            K("concept", "str", "", "the concept the timeline and the knob table show; empty takes the plan's first"),
            K("set", "object", {}, "knob=value (JSON value); 'name.param' targets a transform's params"),
            # studio; the workbench always pre-filled (U:270-280); off keeps the acceptance argv (section 7)
            K("seed_last_round", "bool", False, "start from the knobs of the newest round render of this plan and concept"),
        ],
    },
    {
        "name": "render", "title": "render", "kind": "script", "optional": False,
        "backend": "director_render.py", "terminal": "info.json",  # info.json is written last (D:2105)
        # D:5-8 (the module docstring)
        "what": "The plan names a container in B, the anchors that attach A to it, the camera's pull-back, the "
                "transforms of A's layers into things of B and the end effect. The renderer resolves every name into "
                "pixels, renders the concept and writes the clip, a montage and info.json with every resolved number.",
        "knobs": [
            K("plan", "plan", "", "the plan: a plan saved in this job (job:<name>) or a frozen plan (frozen:<stem>)"),
            K("concept", "str", "", "the concept to render; empty takes the plan's first", "--concept"),
            # studio; P:44 splits the folder name at its last underscore, P:71 drops the tag after the first dash
            K("name", "str", "", "the variant's tag: the folder is <plan stem>_<concept>-<tag>; letters, digits and "
              "dashes, no underscore"),
            K("max_long", "int", 1920, "the canvas's long side in px: 480 for a draft, 1920 for a full render",
              "--max-long", choices=["480", "1920"]),
            # D:2080; the renderer states no range; the workbench refused outside 0.5-20 s and 1-60 fps (U:596)
            K("seconds", "float", 3.0, "the clip's length in seconds", "--seconds"),
            K("fps", "int", 30, "frames per second of the mp4", "--fps"),
            K("set", "object", {}, "knob=value (JSON value); 'name.param' targets a transform's params", "--set"),
        ],
        # always passed: --progress (D:2084: "print 'PROGRESS i n' to stderr every 5 frames and at the last"),
        # --layers-dir and --mattes-dir from the settings
    },
    {
        "name": "skeptic", "title": "skeptic", "kind": "request", "optional": False, "terminal": None,
        # P:3-4, and registry/loop.py:224 for the verdict
        "what": "A request file for the Claude Code session: a subagent reads every candidate's frames and answers with "
                "the faults to expect per clip, which the page prints from notes.json, and a verdict on the md5 it judged.",
        "knobs": [],
    },
    {
        "name": "page", "title": "page", "kind": "script", "optional": False,
        "backend": "director_page.py", "terminal": "index.html",  # written in place in the run folder (P:173)
        # P:1-5 (the module docstring)
        "what": "One page over a run folder of director_render.py outputs (<pair>_<concept>/{transition.mp4, montage.jpg, "
                "info.json}), with the plan's own words per concept, the resolved numbers, the faults to expect and "
                "the owner's grading boxes.",
        "knobs": [
            # studio; an empty title or key would let the script's own defaults through (P:27-28: the round-8 title
            # and "director_r8"), and every exported picks file would then say page "director_r8". So both are
            # computed when empty, as the loop's page stage computes its title (runner/argv.py:250):
            # the title "<pair>: round <n>", the key "<job id>_r<n>".
            K("title", "str", "", "the page's title; empty: '<pair>: round <n>'", "--title"),
            K("head", "str", "", "an HTML file placed under the title", "--head"),               # P:28, P:40, P:54
            K("key", "str", "", "the page's key: its localStorage name and the picks file's page; empty: "
              "'<job id>_r<n>'", "--key"),                                                         # P:28, P:165
            # P:29 (--help)
            K("keyframes", "str", "", "keyframes.json of the generated helpers (name -> model, seed, steps, size)",
              "--keyframes"),
        ],
        # the studio writes notes.json from the skeptic's answers and passes --notes (P:27, P:39, P:74-83)
    },
    {
        "name": "grades", "title": "grades", "kind": "builtin", "optional": False, "terminal": None,
        # P:155-160 and benchmarks/runs/2026-10-17/director_r11/director_picks_11.json
        "what": "His grade per clip in the shape of the picks files: one picture, content transforms, nothing invented, "
                "acceptable as-is and a note, with the best clip per plan.",
        "knobs": [],
    },
]
# Settings (config): layers_dir = benchmarks/runs/2026-09-28/layers_v3 (D:35; --help D:2086 "the layer tables' root"),
#                    mattes_dir = benchmarks/runs/2026-10-17/mattes (D:36; --help D:2087 "the mattes' root").
```

Stage by stage, what each needs beyond the block:

| Stage | Inputs and argv | Outputs and wall time | What the panel shows |
|---|---|---|---|
| import | a pair that a plan names: mismatch_1 (2 plans), mismatch_2 (5), mismatch_3 (5), mismatch_4 (1), mismatch_5 (5), mismatch_6 (1); mismatch_7, match_1–5 and the fabra pairs have none | `job.json` inputs with sha256; the layer and matte counts per photo | per photo the file, the element count and the matte files: mismatch_3 A 75 elements and 43 mattes (32 missing), B 56 and 51 (missing 9, 19, 24, 26, 32); mismatch_5 A 38/23, B 9/6; mismatch_2 B 22/18; the other three pairs complete |
| resolve | `.venv/bin/python scripts/research/director_render.py PLAN OUT --resolve-only [--concept C] [--max-long N] [--set k=v …] --layers-dir L --mattes-dir M` | `canvas_A.png`, `canvas_B.png`, `anchors.json`, `info.json` (no measures); 8.8–13.9 s at 1920 px | A's crop as the render uses it (re-cropped round the anchor under a disc, D:587–611), B covered to the canvas (D:426), the anchors and camera as overlays, the layer list with each beat's window, `motion.adjusted` |
| plan | the plan, the concept, the `--set` dict | a job plan under `plans/` only when saved | section 4: the timeline, the concept's knobs, the 28 global keys, the extra lines, the command |
| render | the resolve's argv without `--resolve-only`, plus `--seconds`, `--fps`, `--progress` | `transition.mp4`, `montage.jpg`, `info.json`; 480 px drafts 10.3–13.7 s, 1920 px renders 32.8–66.4 s | the progress number from `PROGRESS i n` (the last line reads `PROGRESS 89 90` at 90 frames; the measures then run for a few seconds without a line), the viewer, the measures of section 3 |
| skeptic | a request with each candidate's md5 | `answers/skeptic_<stamp>.json`, with `look` and `faults` per candidate added to the loop's answer shape | the verdict chip; the faults as markers |
| page | `.venv/bin/python scripts/research/director_page.py RUN --notes N --title T --key K [--head H] [--keyframes J]` | `RUN/index.html`, printed as `<path> <n> clips` (P:174) | the page and its md5 |
| grades | the picks object | `picks/director_picks_<stamp>.json` | the form of section 4 |

The full `anchors.json` shape (D:1801–1805), with the values of c1 at 1920 px from `benchmarks/runs/2026-11-04/workbench/mismatch_3_20261104-144718_0195/analysis/resolve/anchors.json`:

```
{"pair": "mismatch_3", "concept": "c1", "canvas": [1920, 1440],
 "frames": 90,                                   # round(seconds * fps); the resolve takes the CLI's 3 s and 30 fps
 "anchors": {},                                  # {"a0": {"centre": [x, y], "radius": r}, "b0": {…}} under a disc only (D:611)
 "layers": [{"name": "pane_becomes_view", "by": "keyframe_chain", "window": [0.3, 0.92], "depth": "inside"}],
     # per layer when present: centre, r, k_end, end_blob (recede); theta, off0, off1, pivot (line_to); arrive (guarded);
     # face_A, face_B, box_A and box_B are listed at D:1802, and no layer sets them
 "info": {"canvas", "ls_canvas", "pair", "concept",
          # disc: circle_fit, A_anchor, A_r, B_anchor, B_r, end_scale, shiftA, camera "sim" (D:616)
          # quad or rect: quad, front_in_quad_share, camera, start_zoom (D:655)
          "zoom_centre", "start_zoom", "parallax": {gain, push, sources, dB_ref, dA_ref, dB_range, dA_range},
          "front_elements": [[id, disparity, "forced"?], …], "front_holes", "front_share", "front_soft", "front_per_element",
          "motion": {kind, edge, overlap, adjusted, beats: [{name, window, ease, edge}], held?},
          "guard": [{name, arrive, share_B}], "unplaced", "plate_A_share"?, "sky"?, "matte_fallbacks", "layers": […]},
          # c1: 44 front layers; matte_fallbacks mismatch_3_F 19, 24, 26, 32; guard []; beats pane_becomes_view trapezoid 0.35
 "camera": {"kind": "homog", "S_A3": [[…], […], […]]},   # "sim" or "homog" (D:349-355)
 "renderer_md5": "05cd6e1d95adbb3c83313b98b3f43815"}
```

An optional branch keeps the workbench's Analysis verdict: `reveal.py align` and `transitions.py pair --max-long 480 --seconds 1` (U:437–446). It reads "unrelated (Reveal refused, class B)" on mismatch_3 (U:461–473). It belongs to the pair flow's relation stage (`STUDIO.md §2`); the director flow renders without it.

### 2. The `--set` key table as data

The renderer reads 28 top-level keys: 26 through `knobs.get(` at 25 sites, plus `guard` (D:447) and `end_window` (D:1811). It also reads 18 sky keys under a disc and 60 transform keys. Two of the 28 top-level keys change nothing (table D). The keys that change a render therefore number 26 + 18 + 60 = 104. Table D's other 6 keys are stored and never read. The workbench's globals table (U:165–187) lists 21 of the 28. The other 7 were reachable only through a plan knob or the extra lines box (U:202, U:1034): `front_ids`, `parallax_sources`, `parallax_A_elements`, `sky`, `end_window`, `end_kind`, `end_radius_px`.

Table A, the top-level keys. "Effect only when" is the condition under which the renderer reads the key at all.

| Key | Type, range | Default when unset (source) | Read at | Plan path (U:190–201) | Effect only when | Sentence (source) |
|---|---|---|---|---|---|---|
| `motion` | str: continuous, legacy | the concept's `motion.kind`; absent is off | D:443 | — | always | "knob `motion=continuous` turns the model on for an old plan, `motion=legacy` off" (SCHEMA.md:194–195) |
| `guard` | bool | the concept's `reveal.guard`, else on when the motion model is on (D:449) | D:447 | — | a transform with a `b`, other than colour, hold or exit (D:1332) | "B's target of every transform that has a `b` … cannot show before the transform has delivered it" (SCHEMA.md:201–203) |
| `end_scale` | float | `pullback.params.end_scale`, else the concept's `params.end_scale`, else rB / rA; 0 also derives | D:613 | `pullback.params.end_scale` | a disc container | "the scale from `params.end_scale` or from the two radii" (SCHEMA.md:43); "`end_scale` is read under a disc only" (SCHEMA.md:279) |
| `front_ids` | list of int | `container.spec.front_ids`, else [] | D:628 | `container.spec.front_ids` | quad or rect | "elements forced into B's front layer whatever their depth" (SCHEMA.md:117–118) |
| `cont_feather` | float, frame px | `container.params.feather_px`, else 1.0 | D:653 | `container.params.feather_px` | quad or rect | "softens a rect or quad container's edge in frame px" (SCHEMA.md:277) |
| `parallax_sources` | list: "A", "B" | `pullback.parallax.sources`, else ["A", "B"] | D:677 | `pullback.parallax.sources` | the plan's parallax kind is depth and the plan's own gain is above 0 (D:676) | no sentence in SCHEMA.md; the photos whose depth maps move (D:681–682) |
| `parallax_gain` | float, 0–1 (SCHEMA.md:46) | `pullback.parallax.gain`, else 0.3 | D:678 | `pullback.parallax.gain` | the same gate: this key cannot switch parallax on | "near moves more than far, `gain` 0–1" (SCHEMA.md:45–46) |
| `parallax_gain_A` | float | `pullback.parallax.gain_A`, else the gain in effect | D:679 | `pullback.parallax.gain_A` | the same gate | "the depth gain inside A (default = `gain`)" (SCHEMA.md:83–84) |
| `parallax_blur` | float, px | `pullback.parallax.blur`, else 6.0 | D:680 | `pullback.parallax.blur` | the same gate | no sentence in SCHEMA.md; the sigma of the blur on both disparity maps (D:681–682) |
| `parallax_A_elements` | list of int | `pullback.parallax.a_elements`, else none | D:703 | `pullback.parallax.a_elements` | the same gate, "A" among the sources | "the depth parallax inside A acts on those elements only" (SCHEMA.md:114–116) |
| `parallax_push` | float | `pullback.parallax.push`, else 2.5 for quad or rect, 0.0 otherwise | D:709 | `pullback.parallax.push` | the same gate | "sets how far B's front starts beyond the frame; 1.5 brings it in sooner" (SCHEMA.md:178–179) |
| `push_floor` | float | `pullback.parallax.push_floor`, else 0.3 | D:711 | `pullback.parallax.push_floor` | the same gate, a push above 0 | no sentence in SCHEMA.md; the floor of the disparity difference the push scales (D:409) |
| `front_in` | float, clip fraction | `pullback.parallax.front_in`, else 0.15 | D:712, D:1945 | `pullback.parallax.front_in` | the same gate, a front layer | no sentence in SCHEMA.md; B's front fades in while the camera's ease runs from 0 to this value (D:1945) |
| `front_margin` | float, disparity | `container.spec.front_margin`, else 0.05 | D:715 | `container.spec.front_margin` | quad or rect, the gate, "B" a source | "keep in the front only the elements nearer than the container by a margin (per element mean)" (D:714) |
| `front_hole_max` | float, share of the frame | 0.005 | D:779 | — | a front layer | "only small holes are filled (a gap between a hand and a sofa)" (D:776) |
| `plate_fill` | str: pullpush, telea | "pullpush" | D:793 | — | a front layer | "knob `plate_fill=telea` restores cv2.inpaint" (SCHEMA.md:176–177) |
| `front_per_element` | bool | true | D:823 | — | a front layer | "knob `front_per_element=false` restores the single layer" (SCHEMA.md:160–162) |
| `plate` | bool | true | D:869 | — | always | "the knob `plate=false` turns it off for the whole render" (SCHEMA.md:99–100) |
| `sky` | object | `container.params.sky`, else {} | D:1438 | `container.params.sky` | a disc container | the whole sky dict; `sky.<k>` keys merge into it (D:1439–1441) |
| `key_end` | float, clip fraction | the concept's `params.key_end`, else 0.45 | D:1450 | none; the workbench reads `container.params.sky.key_end` (U:186) | a disc whose sky lacks `key_window` | no sentence in SCHEMA.md; the end of the sky key's window (D:1450) |
| `hole_reveal_from` | float | 0.1 | D:1477 | — | never (table D) | "when holes start to reveal" (U:184) |
| `hole_reveal_over` | float | 0.35 | D:1477 | — | never (table D) | "over how long holes reveal" (U:185) |
| `reflect` | float | `container.params.reflect`, else `container.spec.reflect`, else 0.18 | D:1814, D:1894–1896 | `container.params.reflect` | quad or rect with rim "glass" | "B's own glass content blended over A at `params.reflect`, default 0.18" (SCHEMA.md:32–33) |
| `end_window` | list [t0, t1], clip fractions 0–1 (SCHEMA.md:8–9) | the concept's `end_effect.window`, else [0.78, 1.0] | D:1811 | `end_effect.window` | always | "over its window, B replaces what remains of A" (SCHEMA.md:59–60) |
| `end_kind` | str: luma_reveal, edge_reveal, b_luma_reveal, radial_reveal | the concept's `end_effect.kind`, else luma_reveal; an unknown name orders by A's brightness | D:1908 | `end_effect.kind` | always | "in the order of A's brightness (`luma_reveal`, bright first) or from the rim inward (`edge_reveal`)" (SCHEMA.md:59–60); `b_luma_reveal` (SCHEMA.md:68–71); `radial_reveal` is in the code only (D:1912–1914) |
| `end_band` | float | `end_effect.params.band`, else 0.16 | D:1909 | `end_effect.params.band` | always | "over a wide band" (SCHEMA.md:68–70) |
| `end_radius_px` | float, A canvas px | 0.6 × the long side of A's canvas | D:1913 | — | `end_kind` radial_reveal under a disc, where the anchor a0 exists (D:611) | "far from the anchor first" (D:1914) |
| `vacated_first` | float | `end_effect.params.vacated_first`, else 0.35 | D:1917 | `end_effect.params.vacated_first` | a layer has left a footprint | "where A's layer has left, B comes first" (D:1919) |

Table B, the sky keys (`--set sky.<k>=v`; read under a disc container only).

| Key | Default (read at) | Read when | Sentence (source) |
|---|---|---|---|
| `shape` | "radial" (D:1512, D:1561) | always | "radial" or "radial_out" (SCHEMA.md:236–242); any other value is the round-9 border feather (D:1594–1596; "frame", SCHEMA.md:152) |
| `radial_end` | 1.6 (D:1520) | shape radial | "to `sky.radial_end` (1.6) sun radii" (SCHEMA.md:152–153) |
| `radial_width` | 0.35 (D:1521, D:1581) | radial, radial_out | "its edge `sky.radial_width` (0.35) of the radius" (SCHEMA.md:153) |
| `radial_near_at` | 0.25 (D:1524, D:1577) | radial, radial_out | "at the nearest frame edge of A by `sky.radial_near_at` (0.25)" (SCHEMA.md:166–167) |
| `radial_end_at` | 0.9 (D:1524, D:1577) | radial, radial_out | "at `radial_end` sun radii by `radial_end_at` (0.9)" (SCHEMA.md:167–168) |
| `follow` | 2.0 (D:1530, D:1539) | radial, the motion model on, a recede layer | "never tighter than `sky.follow` (2.0) current radii" (SCHEMA.md:228–229) |
| `follow_power` | 1.0 (D:1539) | the same | "scaled by the disc's current shrink (`sky.follow_power`, 1.0)" (SCHEMA.md:228) |
| `band` | "window" (D:1541) | radial | "`window`" or "`limb`" (SCHEMA.md:249–251) |
| `inner` | 1.2 (D:1547) | band limb | "from `sky.inner` (1.2) current luminary radii" (SCHEMA.md:250) |
| `ring` | "b" (D:1554) | radial | "`b`" or "`window`"; window is "TRIED AND WRONG" (SCHEMA.md:254–257) |
| `out_from` | 1.0 (D:1579) | radial_out | "`out_from` (1.0) sun radii is where the front starts" (SCHEMA.md:240–241) |
| `out_at` | 0.7 (D:1580) | radial_out | "it reaches the far corner at `out_at` (0.7) of the recede's progress" (SCHEMA.md:241) |
| `out_border` | true (D:1586) | radial_out | "`sky.out_border` false keeps A's border whole under the outward front" (SCHEMA.md:245–246) |
| `rim_frac` | 0.35 (D:1448) | the border feather | no sentence in SCHEMA.md; the feather's width as a share of the short side (D:1592, D:1595) |
| `key_window` | [the concept's `params.key_start` or 0.0, `key_end`] (D:1450) | always | "A's sky background gives way to B's background dark-first over `key_window`" (SCHEMA.md:74–75) |
| `key_band` | the concept's `params.key_band`, else 0.10 (D:1452) | always | "with the wide `key_band` (a slow luma crossfade, not an iris)" (SCHEMA.md:75–76) |
| `stars` | false (D:1453) | always | "B's bright points … come through A's sky in B's brightness order over `star_window`" (SCHEMA.md:73–74) |
| `star_window` | [0.1, 0.9] (D:1459) | stars true | the same sentence (SCHEMA.md:72–74) |

Table C, the transform keys (`--set <name>.<k>=v`). `window` and `mix` go to the layer (D:884–887); every other key goes into the layer's params (D:888–889). The defaults are the code's; SCHEMA.md's example values differ in places, and the code's take effect.

| Transform kind | Keys with the code's default (read at) | SCHEMA.md |
|---|---|---|
| every kind | `window` [0, 1], a list (D:877, D:885); `mix` "luma": luma, edge, noise, none, read by morph_to and move_to (D:877, D:1751); `skip` (D:891: "an operator's cut ("name.skip=true"): the transform is left out, recorded"); `plate` true (D:924, D:1389, D:1400); `hole_reveal` (D:1404); `hole_from` 0.1, 0.0 for recede (D:1407); `hole_over` 0.35, 0.15 for recede (D:1408); `a_elements` and `a_group`, every kind except colour (D:899–902) | :8–9, :20, :52–53, :99–103 |
| colour | `feather` 3.0 (D:896), `weight` "dark" under a disc else none (D:897), `strength` 0.85 (D:1503) | :55–56 |
| hold | `feather` 2.0 (D:930) | :56 |
| recede | `end_radius` 30 B px (D:936), `soften` 0.0 (D:937), `profile` linear or geometric (D:938), `end_shape` b_blob (D:939), `blob_search` 3.0 (D:942), `blob_frac` 0.6 (D:945), `limb_flatten` 0.55 (D:966), `rim_in` 0.55 and `rim_out` 1.0 (D:971), `blob_L` 110 and `blob_reach` 1.35 (D:976), `disc_scale` 1.02 (D:908, D:973), `min_L` 60 (D:908, D:1418), `plate_reach` 1.6 (D:996), `fill_in` 0.3 (D:1428), `feather` 2.0 (D:1638), `mix_window` [0.55, 0.95] and `mix_ramp` 0.5 (D:1646) | :48–50, :104–113, :155–159, :169–170, :196–198, :209–214 |
| line_to | `width` 4.0 B px and `stretch` 1.0 (D:1018), `end_taper` 0.12, 0.0 for a dark line (D:1021), `thin_power` 0.45 (D:1669), `mix_window` [0.3, 0.9] (D:1688) | :50–51, :77–79, :97–98 |
| morph_to, move_to | `mass` by the a-mask's mean luma (D:1044, D:1107), `alpha` mass when dark else mask (D:1045), `alpha_L` [0.12, 0.35] (D:1046), `margin` 0.15 (D:1057), `work_px` 3200 (D:1062), `map` box (D:1079), `rotate` (D:1079), `iso` true (D:1100), `ot_weight` 0.35 for the axis map else 1.0, range 0–1 (D:1104), `feather` 0.0 (D:1116), `end_taper` 0.0 (D:1120), `ot_grid` 64 and `ot_eps` 0.04 for morph_to (D:1126), `seed` 7 and `noise_px` 24 (D:1142), `mix_window` [0.25, 0.9] (D:1744), `grow_matte` true (D:1760) | :51–57, :85–86, :275–276 |
| exit | `direction` left, `fade` 0.3 (D:1155), `feather` 1.5 (D:1164) | :80–82 |
| keyframe_chain | `keyframes` [] (D:1178; generated pictures, which the page labels), `frame` canvas or A (D:1181), `lead` true (D:1207), `face_guide` true for the lead and "not the whole frame" for the segments (D:1208, D:1236), `matte_grow` 0.03 (D:1229), `guide` true (D:1240), `damp` 0.5 with a face guide else 1.0 (D:1258), `times` even, a list or "arc" (D:1278–1290), `arc_floor` 0.2 (D:1282) | :119–131, :135–149, :215–217 |
| the guard, on a kind with a `b` other than colour, hold or exit | `reveal_ahead`, true for recede (D:1334); `arrive`: the chain's first knot after a lead, else 0.95; for the other kinds the end of `mix_window` (D:1343–1345) | :199–206 |

Table D, the 8 keys without effect.

| Key | Why (line) | What the studio's table does |
|---|---|---|
| `<name>.ease` | read from the plan at D:878, before the knob loop at D:881 | a read-only row: "edit the plan's `params.ease`" |
| `<name>.edge` | read from the plan at D:879; SCHEMA.md:221 lists `name.edge=0.2` as a knob | read-only; the plan knob `bridge_to_arm.params.edge` of `mismatch_5_r12.json` c1 maps here |
| `<name>.rate` | read from the plan at D:880; SCHEMA.md:222 lists `name.rate=fast_in` | read-only; the plan knob `cumulus_gathers.params.rate` of `mismatch_1_r12.json` c1 maps here |
| `<name>.depth` | `depth` is a transform key read as `tr["depth"]` (D:877, D:1136), never from params | read-only |
| `<name>.hide_target` | read from the plan's params in `hide_targets_in_plate` (D:751) | read-only |
| `hole_reveal_from`, `hole_reveal_over` | every layer with a footprint sets its own `hole_from` and `hole_over` (D:1407–1408, D:1429–1432), so the fallback at D:1485 never fires | read-only; the rows `<name>.hole_from` and `<name>.hole_over` instead |
| `sky.key_end` | the sky dict has no `key_end` reader (D:1448–1459) | refused as an unknown key; `sky.key_window` instead |

`key_end` itself counts among the 104: it changes the render on a disc without `key_window`. Among the frozen plans that is `mismatch_5.json` (round 8, concepts c1 and c2) only.

Some plan keys have no `--set` path, so a change to one needs a saved plan:

| Plan key | Read at |
|---|---|
| `motion.edge`, `motion.overlap` | D:879, D:1311 |
| `reveal.ramp`, `reveal.band` | D:450 |
| `pullback.ease`, `pullback.parallax.kind` | D:1818, D:674–676 |
| the container's kind, rim and geometry (`spec.box`, `spec.points`, `spec.radius`, `spec.front_groups`) | D:584–655, D:855 |
| the anchors; each transform's `by`, `a` and `b`; the concept's `params.occluder_row` | D:585–611, D:874–1303, D:600 |

The workbench's plan-knob map over the 19 frozen plans: 71 knob rows in 23 concepts, 45 distinct names. It marks 5 rows read-only. Two of those are valid `--set` keys written in the key form instead of the plan-path form: `clouds_become_clouds.ot_weight` and `clouds_through_keyframe.times` (`mismatch_1_r13.json`). The studio's map should accept both forms. Two read-only rows are geometry with no `--set` path (`container.spec.box`, twice), and one is prose (`mismatch_3.json` c1).

The drift items, and what the studio's table does:

| Item | The renderer | The workbench | The studio's table |
|---|---|---|---|
| `key_end`'s default | the concept's `params.key_end`, else 0.45, ignored when the sky has `key_window` (D:1437, D:1450) | `container.params.sky.key_end`, else 0.45 (U:186) | the default from `params.key_end`; the row enabled only under a disc whose sky lacks `key_window`, else pointing at `sky.key_window`. No frozen plan sets either path, so both read 0.45 today |
| `end_radius_px`, `end_kind` | read at D:1908 and D:1913 | the extra lines box only (U:165–187 lacks both) | first-class rows with their conditions |
| `key_start` | the concept's `params.key_start`, no `--set` key (D:1450) | unreachable | reachable as `sky.key_window=[start, end]` under a disc (D:1439–1441, D:1450) |
| one dot per key | routes on the first dot (D:883, D:1441) | the key pattern allows one dot (U:602, U:1039) | keep one dot: a second dot lands on a key nobody reads; `sky.shape` has one and passes |
| `parallax_gain_A`'s shown default | the gain in effect, the knob's when set (D:679) | the plan's gain (U:168) | the gain in effect |

### 3. The measures of `info.json`

The values in the last column are the two-knob c1 draft of the eighth line, 90 frames at 480×360. That DECISIONS line is the durable source for 2.37, 4, 0, 84 and 0.09647; the other values were read today from the scratch copy of its `info.json`. The series use different frames: `motion_px` has one value per pair of neighbouring frames, `b_inside` one per third frame. A shared frame axis has to place each value at its own frame index.

| Measure | Meaning (source) | Unit | Shape | Bar (source) | c1 draft |
|---|---|---|---|---|---|
| `motion_px` | the mean DIS flow between consecutive decoded frames, computed at 480 px or less and scaled to frame px (D:2038–2045; SCHEMA.md:191–193) | frame px per frame | n − 1 floats; entry j is frames j → j + 1 | no bar stated for the whole frame; rule 2's speed bars are per element (retrospective §4 rule 2) | 89 values |
| `motion_median_px` | the median of `motion_px` from 10 % to 90 % of the list (D:2048–2049) | px | scalar | no bar stated | 2.37 |
| `motion_pauses` | entries in that span under a fifth of the median (D:2050; SCHEMA.md:193–194) | count | scalar | no bar stated | 4 |
| `motion_jumps` | consecutive entries that differ by more than max(1 px, half the median), over the whole list (D:2051); SCHEMA.md:194 omits the 1 px floor | count | scalar | no bar stated | 0 |
| `b_inside` | on every third frame and the last, the share of A's region (inside the camera's view, and inside a quad or rect) where B shows, read after the guard (D:1936–1942; SCHEMA.md:207–208) | share 0–1 | [frame, share] pairs: 31 | rule 1: B's share before its beat is 0, except a declared early region (retrospective §4 rule 1) | — |
| `b_inside_first` | the first sampled frame above 1 % (D:2055; SCHEMA.md:208) | frame or null | scalar | at or after the first beat's start (rule 1); the 1 % is the measure's own threshold | 84; the beat starts at frame 31 (t 0.35) |
| `residual_edges` | on every third interior frame, the share of pixels at 720 px or less that are Canny edges of the frame and lie more than 3 px from every edge of A and of B through the camera (D:1985–1995). SCHEMA.md:218–219 calls it a share of the frame's edges; the code divides by all pixels | share of pixels | [frame, share] pairs: 29 | 0.2 % of pixels, with no circle or line over 40 px among them (retrospective §4 rule 5) | max 0.09647 |
| `residual_edge_max` | the maximum (D:2056) | share | scalar | 0.002 (rule 5) | 0.09647, 48 times the bar |
| `halo` | on every third interior frame, when a recede layer sits under a disc: [frame, the largest step between 10 px radial bins, the deepest ring, the blob's radius] round the brightest blob's core, from 1.2 to 5 blob radii (D:2002–2036; SCHEMA.md:265–269) | L levels (8-bit Lab), px | 4-tuples: 29, else null | no bar stated | null |
| `halo_step_max` | the largest step (D:2057) | levels | scalar or null | no bar stated; SCHEMA.md:243–245 and backlog T62 item 2 ask that an outward front stay under B's own steepest gradient, which `info.json` does not carry | null |
| `halo_ring_max` | the deepest ring (D:2058) | levels | scalar or null | no bar stated; T62 item 4 asks the measure to read small radii | null |
| `guard` | the guarded targets: name, the beat progress at which B's target may show, the share of B the grown target covers (D:1348) | list of {name, arrive, share_B} | — | no bar stated | [] |
| `guard_share_max` | the largest share of the frame where the guard held A's base (D:1935, D:2054) | share | scalar | no bar stated | 0.0 |
| `step_first`, `step_second`, `step_last`, `step_max` | the mean absolute difference over three channels between consecutive decoded frames: 0 → 1, 1 → 2, the last pair, the largest (D:2014, D:2052) | levels | 4 scalars | no bar stated in the director documents. Rule 2's whole-frame bar (no run of more than 3 frames under 0.3 levels while a beat is open, retrospective §4 rule 2) needs the full series, which the studio must decode (U:658–685) | 0.27, 0.04, 0.04, 22.38 |
| `plate_A_share` | the share of A's canvas filled under its lifted layers (D:1393–1398); the code fills by pull-push (D:1397), while SCHEMA.md:100–101 and P:143 say cv2.inpaint | share | scalar, absent without a lifted layer | no bar stated | absent |
| `matte_fallbacks` | "photo:id" of each element drawn with its hard mask because its `el_<id>.png` is missing (D:224–230, D:1464; SCHEMA.md:93–96). The list depends on the canvas and the knobs: 4 at the 1920 resolve, 3 here, 0 in the four-knob draft | list | — | no numeric bar; rule 5 names any fallback as a source of hard edges | mismatch_3_F 24, 26, 32 |
| `unplaced` | {name, why} of each transform left out: an empty a-mask, the operator's skip, no keyframes (D:891–893, D:925–928, D:1179–1180) | list | — | no bar stated | [] |
| `motion.adjusted` | {name, from, to, after}: a beat moved earlier to overlap the one before (D:1311–1320; SCHEMA.md:188–190) | list | — | no bar stated | [] |
| `motion.held` | {name, end_from, end_to, for, overlap_of_target}: a layer's end held until the guard releases (D:1364–1379; SCHEMA.md:224–227) | list, absent when empty | — | no bar stated | absent |
| `chain.segments` | per segment of a chain, under `layers[].chain`: {disp_median_px, lead, consistency_mean} (D:1294–1296; SCHEMA.md:130–131) | px, share | list | no gate; the retrospective §6 item 4(i) aims each segment's consistency above 0.5 | the 1920 resolve reads 0.409 and 0.012 |
| `wall_s` | seconds from the scene's start to the end of the measures; the montage and the JSON come after (D:1791, D:2053) | s | scalar | no bar stated | 13.7 and 12.7 |
| `renderer_md5`, `transitions_md5` | the md5 of the two files at the run (D:2100–2101) | hex | 2 scalars | equal to the recorded md5 for a reproduction (the eighth line) | 05cd6e1d…, 7ef5dcae… |
| `plan_sha256` | the plan's sha256, first 16 hex characters (D:2099) | hex | scalar | the record keeps the full sha256 | adec1345aeb6cc96 |

`info.json` holds no md5 of the mp4, so the record's outputs list has to carry it.

### 4. The workbench's page, panel by panel

| Panel (U lines) | What it shows and does | The studio has (its form) | New for the director flow |
|---|---|---|---|
| Rail (926–927, 950–956, 965) | the pairs with a plan (a click makes a job); the jobs with their render counts; the tasks with state, progress, elapsed seconds and cancel | the rail: jobs, running entries with stage, name, progress and elapsed time; cancel in the inspector | a pair picker for a new director job |
| Inputs (950–956) | per pair: the A and B files, layers yes or no, matte counts, plans with the newest last, "new job"; the renderer's flag status | the import tile (a folder of stills) | the pair table with the layer and matte status of both photos |
| Analysis (975–999) | the relation in words (461–473) with Reveal's numbers and the transitions class; the anchors.json link; overlays (elements, disparity) per photo with "toggle both photos together" and an opacity slider; a click on an element row shows its matte; element tables (id, label, group, area, depth rank, disparity, matte file or hard); labels found in both photos with their shares (495–503) | "show" sends any picture to the viewer; the readers panel (loop) | the overlays (section 5), the element tables, the label overlap table, the resolve's canvases and anchors; the verdict through the pair flow's relation stage |
| Plan (1015–1040) | plan and concept selects; path, sha256, relation, planner; idea and risk; the concept's knobs with range, default and the `--set` key, read-only rows with their reason (1022); the 21 globals with a "set" box and the default for this concept (1027–1033); "clear all knobs" and "reset to last round" (1027); extra `key=JSON` lines (1034); the `--set` preview (1035, 1040) | the inspector's knob rows (key, value, range, default, sentence, reset); the plan editor's JSON tab; the copyable command line | the `--set` table of section 2 with each row's condition; the concept-knob map in both name forms |
| Timeline (1042–1059) | a 900 px track over clip time 0–1; one bar per transform window and one for the end effect; drag the middle to move, within 6 px of an end to resize; rounded to 0.01, at least 0.02 wide, clamped to 0–1; on release `<name>.window=[a, b]` or `end_window`; a changed bar orange, a muted one at 30 % opacity; "mute" sets `<name>.skip=true`, "solo" mutes every other beat; under the motion model a note says the renderer may move beats (1049) | the loop editor's bars over frame counts (`plan.js`) | the clip-time bars with drag and resize, mute and solo; also the resolved windows from `motion.adjusted` and `motion.held`, which the workbench never drew (T60) |
| Render and review (1062–1106) | seconds and fps fields; draft 480, full 1920, re-render from `render.json`; the progress line "frame i/n (p %)" with elapsed time and an expected wall from the last render of that size (404–411); the log's last 20 lines; the renders table; the video; the scrubber with frame buttons and arrow keys; three SVG charts on one x: `motion_px` with pauses orange and jumps red by the renderer's rule (1088), the step series decoded from the clip (658–685), `b_inside` with its first frame red; the A (frame 0), frame, B (last frame) strip; "mark this frame" copies the PNG into `owner_frames/` and adds it to the grade (1105) | the render tile with progress and log; the candidates list; the viewer (single, wipe, A/B, onion, difference at fit, 1:1, 2×); the scrubber and the shared frame axis; playback at 25 fps; mark a frame (a JSON record with the md5 and a note); rerun with the last knobs | the director's plots: `motion_px` with the renderer's pauses and jumps, `b_inside` with its first frame, `residual_edges` with the 0.2 % bar, `halo`; the step series computed on decode; playback at the clip's fps |
| Grade (1109–1130) | one form per finished render tagged `<plan>_<concept>-<rid>`: the three boxes, acceptable as-is, the marked frames, a note; best per plan stem; save; the newest picks file pre-fills the form (1113) | the grades panel: his words verbatim per round, the round gate, the review gate | the picks-shape form beside his verbatim words |

### 5. The overlays

`overlay_png` (U:526–579) draws four kinds on the layer table's canvas and scales them to a long side of 960 px (U:59, U:535–537). Each result is cached as `analysis/overlays/<A|B>_<kind>.png` with a plain write, which the review called a non-atomic write (ui1_review.md "Later").

| Kind | How it is built | What the studio's `media/` needs |
|---|---|---|
| base | the fixture photo read by cv2, scaled to cover the table's canvas and cropped at the centre (U:518–523, U:538–543) | the same crop; the resolve's `canvas_A.png` is the crop the render uses when a disc re-crops A |
| elements | `layers.npz["element"]` (uint16 ids); each element filled with its group's colour scaled by `0.7 + 0.6 × frac(id × 0.618)` at alpha 150, element borders by a 3×3 morphological gradient in white at alpha 230; resized by nearest neighbour (U:546–555) | a colour for every group: the table at U:513–515 lacks 11 of the 22 groups in the layer tables (animal, appliance, cloud, floor, luminary, opening, picture, star, structure, tree, vegetation), which draw grey |
| disparity | `layers.npz["disparity"]` clipped to 0–1, the TURBO colour map at alpha 200 (U:556–559) | the same |
| matte_&lt;id&gt; | `<mattes>/<photo>/el_<id>.png` as grey, or the hard element mask when the file is missing; magenta at 0.75 × alpha with the outline of alpha above 127 in yellow, at least 2 px wide (U:560–573) | the same, with the fallback named on screen |

The inputs, as found for mismatch_3:
- `layers.json` holds `canvas` [1920, 1440], `canvas_mode`, `elements`, `frame`, `merge`, `photo` and `provenance`. Each element has 21 keys; the workbench uses `id`, `label`, `group`, `area_share`, `depth_rank` and `median_disparity`.
- `layers.npz` holds six arrays at 1440×1920: `disparity` (float32, 0–1), `edges` (uint8), `element` (uint16), `label` (uint16), `normals` (int8, 3 channels) and `saliency` (uint8).
- A matte folder holds `el_<id>.png` per element plus `mattes.json` (the model, its revision and an md5 per element) and `sheet.jpg`. `mismatch_3_F` has 51 matte files in 53 entries.

The disparity source is the layer table's: Depth Anything V2 Small through `transitions.model_disparity`, at the table's canvas (the `provenance` block of `layers.json`). The render computes its own disparity at its canvas and blurs it by `parallax_blur` (D:681–682). Whether the two maps agree numerically is UNVERIFIED.

### 6. A job folder layout for a director job

The layout keeps `STUDIO.md §4` and the loop job's rules (`job.json` with `root`, records under `stages/`, a candidate never overwritten). Its run folder is shaped so that the page script can read it unchanged.

```
benchmarks/runs/<date>/studio/director_<pair>_<stamp>/
  job.json        {id, flow: "director", created, ui_version, root: "<job>/run", pair,
                   inputs: [{side: "A"|"B", name, path: "fixtures/<pair>_S.jpg", sha256, bytes, link: "raw/<pair>/A.jpg"}],
                   layers_dir, mattes_dir,
                   tables: {A: {path, sha256, elements}, B: {…}}, mattes: {A: {count, missing: [ids]}, B: {…}},
                   helpers: [{path, sha256}]        # the keyframes the job's plans name, outside the job
                   adopted: false}
  raw/<pair>/A.jpg, B.jpg       links to the files find_pair picks (layered_probe.py:152-157); records only,
                                because the renderer reads fixtures/ by the plan's pair (D:420-421)
  stages/<stamp>_<stage>/       stage.json, log.txt, done; the record's script_md5 is the renderer's (or the page
                                script's), with transitions_md5, the plan's full sha256 and the mp4's md5 in outputs
  resolve/<stamp>/              canvas_A.png, canvas_B.png, anchors.json, info.json: outside run/ (P:41, P:87-91)
  plans/<name>.json             byte copies of the frozen plans used, and saved plans, each with a provenance block
  run/                          the run folder (job.json root), read by director_page.py RUN
    <stem>_<concept>[-<tag>]/   the full renders: transition.mp4, montage.jpg, info.json
    index.html                  the page (P:173; the previous one kept beside its record before a rebuild)
    notes.json                  {"<stem>_<concept>[-<tag>]": {"look": "…", "faults": "…"}} (P:74-83)
    head.html, keyframes.json   optional (P:28-29)
    drafts/<stem>_<concept>[-<tag>]/   the 480 px drafts: drafts/ itself holds no info.json, so the page never
                                lists one (P:41), as round 13's director_r13/drafts3/ shows
  requests/, answers/           the skeptic's inbox and answers
  rounds/<n>/round.json, index.html  the candidates, the page md5, the override, the grade (the picks file and his words)
  picks/director_picks_<stamp>.json
  owner_frames/<kind>_<name>_f<i>.json
  cache/                        decoded frames and the step series per render (derived)
```

Rules the layout needs:
- A render folder is `<stem>_<concept>[-<tag>]`, where stem is the frozen plan's file name. The tag uses letters, digits and dashes: the page script splits at the last underscore (P:44) and keeps the part before the first dash as the concept (P:71). Round 13 used `-out` and `-wide`; round 8 used `-full` and `-nosit`.
- The first render of a stem and concept may skip the tag; every later one needs a new tag, because a finished render is never overwritten.
- A render of a plan saved in the job is named under its source's frozen stem. The page then prints the frozen plan's words beside the render's knobs (P:119–122). The alternative is a new default-off `--plans-dir` flag on the page script. That is a decision, and the flag's default path needs a byte-identity proof, as the loop script's flags had.
- The page script writes `RUN/index.html` in place and has no output flag, so the `.part` rename cannot wrap it. The runner therefore copies the existing `RUN/index.html` beside the new record before it starts the script. The loop's page stage keeps its previous page the same way, at the rename.
- Generated keyframes appear on the page as `<img>` tiles. A tile's source is the plan's repo path when the file lies outside the run folder's parent (P:131–136). The studio's file route refuses such a path (`contracts.md`, studio section). The tile then breaks, unless the route serves the helpers a job's plans name (UNVERIFIED by a drive).

The candidate shape, beside the loop's:

| | Loop candidate | Director candidate |
|---|---|---|
| folder | `<root>/<seq>/<name>/`, drafts under `<root>/drafts/<seq>/` | `<root>/<stem>_<concept>[-<tag>]/`, drafts under `<root>/drafts/` |
| clip | `loop.mp4`, `loop.gif` | `transition.mp4`, `montage.jpg` |
| measures | `measure.json` (step series, seam, faces, md5s) | `info.json` (section 3); no mp4 md5 and four step values only |
| frame tags | `frames.json` | none; the beats' windows from `info.json["layers"]` and `motion` |
| identity | `md5_mp4` in `measure.json` | the record's outputs, `renderer_md5` and `transitions_md5` in `info.json` |

The loop's `candidates()` requires `measure.json` and reads `<root>/<seq>/` (`studio/src/reveal_studio/jobs/candidates.py:15–33`), so it would list no director render. A director candidate reader is needed: a folder with `info.json` and `transition.mp4`, its md5 taken from the record that wrote it.

### 7. The acceptance test for mismatch_3 on the studio

The proposed test is `studio/tests/acceptance/test_b_director_flow.py`, in the shape of `test_a2_loop_flow.py`. It starts a `reveal-studio serve` subprocess on a free port with a temporary lock against the real tree. It then drives the API within a budget of 3 minutes. It skips when the renderer's md5 differs from 05cd6e1d…, because the md5 belongs to that renderer. It also skips when the main venv, the fixtures, the layer tables or the depth model are absent.

```python
PAIR, PLAN, CONCEPT = "mismatch_3", "frozen:mismatch_3_r12", "c1"
PLAN_SHA256 = "adec1345aeb6cc96100b29c63a5e440c95ce37cadc720780207b7bc47a9e5aaa"
KNOBS = {"parallax_push": 2, "pane_becomes_view.window": [0.35, 0.97]}   # two knobs: the eighth line's argv
MD5_DRAFT = "01b3cf3c769ee45e44a73f1ade36a3b6"     # 480 px, 3 s, 30 fps, renderer 05cd6e1d..., DECISIONS 2026-11-05 eighth line
RENDERER_MD5, TRANSITIONS_MD5 = "05cd6e1d95adbb3c83313b98b3f43815", "7ef5dcae070c223e360c9c2e533df6c1"
PHOTO_SHA256 = {"A": "b40d042bc390244796ecee27a9164529a7713533df0963bb6765080e444e27c9",
                "B": "bd04d1e782ce2f842e912203f513019d1304deb90d6af3a96d35d02a41d617ed"}
```

| # | Check | PASS when | Red under the mutation |
|---|---|---|---|
| 1 | a job by pair name: `POST /api/jobs {flow: "director", pair: "mismatch_3"}` | 201; two inputs with the sha256s above; the links resolve to `fixtures/mismatch_3_S.jpg` and `_F.jpg`; A 75 elements and 43 mattes, B 56 and 51 with 9, 19, 24, 26, 32 missing; `mismatch_7` answers 400 and makes no folder | the import copies a photo; the matte count includes `mattes.json` and `sheet.jpg` (53) |
| 2 | the resolve: run `resolve {plan, concept: c1}` | done in under 30 s (observed 9.5–13.9 s); both canvases 1920×1440; `anchors.json` keys exactly pair, concept, canvas, frames, anchors, layers, info, camera, renderer_md5; `camera.kind` "homog"; `anchors` {}; one layer `pane_becomes_view` at [0.3, 0.92]; `info.matte_fallbacks` mismatch_3_F 19, 24, 26, 32; the argv holds `--layers-dir` and `--mattes-dir`; the folder lies outside `run/` | the resolve writes under `run/`; `--layers-dir` is dropped |
| 3 | the plan opened, two knobs set | c1's three plan knobs map to `front_per_element`, `pane_becomes_view.times` [0] and `pane_becomes_view.window` [1]; `parallax_push` shows 2.5 (quad, no plan value, D:709); two bars, `pane_becomes_view` [0.3, 0.92] and the end effect [0.92, 1.0]; after `parallax_push` 2 and the bar typed to [0.35, 0.97], the command holds exactly two `--set` arguments | the plan stage pre-fills the round-12 knobs by default |
| 4 | a 480 px draft, 3 s, 30 fps | done; progress values seen, the last 89 of 90; `transition.mp4` md5 01b3cf3c…; folder `run/drafts/mismatch_3_r12_c1-<tag>/`; the record's renderer md5 05cd6e1d…, transitions md5 7ef5dcae…, the plan's full sha256; `info.json`'s `renderer_md5` equal | `--progress` dropped; a knob sent with another value |
| 5 | a re-render from the record's argv into a new tag | the same md5; the first draft's three files unchanged; the same tag again answers 409 | a finished render is overwritten |
| 6 | the measures shown: `GET` the render view | `motion_median_px` 2.37, `motion_pauses` 4, `motion_jumps` 0, `b_inside_first` 84, `residual_edge_max` 0.09647 marked past the 0.2 % bar, `halo` null, `matte_fallbacks` 24, 26, 32; series lengths 89, 31, 29; a decoded step series of 89 values whose first is 0.27 | the view reads `measure.json`; the decode reads `loop.mp4` |
| 7 | a frame marked: frame 47 with a note | `owner_frames/draft_<name>_f0047.json` with md5 01b3cf3c…; frame 90 answers 400 | the frame bound ignores `info.json["frames"]` |
| 8 | a grade in the picks shape | 200 and `picks/director_picks_<stamp>.json` with the top keys best, clips, date, page; `best` {"mismatch_3_r12": "c1-<tag>"}; the clip holds acceptable, note, the three props, render, draft true, frames; an extra top-level key answers 400; props without `not_invented` answer 400 | the key checks of U:695–707 dropped |
| 9 | a restart reconciles | a 1920 render started (32.8–66.4 s), the server stopped by SIGTERM after the first progress value, then started again: the record re-attaches and ends done with its md5, or ends lost when the child is killed; never running with the child gone | the pid check looks for `loop_seq.py` (process.py:324), so a live renderer reads as gone |
| 10 | the originals and the frozen files | the fixtures' mtimes and sha256s unchanged; `mismatch_3_r12.json` still adec1345…; nothing new under `scripts/research/plans/`, `fixtures/` or the layer and matte roots (a `find -newer` sweep) | a write through a `raw/` link |

The page drive keeps the checks that need a browser: the bar dragged to [0.35, 0.97], the three plots on the shared axis, the overlays, the hints.

The plan stage's pre-fill decides which anchor the drive pins. If the plan stage pre-fills like the workbench, the drive sends four knobs. No md5 for those four knobs exists under renderer 05cd6e1d…. One shell render records it, with OUT an empty scratch folder outside the repo:

```
.venv/bin/python scripts/research/director_render.py scripts/research/plans/mismatch_3_r12.json OUT --concept c1 \
  --max-long 480 --seconds 3 --fps 30 --set cont_feather=14 --set front_margin=0.3 --set parallax_push=2 \
  --set 'pane_becomes_view.window=[0.35, 0.97]'
```

If it gives 5b3ee379…, round 13 left the clip unchanged and the knobs alone moved the anchor. Any other md5 means both the renderer and the knobs changed it. The recommendation either way: pin the two-knob argv at 01b3cf3c… with the pre-fill off by default, and keep the four-knob md5 as a second watch.

### 8. The retirement checklist for `director_ui.py`

What the workbench does, and where the studio does it. "Have" means the studio already does it in its own form; "build" is phase B's work; "drop" is on purpose, with the reason.

| Workbench function (U lines) | In the studio | Status |
|---|---|---|
| the pairs with a plan, with the layer and matte status of each photo (131–147, 950–956) | the import panel | build |
| a job by pair name with both photos hashed (301–314) | import: links and sha256s | build |
| Reveal's verdict with the refusal reason, the transitions class (437–446, 461–473) | the pair flow's relation stage, an optional branch here | build (pair-flow track) |
| `--resolve-only` at job start, on the newest plan's first concept (447–451) | the resolve stage, any plan and concept, on request | build |
| element tables, labels in both photos (476–509) | the resolve panel | build |
| the four overlays, both-photos toggle, opacity (512–581, 985–999) | `media/` and the viewer's "show" | build |
| the plan's identity, idea and risk (283–290, 1015–1019) | the plan panel and the inspector | build |
| the concept-knob map with read-only reasons (205–252) | the `--set` table, both name forms | build |
| the globals with this concept's defaults (165–187) | the 28 rows with their conditions | build |
| the last round's knobs pre-filled, "clear all knobs", "reset to last round" (270–280, 1004, 1027) | the plan stage's `seed_last_round` | decide (default off proposed) |
| extra `key=JSON` lines, the `--set` preview (1034–1040) | the plan stage; the inspector's command line | build; have |
| the timeline with drag, resize, mute, solo (1042–1059) | the plan panel | build |
| draft and full renders with checked inputs (583–637) | the render stage | build |
| a re-render from `render.json` (640–645) | rerun with the last knobs | have |
| the progress line, the log tail, cancel (361–426) | the runner's records | have |
| the renders table (1073–1079) | the candidates list | have |
| the video with Range requests (787–803) | the file route | have |
| the scrubber, frame buttons, arrow keys (1094, 1100–1106) | the viewer | have |
| the three charts (1083–1099) | the shared axis | build (the director's series) |
| the A, frame, B strip (1098) | the comparator's A/B and wipe | have |
| mark a frame (883–895, 1105) | `frames/mark`: a JSON record with the md5 and a note | have |
| the grade form, picks saved with key checks, pre-filled from the last picks file (688–707, 1108–1130) | the grades stage | build |
| files under `fixtures/`, `layers/`, `mattes/` (727–740) | the file route: today the job and its root only | build (the layer and matte roots, the plans' helpers) |
| the renderer's flags read from its source text (104–111) | — | drop: the flags exist since 2026-10-21 and the renderer has no commit since (git log); the studio can probe `--help` as it does for `loop_seq.py` |
| render folders named by random ids (604) | — | drop: the page script reads `<stem>_<concept>[-<tag>]/` |
| frames and `steps.json` written into the render folder (658–685) | — | drop: a finished render's files are never written; the decode goes to `cache/` |
| completion recorded by the server's own thread (336–358) | — | drop: the runner reconciles on start and on read (T60) |
| `best` as `<concept>-<rid>` (1123) | — | drop: the round files hold "c1" or "none" (ui1_review.md finding 5); the studio writes `<concept>[-<tag>]` as the page exports (P:159) |
| the workbench folder per `--runs-date` (1142–1147) | — | drop: studio jobs are listed across dates |

The files that name `director_ui` (`/usr/bin/grep -rln director_ui --include='*.md' --include='*.py' --include='*.sh' --include='*.json' .` without `.venv` and `benchmarks/runs`). This shell's `grep` is a function that skips gitignored files, so the system grep was used.

| File | Mentions | Tracked | At retirement |
|---|---|---|---|
| `scripts/research/director_ui.py` | 2 | yes | removed by `git rm` with a DECISIONS line |
| `.claude/claude-docs/STUDIO.md` | 7 (lines 5, 9, 144, 148, 164, 178, 199) | yes | update §0, §7, §9 row B; §7's row says "retired when the studio passes §9 phase A", which disagrees with §0, §9 and §10 (phase B) |
| `.claude/claude-docs/EXPLORATION_PLAN.md` | 5 (rows UI1–UI4, lines 459–462) | yes | status of UI1–UI4 |
| `.claude/skills/reveal/references/tracked-backlog.md` | 3 (T52, T60, T77) | yes | close or supersede T52 and T60 |
| `.claude/claude-docs/research/director-tooling.md` | 1 (line 110) | yes | a dated note |
| `.claude/claude-docs/NEXT_SESSION_PROMPT.md` | 3 (lines 19, 75, 78) | no (gitignored) | rewritten at the handover |
| `.serena/memories/core.md` and three `project/wip-*` memories | 2 in core.md; 1, 1 and 2 in `wip-2026-10-20-round12-generalize.md`, `wip-2026-11-04-studio-design.md`, `wip-2026-11-05-studio-phase-b.md` | no (gitignored, machine-local) | core.md updated; the wip leaves are history |
| `.claude/claude-docs/DECISIONS.md`, `DECISIONS_ARCHIVE.md` | 4 and 4 | yes | history: append-only, never edited |
| `.claude/claude-docs/TRANSITIONS.md` | 2 (§13.22, §13.23) | yes | history; an amendment row if needed |
| `research/2026-10-20/README.md`, `ui_design.md`; `research/2026-10-21/README.md`, `ui1_build.md`, `ui1_review.md` | 1, 4, 2, 3, 13 | yes | dated research copies, left as written |
| `research/2026-11-04/lens1_feasibility.md`, `lens2_intent.md`, `trackA_inventory.md`, `trackB_distill.md`, `trackC_design.md` | 4, 3, 3, 1, 4 | yes | dated research copies, left as written |

That is 18 tracked files and 5 ignored ones.

### Relevant artifacts

| Path:line | Symbol | Purpose |
|---|---|---|
| `scripts/research/director_render.py:2077–2106` | the CLI | flags, `--set` parsing, the stamps written into `info.json` |
| `scripts/research/director_render.py:876–893` | `Scene.build_layers` | the transform keys and the three read before the knob loop |
| `scripts/research/director_render.py:1399–1459` | the plate and sky setup | `hole_from`, `hole_over`, the sky keys, `key_end` |
| `scripts/research/director_render.py:1796–1807` | `render`, resolve-only | `anchors.json` |
| `scripts/research/director_render.py:1936–1995, 2000–2058` | the measures | `info.json`'s series |
| `scripts/research/director_ui.py:165–252` | `GLOBALS`, `PATH_KEYS`, `map_knob` | the workbench's key map |
| `scripts/research/director_ui.py:270–280` | `last_round_knobs` | the pre-fill behind the four-knob anchor |
| `scripts/research/director_ui.py:526–579` | `overlay_png` | the overlays |
| `scripts/research/director_ui.py:688–707` | `save_picks` | the picks shape and its checks |
| `scripts/research/director_ui.py:907–1134` | `PAGE` | the panels |
| `scripts/research/director_page.py:25–174` | `main` | the run folder's rules, notes, keyframe tiles, the picks export |
| `scripts/research/layered_probe.py:152–157` | `find_pair` | how the renderer finds the photos |
| `scripts/research/plans/SCHEMA.md` | rounds 8–13 | the plan grammar and the knob sentences |
| `scripts/research/plans/mismatch_3_r12.json` | concept c1 | the acceptance plan (sha256 adec1345…) |
| `benchmarks/runs/2026-10-21/workbench/mismatch_3_20261021-015336_10e3/` | `renders/*/render.json`, `picks/` | the four-knob acceptance render and its picks file |
| `/private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/9041ff2b-bcdd-448e-b55d-c8250e7a4b44/scratchpad/m3probe/info.json` | — | the eighth line's two-knob render; a scratch folder that a later session will not find (DECISIONS 2026-11-05, eighth line, keeps its numbers) |
| `benchmarks/runs/2026-11-04/workbench/mismatch_3_20261104-144718_0195/analysis/resolve/` | `anchors.json` | a resolve under renderer 05cd6e1d… |
| `benchmarks/runs/2026-09-28/layers_v3/mismatch_3_S/` | `layers.json`, `layers.npz` | a layer table |
| `benchmarks/runs/2026-10-17/mattes/mismatch_3_F/` | `el_<id>.png`, `mattes.json` | a matte folder |
| `benchmarks/runs/2026-10-17/director_r11/director_picks_11.json` | — | the picks shape of record |
| `studio/src/reveal_studio/registry/loop.py:14–257` | `K`, `LOOP_STAGES` | the registry shape |
| `studio/src/reveal_studio/runner/process.py:136, 310–324` | `start_stage`, `pid_alive` | the loop-only script md5 and pid check |
| `studio/src/reveal_studio/runner/argv.py:74–100` | `coerce` | no `object` type yet for the `set` knob |
| `studio/src/reveal_studio/media/pictures.py:53` | `frames_dir` | decodes `loop.mp4` by name |
| `studio/src/reveal_studio/web/js/viewer.js:52, 169` | the axis label, `togglePlay` | playback fixed at 25 fps |
| `studio/src/reveal_studio/jobs/grades.py:76–100` | `save_grade` | the loop's grade shape (verbatim text per round) |
| `studio/tests/acceptance/test_a2_loop_flow.py` | — | the acceptance test's shape |

### Constraints discovered

| Constraint | Source | Consequence for the build |
|---|---|---|
| The renderer finds the photos by the plan's pair under `fixtures/` | D:420–421; `layered_probe.py:152–157` | a director job's links are records; the job cannot point the renderer at another file |
| A render folder's name carries the frozen stem and a tag without underscores | P:44, P:58–64, P:71 | the render stage builds the name; a saved plan renders under its source's stem |
| No child of the run folder may hold an `info.json` without the measures | P:41, P:87–91 | the resolve writes outside `run/` |
| The page script writes `RUN/index.html` in place | P:173 | the previous page is copied aside before the run |
| An unknown concept falls back to the first without a message | D:2095 | the studio checks the name against the plan |
| `round(seconds × fps)` must be at least 3 | D:1795, D:1822, D:2052 | the render stage refuses fewer frames |
| The renderer prints no `FAILED:` line; every failure exits 1 with a traceback or the `find_pair` message | D (no `FAILED`), `layered_probe.py:156` | a failure is `failed` with the log's last line; the `refused` state never applies |
| `info.json` holds no md5 of the mp4 and a 16-character plan sha256 | D:2099–2105 | the record carries both in full |
| Parallax runs only when the plan's own kind is depth and its gain is above 0 | D:674–676 | `parallax_gain` cannot switch parallax on; its row says so |
| A chain reads plan-named keyframes outside the job | `mismatch_3_r12.json` (`benchmarks/runs/2026-10-17/keyframes_r10/out/r10_m3_pane.png`) | the import hashes them as inputs; the file route serves them for the page |
| The face model's path is fixed; without it a chain with a face guide changes and prints an INFO line | D:268, D:280–283 | the import reports its presence; mismatch_3 c1 uses no face guide (a whole-frame chain without a lead) |
| `--layers-dir` and `--mattes-dir` rebind the module's roots and land in `info.json` as absolute paths | D:2089–2092, D:2102 | the settings pass both on every resolve and render |
| The runner, the decode and the playback assume the loop | process.py:136, :324; pictures.py:53; viewer.js:169 | each takes the flow's script, clip name and fps |

### Confidence: 85%

The stage table, the key tables and the measures rest on line-anchored reads of the renderer, the workbench, the page script and SCHEMA.md. They were checked against the 19 frozen plans and the records on disk. No render ran, so each claim about a key without effect stands on reading alone. The four-knob md5 under 05cd6e1d… is also unknown. These keep the figure below 90 %.

### Gaps

| Gap | Effect | How to close |
|---|---|---|
| No render, server or page ran: the research brief allowed read-only commands only | the 8 keys without effect are read from the code only; the four-knob md5 under 05cd6e1d… is unknown | one shell render of the four-knob argv (section 7); a draft with `--set pane_becomes_view.edge=0.1` beside one without, compared by md5 |
| Tool failures: the advisor call timed out once; this shell's `grep` skips gitignored files (the first sweep missed `NEXT_SESSION_PROMPT.md` and four Serena memory files); a zsh glob without matches stopped one loop ("no matches found"); an awk pipeline split its fields wrongly | each was rerun: the sweep with `/usr/bin/grep`, the glob and the scan in Python | — |
| Read in part only: `director_render.py` 1600–1776 (the compositing, read where a search pointed), `studio/src/reveal_studio/views/job.py` (484 lines), `registry/hints.py` (1,170 lines) | the director flow's hint keys are not proposed here | the builder adds them with the prose test |
| UNVERIFIED: the overlay's disparity against the render's own map; a resolve or render without the depth model; the page script on a saved plan's stem (reasoned from P:58–65); the keyframe tile under the studio's file route | each is a reasoned claim | the acceptance drive and one page build |
| The round-8 folder `mismatch_3_c1-nosit` is gone from disk; `benchmarks/runs/2026-10-17/agents/skeptic_r8.md` names it | the tag convention rests on round 8's `-full` and round 13's `-out` and `-wide` | — |
