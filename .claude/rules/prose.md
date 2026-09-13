# Prose gate — every dev-facing text passes `/no-slop` before it is saved or shown

Owner order (verbatim, 2026-09-13): "make sure to create a rule to start using /no-slop skill to
sanitize all dev facing output incluing this session's artifacts".

Rule: before presenting or saving any prose a developer will read, load the `no-slop` skill
(`Skill` tool, name `no-slop`) and run its **pass** on the draft. This applies to the final message
of a turn, `DECISIONS.md` lines (before appending; lines are never edited afterwards),
`NEXT_SESSION_PROMPT.md`, the design docs under `.claude/claude-docs/`, `EXPLORATION_PLAN.md` rows,
`tracked-backlog.md` rows, conventions, memory leaves, audit reports, and commit messages.
Code comments and docstrings follow the same plain-statement rule but are not re-run through the
skill. Run **detect** mode on inherited text (a research artifact, an external report) when you
review it, and name the patterns in the review.

What the pass checks, in this repo's terms: the first sentence is the result; every claim carries a
number or a source or is marked UNVERIFIED; no coined names for things that have a standard name
(say "harness check", not "the gate", unless `AGENTS.md` defines the term); a referent is
introduced by its full name before it is shortened; lists stop at five items; a risk, a failure or
a skipped step is never cut for brevity. The skill's pattern table is the checklist; do not keep a
private banned-word list.

Skipping the pass is a finding in the next audit (Track E, mechanical hygiene).
