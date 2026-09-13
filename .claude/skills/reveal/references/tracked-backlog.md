# Tracked backlog — the ONE debt / tails registry (durable, version-controlled)

Seeded 2026-09-13. This file is the durable copy; the (gitignored) handover mirrors it, never
replaces it.

**Rules**
- One row per item. IDs are stable and never reused (`T1`, `T2`, …); the range and count are
  stated in the header and must have no gaps.
- Every row is dated at creation and dated again at every state change.
- **Audits VERIFY rows; they never re-discover them.** A finding matching a row is reported as
  STATUS VERIFICATION against that row, citing it.
- Closing a row is a dated **state edit**, never a deletion. Cite the closing DECISIONS line.
- New debt found anywhere — a session tail, an owner ruling, an audit finding not fixed in the
  same session — lands here the SAME session.
- The `Pointer` must resolve today. A dangling pointer is itself a finding; a `DECISIONS 2026-09-13`
  pointer may resolve in `DECISIONS.md` **or** its archive, so check both before calling it dead.
- States: OPEN · CLOSED · DEFERRED · PARKED (owner order) · WATCH · ACCEPTED RISK · WON'T-FIX ·
  STANDING RULE · ARMED (a reopener with a named trigger).

- The table is **five columns**. A row with fewer cells is a finding in its own right, and the
  check must read the row SHAPE, not its values — a 3-cell row survived two audits that only ever
  looked at the contents.

Range: T1–T12 · 12 rows · 9 OPEN · 1 DEFERRED (T6) · 2 CLOSED (T4, T7) (update this line at every state change; the range must have no gaps).

| ID | Since | Item | Pointer | State (dated) |
|----|-------|------|---------|---------------|
| T1 | 2026-09-13 | Audit machinery shipped but never exercised: tracks A–C and F have no checklists, and the false-positive ratchet has no baseline | `references/audit-mode.md`; DECISIONS 2026-09-13 | OPEN (2026-09-13) — first Audit scheduled at the first phase boundary |
| T2 | 2026-09-13 | `harness.py` is one all-or-nothing process (~63 s): no way to run one lettered section; algorithm exploration will re-run all 82 checks per iteration | `harness.py:101–918` (sections A–Q); `conventions/testing.md` | OPEN (2026-09-13) — mission slice H1 in EXPLORATION_PLAN.md |
| T3 | 2026-09-13 | No benchmark sheet: an algorithm change has no per-pair before/after row (method · inliers · rmse · confidence · residual · wall s) to be judged against | `conventions/testing.md §Measurement`; `HANDOFF.md §3.4` (per-pair comparison rule); `scripts/bench_transitions.py --reveal` | OPEN (2026-09-13 late) — the first Reveal rows exist in `benchmarks/2026-09-13-real-pairs.md`; H2's remaining part is the committed baseline and the pair-by-pair diff on every later run |
| T4 | 2026-09-13 | Fixture catalogue empty: no real pair in or beside the repo; the graffiti-box pair of `HANDOFF.md §9.1` (the roster's real-pair anchor) has no known path | `conventions/verify.md §fixtures`; `fixtures/MANIFEST.md` | CLOSED (2026-09-13 late) — the owner placed ten pairs (5 match, 5 mismatch, 2 HEIC); catalogue has ten rows; the graffiti-box pair is `match_4` (481 inliers, 0.79 px here). DECISIONS 2026-09-13 late |
| T5 | 2026-09-13 | Video export has no frame-level verification beyond size/fps/duration (checks 34–37); a new transition style cannot be judged by the harness | `reveal.py:1433` `export_video`; `harness.py:325` section L | OPEN (2026-09-13) — slice H3 |
| T6 | 2026-09-13 | No lint/format/type gate; the profile's slots are empty by owner choice pending a decision (ruff? none?) | `AGENTS.md §Build` | DEFERRED (2026-09-13 evening) — owner: "At your discretion"; agent chose no lint gate now, revisit at the first phase boundary (DECISIONS 2026-09-13) |
| T7 | 2026-09-13 | `HANDOFF.md §10` runbook still says "51 assertions" while `§7` says 82 — a volatile count in two places (docs.md item 7) | `HANDOFF.md §10`; `§7`; `§11` | CLOSED (2026-09-13 evening) — §10 now points at §7 for the count; recorded in `HANDOFF.md §11` and DECISIONS 2026-09-13 |
| T8 | 2026-09-13 | PyAV (`av`) is the research artifact's video I/O for PTS-exact clip cuts, but installing it beside `opencv-python-headless` on this Mac prints an objc duplicate-class warning for `libavdevice` (cv2 61.3 vs av 62.3: "may cause spurious casting failures and mysterious crashes"); a new pinned dependency touches `requirements.txt` | `TRANSITIONS.md §4`; scratch run 2026-09-13 | OPEN (2026-09-13) — decision before slice TR4 (clips); alternatives: `cv2.VideoCapture` + PTS via ffprobe, or ffmpeg-piped decode |
| T9 | 2026-09-13 | Transitions have never seen a real photo pair: class routing, morph look and `edge_ratio` on real re-shots are UNVERIFIED (research E2) | `TRANSITIONS.md §7.1`; EXPLORATION_PLAN TR2; `benchmarks/2026-09-13-real-pairs.md` | OPEN (2026-09-13 night) — first sheet done on 12 pairs (routing 11/12 as labelled, flicker gate green); closes when the owner has rated the strips (E2: ≥ 6 of 10 usable) |
| T10 | 2026-09-13 | No seam from Reveal to the transitions engine: `reveal.py align --video --style morph` and the page cannot reach it; doing so adds a one-way lazy import to `reveal.py`, which is a Reveal-side behaviour change needing the owner's yes | EXPLORATION_PLAN TR3; `conventions/architecture.md §seams` | OPEN (2026-09-13) — owner decision |
| T11 | 2026-09-13 | The research artifact's RoMa path picks the MPS device and downloads weights on first call; both violate this repo's rulings (decision 9; decisions 24–27). Not ported. Any learned dense matcher needs CPU-only + warmup/manifest first | `TRANSITIONS.md §4`; research `correspond._roma_displacements` | OPEN (2026-09-13 evening) — precondition of slice TR5; device rule now in `HANDOFF.md §11` (CPU first, MPS only with a CPU-equivalence check) |
| T12 | 2026-09-13 | A copy of the `no-slop` skill (`.claude/skills/no-slop/SKILL.md`, `SKILL-DNA.md`, byte-identical to `~/.claude/skills/no-slop/`) was vendored into the project and staged when the skill was invoked at 21:12, and went out unnoticed in commit `39d2c67` under a message that names only the research artifact. Keeping it makes `.claude/rules/prose.md` work on a fresh clone; it can drift from the global copy | `git show --stat 39d2c67`; `.claude/rules/prose.md` | OPEN (2026-09-13) — owner decides keep-and-sync or remove; until then the rule loads whichever copy the Skill tool resolves |
