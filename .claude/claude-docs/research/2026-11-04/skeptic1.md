<!-- Provenance: written by an Opus 5.5 subagent (the skeptic, pass 1) of the Claude Code session of 2026-11-04 (the angel portrait loop; DECISIONS 2026-11-04); copied verbatim from benchmarks/runs/2026-11-04/angel/agents/skeptic1.md (sha256 fcbb2c896a7a4026) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). The pass on the round-1a renders a1–a3 (the far-field registration): the ring 7.9 px off at its top (the main thread's probe windows had sat off the ring), the teeth dissolving through closed lips, a1's whole-frame stall at frames 24–26, a3's glow box ending mid-ring, the sources refocused between the shots; a2 READY WITH A NOTE, a3 and a1 NOT READY. Four fixes followed (the lock on the ring, the RIFE margin, the mouth's local ease, the glow box) and the five candidates were re-rendered as round 1b. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: skeptic (pass 1)

All boxes are canvas pixels (x0,y0,x1,y1) on the 1334×1722 frame. Frames are the decoded loop.mp4 frames, 0–49. "Levels" are 8-bit grey levels. Crops are in `agents/skeptic/`.

### Verdicts (one line per candidate: verdict · the deciding defect · frame · box · number)
- **a2: READY WITH A NOTE**: the left woman's teeth fade in through her closed lips; the lips do not part. All three share it. f17–22 up, f42–46 back. (375,945,515,1010). Teeth at 37/48/58 % of final brightness at f18/19/20, visible through the lip.
- **a3: NOT READY**: the glow brightens only the left two-thirds of the ring. The glow box ends at x=560; the ring spans x≈108–754. f16–34. wall left of the ring (180,580,240,620) +7 levels at f25, right arc and wall right of the ring (690,580,820,620) +0. fix: widen the box to x 3–60 %.
- **a1: NOT READY**: the whole frame stops dead at the end of the up-move. Whole-frame step: 2.00 → 0.05 → 0.14 levels across f23→24→25→26. measure.json steps[24]=0.06 and steps[25]=0.17: a stall below 0.3 while frames 24–25 are still generated. a2 and a3 hide it because the sway is at full speed there (1.00 at the same step).
- **Rank for the page:** a2, a3, a1. a2 has no stall and no lopsided glow. a3 is a2 plus a lopsided glow that is faint (+3 levels mean in its box). a1's stall is a whole-frame stop.

### Defects (one bullet each: candidate · frame(s) · box · what · number · the crop file)
- all. f17–22 and f42–46. left mouth (375,945,515,1010). RIFE dissolves the teeth in rather than opening the lips; at f19 and f44 a half-transparent tooth row sits over the closed lower lip. Teeth mask (1,119 px): 33/37/48/58/70/78 % of final at f17–22 (a2). Back: 67/54/39/27 % at f42–45. `a2_mouthL-teeth_f19.jpg`, `a2_mouthL_f0-26.jpg`, `a2_mouthL_f41-49.jpg`.
- all. every loop, f14–26 and f38–49. whole frame. focus shift between the two source photos: the near field sharpens 3–4× and the far field halves. Laplacian variance k0→k1: cookie 248→956, right eyes 78→185, couch 420→1249, lamp arm 61→30, exit sign 16→8. The halo rim goes soft while the faces go crisp. Fix: none in the pipeline; it is in the source pair. `a2-a3_ringrim-focus_f0-30.jpg`, `a1-a2-a3_lamparc_f0-44.jpg`.
- all. f14→26 and f38→0. ring top arc (380,360,620,470). the halo is not static. The ring's top outer edge is 7.9 px higher in k1 than in k0 (y 395.5 vs 387.6 at x=475; 5–10 px along x 350–650). With the breath the top arc travels 12.1 px (395.5 → 383.4 at f25). The lamp arm moves 1.4 px, so the ring moves against its own arm. visibility at speed UNVERIFIED. `keys_ringtop-k0-k1_f0-26.jpg`, `a2-a3_ringrim-focus_f0-30.jpg`.
- all. f15→16 and f24→25, f48→49→0. subjects. RIFE does not follow the sine ease: motion starts late and lands in one frame. Left mouth step 0.4 → 3.2 px at f15→16 and 2.1 → 0.0 px at f24→25. Left fingers 1.4 → 0.0 px; left eyes 1.7 → 0.1 px at f48→49. a small landing tick, UNVERIFIED at speed. fix: re-time the in-between t from measured displacement, not from the ease.
- a3. f16–34. glow box (40,378,560,861). lopsided bloom (deciding defect above). wall inside the ring +4.5 levels mean, +24 max at f25; ring rim minimum lifted 98 → 108 levels at x=475 f25 (a slight haze on the rim). `a3_glow-heat-vs-a2_f22-28.jpg`, `a2-a3_glow_f0-30.jpg`.
- a1, a2, a3. k0 hold f1–13 and k1 hold f26–37. couch (560,860,760,1060). texture sharpness flutters frame to frame under the breath resample. Laplacian variance 426, 361, 337, 316, 350, 356, 363, 322, 369 at a1 f1–9 (±8–15 %). In the k1 hold: 816 → 982 at f29→30 (+20 %). no moiré seen in 3× crops; shimmer at speed UNVERIFIED. `a1_couch-k0hold_f7-9.jpg`, `a1_couch-hold_f29.jpg`.
- all. f19–25. flyaway hairs left of the left woman's head (180,620,360,820). thin strands cross-fade, a few appear doubled at f20. low contrast, minor. `a2_hairwall_f0-44.jpg`.
- a2, a3. f12 vs f37. laptop (300–1334, 1380–1722). the sway is uneven along the laptop. Left end 6.3 / −5.7 px, right end 5.1 / −10.9 px (a1→a2 phase correlation). a shear of about 0.3°, UNVERIFIED as visible; no stretched band at the laptop edge or the phone in `a1-a2_laptop-phone-edge_f12-37.jpg`.

### Clean (what you checked and found clean, in one line each)
- Cookie faces, both: no doubled or smeared features at f18–21, 26 (`a2_cookieL_f0-26.jpg`, `a2_cookieR_f0-26.jpg`).
- Left woman's raised fingers and the right woman's green-nail hand: no extra or merged fingers at f18–21, 26, 43, 44 (`a2_fingersL_f0-44.jpg`, `a2_handR_f0-44.jpg`).
- Right woman's mouth and teeth: teeth already visible in k0, no smear (`a2_mouthR_f0-44.jpg`).
- Both pairs of eyes: no doubled iris or lid (`a2_eyesL_f0-44.jpg`, `a2_eyesR_f0-44.jpg`).
- Earring: one stud and one ball in every checked frame (`a2_earring_f0-44.jpg`).
- Left woman's hair edge against the ring: no halo line or doubled edge (`a1-a2-a3_hairring_f0-44.jpg`).
- Ring left arc: outer edge x moves 221.2 → 219.7 → 221.2 px over the loop, under 1.6 px in all three; lamp arm under 1.4 px.
- Mirror lower edge and exit sign: smooth travel (exit sign ~14 px, set by the 1.8 % breath), no tearing (`a2_exitsign_f0-44.jpg`).
- Phone in her lap and laptop top edge under a2/a3 sway: no stretched or smeared band (`a1-a2_phone_f0-44.jpg`, `a1-a2_laptop_f12-37.jpg`).
- a3 glow in time: it rises from 0 to +3.07 levels mean over 18 frames and falls back, no flash. No hard edge at the box's right side (+2.05 → +1.67 across x 552–565) or bottom side (about 0).
- Jumps: no step exceeds 3× both neighbours in any measure.json series (largest ratio 1.7, at f14→15).

### Measures (the step series facts, the seam, the faces)
- measure.json whole-frame steps: a1 mean 1.94, max 3.79 at index 43; a2 mean 2.04, max 3.73 at 43; a3 mean 2.04, max 3.77 at 43.
- Stall: a1 steps[24]=0.06 and [25]=0.17, both below 0.3 while frames 24 and 25 are still generated (t 0.94, 0.99). a2 and a3 read 1.05 and 1.08 there. a1 steps[0]=0.06 is the breath starting from rest at the k0 hold, expected.
- Seam (49→0): a1 1.23, a2 1.48, a3 1.48 (measure.json); my whole-frame MAD 48→49 / 49→0 / 0→1 = 0.92 / 1.02 / 0.06 (a1), 1.03 / 1.30 / 0.85 (a2 and a3). No jump; the left cookie lands 1.7 → 0.1 px per frame, the same landing tick as above.
- Faces (YuNet, threshold 0.6): both women's faces found in every checked frame at score 0.93–0.94. Count changes come from the cookies: the left cookie drops out at f20 (0.83 at f0 → 0.69 → absent → 0.69); the right cookie appears only at f0 of a3 (0.61). The 2×-scale crops show no doubled cookie features.
- Correction to the brief: the ring's top arc differs between k0 and k1 by 7.9 px, not 0.4 px; its left arc by 0.6 px, not 2.2 px.
- RIFE double-exposure share (dexp in frames.json) peaks at 0.024 (f19 up, f44 back), the same frames as the teeth dissolve.

### Confidence: 70%

### Gaps (what you could not judge; "not played at speed" goes here)
- Not played at speed: every motion judgement (teeth dissolve, landing tick, couch flutter, ring travel, glow asymmetry) comes from still crops and numbers. Whether each one reads at 25 fps on a 27-inch display is UNVERIFIED.
- loop.gif not inspected; only loop.mp4 was decoded.
- Phase correlation fails on regions whose content changes (e.g. left mouth at f19 returned 197.9 px); I used consecutive-frame steps and edge profiles there instead.
- The a2/a3 sway on the textureless wall and the black laptop body could not be measured by optical flow (reads 0); the laptop figure comes from phase correlation on its edge.
- Couch shimmer judged from 3× crops of k1-hold frames 26–31 and k0-hold frames 7–9 only.
- The no-slop cold read by a fresh reader was not run.
