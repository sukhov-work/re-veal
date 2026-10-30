<!-- Provenance: written by an Opus 5.5 subagent (director track B) of the Claude Code session of 2026-10-30 (the Halloween loops; DECISIONS 2026-10-30); copied verbatim from benchmarks/runs/2026-10-30/halloween/agents/directorB.md (sha256 8e64c2bfc7fa777b) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). Director track B on wand, group1, evgen-npc, sveta-head, nose: one alternative plan each, drafted at 640 px; the doubled mask in group1 c1; the odd-width draft bug. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy except where TRANSITIONS.md §13.24 says so. -->

# directorB: wand, group1, evgen-npc, sveta-head, nose (2026-10-30)

Five alternative plans were written and rendered as 640 px drafts. Four of them drop the breath effect, and two use no generated pixels at all. The c1 version of group1 has real doubled content: in generated frame 41, viewed at full size, the silver mask is visible twice. The YuNet count of 11–13 faces also fluctuates on held frames, which is detector noise. All drafts live under `agents/directorB/<seq>_<cN>/` (loop.mp4, loop.gif, sheet.jpg, measure.json) and the plans under `agents/directorB/plans/`.

Tool defect: `loop_seq.py render --draft 640` crashes in libx264 on 4 of the 5 sequences, because the draft width comes out odd (nose 1266x1890 scales to 429x640). `_scale_to` rounds each side to the nearest pixel and does not force even sides. I did not edit the script. Instead I rendered through `agents/directorB/scratch/render_even.py`, which imports `loop_seq` and replaces `_scale_to` with a version that floors each side to an even number (at most 1 px narrower). wand_c2 went through the unmodified script, since 470 px is already even. The full-size render uses the canvas size, which prep already made even, so it should be unaffected (UNVERIFIED).

## nose
- **c1 verdict:** the twitch does not read. The 2 % breath sets the step series: the step peaks at 10.06 on frame 8, which is a held frame, so the zoom is the only thing moving there. The zoom also makes the curtain mesh shimmer as moire. The change between the stills is visible: in k0 his head tilts to his right, in k1 to his left, and the grin moves with it.
- **c2 gag:** a metronome head waggle. Tick, tock, tick, then a hold and a settle.
- **c2 timeline:** k0 ×14 · →k1 rife n3 snap · k1 ×4 · →k0 rife n3 snap · k0 ×4 · →k1 rife n3 snap · k1 ×12 · →k0 rife n5 smooth. No breath. 48 frames, 1.92 s.
- **Paths:** plan `agents/directorB/plans/nose_c2.json`, draft `agents/directorB/nose_c2/`.
- **Measures:** step mean 0.41 (c1 6.05), step max 2.48 at frame 22, seam step 1.56, generated 29 %, double exposure max 0.071 (c1 0.041; the middle frame of each 3-frame snap carries most of the change), faces 1 on every frame.
- **Look at:** frames 14–16, 21–23 and 28–30, the three head flips. Does each flip read as one snap, or as a blend? In the 640 px crop of frames 13–17 I saw no doubled face.
- **Hand-read values:** none.

## wand
- **c1 verdict:** the tug reads, but 8 even generated frames each way with 6-frame holds make it a symmetric wobble. The breath adds nothing.
- **c2 gag:** the spell lands. A 3-frame jab blows him back, he holds the recoil, then creeps back slowly.
- **c2 timeline:** k0 ×10 · →k1 rife n3 accel · k1 ×12 · →k0 rife n10 smooth. No breath. 35 frames, 1.4 s.
- **Paths:** plan `agents/directorB/plans/wand_c2.json`, draft `agents/directorB/wand_c2/`.
- **Measures:** step mean 1.13, step max 7.09 at frame 12 (the jab), seam step 1.22, generated 37 %, double exposure max 0.035, faces 2.
- **Look at:** frames 11–12. Her witch hat is a RIFE blend of two hat poses there, and in frame 11 the wand shows faintly twice. At 40 ms per frame this may pass as motion blur; at full size it may read as a ghost. Also look at the 10-frame creep back (frames 23–32).
- **Hand-read values:** none.

## group1
- **c1 verdict:** the c1 version doubles content. At full size, generated frame 41 shows the silver mask (bottom left, around x 640–700, y 590–630 in canvas px) twice, and YuNet finds two faces on it, at (640, 628) and (669, 593). Frame 17 shows the red pitchfork half transparent, and in frame 41 the girl's gloved hand over her face is translucent.
- **Face-count fluctuation:** on held frames, which are untouched stills under the breath zoom, the count still moves between 11 and 13. Frame 2 has 13 faces: an extra detection at (416, 194) with score 0.68, and a second box on the mask, also on a real still. So the 11–13 spread is YuNet noise plus breath resampling, while the doubled mask in frames 37–45 is a real artefact.
- **Size of the change:** the two stills differ a lot. Mean absolute difference is 28.1 levels, and 27 % of pixels differ by more than 25 levels. RIFE has 14 people moving at once to interpolate.
- **c2 gag:** spot the difference. The two burst frames alternate with declared hard cuts: the eyeball becomes a lit pumpkin, a pitchfork appears, the girl hides her face. No in-betweens and no breath, so every frame is one of his two stills, byte-exact at draft scale.
- **c2 timeline:** k0 ×30 · cut · k1 ×30 · cut back (declared seam). 60 frames, 2.4 s. The first iteration used holds of 20 (1.6 s); I lengthened them to 30 because 0.8 s is too short to find the changes across 14 people.
- **Paths:** plan `agents/directorB/plans/group1_c2.json`, draft `agents/directorB/group1_c2/`.
- **Measures:** step mean 0.46, cut step 27.01 at frame 29 and at the seam, generated 0 %, double exposure 0.
- **Look at:** the brightness pop at each cut. The background brightness at the frame edges goes from 121 to 133 gray levels (k0 to k1), with a shift of 0.11 px (phase correlation). It may read as a camera flash, which fits a burst, or as a glitch.
- **Hand-read values:** none.

## evgen-npc
- **c1 and c2 verdict:** both read as an idle cycle. In the hand and pumpkin crops of frames 13, 28 and 45, RIFE (c1) and the morph (c2) are indistinguishable at 0.55x; the hand holds a carving knife, and it stays clean in both. c2 has one defect: frame 45 shows a kink in the vertical glass edge right of his head, a morph warp of the background. I prefer c1 over c2 for that reason. The gestures are small (mean absolute difference between stills 5.4–8.6), so a 7-frame smooth leg makes them mushy.
- **c3 gag:** a 2000s-game NPC sprite. Hard cuts between the three poses at about 3.6 poses per second, ping-pong k0-k1-k2-k1.
- **c3 timeline:** k0 ×7 · cut · k1 ×7 · cut · k2 ×7 · cut · k1 ×7 · cut back to k0. No breath. 28 frames, 1.12 s.
- **Paths:** plan `agents/directorB/plans/evgen-npc_c3.json`, draft `agents/directorB/evgen-npc_c3/`.
- **Measures:** step mean 0.76, step max 7.76 at frame 13, seam step 4.73, generated 0 %. Background at the cuts: shift 0.06–0.47 px (phase correlation on the area outside x 0.2–0.75), exposure change ≤1.7 levels, background absolute step 4.4, which is noise and texture, not drift.
- **Look at:** whether the sprite rhythm reads as a joke or as stutter. The brief's floor for a loop is 1 s; 1.12 s is just above it. If it feels too fast, raise the holds to 9 (1.44 s).
- **Hand-read values:** none.

## sveta-head
- **c1 verdict:** a gentle, even sway over 10 generated frames each way. It is clean but flat; the change is small (mean absolute difference 8.0, 5 % of pixels above 25 levels).
- **c2 gag:** a dashboard bobble-witch. Two quick bobs of her head and wand, then a rest.
- **c2 timeline:** k0 ×12 · →k1 rife n4 · k1 ×2 · →k0 rife n4 · k0 ×2 · →k1 rife n4 · k1 ×2 · →k0 rife n4, all smooth. No breath. 34 frames, 1.36 s.
- **Paths:** plan `agents/directorB/plans/sveta-head_c2.json`, draft `agents/directorB/sveta-head_c2/`.
- **Measures:** step mean 1.02, step max 3.06 at frame 13, seam step 1.44, generated 47 %, double exposure max 0.051, faces 1.
- **Look at:** the hat brim and the wand tip in frames 13–15 and 29–31. In the 640 px crop, frames 12–16 showed one hat and one wand.
- **Hand-read values:** none.

## Gaps
- **Breath on held frames:** the breath effect warps every frame after frame 0, so with a breath no held frame is byte-exact. That conflicts with the rule "The endpoints of every leg are his stills, byte-exact". All c1 clips with a breath have this; my c2 and c3 plans set no breath.
- **The draft crash:** the even-size wrapper is a workaround outside `scripts/`. The proper fix is `_scale_to` in `loop_seq.py`, for the main thread to make.
- **Viewing:** I judged generated frames from 640 px crops and sheets. Only the group1 c1 frames were checked at full size, and I did not watch any gif in motion.
- **wand_c2 at full size:** the hat blend in frames 11–12 is unverified at full size.
- **Box and anchor readings:** none of the plans needed one, so there are no ±px readings.

## Confidence
- High that the c1 group1 version doubles the mask and that the face-count spread is mostly YuNet noise.
- High that the nose breath swamps the waggle.
- Medium on the two cut-only plans (group1_c2, evgen-npc_c3): their quality is guaranteed by construction, but whether the owner finds them funny is a taste call.
- Medium-low on wand_c2, because of the hat blend in the 3-frame jab.
