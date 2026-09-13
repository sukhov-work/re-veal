# SKILL-DNA — no-slop

Non-functional documentation: provenance, versions, and locked design decisions for the
`no-slop` skill. Never load this file as instructions during a run.

## Provenance

| Field | Value |
|---|---|
| Created | 2026-08-25, KB v2 program session 2 (decision D19 in the program's DECISIONS.md) |
| Commissioned by | KB owner — "compact metaskill to stop AI slop in reports, designs and responses" |
| Authored by | claude-fable-5 (effort max), operating the investigate-design-v3 engine; skill text hand-authored by the main agent, not delegated |
| Research | dedicated agent pass, 2026-08-25: hardikpandya/stop-slop (full SKILL.md + references), ayghri/i-have-adhd (10-rule set + eval rubric), tropes.fyi (49-trope catalog), Wikipedia Signs-of-AI-writing, HN 49296740 ("Why does Opus 5 feel worse", 869 comments), anthropics/claude-code#77136 (473 reactions, incl. the 183-transcript whack-a-mole measurement), petergyang/no-ai-slop, blader/humanizer, Kobak et al. / Juzek & Ward lexical-tells studies |
| Reviewed | KB owner; merged as ecom-grill-agent-kb PR #436, 2026-08-26 |
| Distribution | master here; planned to ship in the CAP `ecom-platform` plugin alongside `ecom-pilot` (whose exit-gate step 6 invokes this skill's pass) |

## Version record

- **v1.0 (2026-08-25, PR #436)** — initial release: single-file skill, ~105 lines. Order
  rules, claim budget, 10-row pattern table, epistemic floor, formatting rules, the pass
  (rewrite mode) + detect mode, integration hooks.

## Locked design decisions

1. **Both slop directions are in scope** — padding slop (2024-era filler) AND compression
   slop (2026-era coined-jargon density). Sources targeting only the former (stop-slop)
   actively push toward the latter; the skill's core test ("say fewer things, never say each
   thing in fewer words") exists to hold the line between them.
2. **Fix pattern classes, not word lists.** Measured basis (claude-code#77136, 183
   transcripts / 1.46M words): banned named terms drop ~21% but unnamed rhetorical
   scaffolding rises ~7% — blocklists re-form the register. The pattern table names the
   class and the rewrite, not the vocabulary.
3. **A dedicated rewrite pass, not inline rules alone.** Style instructions decay during
   generation (multiple independent reports); a separate pass holds. "The pass" is therefore
   the skill's operative unit, wired into exit gates of report-producing skills.
4. **Epistemic floor is first-class.** For technical reports the highest-damage slop is
   epistemic (fabricated precision, unsourced claims, silenced risks), which prose-oriented
   anti-slop skills omit entirely. Numbers-over-adjectives, source-or-silence, dated
   perishables, keep-real-hedges.
5. **Detect mode names patterns with quotes and never outputs an AI-probability score** —
   named patterns are checkable evidence; scores are guesses.
6. **Never instruct "be concise."** Models resolve it as "dense and cryptic" — the exact
   failure the skill exists to prevent. Budget claims, not words.
7. **Single file, no references/ tree.** A metaskill loaded by other skills' exit gates must
   be cheap; stop-slop's three-layer repetition was the counterexample.
