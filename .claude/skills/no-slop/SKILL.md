---
name: no-slop
description: 'Writing gate for AI-written text: chat answers, reports, handoff prompts, decision records, plans, lists and tables, Slack or PR messages, procedures. Use before presenting or saving any prose, when a reader says output is long, dense, cryptic or hard to act on, or when asked to "de-slop", "humanize", "make this readable", "shorten", "summarize", "explain plainly", "put it in a table". Four parts: the contract (decide who reads, in what shape, under what size budget, before drafting), the shapes (seven forms with counted limits), the pass (check your own draft against the shape and the pattern table, then a mechanical count and a cold read by a reader with no context), and detect mode (review someone else''s text: name patterns, quote lines, never an AI-probability score). Optional scripts add a Stop hook and a write gate.'
---

# no-slop — write for the reader you actually have

Slop is text that costs more to read than it carries. It has two forms, and fixing one by leaning
toward the other produces the other.

- **Padding** — recaps, hype, hedges that carry nothing, three bullets that say one thing.
  Reader cost: wading.
- **Compression** — clipped fragments, coined labels ("the seam", "the fold"), referents never
  introduced ("the fix", "round 1"), codes used in place of names ("see D78"), 50-word sentences.
  Reader cost: deciphering.

Both have one cause: the writer holds context the reader lacks and writes in its own working
shorthand. The damage is worst in text written for the next session. A 2026-11-02 audit of 29
handoff, memory and decision files found up to 91 codes used in place of names per file written
for the next model session, and 0 to 5 in the same author's files for humans. (`SKILL-DNA.md`,
next to this file, holds the evidence behind every rule here.) So the gate starts before
drafting: decide the reader, pick the shape, write, check it yourself, then have something other
than your own eyes check it.

One test governs every sentence: **it states one thing the reader needs, plainly, in standard
words.** Get shorter by saying fewer things, never by saying each thing in fewer words. Never read
"be concise" as "be dense".

Four terms used below. The *calling skill* is the skill or prompt that invoked this one, usually
at its *exit gate*, the last step before it presents or saves its result. A *status block* is a
fixed block such a skill puts at the top or bottom of every reply, for example a "where you are"
summary. A *memory file* is a note a session writes for later sessions to read. A *compaction* is
Claude Code summarizing the conversation to free context.

## 1. Contract — decide before you draft

Settle these before the first word. For a chat reply, a Slack post or a PR body, settle them
silently. For a saved markdown file whose frontmatter allows extra keys, record `reader:` and
`shape:`.

- **Reader** — who reads this, and do they hold the session context? For anything saved or sent,
  the answer is no. The next model session is a cold reader; write for the human who will start
  that session with your text.
- **Shape** — one of the seven in section 2.
- **Channel and budget** — where the text lands and the size target, in that channel's unit.
  A relative cut ("make it half") is not a budget.
- **Action** — what the reader must do after reading. If nothing, the text gets shorter.

Defaults, so the reader never has to ask:

- the answer in the first line, and the current state before the detail;
- plain words, every item named in words, numbers instead of adjectives;
- whether a path, id or session code appears is decided by the reader's need to act on it; one
  that appears is complete and verbatim.

**Re-ask rule.** When the reader asks again — "explain", "shorter", "plainer", "what do you
mean" — they have lost the session. Restart from this contract with reader = cold: fewer claims,
and every referent that stays is introduced by its full name.

## 2. Shapes

| Shape | Reader | First line | Hard limits |
|---|---|---|---|
| **Reply** | the person in the session | the answer, verdict or number | three to four claims and at most 150 words before any detail; detail goes below a line or into the saved file; no closer — a closer is a recap, a thank-you or an offer menu; a concrete next action is not one |
| **Report** | a cold reader, later, maybe one section from a link | the status block, if the calling skill has one, then a summary: verdict · actions asked · open questions | the summary at most 200 words; 2 heading levels; each heading readable alone; glossary before the body when a term is coined; evidence in an appendix; a design bound for review also passes the five tests in `references/shapes.md` |
| **Handoff** | the next session AND the person who pastes it | Goal, then the first step within 15 lines | at most 80 non-empty lines; every fact marked *verified* or *assumed*; traps as a table; a glossary that leaves no term undefined |
| **Decision record** | a future reader checking what holds | the decision, with who decided and when | at most 8 lines: decision · why · rejected option · what reverses it · status |
| **Sibling items** | anyone scanning a list, table, plan, findings or options | — | one grammatical template for every item, and the first two words differ where the template allows (imperatives differ at the verb or the object); a detail present in one item is present in all; at most 5 unranked; 3 or more items sharing 2 or more attributes become a table |
| **Message** | cold, in Slack, GitHub or email, with a cap | the result | the channel's cap, which the calling skill states (Slack 3,000 characters; a PR review summary 400 words); every referent introduced; no code in place of a name, because this reader has no legend |
| **Procedure** | someone acting alone, or a machine | step 1 | the controlled register of ASD-STE100 (the aerospace industry's simplified technical English): one instruction per sentence, at most 20 words, imperative, numbered from 3 steps, no phrasal verbs; never applied to rationale or analysis |

Templates, limits and the test for each shape: `references/shapes.md`, next to this file. A size
budget is a stop condition, not an instruction to compress: when the budget is reached, move
claims below the line or into the file; never shorten sentences to fit. A plan is sibling items
(the steps, each with its outcome). In a saved document, 4 or more parts of a system or an
argument that relate to each other become a diagram; in a chat reply, offer one. When the calling skill fixes its own
template, that template wins on order and the shape rules apply inside each section.

## 3. Words — the pattern table

Fix classes, not words. A banned word list lowers only the listed words, and unlisted filler
rises in their place. These twelve rows cover most of what was measured; the full table with sources is
`references/patterns.md`.

| Pattern | Smell | Fix |
|---|---|---|
| Code in place of a name | "see D78", "per R7 and Q-E1", "rows 18 and 13" | The name in words; the code may follow in parentheses |
| Unintroduced referent | "the fix", "round 1", "the twin"; a person or bot named with no role | The full name once, with the role; the short name after |
| Coined or borrowed jargon | "the seam", "load-bearing", "gated on", "wired up", "the unlock" | The standard term, repeated; the literal relation ("depends on") |
| Inanimate actor, animate verb | "this asymmetry bites", "the check forgot its sibling" | Name the actor, or use a plain verb |
| Noun stack, noun as verb | "absolute dotfile backup path handling", "footnote it" | Break at three nouns and name the relation; a normal verb phrase |
| Late verb, long sentence | the subject, fifteen words of modifiers, then the verb; any sentence over 40 words | Subject and verb in the first eight words; split at the facts, not the commas |
| Negative parallelism | "It's not X — it's Y.", "Not a bug. A design flaw." | State Y |
| Colon reveal, kicker | "The best part: it learns."; a sentence that sounds like a pull-quote | A plain sentence saying which thing did what |
| False agency | "the decision emerged", "the data tells us" | Name the actor: "I ran the tests; they passed" |
| Throat-clearing, reasoning leak | "Here's the thing:", "Looking at…", "I want to be precise about my role…" | Start at the content |
| Counting, puffery | "for two reasons", "three things matter", "crucially" | List them; show the consequence or cut the adverb |
| Tie-back, recap, offer menu | "So, to answer your question…", a recap per section, "Hope this helps, let me know…" | Delete; end when the answer ends |

The single best heuristic is to find the sentence you are most pleased with. It is the one most
likely to be a phrase standing in for a thought. Rewrite it plainly.

**Vocabulary ledger.** A coined term is a label you made up for a thing: not a code identifier,
not a file name, not a term the field already uses. Keep the ones you coin in a scratch note, not in your head. In a
deliverable, define each at first use or replace it. In a durable file — a handoff, a memory, a
decision log, a plan — no term stays undefined; the glossary carries them, because every later
session reads an undefined term as standard.

## 4. Claims

- A claim is one statement the reader can check. Keep the claims that change what the reader
  decides, within the shape's budget. A debugging answer that needs eight items ranks them or
  splits them into "now" and "later". Evidence and query logs go to an appendix, with one line
  saying they are there.
- Report what changed, not how you got there.
- Never buy brevity with silence: a risk, a failure, a skipped step, a thing you did not do, and
  any change made outside the repo (a production prompt, a setting, a bot) always make the cut.
- Number, not adjective. Source or silence. Date the perishable ("as of 2026-11-02"). Keep a hedge
  that carries uncertainty; delete one that carries nothing. List only alternatives you weighed.
- State the simplest version that would work before the one you built. If you did not consider
  it, say so.

## 5. Formatting

Headings, tables and bold are fine when the parts are real. Decoration is emoji headers,
bold-first bullets that restate the bold, a header per two sentences, unicode arrows as logic.
If the prose reads without the scaffolding, remove the scaffolding, not the prose.

## The pass

Style rules decay while you generate; a separate pass holds. After drafting, before presenting or
saving:

1. **Contract check.** The first line is what the shape prescribes (the answer, the status block,
   the goal, step 1). The last line is the next action or the block the calling skill requires.
   If the reader is cold, nothing assumes they saw the session.
2. **Shape check.** The order and the limits of the chosen shape (section 2). A handoff whose
   first step appears on line 33 fails here.
3. **Pattern scan.** Each row of the table: quote yourself, then fix. Read one paragraph aloud in
   your head; a sentence you decode twice is compression — expand it to subject, verb, object.
4. **Claims sweep.** Every number has a source, every perishable has a date, nothing is silenced.
5. **Count.** Run `python3 -I scripts/slop-check.py <file>` when the scripts sit next to this file
   (`--profile message` adds the channel cap, `--profile handoff` the handoff sections). Otherwise
   count by hand. No sentence over 40 words. No two sentences anywhere in the text that open with a negation. No "should
   work" without evidence in the sentence. No filler opener or sign-off. No code in place of a
   name in prose. Under the channel cap.
6. **Cold read.** For a report, a handoff, a design, a KB article, or any text the calling skill
   marks as leaving the session: give the text alone to a reader with no session context (an
   Agent subagent, or `claude -p`). Ask: in one sentence, what is decided or asked of you? What
   would you do first? Which terms, codes or names could you not resolve from the text alone?
   Which sentences did you read twice? Fix everything the reader could not resolve or had to
   re-read. A routine Slack post or PR body skips this step unless the caller asks. Without a
   subagent tool, say so once in the deliverable.
7. **Protected blocks.** These stay in place, in order and with their labels: identifiers,
   numbers, links, data tables, and the calling skill's evidence labels (tags such as
   `[CODE path]` or `[ASSUMPTION]` that say how a claim was verified). So does any block the
   calling skill declares fixed. A sentence inside such a block may still be fixed.

**Detect mode** — reviewing someone else's text (a KB submission, a PR body, a design): name each
pattern found, quote the line, give the one-line fix. Never rewrite wholesale unless asked. Never
output an "AI-written probability": a named pattern can be checked, a score cannot.

## Guard, re-anchoring, integration

**Guard.** Two Claude Code hooks, installed at user scope by the setup wizards (`/ecom-setup` on
team machines, `harness-setup` on personal ones) or by hand with
`scripts/install-guard.sh on --scope user`; `off --scope user` removes them. The Stop hook runs
the checker on every reply and blocks it once when a hard check fails or the reply's top layer
passes 250 words (looser than the 150-word writing budget, so one long reply passes and a wall
does not). The write gate (a PreToolUse hook on Write and Edit) denies a handoff, memory, decision
or plan file with the same faults, at most twice per file per session. Both hooks fail open when
python3 or the script is missing. The hard checks and their thresholds: `scripts/README.md`. The
skill works without the scripts; a runtime that loads only this file has no guard.

**Re-anchoring.** In a long session, re-read sections 1 and 2 before any deliverable that follows
a compaction and before writing a handoff. Prefer a new session between tasks over compacting
through them, and write the handoff in the handoff shape.

**Integration.** What a calling skill declares (protected blocks, cap, artifacts that leave the
session) and how the copies of this skill in other repos are kept in sync:
`references/integration.md`.
