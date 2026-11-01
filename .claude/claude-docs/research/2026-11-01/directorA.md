<!-- Provenance: written by an Opus 5.5 subagent (director track A) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01); copied verbatim from benchmarks/runs/2026-11-01/seasons/directorA/report.md (sha256 718d08e51d9fba89) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). One alternative plan (the barcode: unequal bands from the centre, a random fine shuffle at −62°, the bands closing from the edges), drafted at 640 px and reproduced by md5; rendered at full size as candidate c8 by the main thread. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: directorA

### The plan
Saved as `benchmarks/runs/2026-11-01/seasons/directorA/plan_directorA.json`; draft render in `directorA/barcode/`, repeat render in `directorA/barcode_repro/`.

```json
{
 "seq": "seasons",
 "in": "benchmarks/runs/2026-11-01/seasons/in/seasons",
 "title": "barcode: unequal bands in a 3-1-1-2-1-3-1-2-1-1-3 rhythm zip in from the centre at 62 deg; 22 thin bands at -62 deg shuffle in at random; the barcode closes from the edges onto summer",
 "gag": "Three seasons from one balcony in Ivano-Frankivsk (his order: 1 summer, 2 early autumn, 3 late autumn). Diagonal cards slide the next season into place; every border lands on the registered pixels, so the city continues across each cut.",
 "timeline": [
  {
   "key": 0,
   "hold": 28
  },
  {
   "method": "slices",
   "slide": "across",
   "samples": 8,
   "shutter": 1.0,
   "to": 1,
   "angle": 62,
   "widths": [
    3,
    1,
    1,
    2,
    1,
    3,
    1,
    2,
    1,
    1,
    3
   ],
   "order": "centre",
   "alternate": true,
   "dir": 1,
   "dur": 22,
   "stagger": 2,
   "ease": "smooth"
  },
  {
   "key": 1,
   "hold": 26
  },
  {
   "method": "slices",
   "slide": "across",
   "samples": 8,
   "shutter": 1.0,
   "to": 2,
   "angle": -62,
   "bands": 22,
   "order": "random",
   "seed": 3,
   "alternate": true,
   "dir": -1,
   "dur": 10,
   "stagger": 1,
   "ease": "smooth"
  },
  {
   "key": 2,
   "hold": 26
  },
  {
   "method": "slices",
   "slide": "across",
   "samples": 8,
   "shutter": 1.0,
   "to": 0,
   "angle": 62,
   "widths": [
    3,
    1,
    1,
    2,
    1,
    3,
    1,
    2,
    1,
    1,
    3
   ],
   "order": "edges",
   "alternate": true,
   "dir": 1,
   "dur": 22,
   "stagger": 2,
   "ease": "snap"
  }
 ],
 "crf": 14,
 "gif_long": 540
}
```

### Why
The idea: 11 bands of unequal width in a symmetric 3-1-1-2-1-3-1-2-1-1-3 rhythm zip summer to early autumn from the centre at 62° over 31 frames, 22 thin bands at -62° shuffle early autumn to late autumn at random over 30 frames, and the same unequal bands close from both edges onto summer under the `snap` ease over 31 frames.
No round-1 plan uses `widths`, `order` random or a negative angle, and every round-1 slices plan (c1–c6) repeats one geometry on all three legs, where this one changes geometry and tempo per leg (c2 also zips from the centre, but over 14 equal bands).
The owner should look at whether the slow wide-band legs and the fast random leg read as one rhythm or as two styles, at the wire's small jogs on the -62° borders, and at the thin light strip about 4 frames before the loop wraps.

### Evidence
- Measure line (640×484 draft): 172 frames, 6.88 s, step_mean 1.765, step_max 9.493 at frame 159, seam_step 1.854, generated_share 0.0. Round-1 drafts at the same size: c1 1.41 / 6.58 / 1.87, c3 1.48 / 8.38 / 1.82, c4 5.26 / 24.12 / 2.38, c6 2.27 / 15.91 / 2.39 (step_mean / step_max / seam).
- Peak card displacement per frame, from `frames.json` `disp_px` at 640 px: leg 1 8.5 px, leg 2 5.3 px, leg 3 12.7 px. That is about 25–38 px per frame at the full 1878 px width, by linear scaling [INFERRED].
- md5 of loop.mp4: `ae00ca7efc503862eb3f260b0189e709` in both `barcode/` and `barcode_repro/`, so the draft reproduces exactly.
- I read every frame on the contact sheet and decoded frames 44, 100, 154 and 168 at 640 px (`directorA/v3_frames.png`), plus a crop of the wire in leg-2 frames 86, 92 and 98 at 2× (`directorA/v1_wire.png`, from v1, which has the same leg-2 parameters as the pick).
  - Borders: they land on the registered pixels; mid-slide cards show the next still shifted across the band, as in c1.
  - Wire: at -62° it shows small clean kinks where it crosses a card border, and I saw no doubled copy (v1 frames 86, 92, 98; leg 2 has the same parameters in the pick, but its frame numbers there are 8 higher). At 62° the wide cards carry a wire segment that sits clearly offset until the card lands (v1 frame 38, with 4-unit outer bands).
  - Fog streaks: in leg 2 (frame 100) the cards carry the fog still, and its bright-sky-to-dark-ground gradient shifted along the diagonal reads as grey streaks. In leg 3 (frame 154) the moving cards carry summer over the fog base, and the blurred leading edges average fog and summer across the band. Every `across` slide into or out of the fog still does this; I did not try to remove it.
  - Mirrored content: the reflect padding puts mirrored content at the entering edge of a card (a mirrored blue sky patch in the clouds, v1 frame 38). This is the same mechanism as c1–c6.
  - Blur: the wide bands are heavily smeared at peak speed (frames 44, 154). The leaves are unreadable mid-slide, though the content still moves in the slide direction.
  - Landing: in frame 168, about 4 frames before the loop wraps, one thin bright strip of the fog still is left on the summer frame. It is the last part of the centre band still in flight, and the owner may read it as a light line crossing the sky. The step into frame 0 is 1.85, inside the round-1 draft range (1.82–2.39).

### Rejected variants
- v1 (outer bands 4 units wide, dur 14 on the wide-band legs): peak card speed 16–18 px per frame at 640 px and step_max 10.47. The 4-wide sky cards smeared into bright bars.
- v2 (outer bands 3 units, dur 22, `decel` landing): peak speed fell to 8.5–11.1 px, but the seam step was 2.79, because the centre band was still moving at the wrap.
- v3 is the pick: v2 with a `snap` ease on the closing leg, which brought the seam step to 1.85.

### Confidence: 60%
The mechanics are measured: no generated pixels, a reproducible md5, and a seam step inside the round-1 range. Whether the tempo contrast reads as "cool and trippy" to the owner is a matter of taste, and I could not judge it from stills.

### Gaps
- This is not the brief's "coarse bands then a fine split on the same season": the fine leg is a separate transition between two other stills.
- I did not play the clip at speed. Flicker in the random leg and the effect of the landing sliver are UNVERIFIED in motion.
- 640 px hides the fine borders, the 1 px soft edges and the wire's thickness. At full size the wide cards travel about 3× as many pixels per frame, and the blur sample count rises with them (capped by `samples_max` 48).
- Only seed 3 was tried for the random order; another seed may spread the shuffle more evenly.
- No full-resolution render was made, and none of the clip is graded.
