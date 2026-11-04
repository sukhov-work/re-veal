# Patterns — the full table of constructions to find and rewrite

`SKILL.md` carries the twelve rows that cover most of what the measurements found. This file holds
the full table, grouped by the kind of damage, with the source of each row. Use it in detect mode,
or when the short table did not name the thing you are looking at. Fix the class, never a word
list: when 183 Claude Code transcripts were measured after seven CLAUDE.md rules were added, named
terms fell 21 % but unnamed scaffolding phrases rose 7 %, and "load-bearing" rose 11 % while it was
banned (claude-code issue #77136).

## A. Machine grammar — the constructions that make a sentence hard to parse

Measured in Clark, Martin and Mahowald, "Why is AI-generated language so hard to understand?"
(arXiv 2610.29162, October 2026): fourteen models, three settings, compared with meaning-preserving
paraphrases. Almost every frontier model overuses the first five rows. A length penalty during
reinforcement learning reproduced the shift in a small model, so "be concise" pushes the same way.

| Pattern | Smell | Fix |
|---|---|---|
| Inanimate actor, animate verb | "this asymmetry bites", "the docstring promises", "the check forgot its sibling" | Name the real actor, or use a plain verb: "this asymmetry causes errors" |
| Noun used as a verb | "footnote it", "calendar it", "we should gate this" | A normal verb phrase: "add a footnote", "put this behind a toggle" |
| Noun stack | "absolute dotfile backup path handling" | Break at three nouns and name the relation: "how the backup handles absolute paths to dotfiles" |
| Dropped "that" in a long clause | "the errors the old code never reached", "knew the answer was wrong" inside a 30-word sentence | Restore "that" when the clause is longer than five words |
| Late main verb | subject, then fifteen words of modifiers, then the verb | Subject and main verb inside the first eight words |
| Rare word pair | an unusual adjective-noun or verb-object pairing chosen for effect | The common pairing |
| Sentence over 40 words | one sentence carrying three facts and two conditions | Three sentences. Split at the facts, not at the commas |

## B. Words that stand in for thoughts

| Pattern | Smell | Fix |
|---|---|---|
| Coined jargon | a fresh label for a thing that has a standard name: "the unlock", "the seam", "the fold" | The standard term, repeated — never a cycle of synonyms |
| Borrowed technical metaphor | "gated on", "wired up", "load-bearing", "the crux", "papercut", "belt and braces", "pressure test" | The literal relation: "depends on", "connected", "the boundary between X and Y" |
| Thesaurus swap | "address" for location, "grain" for granularity, "movable" for mutable | The term the codebase or the field uses |
| Invented concept label | "the supervision paradox", "the acceleration trap", "the X divide" | Describe the thing in a full sentence |
| Unintroduced referent | "the fix", "the ask", "the tail", "round 1", "the twin" — never defined | Introduce it once by its full name; after that the short name is fine |
| Code as a name | "see D78", "per R7 and Q-E1", "rows 18 and 13", "T7.20" in prose | The name in words; the code may follow in parentheses; codes alone only as sort keys in a table |
| Nickname for a person or bot | "Tit has not answered", "Codebot round 1", "the grill helper" with no role | Name plus role on first use: "Tit (the FE lead who sets the registry statuses)" |
| Changelog comment | `// changed from X on <date> per ticket` | A comment states what the code does now |

## C. Rhetorical moves

| Pattern | Smell | Fix |
|---|---|---|
| Negative parallelism | "It's not X — it's Y." "Not a bug. A design flaw." "X, not Y." as the opener | State Y directly |
| Colon reveal | "The best part: it learns." | A plain sentence |
| Fake-profound kicker | a sentence that sounds like a pull-quote | A plain statement of which thing did what |
| False agency | "the decision emerged", "the data tells us" | Name the actor: "I ran the tests; they passed" |
| Rhetorical Q&A | "The result? Devastating." | State the result |
| Premise stacking | three sentences of evidence before the point | Point first, evidence after |
| Compulsive counting | "for two reasons", "three things matter" | List them without announcing the count |
| Argumentative framing | "here's where I'd push back", "now you're avoiding the real question" | State the disagreement and the evidence once |
| Importance puffery | "crucially", "fundamentally", "plays a vital role" | Show the consequence, or cut the adverb |
| Comma-clipped tail | "asked forty times, mentoring." | A full clause, or cut it |
| Vague declarative | "The reasons are structural." | The reasons |

## D. Scaffolding — text around the content

| Pattern | Smell | Fix |
|---|---|---|
| Throat-clearing | "Here's the thing:", "What most people miss…", "Looking at…", "Let me…" | Delete; start at the content |
| Reasoning leak | "I want to be precise about my role here…" | Do it; do not narrate doing it |
| Tie-back or fractal summary | "So, to answer your question…", a recap at the end of every section | Delete |
| Offer-menu closer | "Hope this helps — let me know if you want me to dig deeper" | End when the answer ends; one concrete next action only if the task has one |
| Unrequested verification | "I double-checked this against…" when nobody asked and nothing hinged on it | Delete, or move the fact into the evidence line |
| Tangent | a loosely related bug or idea in the middle of the answer | A separate line at the end, or a separate message |
| Decoration formatting | emoji headers, bold-first bullets restating the bold, a header per two-sentence section, unicode arrows as logic, title-case headings | Prose, or a real table |

## E. Epistemic slop — the rows that damage technical reports most

| Pattern | Smell | Fix |
|---|---|---|
| Adjective for a number | "significantly faster" | "220 ms → 40 ms"; if there is no number, say so |
| Invented count or source | "~50+ callers", "experts suggest" | The counted number with its query, or the real source, or drop the claim |
| Unbacked hedge | "should work", "probably fine" with no evidence in the sentence | The evidence, or the plain statement that it was not tested |
| Deleted hedge | a real uncertainty removed to sound confident | Keep the hedge; delete only hedges that carry nothing |
| Undated perishable | a rollout state, a version, an open gap with no date | "as of <date>" |
| Options theater | five alternatives listed, none weighed | Only the alternatives you weighed; two honest ones beat five decorative ones |
| Stale restatement | the state described as it was two turns ago | Re-read the source before restating state |

## Sources

Clark, Martin, Mahowald (arXiv 2610.29162); Reinhart et al., PNAS 2025 (nominalizations at 2.1×
the human rate, participial clauses at 5.3×); claude-code issue #77136 (183 transcripts, 67,000
sentences); hardikpandya/stop-slop; tropes.fyi; ayghri/i-have-adhd; the 2026-11-02 audit of 29
handoff, memory and decision files in three of the author's projects.
