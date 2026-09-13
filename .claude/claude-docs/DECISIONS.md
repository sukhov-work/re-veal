# Reveal — Decisions Log

One line per meaningful change: what was decided, files touched, numbers measured, verification
tier (harness-tested / real-pair-VERIFIED / UNVERIFIED). **Append-only, absolute-dated.**
Supersede a past line with a newer dated line; never edit or delete old ones. Owner orders are
quoted VERBATIM ("Owner order (verbatim intent): …"), never paraphrased. Product decisions taken
before 2026-09-13 live in `HANDOFF.md §6` (27 rows) and are cited by number, not copied here.

Compaction (a move is not an edit): at every era close, and whenever the hot section passes ~100 KB
(≈25k tokens — it must fit one read; the boot hook warns), move the closed era BYTE-VERBATIM to
`DECISIONS_ARCHIVE.md` under a dated `## Moved <date>` divider, record the md5 + line/byte count of
the moved block here in a Compactions table, append a 10–30 line era digest in its place (every
caveat and number preserved), and re-seat the append marker under the heading. Proof of purity =
the removed line count equals the moved block; no dated line changed.

## Compactions
| Round | Date | Moved | md5 | Lines / bytes |
|---|---|---|---|---|

## Traps & gotchas (durable — promoted from `HANDOFF.md`, each naming its origin)
- `findTransformECC` maps TEMPLATE(A) coords into INPUT(B) coords (applied with `WARP_INVERSE_MAP`): seed with `inv(H)`, invert the result back. Cost a bug in the founding build (2026-07-10, `HANDOFF.md §3.2.6`).
- `scale_h` transport shipped inverted once; harness check 19 pins it with ground truth (2026-07-10, `§3.3`).
- rawpy applies the camera flip itself — re-applying EXIF orientation to RAW output double-rotates (2026-07-10, `§3.1`).
- Grayscale change detection misses equal-luminance repaints; per-channel max over normalized channels (harness 21 failure, 2026-07-10, decision 4).
- An unsigned edge detector, or a window spanning two parallel structures, fabricates 5–12 px of fake wobble; judge wobble as residual from a fitted quadratic with signed single-transition tracking (field defect #1, 2026-07-12, `§5a`).
- Inlier counts are not comparable across matchers (SIFT 458 → SSIM 0.566; learned 408 → 0.429); arbitrate on peripheral SSIM (2026-07-13, decision 23).
- Optional code that is never executed is a liability: the learned path shipped unrun for three releases behind a `try/except` returning `None` (2026-07-13, `§5b`).
- kornia's LoFTR derives stride and x-scale from the HEIGHT alone; non-multiple-of-8 inputs mis-scale keypoints (2026-07-13, `§5b`) — moot since LoFTR is out, kept as a class: check a model's input-shape contract before feeding it resized images.

## Recent
<!-- append below this line -->
- **2026-07-10 — v1.0.0 founding build** (backfilled from `HANDOFF.md`). Classical pipeline (SIFT/ORB + MAGSAC++ + ECC), optional learned fallback (LoFTR then), auto-gated residual flow, stdlib HTTP server on 127.0.0.1, embedded page, wipe/fade video via piped frames; 51 harness assertions. Decisions 1–10 in `HANDOFF.md §6`. harness-tested (Linux sandbox).
- **2026-07-10 — v1.1.0 matching modes** (backfilled). `MODES = {reshot, loose}` as a CFG overlay; 4-DOF similarity fallback and always-on learned matcher in loose; residual hard-off in loose. Decisions 11–13. harness-tested.
- **2026-07-10..13 — v1.2.0 → v1.3.0 field defect #1: wavy subject edges** (backfilled; exact day not recorded). Root-cause chain reproduced in harness 63–65 before fixing; three designs rejected empirically (feathered kill zone, distance-ramp attenuation, per-subject rigidification); final: DIS flow as samples only → robust 20-parameter cubic field, whole-field rejection over 6 work-px. Wobble 8.5 px → 0.09–0.12 px on the reproduction. Decisions 14–20. harness-tested; real-pair-VERIFIED on the graffiti-box pair (box edge 0.54 px RMS vs camera original 0.62).
- **2026-07-13 — v1.3.1 confidence rescored on geometry only** (backfilled). Pixel-similarity terms (absolute SSIM, peak sharpness) removed as scene-dependent in opposite directions; local-max boolean kept as a ×0.6 penalty. Decision 21. real-pair-VERIFIED (first real pair: sift, 458 inliers, 0.74 px rmse → 95).
- **2026-07-13 — v1.4.0 learned matcher first executed and replaced** (backfilled). LoFTR out (plain-HTTP weights, input-shape bug, untestable); DISK + LightGlue in; cross-matcher arbitration on peripheral SSIM; latent `max([])` crash fixed. Decisions 22–23. harness-tested (77–79).
- **2026-07-13 — v1.5.0 learned matcher made genuinely offline** (backfilled). `TORCH_HOME` pinned to `models/`; manifest-gated runtime that refuses to download; warmup runs a real forward pass and records sha256s. Decisions 24–27; harness 80–82 (all sockets patched to raise). Footprint 2 files / 52 MB. harness-tested.
- **2026-07-21 — Repo initialised on GitHub** (`sukhov-work/re-veal`, commits `e51b4e5` init, `344e4c4` cleanup): source, harness, docs and the 52 MB of weights committed as-is. No behaviour change.
- **2026-09-13 — Bootstrapped the operating environment** (bootstrap-project v2, Scaffold mode; profile: existing Python 3.13 venv repo, laptop-only + GitHub publish remote, design of record `HANDOFF.md` present, plan absent, Serena registered on the JetBrains backend, Codex present, fan-out 3). Laid down: `AGENTS.md` (contract) + `CLAUDE.md` import · `.claude/settings.json` (allow-list incl. `.claude/**` + `.serena/**`, `models/**` denied, hooks via `${CLAUDE_PROJECT_DIR}`) · hooks `session-start.sh` (verified, 0.7 s) + `pre-compact.sh` (UNVERIFIED leg) · `.codex/hooks.json` SessionStart (UNVERIFIED) · `.claude/conventions/{architecture,testing,naming,error-handling,verify,contracts}.md` · `/reveal` skill + `references/{audit-mode,review-agent,tracked-backlog (T1–T6),laws}.md` + `checklists/{README,docs}.md` · memory graph under `.serena/memories/` (core 3.2 KB, 8 files) · this log with 7 backfilled lines and 8 promoted traps · `NEXT_SESSION_PROMPT.md` (gitignored) · `EXPLORATION_PLAN.md` DRAFT (H1–H3 harness slices, E1–E3 exploration directions — owner ranks) · `audits/README.md` · `scripts/clean.sh` · `.gitignore` agent block; 3 tracked `.DS_Store` untracked. Kept `HANDOFF.md` at the root as the design of record (existing convention). Skipped: Phase F delivery artefacts (shape A), SessionEnd auto-ship (not asked), lint gate (none in repo — T6). Gate baseline: harness 82/82 in 62.7 s · check all OK in 18.5 s (this laptop, torch present). Owner order (verbatim intent): "i want to keep exploring additional capabilities there ( e.g use and improve algorithms for additional modes, video transitions generation etc so need to build proper harness around it first". [tier: Standard] [revert: commit] harness-tested.
