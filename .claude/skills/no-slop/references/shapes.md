# Shapes — the seven forms a deliverable can take

A shape is the fixed order and the limits of one kind of text. You pick the shape in the contract
step of `SKILL.md`, before you draft. Every shape below lists the reader it is for, what its first
line holds, which parts are fixed, what its limits are, and the test you run before you present it.
The limits are counts you can check, not adjectives.

Two rules apply to every shape:

- **Name things in words.** A work item, a decision, a person or a document is introduced by its
  name in words the first time it appears. A code (`D78`, `T7.20`, `§7.1.2`, `row 18`) may follow
  the name in parentheses. It never stands alone in prose. In the 2026-11-02 audit of 29 handoff,
  memory and decision files, the files written for the next model session carried up to 91 bare
  codes each; the same author's files for humans carried 0 to 5.
- **A pointer says what the reader will find there.** "See the storm check (design §1b: the two
  pre-checks that stop a repeat alert)" passes. "See §1b" fails.

## 1. Reply — a chat answer to the person you are working with

Reader: the person in the session. They saw the task but not your tool output.
First line: the answer, the verdict or the number. Nothing before it.
Fixed parts: answer · what changed or what you found (claims that change a decision) · the one next
action, if the task has one · any block the calling skill requires (for example the "Where you are"
block of ecom-pilot), unchanged.
Limits: three to four claims unless the person asked for more; at most 150 words before any
detail, and the detail goes below a `--- detail ---` line or into the saved file; no sentence
over 40 words; a list has at most five items, ranked; no closer, recap or offer menu.
Test: read only the first and the last line. The reader must know what happened and what to do.

## 2. Report — a saved document someone reads later, cold

Reader: a colleague or reviewer who did not attend the session and may read one section from a link.
First page: the status block the calling skill requires (if any) · summary (verdict, the actions
asked of the reader, the open questions) · requirements or the question the report answers.
Fixed parts: summary first · body · evidence appendix (queries, logs, tables of raw data) ·
resources and tool health last. Problem before design; requirements before options.
Limits: the summary at most 200 words; two heading levels; a third level (`7.1.2`) is a sign that the section should be a table
or a list, and section numbers appear only where the calling skill's template fixes them for
interop. Every heading reads alone, so a reader who lands on it from a link knows what they will
learn: "Why the bare mirror is the durable unit" passes, "Considerations" fails, and a heading may
be a sentence. Every enumerable item (a decision, a question, a risk, a finding, an alternative)
gets a short name in words at its first mention. The prose refers to it by that name, linked to
its heading when the document is long. A code appears only as the sort key in the first column
of a table, with the name in the second column. A cross-reference carries the name and the
destination ("see *the worktree-churn risk* (Risks)", or a link to the heading), never a bare
number or code. Each referent is introduced once, in full; after that the short name is fine.
Tickets, PR numbers, toggle names and decision ids are identifiers, not codes: they appear in
full next to the name, never instead of it. A glossary stands before the body when the report
coins a term or uses one the reader's team may not share. Three or more items that share two or
more attributes become a table.

### Reports that go to a design review: five tests

A report that a reviewer reads before a design review passes these five tests as well. Origin:
the first outside review of a flagship design (2026-09-15) failed all five while every fact in
it held; the reviewer opened with "where are the product requirements?" and "it uses
terminologies I never heard of".

- **First-page test.** The header, the first section and the requirements, read alone, tell the
  reviewer the problem, the proposal and what is asked of them. Requirements come before the
  design. Fact tables, research inventories and evidence come after it, in their own section
  before the appendices.
- **Vocabulary test.** Every coined term and every domain term the reader's team may not share
  is defined in a glossary placed before the design and introduced inline at first use. A
  family of codes (decisions, risks, findings) gets a one-line legend. A reader from a
  neighbouring team reads the first two sections without meeting an undefined term.
- **Agenda test.** Each question the review must settle carries why it exists, what is
  suggested, the alternatives with their trade-offs, and who decides, in the order the review
  will discuss them. A list of questions without alternatives is a list of open items, not an
  agenda.
- **Diagram test** (a full design, at the calling skill's deepest effort level). One component
  diagram marks the new, changed and unchanged parts and sits on the first page. One sequence
  diagram per main scenario sits next to the prose it explains. Both are Mermaid, validated
  before saving.
- **Published-copy test.** A copy that leaves the working folder (a knowledge base, a shared
  repository, a PR) references no file by path that its reader cannot open: local research
  notes, scratch files, prior drafts. Embed it, publish it alongside, or omit it. Inputs are
  links, never bare document ids.

Test: open the document at three random headings and read only that section. If any of the three
needs the rest of the document, rewrite it. Then the first-page test above; for a report bound
for a design review, all five.

## 3. Handoff — the prompt or file the next session starts from

Reader: two at once. A fresh model session with no memory of this one, and the person who pastes
it and must judge whether it is right. Write for the person; the model will cope.
Fixed order, with these headings or their plain equivalents:
1. **Goal** — one sentence: what the work is for and what "done" looks like.
2. **First step** — the one concrete thing to do first, within the first 15 lines of the file.
3. **State** — facts the next session can rely on, each dated and marked *verified* (you saw it)
   or *assumed* (you believe it). Nothing the next session must "re-derive".
4. **Decisions that bind** — each one named in words, one line of substance, and where it is
   recorded. A decision the reader cannot act on without opening another file is not recorded here.
5. **Open items** — each states the question and why it still matters. An item that cannot say
   why is dropped.
6. **Traps** — a table: symptom · cause · what to do. One row per trap; no prose list.
7. **Glossary** — every coined term, nickname, bot name, person (with role) and code family used
   above. The reader must meet no undefined term in the first 40 lines.
8. **Pointers** — each path or link with one clause on what the reader will find there.
Limits: the paste block has at most 80 non-empty lines; everything longer moves to a linked report.
One current state and one next step per file. No "carried from session N" item without its
question. No placeholder left unfilled.
Test: a competent engineer who did not attend the session reads it once and can start work without
asking a question. Then the contradiction check: the State section and the First step agree.

## 4. Decision record — one entry in a decision log

Reader: a future session or colleague checking what was decided and whether it still holds.
Fixed parts, in this order, each one line unless stated: **Decision** (present tense, names who
decided and the date) · **Why** (at most two sentences) · **Rejected** (the option not taken and
the one reason) · **Reverses if** (the condition that would reopen it) · **Status** (verified ·
assumed · proposed).
Limits: at most eight lines; no narrative of how the decision was reached; no bare code as the
name — `D81 — the guard is opt-in` is a name, `D81` alone is not.
Test: a reader who sees only this entry can act on it and knows what would change it.

## 5. Sibling items — a list, a table, a set of findings, options or plan steps

Reader: anyone scanning. Readers see about the first two words of each item (Nielsen 2009) and
read the second item faster when its structure matches the first (Frazier 1984, Sturt 2010).
Fixed parts: every item uses the same grammatical template — the same opener type (verb first or
subject first), the same tense, the same part of speech. The first two words of each item differ
where the template allows, and they carry the point. A detail present in one item (a version, a
count, an owner) is present in all or removed. The verb says whether the item is good or bad news.
Limits: five items unranked is the ceiling; past five, rank them or split into "now" and "later".
Three or more items sharing two or more attributes become a table, one fact per cell, and a column
exists only when every row has a value that means something. Four or more components with relations,
or a flow with branches, become a diagram (Mermaid, validated before saving). No visual for
decoration.
Test: cover everything but the first two words of each item. The reader can still tell them apart.

## 6. Message — a Slack post, a PR comment, a review finding, an email, a commit body

Reader: cold, in a channel, with no access to the session and a hard size cap.
First line: the result. Then the evidence the reader can open (links to the real page, not a
local path), then the one action if there is one.
Fixed parts: every referent introduced by its full name on first use · identifiers verbatim and
complete · the follow-up line only when the channel's contract requires it (then it is a protected
block, see `SKILL.md`, The pass) · nothing that only makes sense inside the thread the agent was in.
Limits: the channel's cap, counted in the channel's unit and stated by the calling skill — for
example Slack 3,000 characters including URLs, an on-call bot reply 2,500 characters, a PR review
summary 400 words; a review finding reads alone without the summary. A message never carries a
code as a name; the reader has no legend. File paths, ids and session codes appear only where this reader
needs them to act; a reviewer needs the PR number, not the worktree path.
A PR body is a message with fixed parts: the intent in one line; a table of changes (file · what
changed · why); the gating record (toggle or named exception); the test receipt (command and
result); the review rounds, one line each; the provenance line. Its prose is in the procedure
register. Its author's standing rule, set after three bloated bodies in ten days: short, precise,
controlled English, nothing a reviewer must decode.
Test: paste the message into a fresh window and read it as the recipient. Every name resolves.

## 7. Procedure — a runbook, a checklist, the instruction part of a handoff, a PR body's change
table, an error message, a tool description

Reader: someone who must act with no one to ask, or a machine. This is the only shape written in
the controlled register of ASD-STE100.
Fixed parts: one instruction per sentence · imperative, active voice · at most 20 words per
instruction · numbered steps when there are three or more · each step names its verifiable outcome
("the command prints OK") · no phrasal verbs ("spin up" → "start") · noun clusters of at most
three words · simple tenses, except where "has completed" versus "completed" carries meaning.
Limits: this register is never applied to rationale, trade-off analysis or an explanation of a
bug; those need subordinate clauses and examples. A hedge that carries real uncertainty stays
("the job may have failed").
Test: a reader who follows the steps literally reaches the stated outcome, or knows at which step
to stop.

## Choosing when the text mixes shapes

A report holds sibling items and a procedure; a handoff holds a procedure (the first step) and a
glossary. The outer shape sets the order and the limits; the inner shape sets the form of that
part. When a calling skill fixes its own template (a review template, a prod-report template), the
calling template wins on order and the shape rules apply inside each section.
