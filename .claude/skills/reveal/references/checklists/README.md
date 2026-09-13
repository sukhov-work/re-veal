# Checklist authoring contract

One file per audit track. A checklist item is a **testable assertion with a runnable probe and a
citation** — not a topic, not a reminder.

## Item format (mandatory, all three parts)
```
N. <ASSERTION — one sentence, stated as the property that must HOLD, present tense>
   — check: <the exact probe: a grep, a command, a tool call, or "read X and diff against Y">
   — anchor: <doc§ or dated ruling that makes this normative>
```
- **Assertion**, not a question. "Every fallback logs when it engages", not "check fallbacks".
- **check** must be runnable by an agent with read-only tools and must be able to FAIL. If you
  cannot write the probe, the item is not ready — it is a research task, not a checklist item.
- **anchor** must point at something normative that already exists (a convention section, a dated
  DECISIONS ruling, a plan DoD). An item with no anchor is an opinion; write the ruling first.
- Each file opens with a TOC of item numbers → short names, and a dated provenance line saying
  which items were authored when and which were **DECISIONS-mined** additions.

## Growth rule (the ratchet)
- Every audit run RE-MINES the decision log since the baseline anchor for failure classes not yet
  covered, and appends them as dated items **before** the tracks launch.
- Every run that disproves >20% of its findings TIGHTENS the offending items (dated edit).
- A trap that can be converted into a permanent automated check should become one; the checklist
  item then verifies the check still exists and still bites.

## Laws encoding rule
`references/laws.md` maps engineering laws (Hyrum, Gall, leaky abstractions, Goodhart, Kernighan,
Pesticide Paradox, Zawinski, Postel, Broken Windows, Lehman, Knuth, Hofstadter, Gilb, Technical
Debt, Murphy, Boy Scout, …) to the item numbers that encode them, and carries a **Not applicable
(skip, with reasons)** block so a skipped law is a recorded decision rather than an oversight. Its
header holds the encoding contract — read `laws.md` before authoring new items.

## Track shape (adapt the names to the project; keep the count)
A = core correctness · B = runtime/platform/ops · C = data/tests/integrity · D = docs + memory +
config consistency (D also owns the audit-commit purity rule) · **F = harness** (the operating
environment itself: boot path, recipe runnability, hook and marker lifecycles, store sizes,
pointer resolution). Track E is mechanical tool output, run by the main agent first — it is not a
checklist.

A new project ships **only** `docs.md`, seeded. A–C and F are harvested at the first audit from
the DECISIONS the project has actually accumulated; checklists designed before the project has any
failure history invite decorative items — both source projects authored theirs about four weeks in.
Until `harness.md` exists, Track F borrows the harness assertions already in `docs.md`.
