# Fixture catalogue — real photo pairs (owner-owned; the ONE list both tools test against)

Photos live in this folder and are gitignored; this file is tracked. Rule: a harness or benchmark
never invents its own real inputs; it reads this folder by the naming convention below and this
table for expectations. Location decided 2026-09-13 (owner: "gitignored fixtures INSIDE project").

Naming: `<group>_<N>_S.<ext>` is the START (Reveal's BEFORE), `<group>_<N>_F.<ext>` the FINISH
(AFTER); groups `match` (the pair shares at least some content) and `mismatch` (content is far
apart). `scripts/bench_transitions.py` finds pairs by this pattern; add a row here when you add a
pair. Video clips (planned, slice TR4) will use `clip_<N>_S/F.<ext>` once TR4 exists.

Columns: `mode` = the Reveal mode that passes (`reshot` strict; `refused` = strict fails with the
plain message, as it should for unrelated content) · `class` = transitions routing (A related /
B unrelated) · `expected (dated)` = numbers from the last verified run: Reveal `method inliers
rmse_px confidence`; transitions `class method sparse_inliers median_disp_px edge_ratio(morph 1 s)`.
Transitions ran with the canvas capped at 1920 px. Full sheet: `.claude/claude-docs/benchmarks/2026-09-13-real-pairs.md`.

| id | before | after | mode | class | exercises | expected (2026-09-13, M3 Pro, OpenCV 5.0.0) |
|---|---|---|---|---|---|---|
| match_1 | match_1_S.HEIC | match_1_F.HEIC | reshot | A | first real HEIC (iPhone, 6048×8064, ICC profile, 1.9 s decode); a person re-posed in the same spot: non-rigid subject, 64 px median displacement | Reveal sift 368 · 0.74 px · 95. Transitions A homography+dis · 492 · 63.7 px · 0.23 |
| match_2 | match_2_S.jpg | match_2_F.jpg | reshot | A | restaurant interior, a person moved a lot (141 px), 1196×2560 phone crop | Reveal sift 913 · 1.01 px · 90. Transitions A · 899 · 140.8 px · 0.12 |
| match_3 | match_3_S.jpg | match_3_F.jpg | reshot | A | lake and domed building behind a person; no EXIF orientation tag; ECC returned no rho and the feature H was kept | Reveal sift 1059 · 1.0 px · 90 (ecc_rho None). Transitions A · 986 · 38.5 px · 0.12 |
| match_4 | match_4_S.jpg | match_4_F.jpg | reshot | A | **the graffiti-box → mural pair of `HANDOFF.md §9.1`** (the roster anchor); different pixel sizes (1960×2450 vs 2149×2686) | Reveal sift 481 · 0.79 px · 94, rho 0.946 (sandbox 2026-07-13: 458 · 0.74). Transitions A · 295 · 15.1 px · 0.24 |
| match_5 | match_5_S.jpg | match_5_F.jpg | reshot | A | grey utility boxes → painted; EXIF orientation 6 on S; 52 % of the frame changed; low certainty 0.33 | Reveal sift 121 · 0.67 px · 97. Transitions A · 73 · 103.5 px · 0.17 |
| mismatch_1 | mismatch_1_S.jpg | mismatch_1_F.jpg | refused | B | two skies over the same city, different clouds and light | Reveal refuses (10 sparse inliers). Transitions B saliency-similarity · 10 · 320.8 px · 0.17 |
| mismatch_2 | mismatch_2_S.jpg | mismatch_2_F.jpg | refused | B | a man in a yellow jacket vs a group of people; the smallest pair (canvas 730×800) | Reveal refuses. Transitions B · 6 · 239.4 px · 0.20 |
| mismatch_3 | mismatch_3_S.jpg | mismatch_3_F.jpg | refused | B | a crowded bar vs a lounge group; 889 px median displacement from the saliency boxes | Reveal refuses. Transitions B · 6 · 889.2 px · 0.31 |
| mismatch_4 | mismatch_4_S.jpg | mismatch_4_F.jpg | refused | B | sunset over water → sunset over water: the sun-to-sun case | Reveal refuses. Transitions B · 9 · 269.3 px · 0.25 |
| mismatch_5 | mismatch_5_S.jpg | mismatch_5_F.jpg | refused | B | portrait sunset (4128×6192) → landscape galaxy (3840×2160): the sun-to-galaxy case; the portrait is cover-cropped to 1920×1080 | Reveal refuses. Transitions B · 36 · 367.9 px · 0.26 |
| mismatch_6 | mismatch_6_S.jpg | mismatch_6_F.jpg | refused | B | day → night: a day sky over the city (1146×1528) → a night sky with stars and a tree (3056×4064); the research plan's day→night category; canvas is the small start frame | Reveal refuses. Transitions B · 0 · 232.2 px · 0.52 |
| mismatch_7 | mismatch_7_S.jpg | mismatch_7_F.png | reshot | A | the same city skyline under different skies, portrait vs landscape PNG; owner (2026-09-14): "very roughly match , it is same part of the city but taken in completely different conditions , camera settings , zoom etc ( i.e. it was never intended to be aligned , and this is the point )"; strict passes at 78 inliers and transitions route A with mean certainty 0.053, the clouds tear in the morph — the case slice TR2b exists for | Reveal sift 78 · 0.89 px · 92 (ecc_rho None). Transitions A homography+dis · 70 · 249.9 px · 0.26 |

Wanted next (research plan E2): 2 cityscape/landscape re-shots · one more day→night pair · DNG and ARW
files (never decoded from a real file in a test) · video clips for slice TR4.
