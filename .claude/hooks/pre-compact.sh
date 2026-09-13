#!/usr/bin/env bash
# PreCompact hook — checkpoint the session before context is lost. Clean-exit persistence is
# driven by the /reveal skill's Phase 4; this hook is the safety net. Never fails.
# STATUS: UNVERIFIED as a persistence leg (bootstrap-project references/hooks.md) — the proven
# channel after a compaction is session-start.sh firing with source=compact.
BLOCK='Before context is lost, persist this session so the next one resumes cleanly. Silently:
1. Memory — update the session stub leaf (project/wip-<date>-<slug>), never a second one:
   in-progress findings, "where I left off", the next concrete step, decisions and constraints not
   yet stored, key paths and identifiers IN FULL.
2. DECISIONS.md — append ONE dated line per meaningful change (what · files · numbers ·
   verification tier · reversibility tag). Append-only; never edit old lines; owner orders verbatim.
3. NEXT_SESSION_PROMPT.md — rewrite it: standing order · mission · standing watches with expected
   healthy values · facts · plan with file:line anchors · gate baseline incl. known reds · record
   checklist · harness facts that bite. Advance the Status line in mem:core if the phase moved.
4. If a rule, table, field, or constraint was introduced that the canonical docs do not carry,
   fold it back now (doc-sync) — a ruling that lives only in DECISIONS is invisible to design work.
5. Push the PUBLISH remote (never the deploy remote). Then show the user a 2-3 sentence summary.'

if command -v python3 >/dev/null 2>&1; then
  BLOCK="$BLOCK" python3 - <<'PY'
import json, os
print(json.dumps({
  "systemMessage": "Session checkpoint requested before compaction.",
  "hookSpecificOutput": {"hookEventName": "PreCompact",
                         "additionalContext": os.environ["BLOCK"]}}))
PY
else
  printf '%s\n' "$BLOCK"
fi
exit 0
