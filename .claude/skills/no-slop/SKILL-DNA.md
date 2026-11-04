# SKILL-DNA — no-slop

Non-functional documentation: provenance, versions, and locked design decisions for the
`no-slop` skill. Never load this file as instructions during a run.

## Provenance

| Field | Value |
|---|---|
| Created | 2026-08-25, KB v2 program session 2 (decision D19 in the program's DECISIONS.md) |
| Commissioned by | KB owner — "compact metaskill to stop AI slop in reports, designs and responses" |
| Authored by | v1: claude-fable-5 (effort max) on the investigate-design-v3 engine; v2: claude-fable-5-1 on the ecom-pilot engine. Skill text hand-authored by the main agent in both versions; the scripts were written by an Opus 5.5 subagent to a spec and tested |
| Research | v1 (2026-08-25): hardikpandya/stop-slop, ayghri/i-have-adhd, tropes.fyi, Wikipedia Signs-of-AI-writing, HN 49296740, anthropics/claude-code#77136, petergyang/no-ai-slop, blader/humanizer, Kobak et al., Juzek & Ward. v2 (2026-11-02): Clark, Martin, Mahowald arXiv 2610.29162; Shankar, "Five Principles for Generating Readable AI Text in Bulk" and its 13 linked sources; Reinhart et al. PNAS 2025; Laban et al. arXiv 2505.06120; claude-code#92175; danyuchn/asd-ste100-skill; yzhao062/agent-style; yaplint; unjargon; plus three local studies — an audit of 29 handoff, memory and decision files in three projects, a 51-event re-ask corpus from 64 session transcripts, and the documented complaints in the projects' decision logs and memories. Reports in `.claude/claude-docs/designs/kb/v2/no-slop/` of the ecom monorepo |
| Reviewed | v1: KB owner; merged as ecom-grill-agent-kb PR #436, 2026-08-26. v2: KB owner, Codebot (5 findings) and the grill helper (two rounds, 3 majors and 5 minors, all fixed); merged as PR #642, 2026-11-02 |
| Distribution | master here; shipped in the CAP `ecom-platform` plugin alongside `ecom-pilot` (whose exit-gate step 6 invokes this skill's pass); copied with provenance to the owner's personal `cc-skills` repo; vendored verbatim inside `qa-v1` |

## Version record

- **v1.0 (2026-08-25, PR #436)** — initial release: single-file skill, ~105 lines. Order
  rules, claim budget, 10-row pattern table, epistemic floor, formatting rules, the pass
  (rewrite mode) + detect mode, integration hooks.
- **v2.0 (2026-11-02)** — the gate moves before drafting. New: the contract (reader · shape ·
  channel and budget · action) with the defaults the author kept asking for; seven shapes with
  counted limits (reply, report, handoff, decision record, sibling items, message, procedure);
  the vocabulary ledger; a 12-row core pattern table with the machine-grammar rows from Clark et
  al. and the "code as a name" row from the local audit; the pass gains a mechanical count, a cold
  read by a context-free reader, and protected blocks; optional guard scripts (Stop hook and
  write gate). Layout: `SKILL.md` (core, works alone), `references/shapes.md`,
  `references/patterns.md`, `scripts/` (checker, tests, installer, README).

## Locked design decisions

1. **Both slop directions are in scope** — padding slop (2024-era filler) AND compression
   slop (2026-era coined-jargon density). Sources targeting only the former (stop-slop)
   actively push toward the latter; the skill's core test ("say fewer things, never say each
   thing in fewer words") exists to hold the line between them.
2. **Fix pattern classes, not word lists.** Measured basis (claude-code#77136, 183
   transcripts / 1.46M words): banned named terms drop ~21% but unnamed rhetorical
   scaffolding rises ~7% — blocklists re-form the register. The pattern table names the
   class and the rewrite, not the vocabulary. The checker's lexicon check is advisory for the same reason.
3. **A dedicated rewrite pass, not inline rules alone.** Style instructions decay during
   generation (multiple independent reports); a separate pass holds. "The pass" is therefore
   the skill's operative unit, wired into exit gates of report-producing skills. v2 keeps the
   heading "The pass" verbatim: four consumer flows name it.
4. **Epistemic floor is first-class.** For technical reports the highest-damage slop is
   epistemic (fabricated precision, unsourced claims, silenced risks), which prose-oriented
   anti-slop skills omit entirely. Numbers-over-adjectives, source-or-silence, dated
   perishables, keep-real-hedges.
5. **Detect mode names patterns with quotes and never outputs an AI-probability score** —
   named patterns are checkable evidence; scores are guesses.
6. **Never instruct "be concise."** Models resolve it as "dense and cryptic" — the exact
   failure the skill exists to prevent. Budget claims, not words. v2 adds the mechanism: Clark
   et al. showed a length penalty alone produces the compressed grammar, so a brevity
   instruction pushes a model further along a path it is already on. The contract sets a size
   budget per shape instead, and the budget is a stop condition: when it is reached, claims move
   below a line or into the saved file, never into denser sentences. The side-by-side eval of
   2026-11-02 showed why both halves are needed — with a claim budget alone, nine rewrites under
   v2 came out 29 % longer than their inputs while being preferred 8 of 9 times by a blind judge.
7. **`SKILL.md` works alone; everything else is optional.** (Relaxes the v1 decision "single
   file, no references/ tree".) Three runtimes inject or fetch only `SKILL.md` — the prod-e
   on-call responder, the Kyber BCA session over GITHUBBOT, and the claude.ai account skill —
   and two of them cannot run scripts (a Kyber session with its KB clone can run the checker). So
   the contract, the shapes table, the core pattern table and the
   pass live in `SKILL.md` and read correctly without the other files; `references/` holds the
   full templates and tables, `scripts/` holds enforcement. `SKILL.md` stays under 500 lines and
   its contract within the first 5,000 tokens, the part Claude Code keeps after compaction.
8. **The gate starts before drafting (v2).** The 2026-11-02 audit showed the intended reader
   predicts the damage: files written for the next model session carried up to 91 bare codes
   and 35 undefined terms; the same author's files for humans carried 0 to 5. A pass after
   drafting shortened sentences but did not stop codes used as names. So the skill's first
   step is the contract — reader, shape, channel and budget, action — and the shapes carry
   counted limits a pass can check.
9. **Self-review is not the last check (v2).** Models rate their own prose as fine (HN
   49296740; the v1 pass left codes-as-names in every audited handoff). Anything that leaves
   the session gets a cold read by a context-free reader, and the mechanical counts run as a
   script where one can run. The Stop hook blocks once and never loops (`stop_hook_active`).
10. **Enforcement is on by default, installed by the wizards, never by the skill itself (v2;
    the owner decided 2026-11-02).** `/ecom-setup` and cc-skills `harness-setup` install the
    guard at user scope so one run covers every repo; `install-guard.sh off --scope user` removes
    it and the wizards honour the opt-out. The skill never registers hooks through its own
    frontmatter, so a consumer that loads the file as text or through a plugin is never surprised
    by a blocking hook. The hooks fail open when python3 or the script is missing.
11. **One owner for the readable-structure rules (v2; the owner decided 2026-11-02).** The
    ecom-pilot engine's core §8, including its five reviewer-first tests, moved into the Report
    and Sibling-items shapes; the engine invokes this skill at its exit gate and falls back to a
    six-line inline core with a visible warning when the skill is not installed. Every other
    consumer uses the full `SKILL.md` as primary; its paraphrase is a fallback, not a replacement.

## Mutation log

- 2026-11-02 — v2.0 authored on branch `kbv2/no-slop-v2`; decision 7 relaxed from "single
  file" to "SKILL.md works alone"; decisions 8–11 added. Same day, after the owner's review:
  guard on by default through the wizards (decision 10 rewritten), ecom-pilot §8 consolidated
  here (decision 11), reply budget 150 words with the hook at 250, all consumers switched to the
  full file with their paraphrases kept as fallbacks. Merged as PR #642 the same day after two
  review rounds; the live Kyber agent prompt and the PromptHub router prompt were pasted by the
  owner within hours (state record: `designs/production/n8n-helper/STATE-2026-10-23.md` §7). Consumers to re-sync in the same
  release: `qa-v1/references/no-slop.md`, `cc-skills/skills/no-slop`, the prod-e pilot's
  inlined §8, the claude.ai account skill, the `headless-frame-the-world` project copy.
