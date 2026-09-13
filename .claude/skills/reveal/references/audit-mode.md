# Audit mode — whole-repo / whole-corpus review

WHEN: the owner orders a comprehensive review; a phase/era boundary closes; the cadence below
fires; or a Review-type request exceeds single-artifact scope. TIER: Deep by default; Standard for a
single-track re-run. Owner-supplied scope and quality gates are BINDING and override the default
track list. **The audit session is READ-ONLY on artifacts, config and docs: it produces a report;
fixes are separate sessions sliced from that report.** No rewrite proposal without a named
incremental seam.

TRACKS (independent → parallel finder-agent launches; each gets exactly ONE checklist):

  A  Alignment correctness (geometry, invariants 3–5, arbitration, residual field) → references/checklists/alignment.md (not yet authored)
  B  Runtime + operator surface (HTTP, 127.0.0.1 bind, offline contract, setup/run, optional layers) → references/checklists/runtime.md (not yet authored)
  C  Harness + fixture integrity (ground truth, checks can fail, fixture catalogue, benchmark sheet) → references/checklists/harness-data.md (not yet authored)
  D  Docs + memory + config consistency → references/checklists/docs.md
  E  Mechanical hygiene (MAIN AGENT, FIRST — tool output outranks model reasoning):
     `.venv/bin/python -m py_compile reveal.py harness.py` · `.venv/bin/python harness.py` · `.venv/bin/python reveal.py check` + dead-code/dep/duplication probes + size/inventory baselines.
     PROBE availability before trusting a clean result; classify a failed probe, never skip it
     silently.
  F  **Harness** — audit the operating environment like any other subject. Its whole yield in one project's second audit was three real
     defects: the boot hook's read instruction defeated by the file's own size, a verification
     recipe that existed nowhere runnable, and a marker race. Check: the boot path actually
     reaches what it names (reproduce it on THIS session's boot) · every recipe a session re-runs
     exists as a script + one page, not prose in three memories · hook and marker lifecycles
     (written by whom, read by whom, deleted by whom) · store sizes against their caps · every
     `references/<x>.md` and `mem:<name>` pointer resolves · the permission allow-list still
     covers what the loop actually does.
     Until the project authors `checklists/harness.md`, Track F runs on items 1–6 and 9–12 of
     `references/checklists/docs.md`, which are already harness assertions.

WORKFLOW
  0. Intent gate: load owner scope/gates; pick the **baseline anchor** (the previous audit's
     DECISIONS entry; whole-corpus on the first run). Record `[type: Audit]` in the DECISIONS line
     you will write at the end — do not open with a ritual declaration sentence.
  1. Run Track E. Classify every failure `my-change` / `pre-existing` / `flaky` (re-run ×2) /
     `infra` BEFORE reading anything. The gates' state is the report's baseline block.
  2. **Re-mine first.** Walk DECISIONS (and any §Traps section) since the baseline anchor for
     failure classes not yet in the checklists; append them, dated, BEFORE launching tracks.
     A checklist that never grows only catches the last audit's bugs.
  3. Launch track agents (`references/review-agent.md`) as named background tracks in **waves of at
     most 3**, each with the shared context block, its checklist, and the baseline anchor.
     Four at once has been killed by a usage limit before any track reported; the two-wave re-run
     lost nothing (46 findings, 0 deleted). Long agent reports go to scratchpad files, never inline.
  4. **VERIFICATION PASS (main agent, mandatory):** re-read the cited artifact for every
     candidate finding. *A finding that does not reproduce is DELETED, not downgraded.*
     Zero-result validation on every absence claim.
  5. Falsification gate (SKILL.md Phase 3) on the aggregate verdict; one refutation attempt per
     major finding.
  6. Emit the report (skeleton below) into `.claude/claude-docs/audits/audit-<scope>-<date>.md`. Every finding
     carries: severity · confidence · anchor (`file:line` or doc§) · the violated
     convention/ruling · a SPECIFIC fix (files/commands — never "monitor closely") · verification tier.
  7. Backlog check: a finding matching a `references/tracked-backlog.md` row is reported as
     STATUS VERIFICATION against that row, never as a discovery.
  8. Phase-4 recording. The audit session's diff touches only the report and this skill's files —
     **an artifact diff in an audit session is itself a Track-D FAIL.**

SEVERITY
  BLOCKER  silently wrong results, data corruption, invariant violation, privacy/secret exposure,
           append-only ledger violation. e.g. a network call outside warmup; an original overwritten; a check that cannot fail shipped green.
  MAJOR    resilience/contract gap that will bite under real conditions: missing or silent degrade
           path, unbounded work, contract break, a standing gate weakened or bypassed. e.g. a fallback that engages without an INFO line; a guard widened in place; a strict-profile constant changed for loose-mode feedback.
  MINOR    drift that misleads but produces no wrong result yet: convention/DRY drift, doc/config
           drift, stale sample or pending-tag, dead code.
  NIT      naming, wording, formatting.

FALSE-POSITIVE RATCHET: if >20% of a run's findings are disproved in verification, tighten the
offending checklist items (dated edit) before the next run. The ratchet cuts both ways — step 2
grows the checklists from the same evidence stream.

CADENCE (burst-triggered, no idle timers): Track D alone at every phase boundary and after any
≥3-session ship burst; Tracks D+F after **any unattended window** — a 10.7-day unattended run in
one project hid three silent degradations that only an audit surfaced; ALL tracks before each new
phase and after any platform/environment migration; Track E's gates already ride every session's
Phase 3.

REPORT SKELETON (one file per run; every cell honest — "unmeasured" is a valid value, adjectives
are not; findings sorted severity-first; ID = `<track><n>`, e.g. `A1`, `F3`):

```
# Audit — <scope> — <date> — baseline <DECISIONS anchor>

## Verdict
<≤3 sentences: worst finding, overall state, fitness for the next phase>
<one scope line against the permanently-out list — did anything cross it?>

## Gates baseline
<Track E output, with each red classified my-change / pre-existing / flaky / infra>

## Findings
| ID | Track | Severity | Conf | Anchor | Finding | Specific fix | Violated ruling | Tier |

## Verified clean
<tracks/checks that PASSED, each naming the probe that proved it — never "looks fine">

## Pre-existing / out-of-scope
<classified, each with its backlog row or a proposed new row>

## Backlog status changes
<tracked-backlog rows whose state moved, with evidence>

## Proposed checklist / convention amendments
<the re-mine harvest: dated items to append before the next run>

## Fix-session slicing
<ordered; each slice sized S/M/L with its dependencies and the gate that closes it>
```

LAWS: `references/laws.md` maps engineering laws onto this machinery — which checklist item
encodes which law, and which laws are deliberately skipped. Read it before authoring new items.
