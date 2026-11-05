# Reveal studio: start and use it (the essentials, 2026-11-05)

The studio is one local page over the loop flow: a folder of stills in, a graded loop out. This page
holds what you need to start it and run one loop through it. `README.md` holds the developer side.

## Start

1. Stop any studio server still running from before 2026-11-05 (Ctrl-C in its terminal). It serves
   the retired script's page from memory.
2. Run `make -C studio install` once. It builds `studio/.venv` against PyPI.
3. Run `make -C studio run`. The page opens at 127.0.0.1:8380.
4. Stop the server with Ctrl-C. A stage still running keeps running; the next start picks its record up.

Never run a bare `uv sync` or `uv run` in your shell for this package: your shell exports a work mirror
as the default index, and uv rewrites the lock to it. Use the make targets, or add `--frozen`.

## One loop, start to finish

1. In the rail on the left, press "new loop job…": the folder of developed JPGs and a sequence name.
   The stills are linked and hashed in name order, never copied. "adopt a run folder…" opens an older
   run under `benchmarks/runs/` in place.
2. The strip shows the stages as tiles: import, registration, readers, probe, plan, render, measure,
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

## Keys

| Key | Does |
|---|---|
| Space | plays and pauses the render at 25 fps |
| Left, Right, or `,` `.` | one frame back or forward; with Shift, ten |
| `a` | flips A and B in the A/B mode |
| `m` | marks the frame as a fault, with your note, for the next round |
| Cmd-Z, Shift-Cmd-Z | undo and redo in the plan editor |
| Tab | moves between the controls; a focused control shows its hint |

Hover any control or its "?" for its hint. The hint names the knob's key, default, range and source.

## Where things are

A job lives under `benchmarks/runs/<date>/studio/<job>/`. Each stage run is a record under `stages/`
with its `stage.json` (the command line that reproduces it from the shell), `log.txt` and outputs.
Plans sit under `plans/`, requests and answers under `requests/` and `answers/`, each page under
`rounds/<n>/`. The studio never writes under `models/` or the frozen plans.
