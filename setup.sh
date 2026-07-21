#!/bin/bash
# One-time setup. Run from this folder:   ./setup.sh
# Optional:  ./setup.sh --learned   also installs the neural matcher
#            (bigger download; only helps with very difficult photo pairs)
set -e
cd "$(dirname "$0")"
say() { printf "\n\033[1m== %s ==\033[0m\n" "$1"; }

say "1/3 Checking Python"
PY=""
for c in python3.13 python3.12 python3.11; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c" && break; fi
done
if [ -z "$PY" ] && command -v python3 >/dev/null 2>&1; then
  v=$(python3 -c 'import sys;print(sys.version_info >= (3,11))')
  [ "$v" = "True" ] && PY="python3"
fi
if [ -z "$PY" ]; then
  echo "Need Python 3.11 or newer:  brew install python@3.12  then rerun ./setup.sh"
  exit 1
fi
echo "Using $($PY --version)"

say "2/3 Creating the Python environment and installing packages (2-4 min)"
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel >/dev/null
pip install -r requirements.txt
if [ "$1" = "--learned" ]; then
  echo "Installing the optional neural matcher (this one is big, ~2 GB)..."
  pip install -r requirements-learned.txt
  echo "Downloading its model files once, so it never needs the internet later..."
  python reveal.py warmup
fi

say "3/3 Self-test"
python reveal.py check

echo
echo "Setup finished. Start it any time with:  ./run.sh"
