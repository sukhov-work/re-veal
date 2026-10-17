<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (late evening) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/skeptic_r9.md (sha256 753e15191e306332) on the owner's order; folded into `TRANSITIONS.md §13.14`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic r9: the round-9 clips read as the owner will see them

All three clips have at least one fault the owner has already rejected in his own words. On mismatch_5 the sun keeps a hard double rim from 0.5 s to 2.4 s, and the outer two thirds of the streak fade in where they already are. The pane on mismatch_3 is still a flat photo that ends in a brightness-keyed crossfade. On mismatch_2 the yellow man's head sits on the other man's body, and a black void opens at frame 46.

Method: I decoded all 90 frames of each clip with cv2, made contact sheets of every 6th frame at half size, and viewed single frames at full size (mismatch_3 at 1440x1080). I measured the mean absolute difference between consecutive frames ("step", in 8-bit levels) and compared the first and last frames with the photos, scaled to cover the canvas. Times are frame/30.

## Findings: skeptic_r9

### mismatch_5_r9_c1 (sun and bridge into the galaxy)

- [blocks] 0.5–2.4 s. The sun shows two discs, one inside the other. Frame 15 has an inner rim at x 760 and x 1230 inside the outer disc. Frames 30 and 45 show orange crescents left and right of a paler inner disc. At frame 57 the disc is an empty shell: a dark outline, orange crescents and a red arc below it, with the galaxy core showing through. Faint arcs are still visible at frames 66, 69 and 72. He asked for "no hard halo and luma borders around sun", and this is that halo, now lasting 1.9 s. verifiedBy: observed (frames 15, 30, 45, 51, 57, 60, 66, 72).
- [blocks] 1.0–1.7 s. A's sky stays as a dark-red box around the sun. The box has vertical edges (x about 570 and 1370 at frame 45). Red vertical streaks run above the lamp posts at x 680–800, 1180 and 1450–1500, from y 250 to 650. Those are stretched pixel columns that appear in neither photo. He will read this as "2 separate pictures": a cut-out of A over the galaxy. verifiedBy: observed (frames 30, 45, 51).
- [blocks] 1.0–1.7 s. The bridge is two flat slabs with hard rectangular ends. At frame 30 the left ends are at x 165 and the right ends at x 1720, and there is a hole in the truss at x 1420–1490. By frame 45 the deck has turned into a pale beige slab with a straight lower edge at y about 800. In B the dust lane is dark, so the pale slab never becomes the arm. That is "photoshop cutouts" plus content in neither photo. verifiedBy: observed (frames 15, 30, 45, 51).
- [blocks] 2.4–2.7 s. The wire does not become the streak across the galaxy. Through frames 30–57 the wire is a pale horizontal line plus 2–3 separate diagonal fragments, one of which crosses the bridge at frame 45. From frame 60 to 69 only a short segment next to the core remains. The upper-right and lower-left parts of B's streak then fade in at their own positions between frames 72 and 81. That is a crossfade of the streak, which fails his "powerline transformed into that diagonal streak" ask. verifiedBy: observed (frames 30, 45, 57, 60–81 in 3-frame steps).
- [notes] 0.3–0.5 s. A thin lighter border, 30–40 px wide and holding stars, frames A's whole picture: the rectangle of A's frame. verifiedBy: observed (frames 9, 12, 15).
- [notes] 0.5–0.7 s. Stars arrive in A's sky region (y 100–400, x 400–1500) at frames 15–18: 49 star pixels at frame 15 and 450 at frame 18, against about 30 before. At the same frames the sky background rises from 28 to 36 levels. The brightest stars do come first, but only about 0.1 s ahead of the sky change, and before that the only stars are outside A's frame. verifiedBy: observed (frames 9–27, measured).
- [notes] 0.0–0.3 s. The wire turns from a dark line into a pale dotted line within 9 frames, which matches neither photo. Frame 0 is A at 2.5x zoom rather than the whole photo, as in round 8. The last frame matches B (mean difference 2.15 levels). Steps peak at 4.9 with no spike. verifiedBy: observed (frames 0, 9; step list).

Against round 8: worse. In round 8 the sun went soft and small by frame 42 and showed a rim only at frames 18–30. Round 9 keeps a hard double disc from frame 15 to 72. Round 8 replaced the sky with an oval opening (the iris he disliked). Round 9 replaces it with a rectangular box of A's sky with vertical streaks (frames 30–51), which is no better. Round 8's bridge stayed dark into the dust lane (frames 48–54). Round 9's bridge turns into a pale slab (frames 45–51). The stars arrive slightly ahead of the sky in round 9 (frames 15–18), which is a small gain.

### mismatch_3_r9_c1 (bar crowd into the lounge pane)

- [blocks] 0.5–2.5 s. A stays a flat rectangle with a hard left edge and corner from start to finish (x 38 at frame 15, x 85 at frame 21, top-left corner at (285, 95) at frame 42). At frame 64 the crowd and the pines are on top of each other in the pane. This is his "remains 2d plane till the end" note, unchanged. verifiedBy: observed (frames 15, 21, 42, 54, 64).
- [blocks] 2.0–2.5 s. The finish is a crossfade keyed by brightness. Bright trees show through the brick, the wheels become round holes onto the sky (arched holes at frames 64–72), and the crowd is a ghost over the foliage at frame 64. Nothing in A bends into a tree. He asked for A to "subtly transform into trees" and named "very advanced crossfade" as a dislike. verifiedBy: observed (frames 60, 64, 66, 68, 72).
- [blocks] 2.3–2.5 s. The last part of A to leave is a band of brick along the top of the pane, laid over B's hanging sticks. Its lower edge is jagged and stepped, at y 0–190 of frame 72, and the two images are visibly mixed. verifiedBy: observed (frames 66–76, crop of the top).
- [blocks] 0.5–2.0 s, carried over from round 8. B's foreground enters as cut-outs. Magnified skin and shirt pieces form a strip at the bottom (frames 15, 21). Smeared pink fill sits beside the centre man's head and the right man's shoulder (frame 42). Torn green sofa shards cover x 0–460 (frames 42, 48, 54). This is "photoshop cutouts", and the fill is content in neither photo. verifiedBy: observed (frames 15, 21, 42, 48, 54).
- [notes] 1.4–2.0 s. The wheels become silver discs with warped brick reflected in them, which appear in neither photo. The bench rail in front of the crowd is wavy at y 700–780, while it is straight at frame 0. verifiedBy: observed (frames 42, 48, 54).
- [notes] The first and last frames match the photos (2.81 and 3.30 levels). Steps rise to 25.8 at frame 47 from the camera move and fall smoothly, with no isolated spike. verifiedBy: observed (step list).

Against round 8: same. Frames 0–60 differ from round 8 by 1.4–10.9 mean levels but look the same at viewing size, including the same cut-outs and silver wheels at 42–54. Only the end differs. Round 8 dissolved A in 6 frames (78→84). Round 9 replaces A with a crossfade keyed by B's brightness over about 16 frames (60–76), with the crowd and the trees visibly on top of each other.

### mismatch_2_r9_c1 (yellow man into the nearest man)

- [blocks] 1.53 s. A's head, cut out with the yellow collar, floats on B's man's body. A yellow sleeve with its label lies across B's hand. That is a face of a real person put on someone else, and it appears in neither photo; it is the planner's own F3 risk. verifiedBy: observed (frame 46).
- [blocks] 1.47–2.1 s. A black void with no photo content opens: a wedge on the left (x 20–80, y 300–600) and a band along the bottom (y 740–800). Pure-black pixels number 873 at frame 42, 15,169 at frame 48 and 6,952 at frame 60, against 3,849 in B itself. verifiedBy: observed (frames 44–62, measured).
- [blocks] 1.43–1.47 s. The step rises from 7.7 to 13.4 at frame 44, a visible jump. The jacket turns into a translucent yellow film over B's woman's face and hand, so two images are on top of each other. verifiedBy: observed (frames 42, 43, 44; step list).
- [blocks] 0.5–2.4 s. The yellow man is a cut-out on B. At frames 15–21 B's man appears in a vertical slot between the trunk and the jacket, so two men stand side by side (frames 24–42). From frame 48 to 72 the man's outline remains as a hole with a gold rim: B inside, A's bokeh outside. He will read this as "photoshop cutouts" and "2 separate pictures". verifiedBy: observed (frames 15, 21, 24, 42, 48, 54, 60, 66, 72).
- [blocks] The man does not turn. Between frames 24 and 42 he moves down and shrinks slightly. Then he is swapped out at frames 44–51 rather than becoming the other man. His ask, "rotate and gradually transform", is not visible. verifiedBy: observed (frames 24, 30, 36, 42, 46, 51).
- [notes] The trunk slides left and is down to a sliver by frame 24. The last frame matches B (3.21 levels) and frames 84–89 are a still hold (step 0.0). verifiedBy: observed.

Against round 8: there is no round-8 clip of this concept. Round 8's two mismatch_2 clips used other ideas, and I did not compare them frame against frame.

### Claims on the page the frames contradict

- Page head: "Every pixel comes from the two photos; the fill behind B's lifted foreground on mismatch_3 is the one exception". The frames show four more exceptions. mismatch_2 has a black void (frames 44–62) and A's head on B's body (frame 46). mismatch_5 has red vertical streaks (frames 30–45) and a pale beige bridge slab (frames 45–51). mismatch_3 has silver wheels (frames 48–54).
- mismatch_5: "B's brightest stars come through A's sky first (from 0.25 s …)". Stars enter A's sky at frames 15–18 (0.5–0.6 s). Before that, stars show only in the border outside A's frame (frames 9, 12).
- mismatch_5: "A's sky darkens toward space over the first 1.5 s". The sky background in the upper region rises from 28 to 36 levels at frames 15–21 and is still 32 at frame 45, so it gets lighter and browner.
- mismatch_5: "the edge of A's frame is feathered inward … so no rectangle and no iso-line halo". There is a framed border at frames 9–15, a box of A's sky with vertical edges at frames 30–51, and a hard rim on the sun at frames 15–72.
- mismatch_5: "A thin bright-orange ring at the sun's rim between about 1.3 and 2.0 s … softer than before". The rim shows from frame 15 to 72 (0.5–2.4 s). At frame 57 it has a dark outline. Round 8's rim lasted only frames 18–30.
- mismatch_5: "the diagonal line across the galaxy is the wire". The outer parts of the streak fade in at their own positions at frames 72–81. The wire covers only a short segment near the core.
- mismatch_3: "the crowd moves against its brick wall during the pull-back". The crowd-to-flag offset matches round 8 at frames 30 and 48 (the yellow man's head about 140 px left of the flag in both). I saw no parallax at viewing size.
- mismatch_3: "A's darkest parts (the crowd) give way last". The crowd is gone by frame 72. A band of white brick under the ceiling stays until frame 76.
- mismatch_2: "so the transformed man is the last part of A to go". A's face is gone by frame 51, and A's bokeh at the upper right lasts until about frame 72.
- mismatch_2: "the yellow man turns … (about 14 degrees)". No turn is visible between frames 24 and 42. The page's fault list leaves out the black void, the head on the other man's body and the jump at frame 44.

### What works

- mismatch_5: from frame 66 the galaxy core grows out of where the sun was, without a jump. Steps stay at or below 4.9 for the whole clip. The last frame equals B.
- mismatch_5: stars arrive in A's sky about 0.1 s before the sky colour changes (frames 15–18).
- mismatch_3: the pull-back with B's ceiling, dark wall and men around the pane moves smoothly (steps rise and fall with no spike). The first and last frames equal the photos.
- mismatch_2: the trunk leaves to the left by frame 24, and frames 72–89 settle onto B without a jump.

### Confidence

High for the blocks items. Each one is visible at full size in the frames named, and the void and the frame-44 jump are also measured. Medium for the parallax claim on mismatch_3, which I checked by eye on crops of frames 30 and 48 and did not measure. Low for the exact timing of the start of the mismatch_5 ring, because the double rim at frame 15 is thin.

### Gaps

- I did not play the clips at speed. I judged motion from consecutive-frame steps and from frames 3–6 apart.
- I did not check the mismatch_3 note about the quad's top-right corner sitting above the canvas.
- I did not compare mismatch_2 with the round-8 mismatch_2 clips, which used other concepts.
- I did not compare frame 0 of mismatch_5 against a 2.5x crop of A. It looks like A, and round 8 started the same way.
- I did not check the page's per-layer time windows except where a finding names them.
