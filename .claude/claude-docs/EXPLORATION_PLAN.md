# Reveal — Exploration plan (DRAFT 2026-09-13 — the owner ranks; nothing below is decided)

Status: **DRAFT.** Authority: `HANDOFF.md` wins; a slice that contradicts a `§6` decision needs a new
dated `DECISIONS.md` line before it starts. This file is iterated in place (dated amendment rows at
the bottom), never forked.

## Owner's stated directions (verbatim, 2026-09-13)
> "i want to keep exploring additional capabilities there ( e.g use and improve algorithms for
> additional modes, video transitions generation etc so need to build proper harness around it first"

Read as: (1) the operating environment first — done by the bootstrap; (2) then the *product*
harness gaps that make algorithm and transition work measurable (H-slices); (3) then the
exploration itself (E-slices), each in the experimental lane (`AGENTS.md §Reversibility`).

## H — harness before exploration (evidence: `HANDOFF.md §7`, `harness.py`, backlog T2–T5)
| Slice | Goal (acceptance) | Seam | Revert | Gate / check | Size | Depends on |
|---|---|---|---|---|---|---|
| **H1** section selection | `harness.py --only C,O` runs the named lettered sections in ~seconds; default (no flag) runs all 82 unchanged; numbering untouched | `harness.py` top: wrap sections in `if want("C"):` guards; argparse | `[revert: commit]` — default path identical | full run still 82/82; `--only A` runs exactly checks 1–5 (count asserted) | S | — |
| **H2** benchmark sheet | `scripts/bench.sh` (or `reveal.py bench`) runs `align` over every `fixtures/MANIFEST.md` row and writes one table row per pair (pair · mode · method · inliers · rmse_px · confidence · residual · changed_pct · wall s) to `benchmarks/<date>.md`; a baseline is committed once and every later run is diffed against it pair-by-pair | CLI section (`cmd_align` already writes `metrics.json`) or a script | `[revert: commit]` — no product behaviour changes | the sheet reproduces itself on a second run (deterministic); a deliberately broken constant changes the row | M | **T4** fixture location (owner) |
| **H3** video frame-level checks | harness section R: decode the exported mp4 and assert per style — frame count = fps × seconds ± 1, first/last frames equal the stills, wipe seam position monotone, no all-black frame, fade luminance monotone between holds | `harness.py` after section L (checks 34–37 stay) | `[revert: commit]` | each new check names its red-making mutation (e.g. drop the last hold → frame-count check red) | S–M | — |

## E — exploration directions (each needs its own design pass in `/reveal` Design type before code)
| Slice | Direction (owner's words → concrete candidate) | Lane | Must not touch | First falsification probe |
|---|---|---|---|---|
| **E1** additional modes | a third `MODES` key for a pair class `reshot` refuses and `loose` mis-fits (candidates the owner names — e.g. large parallax, mirrored/rotated re-shots, night/day) | new key; `reshot` and `loose` byte-identical | `CFG` defaults; the strict profile (`§9.8`) | one synthetic scenario triple (strict refuses · new aligns · same-scene still passes) in the harness N style, before any ladder change |
| **E2** algorithm improvements | a candidate estimator or refinement competing inside `estimate_alignment` (e.g. a second learned matcher, a better ECC seed, residual-field order/regularisation) | competes as a candidate; arbitrated on peripheral SSIM (decision 23) | ranking by inlier count; the score formula (decision 21); masked/dense flow (18, 20) | the H2 sheet before/after on every catalogued pair — no sheet, no claim |
| **E3** video transitions | new `--style` values beyond `wipe`/`fade` (e.g. radial wipe, split/blinds, zoom-reveal, morph-through-residual) + easing/hold parameters | new style branch in `export_video`; `wipe` default untouched | the frames-piped renderer (decision 6 rules out the xfade filtergraph) | H3 checks for the style's observable, on a synthetic pair, before the page control exists |

## Open decisions (the owner answers; each becomes a DECISIONS line)
1. **Rank H1–H3 and E1–E3.** Proposed order: H1 → H3 → (T4 lands) H2 → E3 → E1 → E2 — cheapest
   measurability first, then the direction whose gate (H3) exists.
2. **Fixture location (T4):** where do the real pairs live (the graffiti-box pair of `§9.1` first)?
   Proposed: a folder outside the repo, symlinked as `fixtures/` (gitignored), with `MANIFEST.md`.
3. **Lint gate (T6):** none (status quo) or `ruff` added to the venv as Gate 3?
4. **Push policy:** direct to `origin main` at Phase 4 (proposed for a solo repo), or branches + PRs?
5. **`HANDOFF.md` role:** stays the design of record at the root, amended with dated rows (proposed),
   or migrates under `.claude/claude-docs/`?

## Amendments
| Date | Change | By |
|---|---|---|
| 2026-09-13 | Drafted at bootstrap from the owner's directions and `HANDOFF.md §7/§9`; unranked | bootstrap session |
