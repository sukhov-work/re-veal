#!/usr/bin/env bash
# Lists, and with --stop ends, the processes a Claude session starts in this repo (owner order
# 2026-11-05: stop all python work and running test processes and services at the start and the end
# of a session). The owner's own studio server on port 8380 is never touched; a studio server on any
# other port, a headless Chrome with a DevTools port, pytest, the harnesses, loop_seq.py renders,
# reveal.py and transitions.py runs and the impeccable detector are the session's.
# Usage: scripts/session_sweep.sh          # list
#        scripts/session_sweep.sh --stop   # SIGTERM each, then SIGKILL after 5 s if still alive
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATTERN='reveal-studio serve|reveal_studio|studio/\.venv|pytest|harness\.py|loop_seq\.py|reveal\.py (align|check|warmup)|transitions\.py (pair|check|warmup)|impeccable|remote-debugging-port|--headless'
OWNER_PORT="${REVEAL_STUDIO_PORT:-8380}"
owner_pid=""
if [ -f "$ROOT/benchmarks/runs/studio.lock" ]; then
  owner_pid="$(awk '{for(i=1;i<=NF;i++) if($i=="pid") print $(i+1)}' "$ROOT/benchmarks/runs/studio.lock")"
fi
me=$$
found=0
while IFS= read -r line; do
  pid="$(echo "$line" | awk '{print $1}')"
  [ "$pid" = "$me" ] && continue
  [ -n "$owner_pid" ] && [ "$pid" = "$owner_pid" ] && { echo "kept   $line   (the owner's studio server, port $OWNER_PORT)"; continue; }
  if echo "$line" | grep -qE "reveal-studio serve|reveal_studio" && echo "$line" | grep -qE -- "--port $OWNER_PORT( |$)"; then
    echo "kept   $line   (a studio server on the owner's port $OWNER_PORT)"; continue
  fi
  found=$((found+1))
  if [ "${1:-}" = "--stop" ]; then
    kill "$pid" 2>/dev/null && echo "stopped $line" || echo "gone   $line"
  else
    echo "running $line"
  fi
done < <(ps -axo pid=,etime=,command= | grep -E "$PATTERN" | grep -vE "session_sweep|grep -E")
if [ "${1:-}" = "--stop" ] && [ "$found" -gt 0 ]; then
  sleep 5
  ps -axo pid=,command= | grep -E "$PATTERN" | grep -vE "session_sweep|grep -E" | while IFS= read -r line; do
    pid="$(echo "$line" | awk '{print $1}')"
    [ -n "$owner_pid" ] && [ "$pid" = "$owner_pid" ] && continue
    kill -9 "$pid" 2>/dev/null && echo "killed  $line"
  done
fi
echo "session processes: $found$( [ "${1:-}" = "--stop" ] && echo " (stopped)" )"
