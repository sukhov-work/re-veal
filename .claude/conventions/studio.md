# Studio conventions — the package under `studio/` (seeded 2026-11-05)

The studio is the third surface of this repo: the Python package `reveal-studio` under `studio/`,
with its own uv-managed venv, tests and gates. It serves the page of `STUDIO.md` on 127.0.0.1:8380
and runs the research scripts and the two tools as subprocesses of the MAIN venv
(`<root>/.venv/bin/python`). The single-file rule of `architecture.md` covers `reveal.py` and
`transitions.py`; the package is modular by owner order (2026-11-05, verbatim in DECISIONS
2026-11-05). `STUDIO.md` is the design of record; `studio/ARCHITECTURE.md` is the as-built map.

## Layout (fixed 2026-11-05; the 21 modules phase B added the same day are marked "(B)")
```
studio/pyproject.toml · uv.lock (tracked) · Makefile · .importlinter · README.md · ARCHITECTURE.md · GUIDE.md
studio/src/reveal_studio/
  cli.py config.py errors.py fs.py
  registry/  entries.py (K, H; B) · flows.py (every flow, the lookups; B) · common.py (the shared verdict stage; B)
             loop.py (stages, knobs) · pair.py (B) · director.py (the --set table; B)
             hints.py (the loop's rows; HINTS merges three tables) · hints_pair.py (B) · hints_director.py (B)
             schema.py (plan grammar) · rulings.py
  jobs/      store.py · records.py · candidates.py · plans.py · rounds.py (B) · grades.py
  runner/    argv.py (the dispatcher) · argv_common.py (B) · argv_loop.py (B) · argv_pair.py (B)
             argv_director.py (B) · process.py (the Runner) · lock.py
  views/     base.py (B) · job.py · tiles_loop.py (B) · pair.py (B) · director.py (B) · render.py · models.py
             page.py · fits.py · measures.py (the last two since A2, 2026-11-05)
  media/     pictures.py · pair.py (B) · overlays.py (B): the only modules that import cv2; pair.py and overlays.py
             import numpy too
  server/    app.py · handler.py · route.py (B) · routes.py · routes_pair.py (B) · routes_director.py (B)
  web/       index.html · css/ · js/ (plain script tags, no build step; pair.css, director.css, pair.js and
             director.js since phase B)
studio/tests/  unit (the fakes of tests/fakes/ under a tmp root: loop_seq.py, and since phase B reveal.py,
               transitions.py, director_render.py, director_page.py) · integration/ · acceptance/
```

## Rules
- Dependencies: the runtime needs numpy and opencv-python-headless at the pins of
  `requirements.txt` and nothing else. A new runtime dependency is a decision (a DECISIONS line),
  as `AGENTS.md` rules for the tools. Dev tools live in the `dev` dependency group. `uv` never
  touches the main venv; the main venv never installs the package.
- The configuration object: every path and port comes from `reveal_studio.config.Settings`
  (explicit arguments, then the `REVEAL_STUDIO_*` environment, then discovery of a folder that
  holds `reveal.py` and `AGENTS.md`). No module reads a repo path from `__file__` except that
  last-resort discovery.
- Import contracts (`.importlinter`, run by `make audit`): the package never imports `reveal`,
  `transitions`, a research script, torch, transformers or kornia; cv2 only inside `media`;
  the layers are server > views > runner | media > jobs > registry > config | errors | fs. A
  contract change is a design decision recorded as a dated row here.
  - 2026-11-05, phase B's slice: the forbidden names gain `director_render`, `director_page`,
    `director_ui`, `chain_luma`, `layer_merge`, `matte_source`, `layered_probe` and `nest_probe`. The
    cv2 rule and the layers are unchanged. An `import director_render` added to `views/director.py`
    turned the first contract red; its removal turned it green.
- Subprocesses: every heavy call runs the main venv's python with stdout and stderr in the
  record's `log.txt`; the argv is recorded in `stage.json` and reproduces the stage from the
  shell.
- State: the job folder is the only state (`STUDIO.md §4`). A stage writes into a `.part` folder
  and renames it on success; a finished render is never overwritten; a `running` record whose
  process is gone is reconciled from its files at start and on read. Since phase B's fix round
  (2026-11-06): an in-place record (its script writes its output where it stands) is done after
  a restart when its file is newer than the record's start, else lost. A record that another
  server finalizes (its done marker, or its terminal file renamed into `out_final` after it
  started) is left to that server. A refused stage's `.part` folder is removed.
- Errors: one exception class, `StudioError(msg, code, extra)`. The handler answers it as
  `{"error": msg}` with its HTTP code. Any other exception is logged with its type and answered
  as a 500 whose body names the type; no stack trace reaches the page.
- The page: vanilla JavaScript, no framework, no build step; plain `<script src>` tags in a
  fixed order; one global state object `S`. The strip, the rail, the panel, the inspector, the
  viewer and the graph rebuild only when their data changed and restore the keyboard focus by
  data attribute; a restored focus opens no hint. A "?" button and a chip are no Tab stops (the
  fix round of 2026-11-05): a control's own keyboard focus opens its hint, and hover opens it
  after 600 ms. A form that holds typed text is never re-rendered by the poll. Every control, knob, chip, measure and region carries a hint key from
  the hints table. A button is inert while its request runs (since 2026-11-06: `core.js`
  `busy(btn, fn)` shows "working…", ignores a second press and keeps the button's focus).
- Sentences: the registry copies a knob's sentence from the script's `--help` or `SCHEMA.md` and
  never invents a range (null unless the script states one). Every hint and stage sentence passes
  the no-slop checker: `tests/test_prose.py` runs `slop-check.py` over them. Since 2026-11-06 it
  checks every registry sentence at 60 words and holds the hints and the phase B flows' sentences
  to 40 words; the loop's stage and knob sentences keep the 60-word bar, since the loop's snapshot
  test pins them.
- Names: modules and functions `snake_case`; stage, knob and hint keys as the page shows them;
  record ids `<stamp>_<stage>`; `ui_version` is `reveal-studio <version>`.
- Dependencies: PyPI is the only index (`[[tool.uv.index]]` with `default = true`; the Makefile exports
  `UV_DEFAULT_INDEX`). `uv.lock` is tracked and names `pypi.org` and `files.pythonhosted.org` only;
  `tests/test_lock.py` fails on any other host, because the GitHub runner reaches no private mirror.
- Types: mypy strict. A `# type: ignore[code]` carries a dated reason on the same line.
- Style: ruff with the rule set in `pyproject.toml` (line length 120). A per-file ignore carries
  a dated reason.

## Tests (three layers)
| Layer | Marker | Needs | Command |
|---|---|---|---|
| unit | none | the package venv; the fakes of `tests/fakes/` that `conftest.py` copies into a tmp root (five since phase B, 2026-11-05) | `make test-fast` (CI; 550 tests in 120.8 s on 2026-11-05, the phase B review's run; 555 tests since the fix round of 2026-11-06) |
| integration | `integration` | the main venv, the real research script (since phase B also `transitions.py`, `director_render.py` and `director_page.py`, for their `--help`), the jobs under `benchmarks/runs/` | `make test` (this laptop) |
| acceptance | `acceptance` | the owner's stills, RIFE, and since phase B the fixture pair mismatch_3; four drives in about 8 minutes (2026-11-05) | `make acceptance` (before his eye) |

Every assertion names the mutation that turns it red (`testing.md`). A new route gets a test
that hits it; `test_server.py` enumerates the route table and asserts every route is covered. A
new hint key is checked by the existing prose test with no new code.

## Gates
`make -C studio qa` is Gate 3 of the repo (`AGENTS.md`): lint (ruff check and format check),
typecheck (mypy strict), test-fast, audit (vulture, deptry, pip-audit, lint-imports, radon),
prose (slop-check over `README.md`, `ARCHITECTURE.md` and, since 2026-11-05, `GUIDE.md`). `make test` runs before a commit that
touches the runner or the routes; `make acceptance` runs before the owner's eye on a UI change.
`.github/workflows/studio.yml` runs `make qa` on ubuntu with the unit layer only (no fixtures, no
weights on CI).

## The UI build routine (owner rulings of 2026-10-21 and 2026-11-04; detail in the reveal skill's `references/studio.md`)
A UI change passes four checks before his eye. A Fable subagent reviews the served surface against
the hard constraints without editing. An Opus subagent drives the acceptance checks through the
served page. A critique by impeccable's method runs the detector at 2560×1440, 1440×900 and
1280×800 and expects 0 anti-patterns. The no-slop pass covers every sentence the page shows. A
finding is fixed the same session or recorded in the backlog with its reason.
