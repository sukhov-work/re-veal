---
name: reveal
description: >
  Universal work skill for Reveal, the local before/after photo aligner (reveal.py + harness.py),
  and for Transitions, the photo-to-photo transition renderer beside it (transitions.py +
  transitions_harness.py). Implementation, fixes, design, research, review, and whole-repo
  audits. Parallel-first, evidence-cited, falsification-gated. Trigger on: "implement", "build",
  "add", "fix", "debug", "design", "plan", "investigate", "research", "review", "critique",
  "double-check", "verify this claim", "audit", "comprehensive review", a new matching mode, a
  new video transition, style or preset, a morph / correspondence / color-path change, a dense
  matcher or generative backend, an estimator or residual-field change, a harness or benchmark
  change, any EXPLORATION_PLAN.md slice reference (e.g. "slice H2", "TR5"), or any task spanning
  more than one section of either module.
argument-hint: <what to build, fix, investigate, review, or design>
---

# reveal: parallel-first work

Reveal is a local before/after photo aligner: one Python file (`reveal.py`) warps an AFTER photo
onto a BEFORE photo, serves a comparison slider on 127.0.0.1, and exports aligned stills plus a
wipe/fade transition video. Beside it, `transitions.py` renders the change between two photos as a
morph / dissolve / portal / luma video (design of record `TRANSITIONS.md`); the two modules never
import each other. Canonical docs, all under `.claude/claude-docs/`: `HANDOFF.md` (Reveal design of
record — invariants §2, pipeline §3, decisions §6, harness coverage §7, risks §9, amendments §11),
`TRANSITIONS.md` (transitions design of record — invariants §1, pipeline §2, harness §5, numbers §6),
`EXPLORATION_PLAN.md` (work plan, ranked by the owner on 2026-09-13). Prose rule: `.claude/rules/prose.md`
(every dev-facing text passes the `no-slop` skill before it is saved or shown). Standards: `.claude/conventions/` (architecture ·
testing · naming · error-handling · verify · contracts). Known debt lives in exactly one place:
`references/tracked-backlog.md`.

## Domain mapping (read once)

| Generic term | In this repo |
|---|---|
| **artifact** | a section of `reveal.py` or `transitions.py` (the `# ----` blocks mapped in `conventions/architecture.md`), a lettered section of `harness.py` or `transitions_harness.py`, a doc |
| **gate** | Gate 0 `py_compile` (four files) · Gate 1 `harness.py` (82 checks) · Gate 1b `transitions_harness.py` (count in `TRANSITIONS.md §5`) · Gate 2 `reveal.py check` + `transitions.py check` |
| **verify** | harnesses green, then a catalogued real pair (`fixtures/MANIFEST.md`) through `align` or the page with `metrics.json` quoted, or through `transitions.py pair` with `report.json` quoted and the strip looked at |
| **live drive** | `reveal.py align` on a real pair, or the served page (`conventions/verify.md`) |
| **the deploy** | laptop only; "shipped" = committed on `main` and pushed to `origin main` by the agent at Phase 4 — no branches, no PRs (owner ruling 2026-09-13) |
| **the backlog** | `references/tracked-backlog.md` |

## Workflow
```
Phase 0: Classify + calibrate tier + load context (handover FIRST, then the decision log)
Phase 1: Parallel research — every claim cited or UNVERIFIED (only when needed)
Phase 2: Execute — implement / fix / design / review / audit
Phase 3: Verify — falsification gate + verification tiers + exercise the real surface
Phase 4: Record — memory + DECISIONS + handover + doc-sync
```

## Phase 0 — classify, calibrate, load

### 0.1 Type

| Type | Depth | Skips |
|---|---|---|
| **Implement** (new capability / plan slice) | research → build → gates → verify | — |
| **Fix** (defect, broken gate) | locate → diagnose → minimal fix → verify | Phase 1 when the location is known |
| **Design** (a decision with options) | research → options → recommend → write it down | Phase 3 gates |
| **Research** (evaluate an approach/source) | parallel tracks → synthesize → report | Phases 2–3 |
| **Review** (judge one finished artifact: claim, doc, diff, result) | evidence-check against source + gate → verdict | Phase 2 build |
| **Audit** (whole-repo) | tracks → parallel finder agents → verification pass → report (`references/audit-mode.md`) | Phase 2 — **READ-ONLY on artifacts; fixes are separate sliced sessions** |

**Precedence when signals mix:** review > implement > design > research — a finished artifact
outranks intent; a requested state-change outranks a question. An owner "comprehensive review"
order ⇒ **Audit**, not Review.

### 0.2 Tier (gates everything downstream)

| Tier | Trigger | What runs |
|---|---|---|
| **Quick** | one section; "see if…"; a one-function fix; a constant; a new transitions preset (a `PRESETS` entry + one section-F assertion) | No fan-out. Inline evidence. One refutation attempt. Inline answer. |
| **Standard** | one pipeline stage plus its harness section; a normal plan slice; a new video style; a new transitions style (an `iter_frames` branch + a decoded-mp4 observable); a measured performance pass on one stage | Fan out only on real gaps (memory/docs first). Standard gate. |
| **Deep** | a new matching mode or estimator (touches ladder + arbitration + harness + page + CLI); a residual-field change; a new correspondence method, dense matcher or generative backend in `transitions.py` (weights, device, offline proof); a doc critique; "very heavy" | Full fan-out + escalation (see Heavy-task escalation). Full gate. |

Calibrate silently and record the tier as a tag in the DECISIONS line (`[tier: Standard]`). Two
failure shapes: ballooning a "see if" into an XL apparatus; under-scoping a Deep task into a thin pass.

### 0.3 Load
`list_memories` → `mem:core` → its index; **`NEXT_SESSION_PROMPT.md` first** (freshest state), then the
TOP of `DECISIONS.md` — read it **paged (offset/limit) or grepped**; a naive full read truncates.
Then the `HANDOFF.md` section and the `EXPLORATION_PLAN.md` slice your task touches, and the
conventions it touches (a new mode reads architecture + testing + contracts; a video style reads
architecture §seams + testing §can-this-fail). Note early **where the outcome will be recorded**
(which `mem:*` + which DECISIONS line) so the record survives truncation.

### 0.4 Shared-context block (paste into every sub-agent)
```
Request · Type + tier · Affected reveal.py sections / harness sections · Related HANDOFF.md §
and EXPLORATION_PLAN.md slice · Known constraints (AGENTS.md hard constraints + permanently-out
list + conventions) · Key functions / line anchors · Baseline anchor (DECISIONS entry) ·
Gate baseline (82/82, check all OK)
```

## Phase 1 — parallel research (only when ≥2 independent questions remain after memory + docs)

Launch applicable agents as named background tracks in **waves of at most 3** — a usage limit once
killed four at-once tracks before any reported; the two-wave rerun lost nothing. Heavier fan-out
goes through a workflow script; long agent reports go to scratchpad files, never the return value.
Roles: **Codebase** (map the sections and harness checks a change touches) · **Reference**
(`HANDOFF.md` + conventions, to catch a deviation from a cited decision early) ·
**External-source research** (OpenCV / kornia / ffmpeg behaviour from source or docs, never a
blog) · **Review tracks** (Audit, or Review beyond one artifact — `references/review-agent.md`).
Never narrate parallelism you are not running.

**Agent output contract** (terse, no prose padding):
```
## Findings: <agent>
### Key facts — <fact>: <evidence: file:line | doc§ | URL | command output>
### Relevant artifacts — | path:line | symbol | purpose |
### Constraints discovered
### Confidence: XX%
### Gaps: what could NOT be determined (mandatory; tool failures named here)
```

### Evidence discipline (main agent and sub-agents alike)
- Cite `file:line`, a doc section, a URL, or command output — or mark it **UNVERIFIED**.
  *"Could work" is not a finding.* Demand runtime evidence (a gate result, a log line, a
  `metrics.json`) before any causal or "done" claim.
- **Confidence gate:** ≥70% → act; <30% → stop and read the source/design doc; in between →
  reformulate once, then proceed with the gap named.
- **Measurement discipline:** quality numbers need DISTINCT inputs and a stated method; the
  peripheral-SSIM ceiling is scene-dependent, so compare pair-by-pair, never across pairs
  (`HANDOFF.md §3.4`). Verify that the knob you turned moves the mechanism it claims to move.
- **Honest degradation:** a dead tool returns *nothing*, and "no evidence" silently reads as
  "no problem". Classify every tool failure, name it in the report, and let it cap confidence.
- **Zero-result validation:** before reporting "no data / no matches", prove the probe CAN
  match something. Empty ≠ absent.
- **Provenance survives the agent.** Never promote a claim from an agent that was killed,
  interrupted, or reported before finishing.
- **Corrupt input is named in the first line.** A placeholder image, a truncated log, an unreadable
  export: say so immediately and fall back to self-captured evidence.
- Per-model routing is a knob: the expensive model for the critical track, a cheaper one for
  parallel verification runs. Record the routing in the handover.

### Three discipline lines (verbatim, whenever reasoning about causes)
1. **Symptom ≠ defect.** The symptom is where the failure surfaced; the defect may be sections
   away (field defect #1: wobbly edges surfaced in export, the defect was mask holes in the
   changed-region stage — `HANDOFF.md §5a`).
2. **"Could have" isn't "did".** A path that *can* produce the behavior didn't necessarily
   produce it on this case. Demand runtime evidence before promoting.
3. **Blame the cause, not the detector.** If the sanity gate, the ECC trust region, the residual
   cap or the manifest gate fired, fix what violated the condition — never widen the guard.

## Phase 2 — execute

**Implement**
1. **Intent gate.** State the desired outcome in ONE sentence; if you can't, interview first.
   Batch ALL open questions up front → one approval → build without a mid-build question drip.
   Deterministic values (mode names, thresholds, aspect sizes, check numbers) get NO invented
   defaults — derive from source or ask.
2. Read `.claude/conventions/` + the plan slice + 2–3 neighbour functions in the same section and
   the harness section that pins them. Match the neighbourhood; name the conventions you applied.
3. **Fix the baseline.** Gates green BEFORE the first edit — or snapshot and classify the
   pre-existing red. "Was it me?" must be answerable at every step.
4. Smallest vertical slice → change → **external truth decides** (harness output, `metrics.json`,
   a decoded mp4 — never "looks right"), measured against the ORIGINAL baseline every iteration.
   Harness checks alongside the change, not after; each new check names its red-making mutation.
5. **Classify every failure before reacting:** `my-change` / `pre-existing` / `flaky` (re-run
   ×2) / `infra` (torch absent, port busy). Only `my-change` counts against the slice. A failing
   gate halts feature work until diagnosed.
6. **Reversibility before the first edit.** Any change to observable behaviour states how it is
   turned off — a new `MODES` key or `--style` value (the experimental lane, default path
   untouched), a new `PRESETS` entry or `STYLES` branch in `transitions.py` (its lane; `morph`
   untouched), a `CFG` / `TCFG` default, a clean revert commit, or "irreversible" (owner yes
   first). The answer rides the DECISIONS line as `[revert: …]`. A performance change must leave
   the rendered frames byte-identical (hash before and after on the harness pair) or say what
   changed and by how many levels.
7. **Nothing already built regresses.** Before touching a shared surface (the estimation ladder,
   `_arbitrate`, `export_video`, `Job.status`, the page), name the neighbouring behaviours it can
   break and check them after — the no-regression roster in `AGENTS.md` is struck from only by a
   recorded owner ruling.
8. Blocked states are terminal and honest: `cannot_reproduce` · `verification_blocked` (e.g. no
   real pair in the fixture catalogue). A plausible change is NEVER reported as done.

**Fix**
Reproduce and capture the BAD case (a synthetic reproduction in the harness style, as §5a did
before fixing) → **frame-challenge** the reported framing with the cheapest probe → locate →
diagnose to root cause (three discipline lines) → minimal change, no drive-by refactor →
**would-it-fire check**: state the fix as a predicate and evaluate it against the captured BAD case,
and confirm it does NOT fire on a known-good case (the calibrated scenarios in harness N/O) → add
the regression check.

**Review**
Preflight the artifact (ref resolves, doc reachable, claim concrete — fail loud here) → load the
intent it is judged against FIRST (`HANDOFF.md` decision or plan slice), and never flag as missing
what the intent marks out of scope → check every claim against source and drop findings the source
disproves → frame-challenge the artifact's own premise → one refutation attempt on your own
verdict → per-claim **PASS / FAIL / CONTESTED** with evidence and gaps named. Findings only, no
praise padding. Every finding: `[severity] anchor — title` · impact · evidence · specific fix ·
`verifiedBy: source|computed|observed|UNVERIFIED`.

**Design**
Options table (complexity / fits the single-file architecture / risk to the roster) → adversarial
pass (Deep: 2–3 orthogonal skeptic lenses in parallel; Standard: one strong refutation yourself)
→ recommend one with evidence, feasibility stated CONDITIONALLY (best/worst case), counts
enumerated from source → write the deliverable. **Supersede, don't accrete:** iterating on
`EXPLORATION_PLAN.md` or `HANDOFF.md` = targeted edits + a dated amendment row, never a parallel
second file. **Cheapest falsification first:** for an algorithm idea, the cheapest probe is one
synthetic pair in the harness style, or one real pair through `align` — run it before planning.
A `HANDOFF.md §6` rejected alternative is reopened only with new evidence and a new dated line.

**Audit** → `references/audit-mode.md`. Read-only on artifacts; the session's diff touches the
report and this skill's files only.

## Phase 3 — verify

### Falsification gate (before presenting ANY conclusion; Quick = 1–2, Standard/Deep = all)
Any FAIL blocks presenting — rework, or downgrade the claim to an open question. *An
85%-confidence wrong story is more dangerous than a 50%-confidence right one, because the former
gets published* (into DECISIONS, memory and the canonical docs here).
1. **Cite-or-drop** — every load-bearing claim has evidence or an UNVERIFIED tag.
2. **Refutation attempt** — build the strongest counterargument to the main conclusion and check it.
   If the owner already said "not X", never re-confirm X without new evidence.
3. **Would-it-fire** — the fix/recommendation as a predicate, against the real motivating case
   and against a good case where it must NOT fire.
4. **False-positive safety** — 3+ legitimate scenarios where the change fires; any of them
   corrupting correct behavior → tighten first.
5. **Frame-challenge** — the request's own premise tested with the cheapest probe BEFORE heavy
   work (mostly a Phase-0/2 act; here you verify it happened).

Then the prose gate (`.claude/rules/prose.md`, owner order 2026-09-13): load the `no-slop` skill
with the `Skill` tool and run its pass on every dev-facing text before it is saved or shown — the
final message, DECISIONS lines, the handover, design docs, plan and backlog rows, memory leaves,
commit messages. Numbers instead of adjectives, `HANDOFF.md`'s evidence labels (`[VERIFIED …]`,
`[INFERRED]`). **"Not possible" is an acceptable answer.**

### Degrade-path visibility (any change touching the estimation ladder, arbitration, or an optional layer)
A fallback that engages silently is a regression that stays invisible. Any added or touched
degrade path must (a) emit a visible INFO line when it engages (the `arbitration: …` /
`ECC drifted …` pattern), and (b) hand over a named **first-fire watch** in
`NEXT_SESSION_PROMPT.md` stating the expected healthy value.

### Verification tiers — state each claim's tier explicitly
*"It ran here" ≠ verified.* The enum for this repo:
`harness-tested · real-pair-VERIFIED · UNVERIFIED` (+ `[INFERRED]` on reasoning-only statements).
```
harness-tested   every time:  .venv/bin/python -m py_compile reveal.py harness.py transitions.py transitions_harness.py   # Gate 0
                              .venv/bin/python harness.py                           # Gate 1, 82 checks (~63 s, alone)
                              .venv/bin/python transitions_harness.py               # Gate 1b (~5 s; count in TRANSITIONS.md §5)
                              .venv/bin/python reveal.py check                      # Gate 2
                              .venv/bin/python transitions.py check
```
Fix all failures before claiming success.

**Can this check FAIL?** For every assertion you add, name the mutation that turns it red — and for
one of them, apply it. Three shapes are refused: an absolute the current value already satisfies ·
a capture that cannot disagree with itself · a no-op that reads as success. A counter needs a
positive control AND its precondition pinned.
- **real-pair-VERIFIED only** (mark **UNVERIFIED** until actually run on a catalogued pair — see
  `conventions/verify.md §fixtures` and `mem:project/dev_environment`): anything about real
  photographs — HEIC-from-iPhone, DNG, ARW decode; the residual field firing on a real pair;
  runtime on this laptop; the look of an exported video on a real subject; any confidence-score
  claim (the score was rebuilt once because synthetic data misled it, decision 21).

### Exercise the real surface (gates alone ≠ verified)
For any new pipeline, export or page behaviour: drive it with `reveal.py align` on a catalogued pair,
or `transitions.py pair` for a transition (decode the mp4, quote `report.json`, look at `strip.jpg`)
(if no pair is catalogued in `fixtures/MANIFEST.md`, say `verification_blocked` and put the fixture
request in the handover);
**run it twice when state is involved** (run 2 must reproduce); capture `metrics.json` numbers in
the report and the DECISIONS line. A video change additionally decodes the mp4 (`cv2.VideoCapture`)
and asserts the style's observable. Answer **every** surface the behaviour lives on (CLI flag +
page control + status JSON) before saying done.

**The inputs are part of the contract.** Real pairs come from ONE catalogue that the owner owns
(`fixtures/MANIFEST.md`); a harness or benchmark may not invent its own real inputs, and a check
pins the catalogue so it cannot drift. Review benchmark results in batch (one sheet), not one pair
at a time.

## Phase 4 — record (the bookend-out; don't skip)

1. **Memory** — write under the taxonomy (`architecture/ decisions/ patterns/ bugs/ project/`):
   decisions, paths, gotchas, measured numbers. Session narrative goes in the
   `project/wip-<date>-<slug>` leaf stubbed at boot, with its **Traps** section. `mem:core` only
   indexes and states current status (one writer per fact).
2. **DECISIONS.md** — append ONE dated line (Bash heredoc): what changed · sections and checks
   touched · numbers · verification tier · `[tier: …]` · `[revert: …]`. Append-only; supersede with
   a newer line, never edit old ones. **Owner orders are quoted verbatim.**
3. **Handover** — rewrite `NEXT_SESSION_PROMPT.md` (standing order · mission · standing watches ·
   facts · phased plan · gate baseline with known reds · record checklist · harness facts) and
   advance "Next step" in `mem:core`. **Work discovered mid-session goes here, not into this
   session.**
4. **Doc-sync** — a shipped behaviour change that contradicts `HANDOFF.md` gets a dated amendment
   row in its §11 the SAME session (the `82 checks` count, the coverage paragraph §7, a new decision
   row in §6 when a §6 alternative was reopened); a transitions change updates `TRANSITIONS.md`
   §5 (check count and coverage) and §6 (numbers); the plan slice is marked; `conventions/contracts.md`
   gains the new surface. **Volatile counts live ONCE** (Reveal check count → `HANDOFF.md §7`;
   transitions check count → `TRANSITIONS.md §5`; everything else says "as of <date>"). **Resolve
   stale pending-tags** after a ship. Then commit on `main` and `git push origin main` (owner ruling
   2026-09-13: direct to main, no branches) — never with a red gate.
5. **Phase-boundary sweep** (era close only) — 3 parallel tracks: (a) `HANDOFF.md` + plan,
   (b) README + conventions, (c) memories — each armed with SAME-DAY ground-truth anchors. Then
   propose a DECISIONS compaction if the active era is large, and run the harness retrospection
   row ("what should be added to this skill and the hooks?").

*An artifact without a memory + DECISIONS twin is not done; a ruling without a doc-sync is not
done either.*

## Heavy-task escalation (Deep tier only)

`~/.agents/skills/pilot` is the four-mode inquiry engine this skill is distilled from. Escalate for:
a new matching mode or estimator with several viable shapes · a residual-field redesign · a long
external-report critique · anything where you would fan out 3+ tracks or run a multi-lens
adversarial pass. Read its `SKILL.md` + `references/core-disciplines.md`, then the ONE mode file
that matches, and reuse its templates. **Cite it, do not restate it.**
**If `~/.agents/skills/pilot` is missing (fresh clone, other machine, path moved), proceed with
this file alone — everything load-bearing is inlined above.** This skill's Phase 3 and Phase 4
remain the OUTER loop; the engine's gate complements them, never replaces them.

## Anti-patterns
| Don't | Do |
|---|---|
| Start without reading the plan slice and the `HANDOFF.md` section it touches | Read both first |
| Full apparatus on a Quick task / a thin pass on a Deep one | Tier first (0.2), then work |
| Serialize independent research, fan out unbounded, or narrate parallelism you aren't running | Named background tracks in waves of ≤3; narration matches behavior |
| Assume OpenCV / kornia / ffmpeg behaviour | Verify from source or docs (`findTransformECC`'s inverse-map convention cost a bug once) |
| Skip the harness, or report success with a `[XX]` line | Checks alongside the change; fix every failure first |
| Build on an unclassified red baseline | Green (or red snapshotted + classified) before edit 1 |
| Refactor while fixing; split `reveal.py` into modules | Minimal fix + regression check; single file by design |
| Promote "could work" to "done" | Demand runtime evidence (`metrics.json`, a decoded mp4) |
| Claim a real-photo property from a synthetic run | Mark UNVERIFIED until a catalogued pair ran |
| Rank cross-matcher candidates on inlier count | Arbitrate on peripheral SSIM against one mask (decision 23) |
| Put a pixel-similarity term back into the score; mask or clip the residual field | Both are permanently out (decisions 18, 20, 21) — reopen only with a new dated line |
| Empty tool result treated as "nothing there" | Zero-result validation: prove the probe CAN match |
| Present a conclusion no one tried to refute | Falsification gate before presenting |
| Absolute feasibility, estimated counts, "monitor closely" | Conditional scores; counts enumerated; specific fixes |
| A new fresh file each time a doc is iterated | Supersede in place with a dated note |
| An audit session that edits artifacts | Report + sliced fix sessions |
| Re-raising a tracked-backlog item as a discovery | Verify its status and cite the row |
| A silent fallback | Visible INFO line + a named first-fire watch |
| Answering one surface and stopping | CLI flag + page control + status JSON, before "done" |
| A change nobody asked for, riding along with one they did | Every change traces to a request or a recorded decision |
| Changing behaviour with no stated way to undo it | `[revert: …]` in the DECISIONS line, or an explicit owner yes |
| Killing the owner's browser, IDE, or other servers | Kill only the `serve` you started (match its cwd) |
| Executing work you discovered mid-session | It goes into the handover; this session finishes its agenda |
| A new preset or style judged by "looks right" in the strip | A decoded-mp4 observable in `transitions_harness.py` section H (seam monotone, endpoints within codec loss, no black frame) |
| A performance change that alters frames silently | Hash the harness pair's frames before and after; byte-identical, or the DECISIONS line says what moved |
| A model or device (MPS/MLX) added to `transitions.py` without an offline proof and a CPU-equivalence check | Warmup + manifest + refuse-to-download (decisions 24–27) and a harness check comparing device output to the CPU field on a fixture |
| Presenting or saving dev-facing prose without the `no-slop` pass | `.claude/rules/prose.md`: load the skill, run the pass, then save |
