# Verify — runnable recipes (one script or command per recipe; never prose in three memories)

## Gates (run from the repo root; all three before "done")
```
.venv/bin/python -m py_compile reveal.py harness.py       # Gate 0, seconds
.venv/bin/python harness.py                                # Gate 1, 82 checks, ~63 s
.venv/bin/python reveal.py check                           # Gate 2, ~19 s
.venv/bin/python transitions_harness.py                    # Gate 1b, ~10 s (transitions.py; count in TRANSITIONS.md §5: 54 as of 2026-09-26)
.venv/bin/python transitions.py check
```
Baseline 2026-09-13: 82/82 · all OK · Gate 1b all green (38 that day; 54 on 2026-09-26). Exit code 1 from either
harness = at least one `[XX]` line.
Gate 0 compiles the four tool files, `reveal.py harness.py transitions.py transitions_harness.py`, plus
`scripts/bench_transitions.py` and every `scripts/research/*.py` touched in the session (2026-09-26).

## Transitions drive (the real surface of `transitions.py`)
```
.venv/bin/python reveal.py align <BEFORE> <AFTER> --out /tmp/reveal-out
.venv/bin/python transitions.py pair /tmp/reveal-out/before.jpg /tmp/reveal-out/after_aligned.jpg \
    --out /tmp/reveal-out/tr --seconds 1.5 --preset flow-dissolve
cat /tmp/reveal-out/tr/report.json      # class · method · sparse_inliers · quality.flicker.edge_ratio · endpoint
open /tmp/reveal-out/tr/strip.jpg       # eight tiles: the eye check
```
Quote `class`, `method`, `median_disp_px`, `edge_ratio` and `render_s` in the DECISIONS line. Run it
twice: `report.json` and the decoded frames must be identical (harness 33 pins this on synthetic input).

## Headless drive of the real pipeline (the `real-pair-VERIFIED` recipe)
```
.venv/bin/python reveal.py align <BEFORE> <AFTER> --out /tmp/reveal-out --video --aspect 4:5
cat /tmp/reveal-out/metrics.json          # method · inliers · rmse_px · confidence · residual · passed
```
Quote the `metrics.json` numbers in the DECISIONS line. Run it twice when state is involved: the
second run must reproduce the numbers (the pipeline is deterministic given the same inputs; a
difference is a finding).

## Browser drive (only for page-side changes; `run.sh` opens the browser)
```
.venv/bin/python reveal.py serve --port 8400 --no-browser --workdir /tmp/reveal-work &
curl -s -F before=@<BEFORE> -F after=@<AFTER> -F mode=reshot http://127.0.0.1:8400/api/job   # → {"id": …}
curl -s http://127.0.0.1:8400/api/job/<id>/status                                          # poll until state=ready
```
Then open `http://127.0.0.1:8400` for the visual check; kill only the server you started.

## Environment-class table (symptom → counter)
| Symptom | Cause | Counter |
|---|---|---|
| checks 77–82 skipped | torch/kornia absent in `.venv` | `./setup.sh --learned` (network, ~2 GB); skipping is loud, not a failure |
| check 80/81 fail with a `~/.cache/torch` path | `TORCH_HOME` not pinned | `_pin_torch_home()` must run before any kornia import; do not export TORCH_HOME in the shell |
| Gate 1 slower than ~90 s | learned matcher on a cold process, or another CPU-heavy job | re-run once; compare against the 62.7 s baseline before calling it a regression |
| `Address already in use` on 8378 | a `run.sh` still running | `pgrep -fl 'reveal.py serve'`, kill only pids whose cwd is this repo |
| `_reveal/jobs` growing | past sessions' job dirs | `scripts/clean.sh --jobs` |

## Fixtures (owner-owned catalogue — rule: the inputs are part of the contract)
Location decided 2026-09-13 (owner: "gitignored fixtures INSIDE project"): `fixtures/` at the repo
root; `.gitignore` has `/fixtures/*` and `!/fixtures/MANIFEST.md`, so photos stay local and the
catalogue is tracked. `fixtures/MANIFEST.md` is the ONE catalogue: `id · before · after · mode ·
class · exercises · expected (dated)`. As of 2026-09-13 it has no row: the graffiti-box pair from
`HANDOFF.md §9.1` is the first entry once the owner copies it in. A harness or benchmark may not
invent its own real inputs; synthetic pairs stay in the harnesses.

## Concurrency classes
Gate 0 and Gate 2 may run alongside anything. Gate 1 binds a port and times the learned matcher —
run it alone. Two `serve` instances need distinct `--port` and `--workdir`.
