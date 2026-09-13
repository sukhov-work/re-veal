#!/usr/bin/env bash
# scripts/clean.sh — the sanctioned cache reset for Reveal (allowed by name in .claude/settings.json).
# Removes: python bytecode caches, .pytest_cache, harness temp dirs older than an hour.
#   --jobs   also empties _reveal/jobs (copied uploads + outputs of past sessions; the files the
#            user asked for already landed in ~/Downloads, so the job dirs are disposable).
# NEVER touches .venv/ (minutes to rebuild) or models/ (52 MB of checksummed weights; refetch is
# ./setup.sh --learned, which needs the network).
set -euo pipefail
cd "$(dirname "$0")/.."
find . \( -path ./.venv -o -path ./models -o -path ./.git \) -prune -o -name __pycache__ -type d -print0 \
  | xargs -0 rm -rf
rm -rf .pytest_cache
tmp="${TMPDIR:-/tmp}"
find "$tmp" -maxdepth 1 -name 'reveal-harness-*' -type d -mmin +60 -print0 2>/dev/null | xargs -0 rm -rf
if [ "${1:-}" = "--jobs" ]; then rm -rf _reveal/jobs; echo "cleaned: _reveal/jobs"; fi
echo "clean: bytecode caches, .pytest_cache, stale reveal-harness-* temp dirs"
