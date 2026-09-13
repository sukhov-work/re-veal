#!/bin/bash
# One-time setup for Impossible. Separate venv from Reveal on purpose.
set -e
cd "$(dirname "$0")"
PY=""
for c in python3.13 python3.12; do
  command -v "$c" >/dev/null 2>&1 && PY="$c" && break
done
[ -z "$PY" ] && { echo "Need Python 3.12+:  brew install python@3.12"; exit 1; }
echo "Using $($PY --version)"
[ -d .venv-impossible ] || "$PY" -m venv .venv-impossible
source .venv-impossible/bin/activate
pip install --upgrade pip wheel >/dev/null
pip install -r requirements-impossible.txt
echo
python -m impossible probe
echo
echo "Ready. Try:  python -m impossible pair a.jpg b.jpg --out out/"
