# reveal-studio

reveal-studio is the Reveal repo's studio as a Python package: one local web page over the loop flow of
`scripts/research/loop_seq.py`, served on 127.0.0.1.

It ported `scripts/research/studio.py` (phase A1, built 2026-11-04; retired 2026-11-05) with the same page, the same
API and the same job folders. Phase A2 (2026-11-05) added the plan editor, the rulings, the probe and measure
stages, the fits table, the stability plot, the comparator modes and the graph view. A fix round the same day
resized the viewer and took the "?" buttons and the chips out of the Tab order. It has its own venv and lock file
(`studio/.venv`, `studio/uv.lock`). The main venv (`../.venv`) of
`reveal.py`, `transitions.py` and the research scripts stays as it is.

## Install

```
cd studio
uv sync
```

`uv sync` builds `studio/.venv` with Python 3.13 and the pins of `../requirements.txt` (numpy 2.2.6 and
opencv-python-headless 5.0.0.93), plus the dev tools. The studio starts every heavy step as a subprocess of the
main venv's python. `./setup.sh` at the repo root builds that venv; the studio itself holds no model and no torch.

## Run

```
make run                                   # uv run reveal-studio serve: 127.0.0.1:8380, opens the browser
uv run reveal-studio serve --port 8390 --no-browser --lock /tmp/review.lock
uv run reveal-studio requests              # the open requests across every job, with their age
uv run reveal-studio check                 # the resolved settings and the script's flags
```

`serve` takes the tree's lock file, `benchmarks/runs/studio.lock`, which names the port and pid of the server
holding it. A second server on the same tree is refused unless `--second` is given (a review server).
Ctrl-C stops the server. A stage still running keeps running, and the next start reconciles its record.
`check` exits 1 when the root, the main venv's python or `loop_seq.py` is missing.
Every POST, a cancel included, sends a JSON body with `Content-Type: application/json` (an empty `{}` will do);
without that header the server answers 415, the rule that keeps a cross-site form out.

## Where state lives

The job folder on disk is the only state. A job lives under `benchmarks/runs/<date>/studio/<job_id>/`. It holds
`job.json`, the symlinked stills under `raw/<seq>/`, and one record per run under `stages/<stamp>_<name>/`. The
other folders are `plans/`, `requests/`, `answers/`, `rounds/<n>/`, `owner_frames/` and `cache/`.
The run folder keeps the layout of `loop_seq.py page`: the prep in `in/<seq>/` (with the probe's folder `probe/`
under it since phase A2), full renders in `<seq>/<name>/` (each with its measure runs under `measures/<stamp>/`),
drafts in `drafts/<seq>/<name>/`, and `index.html` with `page.md5`. The studio reads the original stills through
symlinks and records their sha256s. It writes nothing under `models/` or `scripts/research/plans/`.

## How the repo and the main venv are found

Each setting comes from its flag, then its environment variable, then the default.

| Setting | Flag | Environment variable | Default |
|---|---|---|---|
| repo root | `--root` | `REVEAL_STUDIO_ROOT` | the first folder at or above the working folder that holds `reveal.py` and `AGENTS.md`, then the same search above the package |
| main venv's python | — | `REVEAL_STUDIO_PY` | `<root>/.venv/bin/python` |
| port | `--port` | `REVEAL_STUDIO_PORT` | 8380 |
| lock file | `--lock` | `REVEAL_STUDIO_LOCK` | `<root>/benchmarks/runs/studio.lock` |
| folder date for new jobs | `--runs-date` | `REVEAL_STUDIO_RUNS_DATE` | today |

`uv run reveal-studio check` prints what was resolved, the md5 of `loop_seq.py` and the flags its `--help` lists.

## Gates

Run every target from `studio/`. `make help` lists them all.

| Target | What it runs |
|---|---|
| `make qa` | `lint`, `typecheck`, `test-fast`, `audit` and `prose`, in that order |
| `make test` | the unit and integration tests; the integration tests skip when `../.venv` is absent |
| `make test-fast` | the unit tests, on a temporary repo root with a fake `loop_seq.py` |
| `make acceptance` | the A1 and A2 loop-flow drives on the owner's stills (`tests/acceptance`): two new jobs under `benchmarks/runs/<date>/studio/`, the registration compared byte for byte with the recorded prep, the full a2 render at its recorded md5 (twice, once from a saved copy), the probe, the measure, the gates, a restart and a cancel; about 3 minutes |
| `make draft-check` | the 480 px draft of `angel_a2` through the package into the job `loop_angel_20261104-220719` (an 8 MB draft per run) |
| `make audit` | vulture, deptry, pip-audit, lint-imports and radon |
| `make detector` | prints the impeccable detector's command for a running server |

The integration tests read the real tree and write nothing. The two acceptance targets write: `make acceptance` makes
a new job from the owner's stills, and `make draft-check` renders a 480 px draft of the frozen `angel_a2` plan into
the job `loop_angel_20261104-220719`, under `drafts/angel/port_check_<stamp>/` (gitignored). `ARCHITECTURE.md` holds the module
map, the import contracts and the hard constraints with their tests.
