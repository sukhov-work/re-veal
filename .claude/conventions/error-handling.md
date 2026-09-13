# Error handling — Reveal

- One exception class for pipeline failures: `AlignError` (`reveal.py:197`) carrying an
  operator-readable message. `run_alignment` turns it into `job.fail(msg)`; anything else is
  logged with a traceback and becomes "Unexpected problem …". Never let a stack trace reach the page.
- Optional layers announce themselves: `pillow_heif`, `rawpy`, `imageio_ffmpeg`, torch/kornia each
  import inside `try/except` and record `_X_ERR`; `cmd_check` prints the whole matrix; a missing
  layer yields a plain "install …" message at the point of use, never a crash and never a silent
  `None` (that exact shape hid the learned matcher for three releases, `HANDOFF.md §5b`).
- Degrade paths are visible: every fallback in the estimation ladder logs its engagement at INFO
  (`arbitration: … -> peripheral SSIM …`, `ECC drifted … keeping feature transform`). A new
  fallback follows suit and names a first-fire watch in the handover.
- Guards stay: the sanity gate, the ECC trust region, the residual cap and the manifest gate are
  detectors; when one fires on a legitimate case, fix what violated the condition, never widen the
  detector in place (`AGENTS.md` hard constraints; `HANDOFF.md §9.8`).
- HTTP: `_err(code, msg)` for every client error; job ids are regex-gated; downloads only from
  the fixed allow-list; body cap 2 GiB; unknown `mode` falls back to `reshot` (check 62) — a bad
  value degrades, it does not 500.
- Network: the runtime raises `AlignError("run ./setup.sh --learned")` rather than downloading
  (check 82). Any new dependency that fetches at first use is a bug by definition.
