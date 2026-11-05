# Reveal studio: start and use it (the essentials, 2026-11-05)

The studio is one local page over three flows. A loop takes a folder of stills to a graded loop, a pair
transition takes two photos to a graded transition, and a director plan takes a fixture pair and its plan to a
graded clip. This page holds what you need to start the studio and run one job of each flow through it.
`README.md` holds the developer side.

## Start

1. Stop any studio server still running from before 2026-11-05 (Ctrl-C in its terminal). It serves
   the retired script's page from memory.
2. Run `make -C studio install` once. It builds `studio/.venv` against PyPI.
3. Run `make -C studio run`. The page opens at 127.0.0.1:8380.
4. Stop the server with Ctrl-C. A stage still running keeps running; the next start picks its record up.

Never run a bare `uv sync` or `uv run` in your shell for this package: your shell exports a work mirror
as the default index, and uv rewrites the lock to it. Use the make targets, or add `--frozen`.

## One loop, start to finish

1. In the rail on the left, press "new loop job…" (the rail has one such button per flow): the folder of
   developed JPGs and a sequence name.
   The stills are linked and hashed in name order, never copied. "adopt a run folder…" opens an older
   run under `benchmarks/runs/` in place.
2. A loop job's strip shows its stages as tiles: import, registration, readers, probe, plan, render, measure,
   skeptic, page, grades. Click a tile to open its panel; the inspector on the right lists its knobs.
3. Registration: set the knobs you want, press the run button. The fits table shows each named window
   under each fit. The probe tile under it compares RIFE, morph and dissolve in-betweens.
4. Plan: the editor shows the timeline as bars with a form per step. Add a hold, a transition or an
   effect; "% faster" scales every count; Cmd-Z undoes; the JSON tab shows the same plan as text.
   "save as a new plan" takes your words. A value you ruled out before shows a chip and a warning;
   nothing refuses.
5. Render: a draft at 480 px first, then the full render. The stages after a rerun go stale until they
   run again.
6. Judge: the viewer shows the frame under judgement at fit, 1:1 or 2×, in one of five modes (single,
   wipe, A/B, onion, difference) over sources A and B. The plot under the scrubber shows each frame's
   step, stalls as bands, jumps as ticks; generated frames carry the violet mark. The measure tile under
   the render reads a window's stability per frame.
7. Skeptic: press "write the request". A Claude session answers it with a verdict per candidate.
   `uv run --frozen reveal-studio requests` lists the open requests.
8. Page: tick the renders the page lists, order them, press "build the page". The page refuses an
   unjudged or NOT READY candidate unless you override, and prints the override.
9. Grades: "save the grade" keeps your words verbatim for the round, or "mark ungraded by his word".
   The next round's first render waits for one of the two.

## One pair transition, start to finish

1. In the rail, press "new pair job…". Pick a fixture pair, or give the paths of photo A (the start) and
   photo B (the finish) and a pair name. The two photos are linked and hashed, never copied.
2. A pair job's strip shows import, verdict, relation, render, skeptic, page and grades. "run the relation"
   makes a 480 px, one-second clip and reports the pair's class: class A morphs along a dense flow, class B
   pans and zooms each photo about its subject.
3. Reveal's verdict is optional: "run Reveal's verdict" aligns B onto A. A refusal means the two photos share
   too little detail to align, and the flow goes on without it.
4. Render: set the knobs in the inspector (preset, seconds, color, warp, camera, zoom and the rest), then run a
   draft (draft 480) or the full size (draft 0 at max_long 1920). The plot under the scrubber shows the decoded
   step series beside the report's flicker numbers.
5. Skeptic, page and grades work as in the loop; the studio writes the page itself. The grade takes the picks
   form: the best render, and per render "acceptable", a note and three boxes (one picture, content transforms,
   nothing invented).

## One director plan, start to finish

1. In the rail, press "new director job…" and pick a fixture pair that a director plan names. The photos are
   linked and hashed; the job also counts each photo's layer table and mattes.
2. A director job's strip shows import, verdict, resolve, plan, render, skeptic, page and grades. The import
   panel shows both photos with their overlays (elements, disparity, one matte) and the element tables.
3. Resolve: press "resolve" for the canvases, the anchors and the layers' windows, with no render. The inspector
   shows the knobs the resolve sends, read-only, with its command.
4. Plan: pick the plan and the concept. Drag a timeline bar in clip time, or focus it and use the keys below. Set
   the renderer's `--set` keys in their table; a key that changes no frame is read-only and says why. "load the
   last round's knobs" fills them in only when you press it. "clear all knobs" asks first, and Cmd-Z brings the
   knobs back.
5. Render: "render a 480 draft" first, then "render full". These controls sit in the column beside the frame,
   under the renders, and the inspector shows the knobs the next render sends, read-only. The tag names the
   render's folder, and a tag used before is refused.
6. Skeptic, page and grades work as in the pair flow. The page is `director_page.py`'s, behind the same review
   gate. The grades show one form per round, newest first: a graded round shows its picks, and an ungraded round's
   form starts from the newest picks file (the boxes, the notes and the best render; never your words).

## Keys

| Key | Does |
|---|---|
| Space | plays and pauses the render at the fps it was rendered at: 25 by default for a loop, 30 for a pair or a director clip |
| Left, Right, or `,` `.` | one frame back or forward; with Shift, ten |
| `a` | flips A and B in the A/B mode |
| `m` | marks the frame as a fault, with your note, for the next round |
| Cmd-Z, Shift-Cmd-Z | undo and redo in the loop's plan editor, and of the knobs in the director's plan panel |
| Left, Right on a director's timeline bar | moves the bar by 0.01 of the clip; with Shift its end, with Alt its start |
| Page Up, Page Down on that bar | moves the bar by 0.1 of the clip |
| Tab | moves between the controls; a focused control shows its hint |

Hover any control or its "?" for its hint. The hint names the knob's key, default, range and source.

## Where things are

A job lives under `benchmarks/runs/<date>/studio/<job>/`. Each stage run is a record under `stages/`
with its `stage.json` (the command line that reproduces it from the shell), `log.txt` and outputs.
Plans sit under `plans/`, requests and answers under `requests/` and `answers/`, each page under
`rounds/<n>/`, and the grades in the picks form under `picks/`. A pair job keeps its two photos under
`raw/<pair>/`, the relation in `relation/`, the verdict in `verdict/`, full renders in `<pair>/<name>/` and
drafts in `drafts/<pair>/<name>/`. A director job renders into `run/<plan>_<concept>[-<tag>]/` (its page is
`run/index.html`), drafts into `drafts/` and resolves into `resolve/<stamp>/`. The studio never writes under
`models/`, `fixtures/` or the frozen plans.
