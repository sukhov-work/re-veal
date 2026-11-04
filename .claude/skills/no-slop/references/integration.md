# Integration — how a calling skill uses no-slop

A calling skill is the skill or prompt that invokes no-slop, usually at its exit gate. This file
says what it declares, what it must never lose, and how copies of the skill stay in sync. The
skill's own text is `SKILL.md`; it works alone, so a runtime that can load only one file loads
that one.

## What a calling skill declares

| Declaration | Why | Example |
|---|---|---|
| Its protected blocks, by name | the pass keeps them in place, in order, with their labels | the "Where you are" block and the Resources & tool health section of ecom-pilot; the follow-up line of the prod-e on-call reply; the nine fixed sections of the weekly production report |
| Its channel cap, in the channel's unit | the Message shape counts against it | Slack digest 3,000 characters; on-call reply 2,500 (1,200 for a storm or repeat alert); PR review summary 400 words; weekly report 36,000 bytes and 400 lines |
| Which artifacts leave the session | pass step 6 (the cold read) runs on those | a saved report, a handoff, a KB article, a design; not a routine chat reply |
| Which shape each artifact takes | the shape sets order and limits | handoff → Handoff; decision log entry → Decision record; findings → Sibling items; PR body → Message with the parts listed in `shapes.md` |

## How to invoke

- Interactive Claude Code with the skill installed: call the `no-slop` skill at the exit gate, on
  the deliverable and on the final reply.
- A runtime that loads only `SKILL.md` as text (the prod-e on-call responder, a Kyber session
  whose KB clone failed and that read the file over GITHUBBOT, the claude.ai account skill): apply
  sections 1 to 5 and pass steps 1 to 4 and the hand count of step 5. There is no checker and no
  cold read; the deliverable says so once. A Kyber session with its KB clone at `/tmp/kb` runs the
  checker (`investigate-kyber/references/pr-review-style.md`, the pass).
- A headless run that can execute python (the weekly report on the coderplex box): run
  `python3 -I scripts/slop-check.py <report> --profile file` after the byte-budget script and
  before publishing; treat exit 1 as a failed gate.
- A skill that writes handoffs, memories, decision logs or plans: apply the Handoff, Decision or
  Sibling-items shape and the vocabulary ledger. With the guard installed, the write gate enforces
  the counts on those paths.
- KB publishing: the author runs detect mode on the article before opening the PR.

## What the pass must never cut

Consumers wrote this list independently (the qa-v1 vendored header, the epistemic-filter dev
skill, the weekly report's publish gate); it is the same list every time.

- Evidence labels and verification tags before claims.
- Full verbatim identifiers: a shortened GUID is a defect, not concision.
- Case tables, findings tables, feature-toggle matrices, data tables.
- The appendix of every query attempted, including empties and failures.
- The "not covered, and why" list and known issues.
- Real hedges and confidence numbers.
- Any change made outside the repo during the session.

## Copies and how they re-sync

| Copy | Mechanism | On each version |
|---|---|---|
| `skills/qa-v1/references/no-slop.md` | the body of `SKILL.md` verbatim under a qa-v1 header that pins the version | replace the body, bump the header |
| the owner's personal `cc-skills/skills/no-slop/` | the directory copied with `PROVENANCE.md` | copy the directory, keep the provenance file |
| the prod-e on-call pilot (`ecom-oncall-pilot.md` §8) | a paraphrase of the Message shape and the word rules | re-paraphrase from the Message shape |
| the claude.ai account skill | `SKILL.md` uploaded by hand | re-upload |
| the AICM `ecom-platform` plugin | directory mirrored from the KB by the distributor | nothing to do; confirm the mirror after the sync PR |

`SKILL-DNA.md` records every version and the decisions behind it.
