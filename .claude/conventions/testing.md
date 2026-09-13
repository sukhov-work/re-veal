# Testing conventions — Reveal

The gate is `harness.py`: numbered assertions with synthetic inputs of known ground truth,
monkeypatched optional layers, and a real HTTP round-trip against the stdlib server. Coverage map:
`HANDOFF.md §7`. Baseline 2026-09-13: 82 passed, 0 failed, 62.7 s wall (Apple Silicon, torch
present).

## Rules the existing 82 checks follow — match them
- `check(n, desc, cond)`; numbers are stable and never reused. A new check takes the next number
  and lands in the lettered section it belongs to (A–Q today); a new capability opens the next
  letter (R…). Update `HANDOFF.md §7`'s coverage paragraph and the `82 checks` count in one place
  (the count is volatile: every other mention says "as of <date>").
- Ground truth is constructed, not observed: `make_pair()` warps A by a known `true_h` with an
  exposure change and a changed-content patch; recovery is judged by `corner_err` against that H.
- Optional layers are exercised both ways: present (real call) and absent (monkeypatched `None`
  → the plain message, never a crash). Section B's `_FakeRawpy` is the pattern.
- The offline contract is tested by patching `socket.socket` to raise (check 81), not by trusting
  a flag.
- A calibrated scenario (section N, checks 56–58) states what strict must REFUSE and what loose
  must ALIGN; a new mode gets its own three: one strict refuses / new aligns, one genuinely
  perturbed pair, one that must still pass in strict.

## Can this check FAIL? (mandatory for every new assertion)
Name the mutation that turns it red, and apply it once for one of them per slice. Refused shapes:
an absolute the current value already satisfies · a capture that cannot disagree with itself ·
a no-op that reads as success. Example from this repo: check 73 ("score no longer depends on raw
SSIM") is red if a SSIM term is added back — that is its mutation.

## Measurement discipline for algorithm work
- Numbers need DISTINCT inputs and a stated method; the peripheral-SSIM ceiling is scene-dependent
  (`HANDOFF.md §3.4`), so compare a change pair-by-pair against the baseline row for the same pair,
  never across pairs.
- Timing is reported as wall seconds on a named machine with the working-copy size; sandbox
  numbers in `HANDOFF.md §8` are Linux x86, not this laptop.
- A benchmark row = `pair · mode · method · inliers · rmse_px · confidence · residual kept ·
  changed_pct · wall s` from `metrics.json` (`reveal.py align --out DIR` writes it). The sheet is
  backlog row T3 until it exists; until then a change's before/after numbers go in the DECISIONS line.

## Real-pair tier
`real-pair-VERIFIED` means a pair from the owner's fixture catalogue (`verify.md §fixtures`) went
through `align` or the page and the observed `metrics.json` is quoted. The harness cannot grant it.
