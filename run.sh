#!/bin/bash
# Everyday run:  ./run.sh
# Starts Reveal and opens it in your browser. Press Ctrl+C here to stop.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Run ./setup.sh first (one time)."
  exit 1
fi
source .venv/bin/activate
exec python reveal.py serve "$@"
