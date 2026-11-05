"""A fake scripts/research/director_page.py for the studio's unit tests: the real flags and --help text, the real rule
for what the page lists, and the page written in place.

RUN/index.html over every child folder of RUN that holds an info.json, sorted by name; a folder name splits at its
last underscore into the plan's stem and the concept (with its tag after a dash), and the plan is read from the
repo's scripts/research/plans/<stem>.json, as the real script reads it (a missing plan raises, as there). The notes
print per clip (look, faults), the head goes under the title, and the last line printed is `<path> <n> clips`.
FAKE_FAIL="page" exits 1.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLANS = ROOT / "scripts/research/plans"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--notes", default=None)
    ap.add_argument("--title", default="The director's first planned renders (2026-10-17)")
    ap.add_argument("--head", default=None)
    ap.add_argument("--key", default="director_r8")
    ap.add_argument(
        "--keyframes", default=None, help="keyframes.json of the generated helpers (name -> model, seed, steps, size)"
    )
    a = ap.parse_args()
    if "page" in os.environ.get("FAKE_FAIL", "").split(","):
        print("RuntimeError: the fake page failed on purpose", file=sys.stderr)
        sys.exit(1)
    run = Path(a.run)
    notes = json.loads(Path(a.notes).read_text()) if a.notes else {}
    head = Path(a.head).read_text() if a.head else ""
    items = sorted(p for p in run.iterdir() if p.is_dir() and (p / "info.json").exists())
    out = [f"<!doctype html><title>{html.escape(a.title)}</title><h1>{html.escape(a.title)}</h1>", head]
    for p in items:
        stem, concept = p.name.rsplit("_", 1)
        plan = json.loads((PLANS / f"{stem}.json").read_text())
        info = json.loads((p / "info.json").read_text())
        n = notes.get(p.name, {})
        out.append(
            f"<h2>{html.escape(p.name)}</h2><video src='{html.escape(p.name)}/transition.mp4'></video>"
            f"<p>plan {html.escape(plan['pair'])} concept {html.escape(concept.split('-')[0])}; "
            f"first step {info['step_first']}</p><p>look: {html.escape(n.get('look', ''))}</p>"
            f"<p>faults: {html.escape(n.get('faults', ''))}</p>"
        )
    out.append(f"<script>const PAGE='{html.escape(a.key)}';</script>")
    (run / "index.html").write_text("\n".join(out))
    print(run / "index.html", len(items), "clips")


if __name__ == "__main__":
    main()
