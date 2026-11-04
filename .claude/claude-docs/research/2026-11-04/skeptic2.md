<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 2) of the Claude Code session of 2026-11-04 (the angel portrait loop; DECISIONS 2026-11-04); copied verbatim from benchmarks/runs/2026-11-04/angel/agents/skeptic2.md (sha256 a7a1d861673ac7e3) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The pass on the round-1b renders a1–a5 (the ring-locked registration, the RIFE margin, the mouth's local ease, the full glow box): a2, a3, a5, a4 READY WITH A NOTE, a1 NOT READY (a one-frame stall as the breath peaks into the hold); the teeth fade shortened to 1–2 frames; the ring's rise at the peak 4.2–4.8 px, of which 2.2–2.4 the zoom and 1.7 the second still's ring; the far field's 16–21 px drift carried by RIFE without a tear. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: skeptic (pass 2)

Second pass on the re-rendered a1–a5 (canvas 1366×1770). Boxes are canvas pixels (x0,y0,x1,y1); frames are decoded loop.mp4 frames. "Levels" are 8-bit grey levels. Crops are in `agents/skeptic/`, named `<cand>2_…`; `a22_` means a2, pass 2.

### Verdicts (one line per candidate: verdict · the deciding defect · frame · box · number)
- **a2: READY WITH A NOTE**. Deciding note: the left woman's teeth still show half-transparent for 1–2 frames each way (f19 up; f43–44 back). Box (380,935,560,1015). The fade is now 2–3 frames long; it was 6 in pass 1. No other defect beyond the ones all five share.
- **a3: READY WITH A NOTE**. Deciding note: the glow lifts the ring's dark rim from 98 to 109 levels at f25 (x=511, y 370–420). It also brightens the right woman's hair edge next to the ring by +8 levels mean (box 745,560,800,720). It rises and falls with the breath; no flash, no hard edge.
- **a5: READY WITH A NOTE**. Deciding note: the depth push is barely measurable. Against a3 it zooms the hands and hoodie +0.19 % and the couch −0.27 % at f31 (≈1–2 px). The ring grows 1.10 % at the peak against a3's 1.55 %. No stretched band at the laptop or phone.
- **a4: READY WITH A NOTE**. Deciding note: the seam step is 1.20 against neighbours 0.55 and 0.49 (2.2×, under the 3× jump threshold). The teeth are half-transparent for 3–4 frames each way (f21–23, f62–65). 70 of 84 frames are generated.
- **a1: NOT READY**. The stall is still there: measure.json steps[25]=0.24 (f25→26). It comes right after 1.35, while frame 25 is still generated (t 0.947). Pass 1 read 0.06 and 0.17. a2–a5 read 1.03–1.07 at the same step because their sway is moving.
- **Rank for the page:** a2, a3, a5, a4, a1. a3 and a5 look alike by the numbers (a5−a3 under 0.5 px of flow in most regions); a3 ranks first because it is the simpler recipe. a4's slower tempo halves the peak step (2.21 against 4.0) but doubles the half-open-teeth frames; at-speed viewing could reorder a4.

### Defects (one bullet each: candidate · frame(s) · box · what · number · the crop file)
- all. Up f19, back f43–44 (a4: f21–23, f62–65). Left mouth (380,935,560,1015). RIFE still fades the teeth in through closed lips. The `snap` ease shortened the half state to 2–3 frames (a4: 3–4). `a22_mouthbox_f0-26.jpg`, `a22_mouthbox_f39-48.jpg`, `a42_mouth_f19-66.jpg`.
- all. f42–46. Left cheek outline against the couch (550,880,650,980). In k1 a hair lock lies over the cheek edge; k0 has none. RIFE dissolves the lock, so the hair is half-transparent at f44–46. The traced outline jogs 9–12 px at y 914–926 in f42–44. The 4× crop shows the lock fading, with no break at the mouth box's top edge (y=920). `a22_cheek-boxtop_f42-46.jpg`, `a22_mouthbox-cheek_f19-46.jpg`.
- all. Every loop. Whole frame. The source photos are focused differently (pass 1 finding, still present). The near field sharpens and the far field softens between k0 and k1. The pipeline cannot fix it; it is in the photo pair.
- all. Holds f1–13 and f26–37. Couch (580,880,780,1040). Texture sharpness still flutters under the breath resample. Laplacian variance on a1 f1–9: 434, 374, 351, 311, 363, 362, 330, 336, 381 (±8–12 %). No moiré in crops; shimmer at speed UNVERIFIED. `a22_couch_f0-44.jpg`.
- a3, a5. f12–37. Glow box (184,336,835,864). The glow is uneven: wall left of the ring +6.0 levels, wall right +2.8, inside the ring +4.9 at f25. The rim lifts 11 levels; the right woman's hair edge lifts +8 mean, +16 at p95. It reads as light spill, UNVERIFIED at speed. `a32_glow-heat-vs-a2_f22-28.jpg`, `a2-a3-a52_hairring_f0-25.jpg`.
- a4. f83→0. Whole frame. The seam step (1.20) is 2.2× both neighbours (0.55 at f82→83, 0.49 at f0→1). The likely cause is the 4 % margin: the last in-between stops at t≈0.96, and frame 0 covers the rest in one step. In a1–a3 and a5 the same jump hides inside faster neighbours.

### Clean (what you checked and found clean, in one line each)
- Mouth box edges (x 355–560, y 920–1044, a2 f15–24 and f39–48): no shear, doubled lip corner, or cheek or scarf smear in the crops. Flow across the edges never exceeds the k0→k1 difference except where the hair lock dissolves (above).
- Cookie faces, left woman's raised fingers, right woman's green-nail hand at a2 f19–21, 43–44 and a4 every 4th frame: no doubled features (`a22_cookies_f0-44.jpg`, `a22_hands_f0-44.jpg`, `a42_cookies-hands_f8-80.jpg`).
- Both pairs of eyes at a2 f19–21, 43–44: no doubled iris or lid (`a22_eyes_f0-44.jpg`).
- Far-field drift (exit sign about 21 px down by f26; mirror edge 16–21 px): the sign keeps five dark bands that step 2–4 px per frame, never splitting. The mirror edge and couch fabric show no tear or double (`a22_exitsign_f0-44.jpg`, `a22_mirror_f0-44.jpg`, `a22_couch_f0-44.jpg`).
- Hair edge against the ring in a2, a3, a5 at f25: no halo line or doubled edge (`a2-a3-a52_hairring_f0-25.jpg`).
- a5 laptop top edge and phone at f20, 25, 30: no stretched or smeared band (`a3-a52_laptop-phone_f0-30.jpg`). The strongest flow gradient between a3 and a5 sits on the black laptop face (x≈840, y≈1495).
- Glow box edges (a3): no hard step. +1.6 → +0.6 levels across x 820–850, +0.6 → +0.4 across y 850–880.
- No stall in a2–a5 and no step above 3× both neighbours in any candidate (largest ratio 1.12 in a1–a3 and a5, 2.19 in a4).

### Measures (the step series facts, the seam, the faces)
- Whole-frame steps (measure.json): a1 mean 2.00, max 4.01 at 19; a2 2.10 / 4.09 at 43; a3 2.11 / 4.14 at 43; a5 2.07 / 4.13 at 43; a4 1.30 / 2.21 at 21.
- Steps below 0.3: a1 at 0 (breath from rest, expected) and 25 (the stall); a2–a5 none.
- Seam step (measure.json): a1 1.31, a2 1.54, a3 1.53, a4 1.20, a5 1.53.
- Ring top (edge at x=511, y 330–470) against frame 0: it rises at most 4.4 px (a1), 4.7 (a2), 4.8 (a3), 4.7 (a4) and 4.2 (a5) at f25–26 (a4 f36–44). The zoom measured from the ring's width (left and right arcs at y=548) explains 2.2–2.4 px of that. The remaining 2.0–2.5 px (max 2.52, a4 f36) is not zoom. Of it, 1.7 px is k1's ring sitting higher than k0's (y 396.5 against 394.8); 0.3–0.8 px is left for RIFE. The ring centre moves sideways at most 1.26 px (a1), 1.64 (a2), 1.59 (a3), 1.98 (a4) and 1.54 (a5); k0→k1 accounts for 0.95 px.
- Ring zoom at the peak: a1 1.55 %, a2 1.50 %, a3 1.57 %, a4 1.53 %, a5 1.10 %. The ring's width differs 0.2 % between the stills, so the true breath is about 0.2 % more.
- Faces (measure.json, YuNet): 3 in every frame of all five candidates; no frame drops a face.
- RIFE double-exposure share (dexp) peaks at 0.031 in a1–a3 and a5, and at 0.0314 in a4.

### Confidence: 70%

### Gaps (what you could not judge; "not played at speed" goes here)
- Not played at speed. The teeth fade, the hair-lock dissolve, couch flutter, glow and a4's seam bump are judged from still crops and numbers only. Whether each one shows at 25 fps on a 27-inch display is UNVERIFIED.
- Optical flow and the cheek-outline trace are confused by moving hair strands. The mouth-box shear call rests on the 4× crops, not on a number.
- a5's zoom on the textureless laptop face could not be measured; the hand and hoodie value stands in for it.
- I did not check a4's cookies and hands at 2× or larger; I checked every 4th frame at 0.75×.
- loop.gif was not inspected. The no-slop cold read by a fresh reader was not run.
