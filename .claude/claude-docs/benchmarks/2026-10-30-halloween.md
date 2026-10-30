# Halloween loops (2026-10-30): the owner's ten photo sequences as looped clips

Sources: `~/Pictures/halloween 2026/gifs/<seq>/raw/*.jpg` (2–6 developed JPGs per sequence, 2682–6192 px, the ARW and XMP files ignored; read only, never copied). Outputs (gitignored): `benchmarks/runs/2026-10-30/halloween/` (the registered stills under `in/<seq>/`, the candidates under `<seq>/<cN>/`, the page `index.html`, the subagent reports under `agents/`, the round-1 candidates that were rebuilt under `round1/`). Tool: `scripts/research/loop_seq.py` (prep · render · page); plans: `scripts/research/plans/loops/`. Grades: none yet (the page opened in his browser at the end of the session).

## Registration (`loop_seq.py prep`; SIFT + MAGSAC to frame 0, chained SIFT, ECC seeded by the chain, a cut for a frame that cannot be registered)
| seq | stills | canvas frame | methods (inliers or ECC cc) | common crop |
|---|---|---|---|---|
| evgen-npc | 3 | 2 | sift 464, 275 | 1242×1908 |
| evgen-thug | 6 | 1 | sift 75, 72, 86; k4 and k5 cuts (a plain wall; the subject fills the frame; ECC locked onto him: scale 0.78, a masked ECC 0.51) | 1200×1794 |
| group-teleport | 2 | 1 | sift 420 | 1870×1278 |
| group1 | 2 | 0 | sift 443 | 1896×1266 |
| nose | 2 | 0 | sift 141 | 1266×1890 |
| sveta-head | 2 | 1 | sift 93 | 1156×1836 |
| talk | 2 | 0 | sift 265 | 1140×1910 |
| wand | 2 | 0 | sift 99 | 1388×1890 |
| zeke-back | 5 | 1 | sift 89, 175, 181, 181 | 1186×1874 |
| zeke-bite | 2 | 0 | ECC cc 0.56 (the second still is whole-frame motion blur; 8 SIFT inliers) | 1098×1792 |

The camera was handheld: 0.5–3 % shifts and up to 3 % scale between shots (the registration probe on 1200 px proxies, 2026-10-30).

## Round 2 candidates (the page of 2026-10-30, md5 3c69dc169b2b8f9b5bcf073de9f436a2; the talk loop re-rendered byte-identical (mp4 2ecbe778…, gif 94d14d6b…); the other 23 were not re-run)
| seq | cand | frames | s | canvas | methods | effects | generated | dexp max | step mean | step max | seam | md5 mp4 | md5 gif | gif MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| evgen-npc | c1 | 49 | 1.96 | 1242x1908 | rife | breath | 0.429 | 0.0468 | 1.693 | 2.83 | 1.441 | 0110654b | 8eaacea8 | 3.5 |
| evgen-npc | c2 | 49 | 1.96 | 1242x1908 | morph | breath | 0.0 | 0.0 | 1.732 | 3.033 | 1.799 | 456fb6b7 | 57b092e1 | 3.5 |
| evgen-npc | c3 | 28 | 1.12 | 1242x1908 | cut | - | 0.0 | 0.0 | 0.852 | 8.637 | 5.499 | 56defaaa | a6e10b88 | 0.4 |
| evgen-thug | c1 | 57 | 2.28 | 1200x1794 | cut+rife | - | 0.14 | 0.1065 | 3.414 | 51.542 | 49.641 | a7be7f5a | 13f09957 | 1.2 |
| evgen-thug | c2 | 75 | 3.0 | 1200x1794 | cut+rewind+rife | - | 0.107 | 0.1065 | 4.972 | 51.542 | 1.142 | 98f1cf17 | 8a72967d | 1.8 |
| evgen-thug | c3 | 54 | 2.16 | 1200x1794 | cut+rife | - | 0.111 | 0.1065 | 3.58 | 51.541 | 49.642 | 980f9e9b | 444fba29 | 1.1 |
| group-teleport | c1 | 44 | 1.76 | 1870x1278 | cut+teleport | - | 0.0 | 0.0 | 2.754 | 57.128 | 25.599 | 3fb9c81e | 383cc740 | 0.6 |
| group-teleport | c2 | 54 | 2.16 | 1870x1278 | teleport | breath | 0.444 | 0.0471 | 3.306 | 7.676 | 5.635 | f554fa23 | 5b7d71b2 | 5.6 |
| group1 | c1 | 48 | 1.92 | 1896x1266 | rife | breath | 0.5 | 0.0494 | 3.358 | 8.822 | 2.003 | e63e21cd | 372e3066 | 5.0 |
| group1 | c2 | 60 | 2.4 | 1896x1266 | cut | - | 0.0 | 0.0 | 0.48 | 28.066 | 28.065 | 1ceb6739 | 3bc03e09 | 0.3 |
| group1 | c3 | 44 | 1.76 | 1896x1266 | morph | - | 0.0 | 0.0 | 2.407 | 6.516 | 3.416 | 30ec5727 | 16668325 | 2.7 |
| nose | c1 | 33 | 1.32 | 1266x1890 | rife | breath | 0.364 | 0.0408 | 6.046 | 10.055 | 2.524 | 1b41e96a | 9fbc77b9 | 3.1 |
| nose | c2 | 48 | 1.92 | 1266x1890 | rife | - | 0.292 | 0.0397 | 1.003 | 5.78 | 2.245 | 9a398764 | 54d4851d | 1.5 |
| sveta-head | c1 | 36 | 1.44 | 1156x1836 | rife | breath | 0.556 | 0.0423 | 1.888 | 3.106 | 1.4 | c2c6c85e | ec5216dd | 2.6 |
| sveta-head | c2 | 34 | 1.36 | 1156x1836 | rife | - | 0.471 | 0.0418 | 1.298 | 3.633 | 2.375 | 7ba3e417 | 31b94813 | 1.6 |
| talk | c1 | 28 | 1.12 | 1140x1910 | rife | breath | 0.286 | 0.0501 | 2.849 | 5.315 | 1.725 | 74d23241 | 21d132ec | 2.2 |
| talk | c2 | 42 | 1.68 | 1140x1910 | rife | - | 0.405 | 0.0514 | 1.172 | 5.933 | 1.576 | 8722e63b | 9b457ee9 | 1.4 |
| wand | c1 | 28 | 1.12 | 1388x1890 | rife | breath | 0.571 | 0.0311 | 2.768 | 5.073 | 1.501 | ace1f768 | 65e1f81e | 2.5 |
| wand | c2 | 35 | 1.4 | 1388x1890 | rife | - | 0.371 | 0.0319 | 1.235 | 7.799 | 1.448 | 91c89865 | c71594f9 | 1.2 |
| zeke-back | c1 | 78 | 3.12 | 1186x1874 | dissolve+rife | breath | 0.282 | 0.0589 | 1.923 | 8.445 | 9.007 | c9ed26e8 | cf0cc02e | 6.1 |
| zeke-back | c2 | 79 | 3.16 | 1186x1874 | rife+teleport | breath | 0.468 | 0.06 | 2.313 | 9.156 | 1.515 | 7c6e24a9 | 50879418 | 6.1 |
| zeke-back | c3 | 72 | 2.88 | 1186x1874 | cut+rife | - | 0.306 | 0.0589 | 1.261 | 29.631 | 23.783 | 557c2028 | 46fd33fb | 2.0 |
| zeke-bite | c1 | 27 | 1.08 | 1098x1792 | rife | breath | 0.222 | 0.0932 | 6.721 | 24.093 | 8.027 | 1d5328d9 | 49516e9e | 2.4 |
| zeke-bite | c2 | 27 | 1.08 | 1098x1792 | cut | breath | 0.0 | 0.0 | 4.854 | 45.823 | 45.417 | c279cdf5 | 1254aebf | 2.2 |

Round-1 and rebuilt candidates moved to `round1/`: evgen-thug_c1 05ad668f; evgen-thug_c2 bf7d9b1d; evgen-thug_c3_r2 c98df8de; group-teleport_c1 17ae26b6; group-teleport_c1_r2 f451d90d; group-teleport_c1_r2b f451d90d; group-teleport_c1_r2c f451d90d; group-teleport_c1_r2d a124b2e7; talk_c1 2ecbe778; zeke-bite_c1 49856f2b

Columns: generated = the share of frames with RIFE pixels inside the change matte; dexp max = rule 7's double-exposure share (the largest over the generated frames); step = the mean absolute difference between consecutive decoded frames; seam = the last frame against the first (a declared cut back shows as a large seam). Round 1's twelve candidates (page md5 31a2d93b…) went through the skeptic's first pass (`research/2026-10-30/skeptic.md`): 1 READY, 4 READY WITH A NOTE, 7 NOT READY; the five rebuilt in place are under `round1/` with the md5s above, plus the renders replaced after the skeptic's second pass (`evgen-thug_c3_r2` c98df8de…; the teleport c1 four times, f451d90d… twice, a124b2e7…, until the box reached her boots: the person matte's threshold 30 missed the tan boots against the grey floor, 24 reaches them, and the largest-component rule dropped them until parts of at least 2 % were kept).

Skeptic pass 2 (`research/2026-10-30/skeptic2.md`, on the 16 changed or new candidates): READY zeke-back c3, zeke-bite c2, group1 c2, evgen-npc c3, sveta-head c2, nose c2; READY WITH A NOTE evgen-thug c1 and c2 (a yellow tint on his face at frame 12), wand c2 (the hat and handle blended at 11–12, 29–30); NOT READY group-teleport c1 (her boots stayed standing; fixed after the pass as above, not re-judged) and c2 (box rectangles, a doubled boot), evgen-thug c3 (the blur leg's RIFE doubled the pumpkin again; a cut now, not re-judged), zeke-back c2 (the pair doubles at 16–17, 74–75), zeke-bite c1 (one ghost frame per leg), talk c1 and c2 (the wand as two sticks; T63), group1 c3 (as c1). The skeptic did not play any clip at speed.

## Owner grades
(none yet)
