<!-- provenance: copied verbatim on 2026-11-05 from benchmarks/runs/2026-11-05/studio/agents/plan_editor.md (gitignored), the report of agent D, the plan-editor builder (Opus 5.5, max effort) of the 2026-11-05 session; a research artifact whose claims carry the author's own confidence and gaps; the main thread ruled on its two deviations (both kept as built; DECISIONS 2026-11-05) and re-ran the package gates after agent E finished -->

---
reader: the main thread of the 2026-11-05 studio session, which did not see this agent's work, then whoever copies it into .claude/claude-docs/research/2026-11-05/
shape: report
---

# The plan editor, the rulings table and the page's variants (studio phase A2, agent D, 2026-11-05)

Agent D built the plan-editor part of the studio's second build phase, which `STUDIO.md` §9 calls A2, in the package
`studio/`. Agent E, the other builder of that phase, worked on the viewer, the graph view, the fits view, the probe and
the measures at the same time. The glossary below the summary names every file and term the sections use.

## Summary

**Result: built.** The five deliverables of the brief: the plan schema as data, the plan editor, the rulings table,
the page's variants, the proof on the real surface. `make qa` is green (66 s wall, 373 unit tests, 3 import contracts
kept); my last plan.js edits came after it, and my 249 tests and the hint-key scan passed again on them. `make test`
is green: 387 passed, 63 s wall, at 02:35. Tests added: 190 cases (section 6).

**Proof.** An unchanged copy of the frozen plan `angel_a2`, saved from the editor, rendered a 480 px draft whose
`loop.mp4` md5 is `2955c25c2611565b3ee57d2d081f8669`, the md5 the same plan's 480 px draft gave on 2026-11-04. A form
edit of the breath's `z` saved one change, `/effects/0/z` 0.018 → 0.02.

**Asked of the main thread:**
1. Rule on two deviations from the brief (section 7); without a ruling they stay as built.
2. Update `ARCHITECTURE.md` and `contracts.md` with the new keys listed in sections 1–3.
3. Stop the headless Chrome (pid 36358, port 9222) once agent E no longer drives it.

## Glossary

| Term | Meaning |
|---|---|
| the brief | agent D's task message from the main thread, 2026-11-05 |
| the owner, "he", "his grade" | the repo's owner; the DECISIONS lines quote his grades and words verbatim |
| DECISIONS, loops.md | `.claude/claude-docs/DECISIONS.md` and `.claude/skills/reveal/references/loops.md`, the loop playbook |
| SCHEMA.md, loop_seq.py | `scripts/research/plans/loops/SCHEMA.md` (the plan grammar) and `scripts/research/loop_seq.py` (the renderer) |
| frozen plans | the 48 plan files under `scripts/research/plans/loops/`; the studio reads them and never writes them |
| a2, a1–a5 | the angel portrait loop's candidate plans; a2 and a3 were accepted on 2026-11-04 |
| rife step, breath, `z` | a transition rendered by RIFE in-betweens; an effect that pushes the frame in and out once per loop, `z` its size |
| the review gate | the page is refused while a listed full render is unjudged or NOT READY, unless he overrides |
| words | the owner's reason for a saved plan, stored verbatim in its provenance block |
| ARCHITECTURE.md, contracts.md | `studio/ARCHITECTURE.md` and `.claude/conventions/contracts.md` |

## 1. The plan schema as data

`registry/schema.py` holds `PLAN_SCHEMA`: 151 entries in 21 groups, one per key a plan can hold. `GET /api/registry`
serves it as `plan_schema` with the date read (2026-11-05), the groups' order and titles, and the chain's methods.
An example entry:

```json
{"path": "timeline[method=slide].mode", "group": "slide", "key": "mode", "type": "str", "item": null,
 "default": "fly", "default_from": "loop_seq.py", "range": null, "choices": ["fly", "dissolve"],
 "units": null, "roles": null, "required": false, "hint": "plan.timeline.slide.mode"}
```

- **Paths.** `crf`, `matte.thr`, `timeline[*].n` (every transition), `timeline[method=rife].margin` (a rife step),
  `timeline[method=sheets].sheets[*].carry` (each sheet), `effects[kind=glow].gain`. The rulings use the same grammar.
- **Types.** int, float, str, bool, list (`item` is a scalar type or the group of an object's keys), box (roles x0 y0
  x1 y1), point (roles x y, or fx fy, or dx dy) and object (JSON text).
- **Defaults.** SCHEMA.md's where it states one (`default_from: "SCHEMA.md"`, 11 entries, its "the code's default is X"
  included). Elsewhere the literal default in loop_seq.py (`"loop_seq.py"`, 100 entries). A required key, or a key whose
  absence turns a branch off, has none (40 entries). SCHEMA.md documents no key of the slide, the rise or the snap.
- **Ranges.** All null except the slices' `shadow`, 0–1, the only range SCHEMA.md states.
- **Coverage.** An integration test reads the 48 frozen plans. Every key is an entry, except three teleport keys that
  loop_seq.py reads and SCHEMA.md does not list (`rest`, `flash`, `flash_gain`). The editor shows those under "other keys".
- **validate_plan** keeps its checks and reads the methods, the eases and the effect kinds from the entries'
  `choices`. A test drops a choice from the entry and sees the plan refused.
- A test checks the 11 methods, 7 eases and 3 effect kinds against lists dated 2026-11-05 copied from SCHEMA.md and
  loop_seq.py. The same test checks each entry's type, its hint key in `HINTS`, and that its default equals its hint's.

## 2. The rulings table

`registry/rulings.py` holds 7 rows `{knob, value, since, why, source}`, each from a cited source. `value` is the
ruled-out value or a range in one of two forms: `{"min": v}` rules out v and above, `{"above": v}` everything above v.
`loops.md` is `.claude/skills/reveal/references/loops.md`.

| Knob | Ruled-out value | Since | Why (in `why`) | Source |
|---|---|---|---|---|
| `timeline[*].method` | `"slices"` | 2026-11-01 | his grade: "simple 2d pattern transtions, boring, tasteless and junky" | DECISIONS 2026-11-01; loops.md §3 |
| `timeline[*].method` | `"rise"` | 2026-10-30 | his grade: "ugly and has lots of artifacts" | DECISIONS 2026-10-30 (fourth); loops.md §5 |
| `timeline[method=slide].mode` | `"fly"`, the code's default | 2026-10-30 | his grade: "very dirty"; he asked for the dissolve | DECISIONS 2026-10-30 (fourth); loops.md §3, §5 |
| `timeline[method=teleport].mode` | `"squeeze"`, the code's default | 2026-10-30 | his grade: "do not beam, this looks like cardbard cut out" | DECISIONS 2026-10-30 (third); loops.md §3, §5 |
| `timeline[method=teleport].flash` | 1 and above | 2026-10-30 | his rule: "no flashes, no double pokes, nothing jerky" | DECISIONS 2026-10-30 (third); loops.md §5 |
| `timeline[method=sheets].sheets[*].carry` | above 0; the code's default is 1.0 | 2026-11-01 | his grade: "all other example are horribly misaligned" | DECISIONS 2026-11-01 (third); loops.md §3 |
| `registration.ecc_refine` | `true` | 2026-11-04 | measured: the far field 2–9 px worse on the angel pair | DECISIONS 2026-11-04; loops.md §2 |

- **Matching.** A row matches on the effective value: an absent key takes its schema default. Three ruled values are
  loop_seq.py's own defaults, so a slide step without `mode` flies and warns. The method condition sits in the path.
- **On the frozen plans.** Of the 48, the table warns on 11: seasons c1–c6 and c8 (slices), s1–s3 (carry above 0),
  group-teleport (the default squeeze and flash 2). It warns on none of a1–a5, s4–s10 or the Halloween round-4 plans.
- **Where it shows.** The editor shows a chip beside the field ("ruled out <date>: <why>"), a summary line and a marked
  bar. The inspector shows the chip on a stage knob and on the render's plan select; the plan rows of the job view now
  carry `warnings`. The run endpoint's 202 body and the record carry `warnings`, each `{knob, value, since, why,
  source, path, absent}`.
- **A warning only.** A run with a ruled value starts; a test proves the record finishes `done` with its warnings.
- **Mutation, applied once.** Deleting the slices row turned 4 tests red (4 failed, 211 passed). The restored file has
  the same md5, 0991f669….

## 3. The page's variants (backlog row T76: list only the named full renders)

- `registry/loop.py`: the page stage gains the knob `variants` (type list, default [], flag `--variants`); the stage
  sentence says the review gate checks the listed candidates only.
- `runner/argv.py`: `coerce` accepts a list or a comma string (`as_list`); `flags_of` joins a list. The page branch
  appends `--variants a,b` when the list is not empty, and its `inputs` are the listed mp4s in that order.
- `views/page.py`: `page_variants` refuses (400) a name that is not a full render, a name given twice, and a value
  that is not a list of names, before the script's own `FAILED:` line. The review gate checks the listed candidates only.
- `runner/process.py`: `rounds/<n>/round.json` records `variants` ([] for every full render) and lists the
  listed names as `candidates`.
- The page panel lists the full renders with an include box, up and down, the verdict chip and the md5, and says which
  flag it will pass. The build button sends `variants`.
- The fake script's `page` accepts `--variants` and refuses an unknown name with a `FAILED:` line, exit 2.
- Tests: the argv order (`c2,c1`), no flag when empty, the review gate on listed candidates, five 400 cases, a comma string,
  the fake's refusal, the HTTP 400 and 202. Mutation applied once: building the review gate over every full render again
  (`listed = full`) turned `test_the_gate_checks_the_listed_candidates_only` red.

## 4. The plan editor

`web/js/plan.js` and `web/css/plan.css` replace the JSON editor of the first build phase (A1) on the plan panel.

- **Bars.** One row of bars: a hold's width is its frames, a transition's its `n`, a cut a 6 px marker. Each bar shows
  its method, ease, frame count and the still index at both ends. The effects are full-width bars below, one per effect.
- **Forms.** Clicking a bar, or arrowing to it and pressing Enter, opens its form beside the bars. The form is
  generated from the schema: number, text, select, checkbox, a box as four named numbers, a scalar list as comma
  text. A list of objects (local boxes, sheets, object plates) is a sub-form per item; a matte spec is JSON text.
- **Edits.** A field edit sets one path on the loaded plan; an empty field removes the key. The editor writes back
  no default, so a saved copy records only the keys changed.
- **Steps.** Add a hold or a transition after the selected step, move it left or right, remove it, add an effect.
- **History.** Undo and redo by buttons and by Cmd/Ctrl-Z and Shift-Cmd/Ctrl-Z, over up to 300 JSON states. A text
  field with uncommitted typing keeps its own undo. The counter reads "n changes from <from>", counted like
  `plan_diff`, so it equals what the save records.
- **"% faster".** Multiplies every hold and every `n` by (100 − p) %, rounded, at least 1, as one change. A cut, a
  rewind and a slices step keep their counts. The rule matches the frame counts recorded in earlier loops after he
  named a pace. The Halloween wand loop went 28 → 22 for "20 % faster" and the group loop 48 → 34 for "30 % faster".
  The seasons loop went from s4 to s5, 90 → 135, for "50 % slower".
- **JSON tab.** It shows the same plan as text. An edit enters the history when the field loses the focus. A parse
  error is shown under the text, the text is kept, and switching to the bars is refused with a message and a
  "discard the text" button.
- **Save.** "save as a new plan" posts `{name, plan, from, words}` and preselects the saved plan in the render
  inspector. The render button stays in the render inspector.
- **Keyboard.** The bars use a roving tabindex with a visible amber focus ring. The arrows stop at the bars, so
  boot.js's scrubber keys never fire there. After a rebuild the focus returns to the same control, hint buttons
  included, and is never pulled in from outside the editor.

## 5. The proof on the real surface

Server `uv run reveal-studio serve --port 8393 --no-browser --lock <scratchpad>/d.lock` (pid 36058), driven by
Playwright in a headless Chrome at 2560×1440. Job `loop_angel_20261104-223204`: its round 2 has no grade text yet, so
the studio refuses a full render there and I rendered a draft. Its registered stills and depth maps have the same md5s
as those of job `loop_angel_20261104-220719`, where a2's 480 px draft gave `2955c25c…` on 2026-11-04 and 2026-11-05.
That md5 is therefore the expected value here.

1. Loaded `frozen:angel_a2`: 4 bars (14, 12, 12, 12 frames; 50 f, 2.00 s), the two rife steps outlined violet.
2. Saved unchanged as `d_a2_copy`, words "agent D: unchanged copy": `changes: []`; without its provenance block the
   file equals `angel_a2.json`.
3. Rendered from the render inspector as a 480 draft named `d_check_20261105-022051`: record `20261105-022108_render`,
   7.2 s, `loop.mp4` md5 `2955c25c2611565b3ee57d2d081f8669`, the expected value. Its `measure.json` records the plan's
   sha256 as `0dab9d4a…` where this job's earlier a2 draft recorded `e9d39488…`: the hash covers the saved plan's
   provenance block, which the render ignores.
4. Set the breath effect's `z` to 0.02 in the form and saved as `d_a2_z`: `changes: [{"path": "/effects/0/z", "old": 0.018,
   "new": 0.02}]`.
5. Also checked in the browser: Tab, undo and redo, the bars by arrows and Enter, a JSON edit reaching the bars,
   a parse error kept, "% faster" at 20 (41 f), add, move and remove a step. The drive caught one error in plan.js
   (`known is not defined`: a line comment had cut a declaration); after the fix the console showed 0 errors.
6. After the drive I put hint keys on the controls that lacked one (clear, plan keys, an item's remove, discard,
   the variants controls). A smoke check on a restarted server (pid 57391) cleared a key, undid it, opened the
   variants control and showed 0 console errors.

Screenshots, all under `benchmarks/runs/2026-11-05/studio/shots/`, taken during the drive; the later plan.js edits
add hint keys and do not change what they show:
- `d_bars_form.png`: the bars with step 1's form open (the local box as x0 y0 x1 y1);
- `d_json.png`: the JSON tab;
- `d_ruled.png`: step 1's method set to `slices` and the chip "ruled out 2026-11-01: …" beside the field;
- `d_inspector_ruled.png`: the same chip on the registration's `ecc_refine` (ticked, not run);
- `d_variants.png`: the page panel with a2 first and a1 left out ("passes --variants a2").

Verification tiers (`AGENTS.md`): the a2 md5 is real-pair-VERIFIED, the angel stills through the served page. The
look of the editor is UNVERIFIED until the owner's eye. The detector, the Fable review and the acceptance drive were
not run.

## 6. Files edited

Mine (line counts before → after): `registry/schema.py` 43 → 433, `registry/rulings.py` 20 → 165, `views/page.py`
46 → 77, `web/js/plan.js` 6 → 278, `web/css/plan.css` 1 → 74, `tests/test_plans.py` 146 → 164,
`tests/test_registry.py` 148 → 289, and two new files, `tests/test_rulings.py` (179) and `tests/test_server_plan.py`
(154). I also edited `jobs/plans.py`, which the brief lists among the code to read and gives to neither agent: lines 11, 54, 72 and 78–81
(`warnings` on the plan rows, `run_warnings`).

Tests added, 190 cases: `test_registry.py` 156 (151 of them one per schema entry, one an integration test over the
frozen plans), `test_plans.py` 3, `test_rulings.py` 18, `test_server_plan.py` 13.

Shared with agent E (Edit tool only, each spot re-read first; line numbers as of 02:35):

| File | Lines | Change |
|---|---|---|
| `registry/loop.py` | 234, 239–245 | the page stage's sentence and the `variants` knob |
| `registry/hints.py` | 460–1108 | one block at the end, 145 keys; ruff format reformatted that block only |
| `runner/argv.py` | 92–93, 99, 103–108, 124–126, 258–263 | the list type, `as_list`, `--variants` and the listed inputs |
| `runner/process.py` | 29, 101, 142, 289–299 | the record's `warnings`; the round's `variants` and `candidates` |
| `web/js/panels.js` | 60–61, 74 | `panelPage`'s variants control and the review gate's preview; the build sends `variants` |
| `web/js/inspector.js` | 9, 22 | the ruling chip on a knob row; the warnings after "started" |
| `tests/fakes/loop_seq.py` | 461–466, 472–476, 541 | `page --variants` |

Approved by the coordinator during the work:

| File | Lines | Change |
|---|---|---|
| `views/models.py` | 14–15, 64–65 | `registry_view` serves `plan_schema` and `rulings` |
| `tests/test_views.py` | 268–269 | the pinned key set gains those two keys |
| `server/routes.py` | 159 | `post_run`'s 202 body gains `warnings` |

These edits add no route, so the route count of `tests/test_server.py` stays as agent E left it.

## 7. Left out, and why

- **Deviation: morph bars are not violet.** The brief says to outline rife and morph bars. loop_seq.py tags morph
  frames "none (morph)", and DESIGN.md's violet marks model-made pixels only. The editor outlines rife, teleport,
  slide and rise, whose frames carry RIFE output. The alternative, adding `morph` to `GEN_METHODS` in plan.js, is a
  one-word change.
- **Deviation: defaults SCHEMA.md does not state.** The brief takes SCHEMA.md's defaults first. SCHEMA.md documents
  no key of the slide, the rise or the snap, and three ruled values are code defaults, so those entries carry
  loop_seq.py's default and say so in `default_from`. The alternative is null there: the forms then show "absent",
  and the three rulings on code defaults stop warning when the key is absent.
- **Rulings not added:**
  - "RIFE frames within 4 % of a still" (loops.md §5): a `margin` below 0.04 would warn on every rife step without a
    margin, the accepted Halloween plans included.
  - "a sine ease after a snap", "per-segment eases on a chain" and "a hold on an inner still": each depends on the
    step order, not on one key's value.
  - `--depth-blend`: the registry has no knob for it. The director's `hole_reveal=true` (`STUDIO.md` §4) belongs to the
    director flow, phase B. "30 fps gifs" is in loops.md §4, outside the listed sources.
- **The A1 editor's leftovers** (handlers in `wirePanel`, the `S.planText` fields in core.js) are unused now. They
  sit in shared files outside my edits, so I left them.
- **Not run:** impeccable's detector, the Fable review and the acceptance drive, which belong to the main thread.

## 8. Found, not changed

1. The A1 save handler set `S.knobs.plan`, not the render stage's knob state, so the render inspector never
   preselected a saved plan. The new editor sets the render stage's knob state.
2. Four A1 hints carry no `default` although the schema has one: `plan.crop` (1.0), `plan.timeline.local` ([]),
   `plan.effects.parallax.ref` (0.0), `plan.effects.glow.gain` (0.15). The form row shows the default; the popover
   does not.
3. The A1 hint `plan.timeline.ease` does not say that a snap or a rewind step ignores its ease; loop_seq.py's
   `frames_snap` and the rewind branch never read it.
4. core.js opens a hint on hover over any element inside a `data-hint` container, so a container with `data-hint`
   shows its hint over its whole area. The editor puts its region hints on `?` buttons for that reason.
5. The Playwright browser is shared between agents: agent E's tab on port 8394 appeared in my drive's browser.
6. `tests/test_registry.py`, my file, now pins agent E's ten-stage order (probe after readers, measure after render),
   which E cannot edit: if E reorders the stages, that test turns red.
7. Agent E's tests briefly failed lint (`tests/test_server_views.py`) and `make test` (`ARGV_FLAGS` without probe and
   measure) during my runs; both were fixed by 02:35.

## 9. Hints added

145 keys in one block at the end of `HINTS`, headed `# ---- A2: the plan editor, the rulings and the page's variants
(agent D)`: 127 plan keys, from SCHEMA.md's words or else loop_seq.py's docstrings, and 18 keys for the editor's
controls, the ruling chip and the variants control. `HINTS` now holds 267 keys. `tests/test_prose.py` passes with them,
and `tests/test_rulings.py` runs the same checker over the 7 `why` sentences.

## Appendix: commands

- Gates: `cd studio && make qa` (66 s, green), `make test` (63 s, 387 passed at 02:35).
- My files alone: `uv run pytest tests/test_plans.py tests/test_registry.py tests/test_rulings.py
  tests/test_server_plan.py tests/test_prose.py` (249 passed).
- Server: started as in section 5 (pid 36058), restarted once for the smoke check (pid 57391), stopped both times
  by SIGINT to its pid; it reported no child process left running.
