#!/usr/bin/env bash
# SessionStart hook — load the carry-over context. Prints an instruction block; never fails.
# Fires with source = startup|resume|clear|compact|fork. On `compact` it prints the SHORT
# re-read block: this is the one channel after a compaction that is proven to reach the model.
STDIN_JSON="$(cat 2>/dev/null || true)"
project=""; src=""
jget() { printf '%s' "$STDIN_JSON" | python3 -c "import json,sys
try:
    v=json.load(sys.stdin).get('$1'); sys.stdout.write(v if isinstance(v,str) else '')
except Exception: pass" 2>/dev/null || true; }
if command -v python3 >/dev/null 2>&1 && [ -n "$STDIN_JSON" ]; then
  project="$(jget cwd)"; src="$(jget source)"
fi
[ -n "$project" ] && [ -d "$project" ] || project="${CLAUDE_PROJECT_DIR:-$PWD}"

if [ "$src" = "compact" ]; then
  cat <<'EOT'
Context was just compacted. Silently, before responding: re-read your session memory stub
(project/wip-<date>-<slug>) and .claude/claude-docs/NEXT_SESSION_PROMPT.md, then continue from the
"where I left off" line. Anything the compaction summary lost is in those two files.
EOT
  exit 0
fi

# Memory root = the MAIN worktree when this is a linked worktree (memories outlive worktrees).
mem_root="$project"
if command -v git >/dev/null 2>&1; then
  gd="$(git -C "$project" rev-parse --git-dir 2>/dev/null || true)"
  cd_="$(git -C "$project" rev-parse --git-common-dir 2>/dev/null || true)"
  if [ -n "$gd" ] && [ -n "$cd_" ] && [ "$gd" != "$cd_" ]; then
    case "$cd_" in /*) ;; *) cd_="$project/$cd_" ;; esac
    mw="$(cd "$(dirname "$cd_")" 2>/dev/null && pwd -P || true)"; [ -n "$mw" ] && mem_root="$mw"
  fi
fi

# Memory backend: probe for the STORE, not for the tool — the store is what the loop needs.
if [ -f "$mem_root/.serena/memories/core.md" ] && grep -q '"serena"' "$HOME/.claude.json" 2>/dev/null; then
  MEM="1. Call mcp__serena__activate_project with project \"$mem_root\". Then mcp__serena__list_memories;
   read mem:core (the graph root) and follow its index to the memories relevant to this task."
elif [ -f "$mem_root/.serena/memories/core.md" ]; then
  MEM="1. Memory backend = files (Serena is not registered on this machine): read
   $mem_root/.serena/memories/core.md and follow its index. Write memories as plain files there."
else
  MEM="1. Memory backend = files: read $mem_root/.claude/memories/core.md and follow its index."
fi
ATTN=""
[ -s "$mem_root/.claude/ATTENTION.md" ] && ATTN="5. .claude/ATTENTION.md EXISTS — read it, resolve what it reports (for a ship anomaly, verify
   by tree identity: git diff <tip> <publish-remote>/<main>), then DELETE it. Re-check it once
   LATE in the session: a detached job can append up to ~45 min after the previous session ended."
DEC="$mem_root/.claude/claude-docs/DECISIONS.md"; SIZE_NOTE=""
[ -f "$DEC" ] && [ "$(wc -c < "$DEC")" -gt 100000 ] && SIZE_NOTE="6. DECISIONS.md is over the 100 KB read budget — schedule a compaction (session-workflow contract)."
if [ -z "$ATTN" ]; then
  if [ -x "$mem_root/.claude/hooks/session-end-ship.sh" ]; then   # delivery shape D only
    ATTN="5. No ATTENTION.md. If the checkout is on a ship branch or the last ship never landed,
   re-seat onto the publish remote's main FIRST (tree-identity check → rebase --onto; never force-merge)."
  else
    ATTN="5. No ATTENTION.md — no background job flagged anything."
  fi
fi

cat <<EOT
You MUST do the following silently before responding to the user:
$MEM
2. Read .claude/claude-docs/NEXT_SESSION_PROMPT.md FIRST (the handover — freshest state), then the
   TOP of .claude/claude-docs/DECISIONS.md. DECISIONS carries multi-KB single lines: read it PAGED
   (offset/limit) or grep for the entry you need — a naive full Read truncates before §Recent.
3. If the handover has a "Standing watches" section, run those watches BEFORE the agenda. A FAILED
   watch outranks the planned work; a passed watch is closed in the handover rewrite, never dropped.
4. Stub the record NOW, before the work: create the session memory leaf
   (project/wip-$(date +%F)-<slug>) with the mission and a "where I left off: —" line. Every later
   write updates that leaf. A session cut off after a stub still leaves a findable record.
$ATTN
${SIZE_NOTE:+$SIZE_NOTE
}Do all of this silently — do not narrate these steps to the user.
EOT
exit 0
