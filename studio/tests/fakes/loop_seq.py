#!/usr/bin/env python3
"""A stand-in for scripts/research/loop_seq.py in the unit tests: the real subcommands and flags, tiny outputs.

prep writes k<i>.png per still (depth_k<i>.npy with --depth-maps) and prep.json in the real shape (a `lock` block
with --lock-window); readers writes readers.json and depth previews into --out and the depth maps beside the prep;
render writes loop.mp4 (cv2, mp4v), loop.gif, sheet.jpg, frames.json, measure.json and plan.json (frames/ with
--frames), with PROGRESS lines on stderr under --progress; page writes the page and in/<seq>/keys.jpg.
prep --windows adds the top-level `windows` and `frames[i].windows` (fits all, far with --bg-depth, ecc with
--ecc-refine, final) and windows.jpg; probe writes the strips, crops/ and probe.json; measure writes measure.json
(with --window: `stability` and `stability_max`). A malformed window prints a FAILED: line and exits 2.

The environment steers it: FAKE_SLOW="render=3,prep=1" spends that many seconds inside the command (with progress
lines), FAKE_FAIL="render" exits 1 after a traceback line, FAKE_REFUSE="prep" prints a FAILED: line and exits 2,
FAKE_NO_FLAGS=1 drops --progress, --frames, --windows and the readers, probe and measure commands (an older
script), FAKE_NO_RIFE=1 makes the probe skip its RIFE strips with the reason in `rife_skipped`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import struct
import sys
import time
import zlib
from pathlib import Path

W, H = 64, 48
NO_FLAGS = os.environ.get("FAKE_NO_FLAGS") == "1"


def png(w: int, h: int, seed: str) -> bytes:
    """A deterministic RGB PNG whose colour comes from `seed`."""
    r, g, b = (int(seed[i : i + 2], 16) for i in (0, 2, 4))
    rows = b"".join(b"\x00" + bytes((r, g, (b + y) % 256)) * w for y in range(h))

    def chunk(t: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def npy(w: int, h: int, seed: str) -> bytes:
    """A deterministic float32 .npy of shape (h, w) in [0, 1]."""
    base = int(seed[:2], 16) / 255.0
    data = b"".join(struct.pack("<f", (base + x / w) % 1.0) for _ in range(h) for x in range(w))
    header = f"{{'descr': '<f4', 'fortran_order': False, 'shape': ({h}, {w}), }}"
    pad = (64 - (10 + len(header) + 1) % 64) % 64
    header = header + " " * pad + "\n"
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header.encode("latin1") + data


def steer(name: str, n: int = 4, progress: bool = False) -> None:
    """Sleeps, refuses or fails as the FAKE_* environment asks for this command."""
    slow = dict(kv.split("=") for kv in os.environ.get("FAKE_SLOW", "").split(",") if "=" in kv)
    if name in slow:
        seconds = float(slow[name])
        for i in range(n):
            if progress:
                print(f"PROGRESS {i} {n} frames", file=sys.stderr, flush=True)
            time.sleep(seconds / n)
    if name in os.environ.get("FAKE_REFUSE", "").split(","):
        print(f"FAILED: the fake {name} refuses this input", flush=True)
        sys.exit(2)
    if name in os.environ.get("FAKE_FAIL", "").split(","):
        print("Traceback (most recent call last):", file=sys.stderr)
        print(f"RuntimeError: the fake {name} failed", file=sys.stderr, flush=True)
        sys.exit(1)


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes(), usedforsecurity=False).hexdigest()


def parse_windows(spec: str, what: str) -> list[tuple[str, list[int]]]:
    """'name:x0,y0,x1,y1;...' as the real script reads it; a malformed or repeated window exits 2 with a FAILED line."""
    out: list[tuple[str, list[int]]] = []
    for part in (spec or "").split(";"):
        if not part.strip():
            continue
        name, sep, box = part.partition(":")
        try:
            xs = [int(float(v)) for v in box.split(",")]
        except ValueError:
            xs = []
        bad = not sep or not name.strip() or len(xs) != 4 or name.strip() in [n for n, _ in out]
        if bad or xs[2] - xs[0] < 4 or xs[3] - xs[1] < 4:
            print(f"FAILED: {what}: {part.strip()!r} is not a new name:x0,y0,x1,y1 with sides of 4 px or more")
            sys.exit(2)
        out.append((name.strip(), xs))
    return out


def window_entry(k: int, box: list[int], i: int, a: argparse.Namespace) -> dict[str, object]:
    """frames[i].windows.<name>: a window touching frame 0's border reads its peak on the search's edge."""
    edge = box[0] == 0 or box[1] == 0

    def fit(dx: float, dy: float, corr: float) -> dict[str, object]:
        return {"dx": 30.0 if edge else round(dx, 2), "dy": round(dy, 2), "corr": corr, "edge": edge}

    fits = {"all": fit(6.14 + k, -12.59, 0.992)}
    if a.bg_depth:
        fits["far"] = fit(5.25 + k, -7.32, 0.994)
    if a.ecc_refine:
        fits["ecc"] = fit(1.38, -12.29, 0.994)
    fits["final"] = fit(1.4 + k / 10, -1.09 * i, 0.994)
    return {"box": box, "box_canvas": box, "fits": fits}  # the fake's crop is the whole canvas


def cmd_prep(a: argparse.Namespace) -> None:
    seq_dir, out = Path(a.seq_dir), Path(a.out)
    stills = sorted(
        p for p in seq_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg") and not p.name.startswith(".")
    )
    out.mkdir(parents=True, exist_ok=True)
    steer("prep", len(stills))
    frames, sources = [], []
    wins = [[int(v) for v in w.split(",")] for w in (a.lock_window or "").split(";") if w.strip()]
    for i, p in enumerate(stills):
        data = p.read_bytes()
        h = hashlib.sha256(data).hexdigest()
        (out / f"k{i}.png").write_bytes(png(W, H, h))
        if a.depth_maps or a.bg_depth:
            (out / f"depth_k{i}.npy").write_bytes(npy(W, H, h))
        sources.append({"source": str(p), "bytes": len(data), "sha256": h, "native": [W * 4, H * 4], "scaled": [W, H]})
        if i == 0:
            frames.append({"method": "reference", "trusted": True, "scale_to_canvas": 1.0})
            continue
        f: dict[str, object] = {
            "method": "sift+magsac" + (" + lock" if wins else ""),
            "inliers": 120 + i,
            "matches": 200,
            "sane": True,
            "why": "scale 1.000 corner max 0.0 px",
            "residual_px": 1.0,
            "trusted": True,
        }
        if wins:
            f["lock"] = {
                "windows": wins,
                "offsets_px": [[1.0, -2.0] for _ in wins],
                "shift_px": [-1.0, 2.0],
                "corr": [0.99 for _ in wins],
            }
        f["scale_to_canvas"] = 1.0
        f["H_to_canvas"] = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        frames.append(f)
    prep = {
        "date": dt.datetime.now().isoformat(timespec="seconds"),
        "seq": seq_dir.name,
        "sources": sources,
        "long": a.long,
        "cuts": [int(c) for c in a.cut.split(",") if c.strip()] if a.cut else [],
        "bg_depth": a.bg_depth,
        "depth_blend": False,
        "min_inliers": a.min_inliers,
        "ecc_refine": a.ecc_refine,
        "ref_requested": a.ref,
        "lock_window": a.lock_window or None,
        "reference": max(a.ref, 0),
        "reference_size": [W, H],
        "crop": [0, 0, W, H],
        "canvas": [W, H],
        "frames": frames,
    }
    named = parse_windows(getattr(a, "windows", ""), "prep --windows")
    for n, b in named:
        if b[0] < 0 or b[1] < 0 or b[2] > W or b[3] > H:
            print(f"FAILED: prep --windows: {n} {b} lies outside frame 0 ({W}x{H})")
            sys.exit(2)
    if named:
        prep["windows"] = dict(named)
        for i, f in enumerate(frames[1:], 1):
            f["windows"] = {n: window_entry(k, b, i, a) for k, (n, b) in enumerate(named)}
        (out / "windows.jpg").write_bytes(png(W, H, "a0a0a0"))
    (out / "prep.json").write_text(json.dumps(prep, indent=1))
    print(f"prep: {len(stills)} stills registered into {out}")


def cmd_readers(a: argparse.Namespace) -> None:
    prep = Path(a.prep_dir)
    out = Path(a.out) if a.out else prep / "readers"
    out.mkdir(parents=True, exist_ok=True)
    ks = sorted(prep.glob("k*.png"), key=lambda p: int(p.stem[1:]))
    steer("readers", len(ks))
    stills = []
    for i, k in enumerate(ks):
        dep = prep / f"depth_k{i}.npy"
        if not dep.exists():  # computed and saved beside the prep only when missing, as the real command does
            dep.write_bytes(npy(W, H, hashlib.sha256(k.read_bytes()).hexdigest()))
        (out / f"depth_k{i}.jpg").write_bytes(png(W, H, hashlib.sha256(dep.read_bytes()).hexdigest()))
        stills.append(
            {
                "still": k.name,
                "size": [W, H],
                "faces": [[10, 10, 20, 20, 0.9]],
                "depth": dep.name,
                "depth_stats": {"min": 0.0, "max": 1.0, "mean": 0.5},
                "mean_level": 100.0 + i,
                "clipped_high_px": 0,
                "clipped_low_px": 0,
                "laplacian_var": 50.0 + i,
            }
        )
    pairs = [{"a": i, "b": i + 1, "lab_above_14": 0.25, "lab_above_30": 0.1} for i in range(len(ks) - 1)]
    (out / "readers.json").write_text(json.dumps({"prep": str(prep), "stills": stills, "pairs": pairs}, indent=1))
    print(f"readers: {len(ks)} stills read")


# the angel's locked probe at 960 px (research/2026-11-05/loopseq_a2.md §4), as the fake's numbers
PROBE_DEXP = {"rife": (0.0413, 0.0611, 0.0341), "morph": (0.0233, 0.065, 0.0245), "dissolve": (0.0012, 0.231, 0.0012)}


def cmd_probe(a: argparse.Namespace) -> None:
    prep, out = Path(a.prep_dir), Path(a.out)
    ks = sorted(prep.glob("k*.png"), key=lambda p: int(p.stem[1:]))
    if not (prep / "prep.json").exists() or len(ks) < 2:
        print(f"FAILED: probe: {prep} holds no prep.json with two k<i>.png or more")
        sys.exit(2)
    pairs = [(i, i + 1) for i in range(len(ks) - 1)]
    if a.pairs:
        try:
            pairs = [(int(x), int(y)) for x, y in (p.split(",") for p in a.pairs.split(";") if p.strip())]
        except ValueError:
            pairs = [(-1, -1)]
        if any(not (0 <= i < len(ks) and 0 <= j < len(ks)) or i == j for i, j in pairs):
            print(f"FAILED: probe --pairs: {a.pairs!r} names a still outside 0..{len(ks) - 1}")
            sys.exit(2)
    steer("probe", len(pairs))
    (out / "crops").mkdir(parents=True, exist_ok=True)
    skipped = "no RIFE_MANIFEST.json (the fake's FAKE_NO_RIFE)" if os.environ.get("FAKE_NO_RIFE") else None
    rows = []
    for i, j in pairs:
        for s in (i, j):
            (out / "crops" / f"{i}_{j}_k{s}_face0.jpg").write_bytes(png(16, 16, "c08040"))
        methods: dict[str, object] = {}
        for m, dexps in PROBE_DEXP.items():
            if m == "rife" and skipped:
                continue
            (out / f"probe_{i}_{j}_{m}.jpg").write_bytes(png(W * 3, H, "6080a0"))
            frames = []
            for t, dexp in zip((0.25, 0.5, 0.75), dexps, strict=True):
                crop = f"crops/{i}_{j}_{m}_t{t}_face0.jpg"
                (out / crop).write_bytes(png(16, 16, "a06040"))
                fr: dict[str, object] = {"t": t, "dexp": dexp, "dexp_frame": round(dexp / 2, 4)}
                fr.update(step_a=round(12 * t, 3), step_b=round(12 * (1 - t), 3))
                if m == "rife":
                    fr["seconds"] = 0.01
                fr["crops"] = [crop]
                frames.append(fr)
            entry: dict[str, object] = {"strip": f"probe_{i}_{j}_{m}.jpg"}
            if m == "morph":
                entry["flow"] = "homography+dis"
            entry["frames"] = frames
            methods[m] = entry
        faces = [{"box": [8, 6, 30, 30], "a": [10, 8, 20, 20, 0.9], "b": [11, 8, 20, 20, 0.9]}]
        rows.append({"a": i, "b": j, "matte_share": 0.4751, "faces": faces, "methods": methods})
    probe = {
        "prep": str(prep),
        "long": a.long,
        "size": [W, H],
        "t": [0.25, 0.5, 0.75],
        "matte": {"thr": 14.0, "grow": 0.015, "feather": 0.01, "min_share": 0.0005},
        "rife_version": None if skipped else "fake RIFE",
        "rife_skipped": skipped,
        "faces_model": True,
        "pairs": rows,
        "seconds": 0.01,
        "script_md5": md5(Path(__file__)),
    }
    (out / "probe.json").write_text(json.dumps(probe, indent=1))
    print(json.dumps({"pairs": len(rows), "size": [W, H], "rife_skipped": skipped}))


def cmd_measure(a: argparse.Namespace) -> None:
    import cv2

    mp4, out = Path(a.mp4), Path(a.out)
    if not mp4.is_file():
        print(f"FAILED: measure: no mp4 at {mp4}")
        sys.exit(2)
    cap = cv2.VideoCapture(str(mp4))
    levels: list[float] = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        levels.append(float(f.mean()))
    n = len(levels)
    rows = json.loads(Path(a.frames_json).read_text()) if a.frames_json else None
    if not n or (rows is not None and len(rows) != n):
        print(f"FAILED: measure: {a.frames_json} holds {len(rows or [])} rows for {n} decoded frames")
        sys.exit(2)
    named = parse_windows(a.window, "measure --window")
    if named and not 0 <= a.ref < n:
        print(f"FAILED: measure --ref {a.ref}: the clip has frames 0..{n - 1}")
        sys.exit(2)
    steer("measure", 2)
    steps = [round(abs(levels[i + 1] - levels[i]) / 10, 3) for i in range(n - 1)]
    gen = sum(1 for r in rows if not str(r["generated"]).startswith("none")) if rows is not None else None
    m: dict[str, object] = {
        "mp4": str(mp4),
        "frames_json": a.frames_json,
        "frames": n,
        "fps": 25,
        "canvas": [W, H],
        "seconds": round(n / 25, 3),
        "step_mean": round(sum(steps) / len(steps), 3) if steps else 0.0,
        "step_max": max(steps) if steps else 0.0,
        "step_max_at": steps.index(max(steps)) if steps else 0,
        "seam_step": round(abs(levels[-1] - levels[0]) / 10, 3),
        "steps": steps,
        "faces_per_frame": [1] * n,
        "faces_keyframes": [1] if rows is not None else None,
        "generated_frames": gen,
        "generated_share": round(gen / n, 4) if gen is not None else None,
        "dexp_max": 0.01 if gen else None,
        "rife_seconds_per_frame": 0.0 if gen else None,
        "md5_mp4": md5(mp4),
    }
    if named:
        series, peak = {}, {}
        for k, (name, box) in enumerate(named):
            wave = [math.sin(math.pi * f / max(1, n - 1)) for f in range(n)]
            s = [
                [round(0.3 * (k + 1) * w, 2), round(-4.0 * w * w, 2), round(1.0 - 0.001 * f, 3)]
                for f, w in enumerate(wave)
            ]
            dxs, dys = [abs(v[0]) for v in s], [abs(v[1]) for v in s]
            series[name] = s
            peak[name] = {
                "box": box,
                "dx_max": max(dxs),
                "dx_max_at": dxs.index(max(dxs)),
                "dy_max": max(dys),
                "dy_max_at": dys.index(max(dys)),
                "corr_min": min(v[2] for v in s),
                "edge_frames": [],
            }
        m.update(stability_ref=a.ref, stability_margin=a.margin, stability=series, stability_max=peak)
    m["script_md5"] = md5(Path(__file__))
    out.mkdir(parents=True, exist_ok=True)
    (out / "measure.json").write_text(json.dumps(m, indent=1))
    print(json.dumps({"frames": n, "step_max": m["step_max"], "stability_max": m.get("stability_max")}))


def expand(plan: dict[str, object]) -> list[dict[str, object]]:
    """frames.json's rows for the plan's timeline: holds are photos, rife legs generated, a repaint leg in the real
    script's row shape (`none (repaint)` with u, segment and t; frames_repaint, 2026-11-05), others blends."""
    rows: list[dict[str, object]] = []
    cur = 0
    for si, st in enumerate(plan["timeline"]):
        if "key" in st:
            cur = st["key"]
            rows += [{"step": si, "key": cur, "generated": "none (photo)"} for _ in range(int(st.get("hold", 1)))]
            continue
        n, m = int(st.get("n", 0)), st.get("method", "rife")
        for j in range(n):
            t = round((j + 1) / (n + 1), 4)
            if m == "rife":
                rows.append(
                    {
                        "t": t,
                        "generated": "rife",
                        "matte_share": 1.0,
                        "dexp": 0.01,
                        "seconds": 0.0,
                        "step": si,
                        "from": cur,
                        "to": st["to"],
                        "method": "rife",
                    }
                )
            elif m == "repaint":
                knots = [cur, *[int(k) for k in st.get("through", [])], st["to"]]
                pos = t * (len(knots) - 1)
                seg = min(int(pos), len(knots) - 2)
                rows.append(
                    {
                        "generated": "none (repaint)",
                        "u": t,
                        "segment": [knots[seg], knots[seg + 1]],
                        "t": round(pos - seg, 4),
                        "step": si,
                        "from": cur,
                        "to": st["to"],
                        "method": m,
                    }
                )
            else:
                rows.append({"t": t, "generated": "none (blend)", "step": si, "from": cur, "to": st["to"], "method": m})
        cur = st["to"]
    return rows


def cmd_render(a: argparse.Namespace) -> None:
    import cv2
    import numpy as np

    plan = json.loads(Path(a.plan).read_text())
    for s in a.set or []:
        k, _, v = s.partition("=")
        plan[k] = json.loads(v)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = expand(plan)
    n = len(rows)
    steer("render", n, progress=getattr(a, "progress", False))
    for i in range(n):
        if getattr(a, "progress", False):
            print(f"PROGRESS {i + 1} {n} frames", file=sys.stderr, flush=True)
    # a repaint row's t restarts in each pair, so its level follows u, the leg's own profile
    levels = [40 + 10 * int(r.get("key", 0) or 0) + int(100 * float(r.get("u", r.get("t", 0)) or 0)) for r in rows]
    mp4 = out / "loop.mp4"
    vw = cv2.VideoWriter(str(mp4), cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (W, H))
    for lv in levels:
        vw.write(np.full((H, W, 3), lv, np.uint8))
    vw.release()
    if getattr(a, "progress", False):
        print(f"PROGRESS 0 {n} encode", file=sys.stderr)
        print(f"PROGRESS {n} {n} encode", file=sys.stderr, flush=True)
    (out / "loop.gif").write_bytes(b"GIF89a" + bytes(levels))
    cv2.imwrite(str(out / "sheet.jpg"), np.full((H, W * 2, 3), 90, np.uint8))
    if getattr(a, "frames", False):
        (out / "frames").mkdir(exist_ok=True)
        cap = cv2.VideoCapture(str(mp4))
        i = 0
        while True:
            ok, f = cap.read()
            if not ok:
                break
            cv2.imwrite(str(out / "frames" / f"f{i:04d}.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 90])
            i += 1
    steps = [round(abs(levels[i + 1] - levels[i]) / 10, 3) for i in range(n - 1)]
    gen = sum(1 for r in rows if r["generated"] != "none (photo)" and not str(r["generated"]).startswith("none"))
    measure = {
        "frames": n,
        "fps": a.fps,
        "canvas": [W, H],
        "seconds": round(n / a.fps, 3),
        "render_s": 0.1,
        "step_mean": round(sum(steps) / len(steps), 3) if steps else 0.0,
        "step_max": max(steps) if steps else 0.0,
        "step_max_at": steps.index(max(steps)) if steps else 0,
        "seam_step": round(abs(levels[-1] - levels[0]) / 10, 3),
        "steps": steps,
        "faces_per_frame": [1] * n,
        "faces_keyframes": [1],
        "generated_frames": gen,
        "generated_share": round(gen / n, 4),
        "dexp_max": 0.01 if gen else None,
        "rife_seconds_per_frame": 0.0 if gen else None,
        "md5_mp4": md5(mp4),
        "md5_gif": md5(out / "loop.gif"),
        "gif_bytes": (out / "loop.gif").stat().st_size,
        "mp4_bytes": mp4.stat().st_size,
        "draft": a.draft,
        "plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:16],
        "script_md5": md5(Path(__file__)),
        "rife_version": "fake RIFE" if gen else None,
    }
    (out / "frames.json").write_text(json.dumps(rows, indent=1))
    (out / "plan.json").write_text(json.dumps(plan, indent=1))
    (out / "measure.json").write_text(json.dumps(measure, indent=1))
    if getattr(a, "progress", False):
        print(f"PROGRESS {n} {n} measure", file=sys.stderr, flush=True)
    print(f"render: {n} frames into {out}")


def cmd_page(a: argparse.Namespace) -> None:
    root, out = Path(a.root), Path(a.out)
    steer("page", 1)
    notes = json.loads(Path(a.notes).read_text()) if a.notes else {}
    names = [n.strip() for n in a.variants.split(",") if n.strip()]  # --variants a,b: these, in this order
    for seq in (a.order or "").split(","):
        for n in names:  # checked before anything is written, as the real command does
            if names.count(n) > 1 or not (root / seq / n / "measure.json").exists():
                print(f"FAILED: page --variants: {n} is not a full render of {seq}", flush=True)
                sys.exit(2)
    items = []
    for seq in (a.order or "").split(","):
        base = root / seq
        if not seq or not base.is_dir():
            continue
        found = [v for v in sorted(base.iterdir()) if v.is_dir() and not v.name.endswith(".part")]
        for v in [base / n for n in names] if names else found:
            if (v / "measure.json").exists():
                note = (notes.get(seq) or {}).get(v.name, "")
                items.append(f"<li>{seq}/{v.name} {note}</li>")
        prep = root / "in" / seq
        if prep.is_dir():
            (prep / "keys.jpg").write_bytes(png(W * 2, H, "8080ff"))
    out.write_text(
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{a.title}</title></head><body>"
        f"<h1>{a.title}</h1><p>{a.intro}</p><ul>{''.join(items)}</ul><footer>{a.footer}</footer></body></html>\n"
    )
    print(f"page: {len(items)} candidates into {out}")


def main() -> None:
    desc = (
        "A fake loop_seq.py for the studio's tests. Subcommands: prep, render"
        + ("" if NO_FLAGS else ", readers, probe, measure")
        + ", page."
    )
    ap = argparse.ArgumentParser(prog="loop_seq.py", description=desc)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("seq_dir")
    p.add_argument("--out", required=True)
    p.add_argument("--long", type=int, default=1920)
    p.add_argument("--ref", type=int, default=-1)
    p.add_argument("--cut", default="")
    p.add_argument("--bg-depth", type=float, default=0.0)
    p.add_argument("--depth-blend", default="")
    p.add_argument("--min-inliers", type=int, default=40)
    p.add_argument("--ecc-refine", action="store_true")
    p.add_argument("--depth-maps", action="store_true")
    p.add_argument("--lock-window", default="")
    if not NO_FLAGS:
        p.add_argument("--windows", default="", help="named windows of frame 0, measured, never applied")
    r = sub.add_parser("render")
    r.add_argument("plan")
    r.add_argument("--out", required=True)
    r.add_argument("--fps", type=int, default=25)
    r.add_argument("--draft", type=int, default=0, help="render at this long edge (0 = the prep canvas)")
    r.add_argument("--set", action="append", help="override a top-level plan key: key=<json>")
    if not NO_FLAGS:
        r.add_argument("--progress", action="store_true", help="print `PROGRESS i n phase` lines on stderr")
        r.add_argument("--frames", action="store_true", help="also write OUT/frames/f0000.jpg, ...")
        rd = sub.add_parser("readers")
        rd.add_argument("prep_dir")
        rd.add_argument("--out", default=None)
        pb = sub.add_parser("probe")
        pb.add_argument("prep_dir")
        pb.add_argument("--out", required=True)
        pb.add_argument("--long", type=int, default=960)
        pb.add_argument("--pairs", default="")
        ms = sub.add_parser("measure")
        ms.add_argument("mp4")
        ms.add_argument("--out", required=True)
        ms.add_argument("--frames-json", default=None)
        ms.add_argument("--window", default="")
        ms.add_argument("--ref", type=int, default=0)
        ms.add_argument("--margin", type=int, default=30)
    g = sub.add_parser("page")
    g.add_argument("--root", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--notes", default=None)
    g.add_argument("--order", default="")
    g.add_argument("--title", default="")
    g.add_argument("--intro", default="")
    g.add_argument("--footer", default="")
    g.add_argument("--variants", default="", help="the full renders to list, 'a2,a3', in this order")
    a = ap.parse_args()
    cmds = {"prep": cmd_prep, "render": cmd_render, "readers": cmd_readers, "probe": cmd_probe, "measure": cmd_measure}
    {**cmds, "page": cmd_page}[a.cmd](a)


if __name__ == "__main__":
    main()
