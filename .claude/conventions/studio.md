# Studio conventions — the package under `studio/` (seeded 2026-11-05)

The studio is the third surface of this repo: the Python package `reveal-studio` under `studio/`,
with its own uv-managed venv, tests and gates. It serves the page of `STUDIO.md` on 127.0.0.1:8380
and runs the research scripts and the two tools as subprocesses of the MAIN venv
(`<root>/.venv/bin/python`). The single-file rule of `architecture.md` covers `reveal.py` and
`transitions.py`; the package is modular by owner order (2026-11-05, verbatim in DECISIONS
2026-11-05). `STUDIO.md` is the design of record; `studio/ARCHITECTURE.md` is the as-built map.

## Layout (fixed 2026-11-05)
```
studio/pyproject.toml · uv.lock (tracked) · Makefile · .importlinter · README.md · ARCHITECTURE.md
studio/src/reveal_studio/
  cli.py config.py errors.py fs.py
  registry/  loop.py (stages, knobs) · hints.py · schema.py (plan grammar) · rulings.py
  jobs/      store.py · records.py · candidates.py · plans.py · grades.py
  runner/    argv.py · process.py (the Runner) · lock.py
  views/     job.py · render.py · models.py · page.py · fits.py · measures.py (the last two since A2, 2026-11-05)
  media/     pictures.py (the only module that imports cv2)
  server/    app.py · handler.py · routes.py
  web/       index.html · css/ · js/ (plain script tags, no build step)
studio/tests/  unit (a fake loop_seq script under a tmp root) · integration/ · acceptance/
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
- Subprocesses: every heavy call runs the main venv's python with stdout and stderr in the
  record's `log.txt`; the argv is recorded in `stage.json` and reproduces the stage from the
  shell.
- State: the job folder is the only state (`STUDIO.md §4`). A stage writes into a `.part` folder
  and renames it on success; a finished render is never overwritten; a `running` record whose
  process is gone is reconciled from its files at start and on read.
- Errors: one exception class, `StudioError(msg, code, extra)`. The handler answers it as
  `{"error": msg}` with its HTTP code. Any other exception is logged with its type and answered
  as a 500 whose body names the type; no stack trace reaches the page.
- The page: vanilla JavaScript, no framework, no build step; plain `<script src>` tags in a
  fixed order; one global state object `S`. The strip, the rail, the panel, the inspector, the
  viewer and the graph rebuild only when their data changed and restore the keyboard focus by
  data attribute; a restored focus opens no hint. A "?" button and a chip are no Tab stops (the
  fix round of 2026-11-05): a control's own keyboard focus opens its hint, and hover opens it
  after 600 ms. A form that holds typed text is never re-rendered by the poll. Every control, knob, chip, measure and region carries a hint key from
  the hints table.
- Sentences: the registry copies a knob's sentence from the script's `--help` or `SCHEMA.md` and
  never invents a range (null unless the script states one). Every hint and stage sentence passes
  the no-slop checker: `tests/test_prose.py` runs `slop-check.py` over them.
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
| unit | none | the package venv; the fake `loop_seq.py` of `conftest.py` | `make test-fast` (seconds; CI) |
| integration | `integration` | the main venv, the real research script, the jobs under `benchmarks/runs/` | `make test` (this laptop) |
| acceptance | `acceptance` | the owner's stills, RIFE, about 5 minutes | `make acceptance` (before his eye) |

Every assertion names the mutation that turns it red (`testing.md`). A new route gets a test
that hits it; `test_server.py` enumerates the route table and asserts every route is covered. A
new hint key is checked by the existing prose test with no new code.

## Gates
`make -C studio qa` is Gate 3 of the repo (`AGENTS.md`): lint (ruff check and format check),
typecheck (mypy strict), test-fast, audit (vulture, deptry, pip-audit, lint-imports, radon),
prose (slop-check over `README.md` and `ARCHITECTURE.md`). `make test` runs before a commit that
touches the runner or the routes; `make acceptance` runs before the owner's eye on a UI change.
`.github/workflows/studio.yml` runs `make qa` on ubuntu with the unit layer only (no fixtures, no
weights on CI).

## The UI build routine (owner rulings of 2026-10-21 and 2026-11-04; detail in the reveal skill's `references/studio.md`)
A UI change passes four checks before his eye. A Fable subagent reviews the served surface against
the hard constraints without editing. An Opus subagent drives the acceptance checks through the
served page. A critique by impeccable's method runs the detector at 2560×1440, 1440×900 and
1280×800 and expects 0 anti-patterns. The no-slop pass covers every sentence the page shows. A
finding is fixed the same session or recorded in the backlog with its reason.
