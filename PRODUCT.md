# Product

<!-- impeccable:product-schema 1 -->

<!-- Written 2026-11-04 by the Claude Code session from the owner's orders in DECISIONS.md and the design docs, not from an interview: the owner runs sessions unattended. Every fact marked [inferred] is read from those orders; the owner corrects it in the next session (the handover lists the three init questions). -->

## Platform

web

## Stack

Existing codebase: Python 3.13 in a pinned venv, two single-file tools (`reveal.py`, `transitions.py`) and research scripts under `scripts/research/`; a local HTTP server from the standard library bound to 127.0.0.1, one embedded page in vanilla JavaScript, no build step, no npm, no framework (`AGENTS.md` hard constraints; the 2026-10-20 design `research/2026-10-20/ui_design.md §6`).

## Users

One user: the owner, a software engineer and photographer, on a 27-inch display on a Mac laptop, alone [inferred from the sessions since 2026-09-13]. He grades the output by eye and gives direction in short written notes ("make it 50 % slower", "no breathing", "all ugly except s4"). The Claude Code session is the second operator: it runs the same scripts from the command line, writes plans, runs a skeptic pass, and builds the review pages he grades.

## Product Purpose

Reveal aligns an AFTER photo onto a BEFORE photo and shows the pair behind a comparison slider with exports (the aligner, 2026-07). Transitions renders the change between two photos as a short clip (morph, dissolve, portal, luma; a depth camera; the director's planned beats). The loops render a photo sequence (two to six stills) as a looped clip: registration on a chosen anchor, in-betweens by a frame-interpolation model inside a matte, holds and transitions with per-leg eases, effects (a breath, a depth sway, a bloom), measures, a review page. Success is a clip the owner accepts by his eye: "perfect" (the seasons wipe, 2026-11-01), "all looks good" (the Halloween loops, 2026-10-30).

## Positioning

Every pixel comes from the owner's own photographs; nothing is generated except declared helpers (in-between frames inside a matte, a keyframe on the remote box) under his 2026-09-29 conditions. Every run is reproducible from a plan file plus the renderer's version (md5s recorded), offline on the laptop, and judged by measures on the decoded clip before his eye sees it.

## Operating Context

The owner asks for a transition or a loop in words; the session registers the photos, probes the methods, writes a plan, renders drafts and full clips, runs a skeptic pass, builds a page and opens it; he grades it in words; the next round starts from his words only. Heavy work runs as subprocesses that write files into a run folder (`benchmarks/runs/<date>/…`); the remote Strix Halo box renders diffusion keyframes over SSH (40 s to 30 min each) with a hold file and a pre-flight memory check. The design docs (`.claude/claude-docs/`), the decision log, the playbook (`.claude/skills/reveal/references/loops.md`) and the dated sheets are the record.

## Capabilities and Constraints

- Server on 127.0.0.1 only; the runtime never downloads; originals never modified; B is warped onto A, never the reverse (`AGENTS.md`).
- Neither tool imports the other; the UI imports neither; every heavy call is a subprocess; the job folder on disk is the only state (the 2026-10-20 design, the Fable review of 2026-10-21).
- Models on the laptop, offline behind manifests: DISK+LightGlue (the learned matcher), Depth Anything V2 Small (depth), RIFE v4.26 (in-betweens), YuNet (faces), ViTMatte (mattes), SAM 3 (layers, a scratch venv). On the box: FLUX.2 klein 9B at 8-bit and Qwen image edit (keyframes). No 4-bit quants; licences never a constraint.
- Permanently out (`AGENTS.md`): LoFTR, GPU inference for Reveal, a settings file, ffmpeg xfade, dense residual flow in the alignment output, a pixel-similarity score term, lazy model download at runtime.
- Terminology: a pair (two photos), a sequence (two to six stills), a plan (the JSON that drives a render), a round (one page of candidates and his grades), a candidate (one render on the page), a draft (a 480 or 960 px render), the skeptic (a review pass before the page), a watch (a reproduction check by md5).
- Undecided: whether the UI becomes a third root tool or stays a research script (`ui_design.md §9 Q1`, answered "research script" on 2026-10-21 for phase 1; open for the rebuild).

## Evidence on Hand

Real photo pairs under `fixtures/` (14 catalogued rows in `fixtures/MANIFEST.md`), the owner's own sequences (Halloween, the seasons, the angel portrait) read in place from his folders, every rendered candidate under `benchmarks/runs/<date>/` with its measures, the review pages he graded, his grades verbatim in the dated sheets under `.claude/claude-docs/benchmarks/`. No testimonials, customers, benchmarks against other products, or pricing exist; none may be invented.

## Product Principles

1. His eye grades; measures gate. A render reaches him only after a skeptic pass and a measure on the decoded clip.
2. Everything reproducible: a plan plus a renderer version gives the same md5; every knob rides the plan or the render record, never a hidden default.
3. The honest mechanism beats the clever one: a dissolve in place beat a flight; a registered wipe beat drifting pictures; a locked anchor beat a blended warp.
4. Universal, never overfit: a knob is a general mechanism (a box, an ease, a depth range), not a fix for one photo.
5. Nothing jerky, no flashes, no hard cutouts, natural colour and light.

## Accessibility & Inclusion

One expert user at a desk; keyboard scrubbing of frames and visible focus are required for the review loop [inferred]. No further product-specific requirement was established.
