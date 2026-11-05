# reveal-studio

reveal-studio is the Reveal repo's studio as a Python package: one local web page over three flows, served on
127.0.0.1. The flows are the loop of `scripts/research/loop_seq.py`, the pair transition of `transitions.py` and the
director plan of `scripts/research/director_render.py`.

It ported `scripts/research/studio.py` (phase A1, built 2026-11-04; retired 2026-11-05) with the same page, the same
API and the same job folders. Phase A2 (2026-11-05) added the plan editor, the rulings, the probe and measure
stages, the fits table, the stability plot, the comparator modes and the graph view. A fix round the same day
resized the viewer and took the "?" buttons and the chips out of the Tab order. Phase B (2026-11-05) added the pair
transition and director plan flows and the loop's repaint leg; `ARCHITECTURE.md` lists what each part added. It has
its own venv and lock file
(`studio/.venv`, `studio/uv.lock`). The main venv (`../.venv`) of
`reveal.py`, `transitions.py` and the research scripts stays as it is.

## Install

```
cd studio
make install     # uv sync against PyPI, the project's only index (the note below)
```

`make install` builds `studio/.venv` with Python 3.13 and the pins of `../requirements.txt` (numpy 2.2.6 and
opencv-python-headless 5.0.0.93), plus the dev tools. The studio starts every heavy step as a subprocess of the
main venv's python. `./setup.sh` at the repo root builds that venv; the studio itself holds no model and no torch.

PyPI is the project's only index: `pyproject.toml` names it under `[[tool.uv.index]]` with `default = true`, and the
Makefile exports `UV_DEFAULT_INDEX` for every target. A bare `uv sync` or `uv run` in a shell that exports another
default index re-resolves against that index and rewrites `uv.lock` with its URLs (uv treats a lock whose registry
is not among the configured indexes as stale). That happened on 2026-11-05 with a work mirror, and the GitHub runner
could not reach it. Use the make targets, or add `--frozen` to a direct `uv run`; `tests/test_lock.py` fails on any
other host in the lock.

## Run

The owner's start and usage guide is `GUIDE.md` (the essentials; it grows with the flows).

```
make run                                   # uv run reveal-studio serve: 127.0.0.1:8380, opens the browser
uv run --frozen reveal-studio serve --port 8390 --no-browser --lock /tmp/review.lock
uv run --frozen reveal-studio requests     # the open requests across every job, with their age
uv run --frozen reveal-studio check        # the resolved settings and the script's flags
```

`serve` takes the tree's lock file, `benchmarks/runs/studio.lock`, which names the port and pid of the server
holding it. A second server on the same tree is refused unless `--second` is given (a review server).
Ctrl-C stops the server. A stage still running keeps running, and the next start reconciles its record.
`check` exits 1 when the root, the main venv's python or `loop_seq.py` is missing; a missing path of the pair or
director flows prints MISSING and leaves the exit code alone (the settings section below).
Every POST, a cancel included, sends a JSON body with `Content-Type: application/json` (an empty `{}` will do);
without that header the server answers 415, the rule that keeps a cross-site form out.

## Where state lives

The job folder on disk is the only state. A job lives under `benchmarks/runs/<date>/studio/<job_id>/`. It holds
`job.json`, the symlinked inputs under `raw/<seq>/`, and one record per run under `stages/<stamp>_<name>/`. The
other folders are `plans/`, `requests/`, `answers/`, `rounds/<n>/`, `picks/` (since phase B), `owner_frames/` and
`cache/`. The run folder's layout depends on the flow:

| Flow | Inputs under `raw/<seq>/` | The run folder and what it holds |
|---|---|---|
| loop | the stills `<nn>.jpg` | the job folder, or an adopted run folder, in the layout of `loop_seq.py page`. The prep sits in `in/<seq>/`, with the probe's folder `probe/` under it since phase A2. Full renders sit in `<seq>/<name>/`, each with its measure runs under `measures/<stamp>/`; drafts in `drafts/<seq>/<name>/`; the page is `index.html` with `page.md5` |
| pair (since phase B) | the photos `A.<ext>` and `B.<ext>` | the job folder: `relation/` and `verdict/`, full renders in `<pair>/<name>/`, drafts in `drafts/<pair>/<name>/`, and the page the studio writes (`index.html`, `page.md5`, `page_A.jpg`, `page_B.jpg`) |
| director (since phase B) | the photos `A.<ext>` and `B.<ext>`, as records (the renderer reads `fixtures/` by the plan's pair) | `run/`: full renders in `<stem>_<concept>[-<tag>]/` and `director_page.py`'s `index.html` with `page.md5`; beside `run/` sit `resolve/<stamp>/`, `drafts/<stem>_<concept>[-<tag>]/` and `verdict/`. Its `job.json` also names the layer and matte roots, each photo's layer table and matte count, and the helper files the pair's plans name |

The studio reads the original photos through symlinks and records their sha256s. It writes nothing under `models/`,
`fixtures/` or `scripts/research/plans/`.

## How the repo and the main venv are found

Each setting comes from its flag, then its environment variable, then the default. A row without a flag or an
environment variable takes its default.

| Setting | Flag | Environment variable | Default |
|---|---|---|---|
| repo root | `--root` | `REVEAL_STUDIO_ROOT` | the first folder at or above the working folder that holds `reveal.py` and `AGENTS.md`, then the same search above the package |
| main venv's python | — | `REVEAL_STUDIO_PY` | `<root>/.venv/bin/python` |
| port | `--port` | `REVEAL_STUDIO_PORT` | 8380 |
| lock file | `--lock` | `REVEAL_STUDIO_LOCK` | `<root>/benchmarks/runs/studio.lock` |
| folder date for new jobs | `--runs-date` | `REVEAL_STUDIO_RUNS_DATE` | today |
| the pair flow's script (since phase B) | — | — | `<root>/transitions.py` |
| Reveal's verdict, the branch of the pair and director flows (since phase B) | — | — | `<root>/reveal.py` |
| the director's renderer (since phase B) | — | — | `<root>/scripts/research/director_render.py` |
| the director's page script (since phase B) | — | — | `<root>/scripts/research/director_page.py` |
| the director plans (since phase B) | — | — | `<root>/scripts/research/plans/`; the loop's frozen plans stay in its `loops/` folder |
| the fixture pairs (since phase B) | — | — | `<root>/fixtures/` |
| the layer tables' root (director flow) | `--layers-dir` | `REVEAL_STUDIO_LAYERS_DIR` | `<root>/benchmarks/runs/2026-09-28/layers_v3`, `director_render.py`'s own default |
| the mattes' root (director flow) | `--mattes-dir` | `REVEAL_STUDIO_MATTES_DIR` | `<root>/benchmarks/runs/2026-10-17/mattes`, `director_render.py`'s own default |

`uv run reveal-studio check` prints what was resolved, the md5 of `loop_seq.py` and the flags its `--help` lists. It
also prints the md5 of each script above and a count for each folder. A missing one prints MISSING and leaves the exit
code alone, because the loop flow runs without it.

## Gates

Run every target from `studio/`. `make help` lists them all.

| Target | What it runs |
|---|---|
| `make qa` | `lint`, `typecheck`, `test-fast`, `audit` and `prose`, in that order |
| `make test` | the unit and integration tests; the integration tests skip when `../.venv` is absent |
| `make test-fast` | the unit tests, on a temporary repo root with the five fakes of `tests/fakes/` (`loop_seq.py`, `reveal.py`, `transitions.py`, `director_render.py`, `director_page.py`) |
| `make acceptance` | four drives, one at a time (`tests/acceptance`), in about 8 minutes, each in a new job under `benchmarks/runs/<date>/studio/`. The A1 and A2 loop drives run on the owner's stills. They compare the registration byte for byte with the recorded prep and check the full a2 render at its recorded md5, twice (once from a saved copy). They also run the probe, the measure, the gates, a restart and a cancel. The pair and director drives on the fixture pair mismatch_3 (since phase B): the relation at its recorded md5s, the director's two drafts at theirs, the page gate, a grade and a restart |
| `make draft-check` | the 480 px draft of `angel_a2` through the package into the job `loop_angel_20261104-220719` (an 8 MB draft per run) |
| `make audit` | vulture, deptry, pip-audit, lint-imports and radon |
| `make detector` | prints the impeccable detector's command for a running server |

The integration tests read the real tree and write nothing. The two acceptance targets write into job folders. `make acceptance` makes
four jobs: two loop jobs from the owner's stills, a pair job and a director job on mismatch_3. `make draft-check`
renders a 480 px draft of the frozen `angel_a2` plan into the job `loop_angel_20261104-220719`, under
`drafts/angel/port_check_<stamp>/` (gitignored). `ARCHITECTURE.md` holds the module
map, the import contracts and the hard constraints with their tests.
