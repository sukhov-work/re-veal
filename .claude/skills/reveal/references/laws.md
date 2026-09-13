# Laws of software engineering — encoded checks (template)

A law is only "applied" if a check or practice encodes it. A table row with no encoding is
decoration. Fill the **Encoding** column with the checklist item numbers or practices in THIS
project that encode the law; move a law to the skip block, with a reason, when it does not apply.
Read this before authoring new checklist items so the encoding stays deliberate, and add the
encoding cell in the same commit as the item. Lineage: epistemic-filter audit plan §9 (2026-08-01)
→ frame-the-world `references/laws.md` (2026-08-13); the universal rows below are the ones both
projects encoded.

| Law | What it predicts | Encoding (fill per project) |
|---|---|---|
| **Hyrum's** | every observable behavior gets depended on | an inventory of implicit public contracts (URL grammars, persisted keys, file layouts, schemas) — `conventions/contracts.md`; parsers tolerant both ways |
| **Gall's** | working complex systems grow from working simple ones | audit mode is read-only + fix-slicing; any rewrite proposal names its strangler seam |
| **Leaky abstractions** | the layer below leaks into the layer above | the project's dominant trap class gets a `§Traps` line + a checklist item + (where cheap) a test |
| **Tesler's** | complexity is conserved | irreducible cost lives in workers, offline steps, or budgets — the interactive path stays light |
| **Unintended consequences** | every change has effects outside its intent | the mandatory verification pass + golden gates + the regression roster riding every session |
| **Zawinski's** | programs expand until they read mail | a named permanently-out list; every audit verdict carries a scope line |
| **Bus factor = 1** | one person holds the context | the persistence loop (DECISIONS + memory graph + handover) + the audit engine INLINED in-repo, no external dependency |
| **Knuth** | premature optimization | every perf change cites its measurement; one sanctioned perf lever |
| **Parkinson's** | work expands to fill time | audit cadence is burst/boundary-triggered, no idle timers |
| **Ninety-ninety** | the last 10% takes 90% | fix slices sized S/M/L honestly; convergence-class work called out as open-ended |
| **Hofstadter's** | it always takes longer | estimates labeled as estimates; measured beats estimated in every cell ("unmeasured" is a valid value) |
| **Goodhart's** | a measure that becomes a target stops measuring | verification tiers (a green gate ≠ the real surface); never a single-metric verdict |
| **Gilb's** | quantify | report template requires numbers per finding; adjectives are not values |
| **Boy Scout** | leave it better | bounded to non-frozen surfaces via audit slices — never drive-by refactors while fixing |
| **Murphy's** | whatever can fail will | every fallback warns when it engages; a success-shaped failure is a first-class test case |
| **Postel's** | liberal in, strict out | tolerant ingest of external data + validated, minimal emit |
| **Broken windows** | small drift invites large drift | mechanical hygiene (Track E) triaged first; suppressions are dated temporary states with a baseline count that must not grow |
| **Technical debt** | unpaid debt compounds | `references/tracked-backlog.md` — one dated registry; audits verify rows, never re-discover |
| **Kernighan's** | debugging is twice as hard as writing | the review agent's "prefer boring" lens; cleverness in the hot loop needs a stated reason |
| **Pesticide paradox** | tests stop finding new bugs | every audit starts by re-mining DECISIONS since the baseline into new checklist items; testable traps become tests |
| **Lehman's evolution** | systems must adapt or decay | every external dependency carries a dated currency note + refresh path |
| **Lindy** | what has lasted tends to last | design lens only — boring-tech bets are deliberate; cite when evaluating new dependencies |
| **Sturgeon's** | 90% of everything is crud | defend at ingest; new data sources get the same posture |
| **Map ≠ territory / confirmation bias** | the model is not the thing | verification tiers, evidence discipline, zero-result validation, the falsification pass |

**Not applicable (skip, with reasons) — Reveal, 2026-09-13.** Solo project, single process, one machine: Conway / Brooks / Dunbar / Ringelmann / Price / Putt / Peter skipped (no team; parallel review agents are a synthetic partial substitute, noted, not claimed equivalent); CAP + the fallacies of distributed computing skipped (one local process, one thread pool); Amdahl / Gustafson / Metcalfe / Moore skipped (no scaling target — the whole pipeline runs in seconds on one laptop); Second-system effect watch-flag only (Gall encoding guards it). Encoding column: `docs.md` items 1–12 encode Hyrum (contracts.md seed), Broken windows (Track E first), Technical debt (tracked-backlog), Murphy (item 12), Map ≠ territory (items 2, 11); the rest are filled when checklists A–C are authored at the first audit.

**Universal rows above, typical for a solo project:** Typical for a solo project: Conway /
Brooks / Dunbar / Ringelmann / Price / Putt / Peter (no team — parallel review agents are a
synthetic partial substitute for many eyeballs, noted, not claimed equivalent); CAP + the fallacies
of distributed computing (unless the project is distributed); Amdahl / Gustafson / Metcalfe /
Moore-class scale laws (no scaling target); Second-system effect (guarded by the Gall encoding —
watch-flag only).
