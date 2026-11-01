<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 3) of the Claude Code session of 2026-11-01 (the seasons loop; DECISIONS 2026-11-01); copied verbatim from benchmarks/runs/2026-11-01/seasons/agents/skeptic3.md (sha256 bde38d17c31b53a5) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The pass on the round-2b renders (now under round2b/): no mirrored pixel in s2–s4, the corners clean, the gap milder; the sheets' travel was computed on the full canvas so the crop hid the slow ends of the ease (motion only over frames 46–103, 61 still frames instead of 30); s1's shadow floated where its picture had no pixels and its picture edges were hard; s2, s3, s4 READY WITH A NOTE, s1 NOT READY. Three fixes followed (the travel over the visible crop, the shadow masked by the casting pixel's validity, a 24 px soft picture edge; plus lead 4 and a fourth object for s4) and the set was re-rendered and judged in pass 4. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic pass 3: seasons loop, round 2b (2026-11-01)

s2 is the strongest of the four, and s1 is not ready. In all four clips the sheets stay outside the visible frame until about frame 46 and are gone again by frame 103. That leaves 61 of 119 frames of still summer instead of the planned 30, and the sine ease runs off-screen. I judged frames decoded from each mp4 at 1:1 and 2× (plus a 15-frame contact sheet per clip) and did not play the clips at speed. Crops are in `agents/skeptic3_crops/`. Numbers come from `measure.json`, `frames.json`, or a per-frame difference against the centre of `k0` (offset 440, 333). On held frames it is 2.6 grey levels (codec floor).

## The five changes in the brief

| Change | Result | Evidence |
|---|---|---|
| 1. No mirrored or foreign pixels | Holds for s2–s4. **Fails for s1**: its pictures show hard, axis-aligned rectangle edges with no shadow on them, and the contact shadow floats in summer's sky where no sheet content exists. | `s1_f056_leadedge_1x.png`, `s1_f081_left_1x.png`, `s*_overview.jpg`. Border scan: at most 415 of 9,272 edge pixels per frame are flagged, which is noise level. No strip is visible. |
| 2. Corners at f29–31 and f117–118 | All four show 0 change. The corner patches (300 px) match frame 0 exactly: bottom-left 4.7/4.9, top-right 3.5. The output is identical to summer from f0 to f44 and from f104 to f118 (changed share 0.002). | stats per frame |
| 3. Gap between the fronts before the crossing | In s2–s4 at f56–f60, a strip of summer sky about 360 px wide (horizontally) separates the fronts. Its left side is darkened by the front sheet's shadow (the 10–90 % ramp spans 136 px on row 200), so the strip reads slightly as a shaded tube; milder than pass 2's dark band (the "rod"). | `s2_f060_gap_1x.png`, `s4_f060_gap_1x.png` |
| 4. s3 blur amount | At f60 (edge speed 122 px per frame), the 10–90 % edge width is 8 px in s3 against 4 px in s2. A building corner at the front edge smears into a soft ghost about 20 px long. There is no comb on the wire at f74. | `s2_vs_s3_f060_edge_2x.png`, `s3_f074_wire_1x.png` |
| 5. s4 objects at full size | No seam or halo. The 40 px ring outside each box stays at the 3.8–4.7 floor while the inside changes. The tower matte is clean (0.2 % of its vegetation changed). The house matte spills onto foliage in front of the house (11.9 % of vegetation pixels change by more than 15 levels at f93). At 1:1 the effect is barely visible. Only 135 of the apartments' 570 px of width fall inside the output. | `s4_f093_vs_k0_tower_house_1x.png`, `s4_f093_diffmap_x4_tower_house.png`, `s4_apartments_f47_f50_f101_f106_k0_1x.png` |

## Shared defect: the motion is confined to f46–f103

The sheets start at f30, with a displacement of about 3,921 px (s2–s4) or 4,356 px (s1), but no pixel in the output changes before f44–f46. At that point the edge already moves 70–90 px per frame (`edge_px` 70.5 at f44, 82.4 at f47). The exit is the same: the last change is at f102–f103, at about 80 px per frame. The slow ends of the sine ease therefore fall outside the crop: each sheet enters and leaves at speed, and summer stands still for 61 frames (f0–f45, f104–f118; 2.4 s of 4.76 s).

[INFERRED] At speed this may read as summer, then a fast swipe, then summer again, and the entry may look abrupt. I could not confirm this because I did not play the clips.

## s1 cross (carry 1, width "photo", front opaque): NOT READY

| Check | Frames | Result |
|---|---|---|
| Three sliding at once, all three on one frame | f56–f67, f81–f90 | Yes, but as rectangles. At the crossing (f74) early autumn covers 96 % of the frame, and late autumn is under 1 %. |
| Alignment on borders | all but f74 | Not aligned by design: at f56 early autumn's clouds sit against summer's skyline (`s1_f056_leadedge_1x.png`). |
| Shadow | f56 | A grey shadow about 70 px wide runs from the top of the frame down to the picture's corner, over summer's sky, with nothing casting it. |
| Picture edges | f56, f81 | Hard horizontal and vertical cuts with no feather and no shadow. Late autumn's fog is cut against early autumn at x≈490 and against summer's sky at y≈160 (`s1_f081_left_1x.png`). |
| Steps | f47 | 0.11 → 2.22 (20×) when the pictures appear. |

Defects:
- Floating shadow at f52–f60 (high).
- Rectangular hard edges throughout, the "hard cutouts … cheap 2d" he rejected (high).
- Borders misaligned except at f74 (high, by design).

First knob: `width` "photo" → 0.8. [INFERRED] That keeps the band inside its picture, so no rectangle edge shows, and the shadow then has something to come from.

## s2 drift with depth (carry 0.12, parallax 0.06, overlap 0.5, no blur): READY WITH A NOTE

| Check | Frames | Result |
|---|---|---|
| Three sliding, all three on one frame | f52–f62, f88–f95 | Yes. At f56 the shares are summer 0.46, early autumn 0.04, late autumn 0.11 (matched pixels). |
| Crossing | f64–f85 | Early and late autumn mixed at half opacity. Summer's share is 0.01. |
| Edges | f60 | The edge is 4 px and clean. Building and sky continue into the fog sheet (`s2_f060_gap_1x.png`). |
| Steps | f44–f103 | Smooth rise (0.06, 0.29, 0.69, 1.22 …), maximum 13.8 at f60, no jump above 3× outside the crossing. Seam 0.746. |

Defects:
- Visible motion only f46–f103, with 61 still frames (medium; shared).
- The shaded gap strip at f56–f60 (low).

First knob: `shadow_px` 60 → 30 to thin the tube look at the gap. The tempo fix is code, not a knob (see the two changes below).

## s3 drift with depth and blur (as s2, shutter 0.1): READY WITH A NOTE

Same mechanism, coverage and steps as s2 (maximum 13.7 at f59, seam 0.750).

| Check | Frames | Result |
|---|---|---|
| Blur | f60 | Edge 8 px against 4 px in s2. A building corner at the sheet edge smears into a ghost of about 20 px. |
| Wire | f74 | Single, slightly soft, no comb. |

Defects:
- The same tempo problem as s2 (medium).
- The smear is visible at 2× ([INFERRED] it reads as speed, not damage).

First knob: the same as s2 (`shadow_px` 60 → 30); keep `shutter` at 0.1.

## s4 wipe with objects (carry 0, overlap 0.5, three mattes): READY WITH A NOTE

| Check | Frames | Result |
|---|---|---|
| Three on one frame | f52–f62, f88–f95 | Yes. At f60 the shares are summer 0.07, early autumn 0.46, late autumn 0.45, and every border is aligned. |
| Objects before a sheet | apartments f49–f50 | Inside the box the difference goes 4.3 → 6.7 → 11.0 while the ring stays at 4.2. The colour change is a 2-frame step (alpha 0 → 0.5 → 1.0). No visible colour cast at 1:1 at f50. |
| Objects after a sheet | tower and house f89–f99, apartments f98–f111 | A monotone fade: the tower goes 15.1 → 4.8 against a ring of 3.8. No seam. |
| Matte shape | f93 | The tower takes only the building. The house matte also takes foliage in front (11.9 %). |
| Visibility | f93 | At 1:1 the tower and house are hard to tell from summer, which is "very subtly", perhaps too subtle. |

Defects:
- The house matte spills onto foliage (low).
- The apartments are 76 % outside the frame, so one of three objects barely shows (medium).
- The entry is a 2-frame switch while the exit is a 12-frame fade (low).
- The same tempo problem (medium).
- [INFERRED] With the content static, the pictures do not travel. He may read it as a wipe rather than "move … slide past each other".

First knob: `lead` 2 → 6, so the entry is a fade like the exit. Replace the apartments box with an object inside the centre 75 % (that is a plan change, not a knob).

## Ranking (confidence that he calls it what he asked for)

1. s2: the pictures slide with depth drift, all three meet, and the edges are clean.
2. s3: same as s2, with visible but plausible blur.
3. s4: every border aligned and the mattes clean, but the content does not travel and the objects barely show.
4. s1: rectangular cuts, a floating shadow, misaligned borders.

## The two changes to make first

1. Compute the sheets' start and end displacement from the output crop, not the 3,522 px canvas. Each sheet then enters as a sliver under the slow end of the ease at f30 and leaves by f118, and the still part drops from 61 frames to the planned 30.
2. s1: cut the band inside the carried picture (`width` 0.8), or mask the shadow by the validity mask. A shadow must never be drawn where its sheet has no pixels.

## What I could not determine

- Motion at playback speed (judder, whether the fast entry reads as jerky); not played.
- The gif against the mp4 (timing, sky palette); not opened.
- The depth parallax in s2/s3 as a separate effect from the drift. I did not isolate the near tree against the skyline.
- Whether the 2-frame object switch in s4 is visible at speed.
