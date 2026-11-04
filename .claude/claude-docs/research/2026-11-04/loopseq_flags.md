<!-- Provenance: written by an Opus 5.5 subagent (the four default-off additions to scripts/research/loop_seq.py for the studio: render --progress, --frames, script_md5 and rife_version in measure.json, the readers command; the byte-identity proof on a2 and s6) of the Claude Code session of 2026-11-04 (the studio phase A1 build; DECISIONS 2026-11-04 sixth line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/loopseq_flags.md (sha256 ce643ccd82e86d50) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: loop_seq flags

### Key facts
- The mp4 bytes do not depend on the flags. a2 gave c302623f293eacd069218fd7518e0967 and s6 gave 5908af3d5300046579548848679b0cbb, with and without them: `md5_mp4` in each `measure.json`, and `md5 -q loop.mp4`.
- Without the flags the render's stderr is unchanged. The plain a2 stderr equals, line for line with the seconds masked, the HEAD script's stderr in /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/watch/a2_first.log: `diff` printed nothing.
- With `--progress`, stderr gains `PROGRESS` lines and nothing else. With those lines removed, the a2 and s6 stderr equal the plain runs' stderr: `diff` printed nothing.
- The `frames/` JPEGs hold the decoded mp4. a2's decoded frames 0, 25 and 49, re-encoded at quality 90 by `cv2.imencode`, are byte-equal to `f0000.jpg`, `f0025.jpg` and `f0049.jpg`.
- The Lab share in `readers` reproduces the session's 19.6 % on the session's input: 0.1964 above 14 and 0.0666 above 30 on the unlocked prep that /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/angel/work/intake.py read, with the same formula.
- The recorded prep reads 0.3021 because the ring lock moves k1. Both preps hold the same SIFT fit (467 inliers of 751 matches), and the lock adds a shift of (−4.93, +11.48) px: `frames[1]` of the two `prep.json` files.
- Under that lock, k1's exit sign sits 27.1 px from its place in k0 and the left face 23.0 px: `.claude/claude-docs/benchmarks/2026-11-04-angel.md:29`.
- The task's ring window (x 422–582, y 371–441) is in frame-0 pixels before the crop. It is the first lock window in the recorded `prep.json`, and the canvas crop starts at x 29.
- On the canvas the same window is x 393–553. Its ring pixels (grey above 235, 6,630 of 11,200) read depth 0.1408, and the wall above the arc reads 0.0953: numpy on `depth_k0.npy`.
- `readers` computes a missing depth map byte-identical to the one `prep` saved: md5 be5f197b14139379a68bf778378f7203 (k0) and abc016300ed337e4e653cba82599b08f (k1) for both, and `np.array_equal` True.
- YuNet's third face on k0 (box 616, 1087, 114 × 114, score 0.758) is the cartoon face printed on a cookie, checked by eye on a crop. YuNet misses it on the locked k1, which reads 2 faces.

### What changed
| file:line | symbol | the change |
|---|---|---|
| `scripts/research/loop_seq.py:19–45` | module docstring | `render` lists `[--progress] [--frames]` and the two new `measure.json` keys; a `readers` paragraph follows |
| `loop_seq.py:90–113` | `_PROG`, `progress`, `tick`, `replan` | the module-level switch and frame counter; `progress` prints only when `cmd_render` turned the switch on |
| `loop_seq.py:466–471` | `_rife_version` | the RIFE manifest's `model` string when `_RIFE.net` is loaded, else `None` |
| `loop_seq.py:512`, `:547` | `frames_rife`, `frames_chain` | `tick` after each in-between, one `frames` line each |
| `loop_seq.py:557`, `:571–575`, `:935`, `:1109`, `:1324` | `frames_dissolve`, `frames_morph`, `frames_snap`, `frames_slices`, `frames_sheets` | `tick` with a line every 10th frame; `frames_morph`'s list comprehension became a loop over the same frames |
| `loop_seq.py:1051` | `frames_slices` | `replan` swaps the plan's `n` for the schedule's count before the first frame |
| `loop_seq.py:1342`, `:1412`, `:1433` | `apply_breath`, `apply_camera`, `apply_glow` | an `effects` line every 10th frame |
| `loop_seq.py:1438–1598` | `render_plan` | the `frames_jpg` keyword (`:1438`); the planned total (`:1454`); the counter re-synced after every step (`:1461`, `:1503`); `replan` for `rewind` (`:1497`); the `encode` lines (`:1532`, `:1550`); the two keys (`:1588`); the JPEGs (`:1592–1597`); the `measure` line (`:1598`) |
| `loop_seq.py:1604–1609` | `cmd_render` | sets the switch from `--progress` and passes `--frames` |
| `loop_seq.py:1614–1664` | `_lab_distance`, `cmd_readers` | the new command; `change_matte` is unchanged (the helper repeats its three lines) |
| `loop_seq.py:1765–1778` | `main` | `--progress` and `--frames` on `render`; the `readers` parser with its description |
| `scripts/research/plans/loops/SCHEMA.md:46–48`, `:138–174` | the outputs paragraph; a new last section | the two keys and `frames/`; the flags, the `PROGRESS` phases and the fields of `readers.json` |

### Proof
The four renders ran one at a time after `CHAIN_DONE` appeared, with the script at md5 eba20856bdccd17bbfedde0d7ae17b08, the `script_md5` that each `measure.json` records. Commands, from the repository root:
1. `.venv/bin/python scripts/research/loop_seq.py render scripts/research/plans/loops/angel_a2.json --out /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/a2_flags --progress --frames`
2. `.venv/bin/python scripts/research/loop_seq.py render scripts/research/plans/loops/seasons_s6.json --out /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/s6_flags --progress --frames`
3. `.venv/bin/python scripts/research/loop_seq.py render scripts/research/plans/loops/angel_a2.json --out /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/a2_plain`
4. `.venv/bin/python scripts/research/loop_seq.py render scripts/research/plans/loops/seasons_s6.json --out /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/s6_plain`

| render | md5_mp4 | recorded | exit, wall | `grep -c PROGRESS` on stderr (frames / effects / encode / measure) | `frames/` |
|---|---|---|---|---|---|
| 1. a2, both flags | c302623f293eacd069218fd7518e0967 | c302623f… | 0, 76 s | 32 (24 / 5 / 2 / 1) | 50 JPEGs, f0000–f0049 |
| 2. s6, both flags | 5908af3d5300046579548848679b0cbb | 5908af3d… | 0, 91 s | 16 (13 / 0 / 2 / 1) | 164 JPEGs, f0000–f0163, 182 MB |
| 3. a2, no flags | c302623f293eacd069218fd7518e0967 | c302623f… | 0, 64 s | 0 | absent (`ls`: no such file) |
| 4. s6, no flags | 5908af3d5300046579548848679b0cbb | 5908af3d… | 0, 88 s | 0 | absent (`ls`: no such file) |

- All four `measure.json` files hold `script_md5` eba20856bdccd17bbfedde0d7ae17b08. `rife_version` is "Practical-RIFE v4.26 (zip RIFEv4.26_0921; RIFE_HDv3.py inside says version 4.25)" in both a2 runs and null in both s6 runs.
- Between each flagged render and its plain twin, `measure.json` differs only in `render_s`, plus `rife_seconds_per_frame` for a2. a2's `frames.json` differs only in the per-frame RIFE `seconds`.
- a2's `frames` lines run 15/50 to 26/50, then 39/50 to 50/50. s6's run 40/165 to 160/165: 165 planned, 164 rendered.
- `loop_seq.py render --help` lists `--progress` and `--frames` with their text. `loop_seq.py readers --help` prints the description and both arguments, and `loop_seq.py --help` prints the new docstring lines.

`readers` ran on a copy of `benchmarks/runs/2026-11-04/angel/in/angel/` (`k0.png`, `k1.png`, `prep.json`, `depth_k0.npy`, `depth_k1.npy`): `.venv/bin/python scripts/research/loop_seq.py readers /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/angel_prep` printed `{"stills": 2, "faces": [3, 2], "lab_above_14": [0.3021]}`, exit 0, 1 s. The five copied files kept their md5s.

| measure | value | expected | match |
|---|---|---|---|
| Lab above 14 (above 30), the recorded locked prep | 0.3021 (0.1343) | 0.196 | no: the ring lock moves k1 by (−4.93, +11.48) px |
| Lab above 14 (above 30), `readers` on /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/subject_prep, a copy of the unlocked prep | 0.1964 (0.0666) | 0.196 (6.7 %) | yes |
| depth mean in x 422–582, y 371–441, read as canvas pixels | 0.1184 | 0.14–0.16 | no: the window is in frame-0 pixels, and 42 % of it is darker than grey 235 (the wall) |
| depth mean in x 393–553, y 371–441, the same window on the canvas | 0.1222; ring pixels 0.1408 | 0.14–0.16 | the ring pixels: yes |
| maps that `readers` computed in /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/angel_prep_nodepth, a copy without them | `np.array_equal` True against the recorded maps | equal | yes |

Per still of the recorded prep, k0 holds 3 faces, depth mean 0.269, grey mean 109.6, 0 pixels above 250, 287,417 below 5 and Laplacian variance 51.6. k1 holds 2 faces, 0.287, 115.3, 40,645, 285,583 and 73.3.

Five more renders, beyond the task, ran with `--progress --draft 480`, one at a time, and all exited 0:

| plan | methods | `frames` lines | `effects` lines | planned total, then frames rendered |
|---|---|---|---|---|
| zeke-back_c2, snaps set to n 12 in a scratch copy | snap, `through` | 38 | 0 | 85, 85 |
| evgen-thug_c2 | `through`, `rewind` | 36 | 0 | 64, then 85 after the rewind; 85 |
| zeke-back | dissolve, rife, breath | 23 | 7 | 78, 78 |
| evgen-npc_c2, morphs set to n 12 in a scratch copy | morph, breath | 3 | 6 | 64, 64 |
| seasons_c1 | three `slices` steps | 9 | 0 | 90, 123, 156, 189; 189 |

The morph plan gave md5 83169f6e23c6f6b2141a16d9b932af5a under the new script and under /private/tmp/claude-501/-Users-yevhens-Projects-personal-reveal-1-5-0/f9495174-91eb-4fda-b938-997caac0ae17/scratchpad/flags/loop_seq_head.py, the HEAD copy run through `exec` under the repository path. `find -newer` over `benchmarks/runs/2026-11-04/angel`, `benchmarks/runs/2026-11-01/seasons` and `benchmarks/runs/2026-10-30/halloween/in` printed nothing, so no recorded folder was written.

### Confidence: 92%
The four md5s, the stderr diffs and the JPEG byte check are direct measurements. The remaining 8 % covers the paths no render exercised, listed below.

### Gaps
- `teleport`, `slide` and `rise` print no `frames` line inside their step, because the contract does not list them; the next line counts their frames. No plan uses `rise`, and I rendered no `teleport` or `slide` plan.
- For s6, I compared the stderr without the flags with the new script's flagged run only. The comparison with the HEAD script's stderr exists for a2 alone.
- `readers` ran only on two-still preps. A prep of three or more stills (several pairs) and a prep whose stills differ in size (which exits) were not run.
- The task's ring window reads 0.1184 on the canvas, below 0.14–0.16. I did not change the window; only the ring's own pixels in the converted window read inside the range (0.1408).
- A render without `--frames` into a folder that already holds `frames/` leaves the old JPEGs in place.
- The planned total runs one frame high per `sheets` step (s6: 165 planned, 164 rendered), so the studio must treat `n` as an estimate.
- I ran none of `harness.py`, `transitions_harness.py`, `reveal.py check` or `transitions.py check`. Neither tool changed, and the main session's chain ran them before my edit.
