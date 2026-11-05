#!/usr/bin/env python3
"""A stand-in for reveal.py in the unit tests: `align A B --out DIR`, the one command the studio runs (Reveal's
verdict, the branch the pair and director flows share).

It writes DIR/before.jpg and DIR/after_aligned.jpg (copies of A and B), then DIR/metrics.json last, as reveal.py
writes its metrics last: {"metrics": {"method": "sift", "inliers": 481, "rmse_px": 0.79, "confidence": 94,
"passed": true}} (the first real pair's numbers on this laptop, HANDOFF.md §11). The environment steers it:
FAKE_SLOW="align=2" spends that many seconds before writing, FAKE_REFUSE="align" prints a FAILED: line and exits 2
with nothing written, FAKE_FAIL="align" exits 1 after a traceback line. In a tmp root it also stands for the root's
marker file reveal.py.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path


def steer(name: str) -> None:
    slow = dict(kv.split("=") for kv in os.environ.get("FAKE_SLOW", "").split(",") if "=" in kv)
    if name in slow:
        time.sleep(float(slow[name]))
    if name in os.environ.get("FAKE_REFUSE", "").split(","):
        print("FAILED: the photos share too little detail", flush=True)
        sys.exit(2)
    if name in os.environ.get("FAKE_FAIL", "").split(","):
        print("Traceback (most recent call last):", file=sys.stderr)
        print(f"RuntimeError: the fake {name} failed", file=sys.stderr, flush=True)
        sys.exit(1)


def cmd_align(a: argparse.Namespace) -> None:
    steer("align")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a.before, out / "before.jpg")
    shutil.copyfile(a.after, out / "after_aligned.jpg")
    metrics = {"metrics": {"method": "sift", "inliers": 481, "rmse_px": 0.79, "confidence": 94, "passed": True}}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print(f"align: {a.before} and {a.after} into {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="A fake reveal.py for the studio's tests: align only.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    al = sub.add_parser("align")
    al.add_argument("before")
    al.add_argument("after")
    al.add_argument("--out", required=True)
    a = ap.parse_args()
    cmd_align(a)


if __name__ == "__main__":
    main()
