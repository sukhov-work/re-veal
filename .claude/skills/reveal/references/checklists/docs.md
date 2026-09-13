# Track D — docs + memory + config consistency (seed)

Format: one assertion per item, then `— check:` and `— anchor:`. Items 1–12 are the universal seed
(2026-09-06, from two projects' audits); the project appends its own, dated, at each audit.
Re-mine DECISIONS since the baseline anchor at every audit start.

Items 1–6 and 9–12 double as the **Track F (harness)** checklist until the project authors its own
`harness.md` — they assert things about the operating environment, not about the product.

TOC: 1 DECISIONS read budget · 2 memory reachability · 3 root memory cap · 4 handover shape ·
5 hook paths · 6 markers ignored · 7 volatile counts · 8 pending tags · 9 audit purity ·
10 backlog row shape · 11 new checks can fail · 12 degrade paths announce

1. `DECISIONS.md` fits one read: the hot section is under ~100 KB and the header carries the
   compaction contract with an md5 receipt for every moved era.
   — check: `wc -c .claude/claude-docs/DECISIONS.md`; Compactions table rows ≥ rounds run.
   — anchor: session-workflow.md §DECISIONS; frame-the-world audit-2 F1.
2. Every `mem:<name>` reference resolves to a memory file — and the probe fails on a fake one.
   — check: `grep -rho --exclude=docs.md 'mem:[a-z0-9_/-]*' AGENTS.md .claude .serena | sort -u` vs the memory dir listing (exclude this file: its own instruction text is a false hit — found at the 2026-09-13 bootstrap probe); add `mem:does-not-exist` to a scratch file and confirm it is reported.
   — anchor: memory_maintenance.md §Graph health; serena-playbook.md §Health check.
3. `mem:core` ≤ 12 KB; every `project/wip-*` leaf appears in its era index.
   — check: `wc -c <memdir>/core.md`; `ls <memdir>/project | wc -l` vs era rows.
   — anchor: memory_maintenance.md caps.
4. `NEXT_SESSION_PROMPT.md` carries the v2 sections: Standing order · Mission · Standing watches · Gate baseline · Record · Harness facts.
   — check: `grep -c '^## ' NEXT_SESSION_PROMPT.md` ≥ 6 and each heading present.
   — anchor: session-workflow.md §handover template.
5. No hook command carries an absolute machine path; project hooks use `${CLAUDE_PROJECT_DIR}`, and every command in `settings.json` points at a file that exists.
   — check: `grep -n '"/Users\|"/home' .claude/settings.json` is empty; every `.claude/hooks/*.sh` named in settings.json exists and passes `bash -n`.
   — anchor: hooks.md.
6. Markers and agent artefacts are gitignored: `.ship-title`, `BLOCKING_QUESTIONS.md`, `ATTENTION.md`, `NEXT_SESSION_PROMPT.md`, the scratch/artefact dirs.
   — check: `git check-ignore -q .claude/.ship-title .claude/ATTENTION.md .claude/claude-docs/NEXT_SESSION_PROMPT.md`.
   — anchor: scaffold-manifest.md §.gitignore.
7. Every volatile count has one canonical home; every other occurrence references it or is dated.
   — check: grep the last three counts changed in DECISIONS across docs; each extra occurrence carries "as of <date>".
   — anchor: session-workflow.md rules; epistemic-filter 2026-08-09 ("19 jobs" in 7 places).
8. No stale pending tag survives a ship: `UNVERIFIED|pending|NOT built|DESIGNED` in docs touched by the last deploy were re-read.
   — check: `git diff --name-only <last-deploy-sha>..HEAD -- '*.md' | xargs grep -ln 'UNVERIFIED\|pending\|NOT built\|DESIGNED'` reviewed.
   — anchor: dev-skill-template Phase 4; epistemic-filter 2026-08-09 (a tag survived 5 deploys).
9. The audit session's diff touches only the report and the skill's files.
   — check: `git status --porcelain` at session end shows nothing under the artifact dirs.
   — anchor: audit-mode.md step 8.
10. Every `tracked-backlog.md` row has all its columns, a stable unique ID with no gaps in the
    range, and a `Pointer` that resolves today (a `DECISIONS <date>` pointer may resolve in the
    log **or** its archive).
    — check: `awk -F'|' 'NF && NF!=7 {print NR": "$0}' references/tracked-backlog.md` is empty
    (adjust `NF` to the table's column count + 2); IDs sorted are contiguous; each pointer grepped
    in `DECISIONS.md` and `DECISIONS_ARCHIVE.md`.
    — anchor: tracked-backlog.md §Rules. Twelve rows shipped with 3 cells in a 5-column table and
    survived **two** audits, because the earlier check read the values and not the shape.
11. Every check added since the baseline anchor can FAIL: for each, the mutation that turns it red
    is named.
    — check: list the assertions added since the anchor (`git diff <anchor>..HEAD -- <test glob>`);
    for a sample of 3, apply the named mutation and confirm red. A counter also needs a positive
    control and its precondition pinned.
    — anchor: SKILL.md Phase 3 §Can this check FAIL? (the three refused shapes); task_completion
    item 3; checklists/README §item format. Five checks that could not fail — four written in the
    same session — shipped past four green gates.
12. Every fallback and degrade path added since the baseline emits a visible line when it engages,
    and each has a named first-fire watch in the handover with an expected healthy value.
    — check: grep the touched degrade paths for their log/warn emission; cross-check each against
    a `## 1. Standing watches` row.
    — anchor: dev-skill-template Phase 3 §Degrade-path visibility. A silent fallback ran 41 h
    unnoticed in one project; in another the entire main visual fell back to a placeholder twice,
    invisible to every gate.
