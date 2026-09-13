# Fixture catalogue — real photo pairs (owner-owned; the ONE list both tools test against)

Photos live in this folder and are gitignored; this file is tracked. Rule: a harness or benchmark
never invents its own real inputs; it reads this table. Add a row when you drop a pair in.
Location decided 2026-09-13 (owner: "gitignored fixtures INSIDE project").

Columns: `id` (stable, never reused) · `before` / `after` (paths relative to this folder) · `mode`
(Reveal mode the pair is for: `reshot` / `loose`) · `class` (expected transitions routing: A related
/ B unrelated) · `exercises` (what the pair proves) · `expected` (dated numbers from the last
verified run: Reveal `method inliers rmse_px confidence`; transitions `class method edge_ratio`).

| id | before | after | mode | class | exercises | expected (dated) |
|---|---|---|---|---|---|---|
| — | — | — | — | — | first entry: the graffiti-box pair of `HANDOFF.md §9.1` (sift, 458 inliers, 0.74 px, box edge 0.54 px RMS on 2026-07-13) | — |

Wanted next (research plan E2): 3 Dnipro box re-shots · 2 cityscape/landscape pairs · 2 day→night
pairs · 3 unrelated pairs (person→sky, box→galaxy, …). HEIC from the iPhone and ARW from the a6700
count double: neither format has ever been decoded from a real file in a test.
