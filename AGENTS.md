# AGENTS.md — Reveal

Reveal is a local before/after photo aligner: one Python file (`reveal.py`) warps an AFTER photo
onto a BEFORE photo, serves a comparison slider on 127.0.0.1, and exports aligned stills plus a
wipe/fade transition video. Since 2026-09-13 a second single-file tool, `transitions.py`, renders
the change between two photos as a transition video (harness `transitions_harness.py`); the two
modules never import each other. Design docs live under `.claude/claude-docs/` (moved there
2026-09-13 by owner ruling): `HANDOFF.md` (Reveal design of record — invariants, pipeline, 27-row
decision log, harness coverage, risks, amendments §11), `TRANSITIONS.md` (transitions design of
record), `EXPLORATION_PLAN.md` (work plan, ranked by the owner on 2026-09-13). A bare `HANDOFF.md §N`
or `TRANSITIONS.md §N` in any doc means that file there.
Authority: `HANDOFF.md` wins over the plan; any new decision
EXTENDS `.claude/claude-docs/DECISIONS.md` or supersedes a prior line by date — it never edits
history. `HANDOFF.md §6` is the pre-bootstrap decision log; decisions from 2026-09-13 on go to
`DECISIONS.md`, and `HANDOFF.md` gets a dated amendment row when a shipped change contradicts it.

## Session loop (the persistence spine — hooks run the bookends)
- Memory graph root `mem:core` (`.serena/memories/`, machine-local) · `DECISIONS.md` (append-only,
  compacted in eras) · `NEXT_SESSION_PROMPT.md` (read FIRST at boot, gitignored) · conventions +
  design docs. Rules: `mem:decisions/session_workflow`.
- Verification tiers in every claim: **harness-tested** (synthetic pairs, `harness.py`) /
  **real-pair-VERIFIED** (a catalogued real photo pair through `align` or the page) /
  **UNVERIFIED**; reasoning-only statements keep `HANDOFF.md`'s `[INFERRED]` label.
  "It ran here" ≠ verified; green gates ≠ the real surface — the harness has never seen a real
  HEIC, DNG or ARW file, and the first real pair only arrived at v1.3.1.
- Done = change + gates + real-surface run + memory + DECISIONS line + handover + doc-sync.

## Reversibility (every behaviour change)
Before the first edit, state how the change is turned off: a flag (default-off), a config default,
a clean revert commit, or **irreversible** — which needs an explicit owner yes before it starts.
The answer rides the DECISIONS line as `[revert: …]`. Risky quality work ships in the experimental
lane: default-off, one surface, no effect on the default path. In this repo the lane has two
ready-made shapes: a new key in `MODES` (`reveal.py:157`) leaves `reshot` untouched; a new value
of `--style` (`reveal.py:1433`, `export_video`) leaves `wipe` untouched. A change to `CFG`
defaults or to the strict `reshot` profile is NOT in the lane — it needs its own decision line.

## No-regression roster (struck from only by a recorded owner ruling)
- `harness.py` 82/82 green (62.7 s wall on 2026-09-13) and `reveal.py check` all OK (18.5 s).
- `transitions_harness.py` green (count in `TRANSITIONS.md §5`; 54 on 2026-09-26, ~10 s) and
  `transitions.py check` all OK.
- The seven invariants in `HANDOFF.md §2`: localhost only · originals never modified · BEFORE is
  the reference frame · convergence judged on inlier statistics, never pixel similarity · the
  residual field is low-order by construction · graceful degradation of optional layers · the
  operator surface stays `./setup.sh` + `./run.sh` + the page.
- The first real pair's result (`HANDOFF.md §9.1`, fixture `match_4`): sift, 458 inliers, 0.74 px
  rmse in the 2026-07-13 sandbox; 481 inliers, 0.79 px, confidence 94 on this laptop (OpenCV 5.0.0,
  2026-09-13, `HANDOFF.md §11`); box edge straight to 0.54 px RMS (sandbox; not re-measured by the
  CLI). Re-measure it after any estimation or residual change with
  `scripts/bench_transitions.py --reveal --only match_4`.
- The offline contract: no network call outside `cmd_warmup` (harness 80–82).

## Knowledge — search order (stop at first hit)
1. memory (`mem:core` → index) · 2. `.claude/claude-docs/` (handover, DECISIONS top, plan) and
`HANDOFF.md` · 3. `.claude/conventions/` · 4. the codebase (`reveal.py` section map in
`.claude/conventions/architecture.md`, then grep, then read) · 5. external (OpenCV / kornia /
imageio-ffmpeg docs via Context7, `gh`, web) — never fabricate an API; `HANDOFF.md §8` shows the
`[VERIFIED via …]` label a versioned fact needs.

## Build / test / run — Python 3.13, venv + pinned pip requirements (no build step)
- Deps `./setup.sh` (`--learned` adds torch+kornia+transformers and fetches the 52 MB matcher
  weights into `models/` and the 99 MB depth model into `models/depth/`, both by a `warmup`)
  · Gate 1 `.venv/bin/python harness.py` (82 checks, ~63 s, needs the learned deps for 77–82)
  · Gate 2 `.venv/bin/python reveal.py check` (dependency + offline matrix, ~19 s)
  · Gate 1b `.venv/bin/python transitions_harness.py` (~10 s; own numbering space; count in `TRANSITIONS.md §5`)
  · Gate 0 `.venv/bin/python -m py_compile reveal.py harness.py transitions.py transitions_harness.py`
  (seconds; run before Gate 1)
  · Run `./run.sh` (serves 127.0.0.1:8378 and opens the browser) · headless
  `.venv/bin/python reveal.py align BEFORE AFTER --out DIR [--mode loose] [--video --aspect 9:16 --style wipe|fade]`
  · Clean `scripts/clean.sh` (`--jobs` also empties `_reveal/jobs`).
- Never claim done with a failing gate. The harness is one process, all-or-nothing, and takes a
  minute; section selection is backlog row T2, not a thing you invent inline.
- `models/` is write-protected by `.claude/settings.json`: only `reveal.py warmup` and
  `transitions.py warmup` (under `models/depth/` + `models/DEPTH_MANIFEST.json`, gitignored) write there.

## Workflow
`/reveal` for implement / fix / design / research / review / audit. Heavy design →
`~/.agents/skills/pilot` if installed, else `/reveal` alone.
- **Prose gate** (`.claude/rules/prose.md`, owner order 2026-09-13): every dev-facing text — the
  final message, DECISIONS lines, handover, design docs, plan and backlog rows, memory, commit
  messages — passes the `no-slop` skill (load it with the `Skill` tool, run its pass) before it is
  saved or shown.
- **Ship** (owner ruling 2026-09-13): Phase 4 ends with a commit on `main` and `git push origin main`.
  No branches, no PRs. Never push with a red gate; never force-push.
- **Fixtures** live in `fixtures/` inside the repo, gitignored except `fixtures/MANIFEST.md` (the
  tracked catalogue; owner ruling 2026-09-13). The real-pair tier starts when the first row exists.

## Hard constraints (violations = bugs)
- Server binds 127.0.0.1 only; no external request at runtime; the runtime never downloads
  (manifest-gated, `HANDOFF.md` decisions 24–27).
- Originals are never modified; every output is a new file in the job dir.
- B is warped onto A, never the reverse; every geometric quantity is B→A; `scale_h` transport is
  pinned by harness check 19.
- No pixel-similarity scale in the confidence score (`HANDOFF.md §3.4`, decision 21); no spatially
  masked dense flow in the residual stage (decision 18); the strict `reshot` profile is never
  widened in response to loose-mode feedback (`§9.8`).
- Engineer features go into the CLI or constants, not the UI (invariant 7).
- Single file by design: `reveal.py` stays one module, and so does `transitions.py` (a second
  single-file tool by the 2026-09-13 decision); helpers live in sections, not packages.
- `transitions.py` never imports `reveal`, `reveal.py` never imports `transitions`, and
  `transitions.py` imports nothing that can reach the network or load weights at module level;
  torch and transformers appear only inside its depth section, behind `transitions.py warmup` +
  `models/DEPTH_MANIFEST.json` + refuse-to-download (transitions harness 1–3, 48–51; 2026-09-23).
  The two tools share the venv and `requirements*.txt`; a new dependency is a decision.

## Recurring gotchas (cost real time — check before they bite)
- `findTransformECC` maps TEMPLATE(A) → INPUT(B) coordinates; seed with `inv(H)` and invert back
  (`HANDOFF.md §3.2.6`, 2026-07-10).
- rawpy applies the camera flip itself — do NOT re-apply EXIF orientation to RAW output
  (`§3.1`, 2026-07-10).
- Inlier counts do not compare across matchers; arbitrate on peripheral SSIM against one fixed
  mask (`§5b`, decision 23, 2026-07-13).
- A wobble metric from an unsigned edge detector, or a window spanning two parallel structures,
  fabricates 5–12 px of fake wobble; use signed single-transition tracking and a fitted quadratic
  (`§5a`, 2026-07-12).
- Unexercised optional code is a liability: the learned matcher shipped unrun for three releases
  behind a `try/except` that returned `None` (`§5b`, 2026-07-13). Anything optional gets a harness
  check that runs it, or a check that proves it is skipped loudly.
- Serena on this machine uses the JetBrains backend: symbol navigation works only while the IDE
  has this project open; memory reads and writes work regardless (2026-09-13).

## Permanently out (scope fence — each is a cited HANDOFF ruling; reopening one needs a new dated DECISIONS line)
- LoFTR as the learned matcher (decision 22) · MPS/GPU inference (decision 9) · an
  operator-editable settings file (decision 8) · the ffmpeg `xfade` filtergraph for video
  (decision 6) · dense or masked residual flow applied to pixels (decisions 16, 18, 20) · a
  pixel-similarity term in the score (decision 21) · lazy model download at runtime
  (decisions 24, 27). Every audit verdict states whether anything crossed this line.
