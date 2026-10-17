<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (evening) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/skeptic_r8.md (sha256 0ef670836a358ee1) on the owner's order; folded into `TRANSITIONS.md §13.11`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: skeptic_r8

Scope: the six round-8 director clips under `benchmarks/runs/2026-10-17/director/`, all 90 frames at 30 fps (3.0 s each). I decoded every frame with cv2, looked at contact sheets of every 6th frame and at full- or half-size frames where a fault showed, computed the mean absolute step between consecutive frames, and registered frame 0 against A and frame 89 against B with SIFT and a homography. Frame numbers are 0-based; time = frame / 30.

Ends, all clips: frame 89 equals B as a cover crop (mean residual 2.1 to 4.6 levels after registration, codec level). Frame 0 is a cover crop of A: mismatch_3 loses 50 px per side of 2020; mismatch_2 loses 64 px per side of 730 (17.5 % of A's width); mismatch_5 shows 1080 of the 2875 rows A occupies on the canvas (37 %), so the water and the top of the sky are never on screen.

### mismatch_5_c1
- [blocks] 0.8–1.3 s — two sun discs at once: a large disc with a dark rim, and inside it a smaller disc with its own limb offset to the right, then a soft outer ring around the shrinking disc — "very advanced crossfade", the "two suns" the planner itself flagged as F1 — verifiedBy: observed (frames 24, 27, 33, 39; full-res crop of frames 24 and 39)
- [blocks] 0.4–1.6 s — the truss is three hard-edged slabs with the piers removed; the galaxy shows through the gaps and below them, and the slabs fly across the galaxy as flat cards; their girders look vertically stretched at frame 33 — "photoshop cutouts", "moving it as cheap 2d cutout" — verifiedBy: observed (frames 6, 12, 18, 27, 33, 39, 45)
- [blocks] 1.6–2.4 s — after the slabs the truss becomes torn translucent patches with wavy, polygonal hard outlines over the dust lane, including a pale rectangle with a straight left edge at frame 54 — "2d mixup/melt" — verifiedBy: observed (frames 51, 54, 57, 60, 66, 72; crop x 300–1300, y 350–850)
- [blocks] 0.6–1.7 s — a strip of the bridge (railing, a car roof, two lamp posts, a horizontal rail line) stays inside the bottom of the sun disc and rides with it as it shrinks; a dark sliver of it is still visible at frame 51 — content from one layer pasted into another; he will read it as a cut-out stuck to the sun — verifiedBy: observed (frames 24, 33, 39, 45, 51; full-res crops)
- [blocks] 0.4–2.4 s — the deck never becomes the streak. B's own bright satellite streak is on screen from frame 12, running parallel to the deck and offset from it, while the deck is a separate dark bar (grey and translucent from frame 51) with a square-cut, motion-smeared right end. Two lines run side by side until about frame 72 — "nothing happens to the bridge" in a new form: the deck is moved as a 2-D bar, not transformed — verifiedBy: observed (frames 12, 18, 27, 33, 39, 45, 51, 57, 66, 72)
- [notes] 0.2–0.4 s — a dark elliptical halo of about 700 px radius around the sun in the sky, the edge of the sky key; the deck's right end fades to black — "harsh transitions and borders" — verifiedBy: observed (frames 6, 12)
- [notes] 0.6 s — the grey lamp-post ghost (an "M" shape left of the sun) is still visible at frame 18, later than the page's "first 0.5 s" — verifiedBy: observed (frame 18)
- [notes] 0.6–1.4 s — the dark ring at the limb is visible from frame 18 (0.6 s), earlier than the page's 0.9 s — verifiedBy: observed (frames 18, 24)
- [notes] whole clip — no Z depth reads in the galaxy: the bridge separates from the sun as flat pieces, and the galaxy is one plane (the page says so) — verifiedBy: observed (contact sheet frames 0–89)

### mismatch_3_c1
- [blocks] 0.5–1.3 s — the inpainted plate is visible far longer and wider than the page says: an olive-to-black smeared column down the whole left edge, a pink-brown smear along the bottom, and blurred head fragments. A's left, top and bottom edges are hard straight lines against this fill and nothing covers them — content in neither photo, "photoshop cutouts", "hard edges" — verifiedBy: observed (frames 15, 18, 21, 24, 27, 30, 33, 36, 39)
- [blocks] 1.1–1.7 s — the men come in at about twice their final size with ragged matte edges and holes: a black blob on a shoulder at frame 33, a jagged arm outline at frame 39, and sofas mottled with green patches where the plate shows through — "cheap 2d cutout", "weird motion" — verifiedBy: observed (frames 33, 39, 45, 51)
- [blocks] 1.33–1.37 s — a local cut: between frames 40 and 41 the top-right quarter switches from A's opaque brick and wheels to wheels ghosted over B's pines, and the flag vanishes except for a vertical blue-yellow strip and a separate yellow bar. The step peaks at 30.7 against 26.0 the frame before — "harsh transitions" — verifiedBy: observed (frames 39, 40, 41, 42; step 40→41)
- [blocks] 1.4–2.0 s — the wheels-to-trunks move is a double exposure: transparent wheels lie over the pine trunks, and nothing moves or straightens — "crossfade" — verifiedBy: observed (frames 42, 45, 51, 57)
- [blocks] 1.9–2.2 s — the flag-to-painting move puts a second copy of B's blue painting inside the pane, so two blue paintings stand side by side at frame 63 — content duplicated; a viewer sees two paintings that B does not have — verifiedBy: observed (frames 57, 63)
- [blocks] 1.9–2.3 s — the crowd-onto-men morph: A's crowd is pasted over the sofas with the fence pattern on it (frame 63), then turns into blob-shaped cut-outs with dark smeared halos (frame 66), then pure black silhouette voids at frame 69 — black holes in neither photo, "photoshop cutouts", "2d mixup/melt" — verifiedBy: observed (frames 57, 63, 66, 69)
- [blocks] 2.3–2.5 s — a second, smaller copy of B's whole lounge (men, sofas, ottomans) appears as a hard-edged quadrilateral card inside the pane area, over the full-size B. The same men show twice; the card's lower edge is a straight diagonal that cuts a man's legs — "2 separate pictures", double exposure, hard edge — verifiedBy: observed (frames 69, 72, 75)
- [notes] 2.7 s — A's air-conditioner unit still floats above the glass when everything else is B — verifiedBy: observed (frame 81)

### mismatch_3_c1-nosit
- [blocks] 0.5–1.7 s — the same fill column and bottom smear, hard pane edges and magnified, holed men as c1 (identical frames up to about frame 40; steps match c1 to 0.1 levels) — verifiedBy: observed (contact sheet frames 18–42; step list)
- [blocks] 1.4–2.4 s — the flag move is skipped, but the flag is still torn into a vertical blue-yellow strip and a separate yellow bar inside the pane; the wheels are transparent over the pines — double exposure and a cut-up flag — verifiedBy: observed (frames 42, 48, 57, 66, 72)
- [blocks] 1.9–2.7 s — A stays a static picture in the pane behind the men, then clears with a vertical seam: crowd on the left, pines on the right at frame 78 — the "picture A remains a static transformed photo ... simply crossfades out" he already rejected — verifiedBy: observed (frames 57, 66, 72, 78)

### mismatch_3_c2
- [blocks] 0.6–1.4 s — the fill around the pane covers about 40 % of the frame: horizontally stretched pink skin-coloured ovals, olive and black streaks, and vertical streaks along the top (B's top edge replicated). The pane's bottom edge is wavy. This is the largest invented area in the round — content in neither photo, "stretched/smeared" — verifiedBy: observed (frames 24, 27, 30, 33, 36, 39)
- [blocks] 1.0–2.5 s — A is squeezed to about 0.6 of its height with B's glass laid over it: the whole pane is a double exposure (brick and crowd through pines) — "very advanced crossfade", "static transformed photo" — verifiedBy: observed (frames 30, 36, 42, 48, 57, 66, 72)
- [notes] 1.17 s — a step spike of 23.9 against 20.5 the frame before — verifiedBy: observed (step 35→36; not inspected visually)

### mismatch_2_c1
- [blocks] 0.2–2.6 s — the face_rides layer draws a visible rectangle around the man's face, a thin outline at first and later a separate hard-edged face patch detached from the jacket. It stays on screen for 2.4 s, the longest single fault in this clip — "photoshop cutout" — verifiedBy: observed (frames 6, 9, 12, 18, 27, 36, 48, 57, 63, 69, 75)
- [blocks] 0.8–1.6 s — A is a card with straight edges over B's plants; the raised hand enters magnified, blurred and translucent, with ghost fingers lying across his forehead — double exposure, "2 separate pictures" — verifiedBy: observed (frames 24, 27, 30, 36, 42, 48)
- [blocks] 1.9–2.7 s — his face patch sits on the woman in green's face with B's hand drawn translucently across it, then shrinks to a magenta-tinted horizontal strip with straight top and bottom edges over her eyes, gone by frame 82. Two faces share the same pixels — the face double exposure the planner named as F1 — verifiedBy: observed (frames 63, 69, 75, 76, 78, 80, 82)
- [notes] 1.9–2.3 s — the jacket-to-cardigan colour and the yellow-to-planter move are hard-edged colour patches (a dark green block, yellow fragments), not a flow of colour — verifiedBy: observed (frames 57, 60, 63, 69)

### mismatch_2_c2
- [blocks] 0.27–0.30 s — a cut on the trunk: between frames 8 and 9 the bark turns into a dark navy matte with a jagged top in one frame. The step is 22.3 against 11.7 and 11.0 on either side — "harsh transitions" — verifiedBy: observed (frames 7, 8, 9, 10; step 8→9)
- [blocks] 0.3–0.6 s — A is a skewed, hard-edged quad over a giant blurred thumb, with B's thumb showing through the bark — double exposure, "photoshop cutout" — verifiedBy: observed (frames 9, 12, 18)
- [blocks] 0.8–1.5 s — the man is cut out of his background and floats as a silhouette left of the phone, over the woman in green's face, not on the phone. The phone quad shows only a white-blue sliver of bokeh — "cheap 2d cutout" — verifiedBy: observed (frames 24, 30, 36, 39, 42, 45)
- [blocks] 1.5–2.0 s — the trunk-to-man's-shirt move lands on the woman in green's face as navy and brown polygon fragments and a yellow chunk. Thin black hairline curves appear on the thumb and hand — content in neither photo — verifiedBy: observed (frames 45, 48, 51, 54, 57)
- [notes] 1.5–2.3 s — a jagged white strip stays on the phone's right edge — verifiedBy: observed (frames 48, 54, 60, 66)

### Claims on the page the frames contradict
- mismatch_5: "so the line that crosses the galaxy below the core is the deck." — B's bright streak is on screen from frame 12, beside the dark deck bar. Two separate lines run until about frame 72; the deck never thins into the streak's pixels.
- mismatch_5: "The truss arrives at the lane as a dark cluster for about 0.4 s before it dissolves." — it is three hard-edged slabs from frame 12 to 48 (1.2 s), then torn translucent patches to about frame 72 (another 0.8 s).
- mismatch_5: "A thin dark ring at the sun's limb from about 0.9 s to 1.4 s" — the ring is at frame 18 (0.6 s). From frame 24 to 39 there is also a second, offset disc, which the faults list does not name.
- Page head: "the bridge, nearer than the sun by the depth model, eases ahead of it" (the Z depth answer) — what reads is flat pieces sliding apart; part of the bridge stays inside the sun disc (frames 24–51).
- mismatch_3_c1: "The filled plate shows beside the quad for a few frames (a brown smear at the top-left corner, 0.1–0.5 s)" — the fill runs down the whole left edge and along the bottom from frame 15 to about 39 (0.5–1.3 s); in c2 it covers about 40 % of the frame at frames 27–39.
- mismatch_3_c1: "scaled 1.5x so A keeps its shape and its edges end behind B's occluders" — at frames 21–30 A's left, top and bottom edges are straight lines against the fill with no occluder.
- mismatch_3_c1, "Faults to expect": it lists the double exposure and the flag matte, but not the duplicate painting (frames 57–63), the black voids (frame 69) or the second copy of the lounge (frames 72–75).
- mismatch_3_c1-nosit: "A stays behind the glass and the pane clears from its rim inward" — the flag is still torn into strips (frames 42–72), and the pane clears with a vertical seam at frame 78, not from the rim.
- mismatch_2_c1: "between 0.9 s and 1.5 s A's edges read as a card over B" — the face rectangle is visible from frame 6 to 78 (0.2–2.6 s); the card edge is only part of it.
- mismatch_2_c2: "A shrinks onto the phone the man holds up" — from frame 36 to 45 the cut-out man floats left of the phone over the woman's face; the phone quad holds only a bokeh sliver.
- All clips: "90 frames, 13.9 s" (and 23.4, 67.3, 49.3, 50.0, 39.0 s) — `info.json` gives that number as `wall_s`, the render time. Every clip plays for 3.0 s, and the page does not say which number is which.

### What works
- Every clip ends on B (residual 2.1 to 4.6 levels) and starts on a crop of A, with no step above 1.5 levels in the first and last 3 frames.
- mismatch_5: the sun lands centred on the core, and from frame 57 (1.9 s) to 89 the frame is a clean galaxy with the core's heart where the sun was. The owner's "off center" and "too large at the end" notes are answered at the end of the clip.
- mismatch_3: B's ceiling dropping in from the top during the pull-back (frames 33–48) is a real foreground layer and reads as the camera moving back.

### Confidence
High for the blocks items: each was seen on full- or half-size frames, and the cuts are also in the step numbers. Medium for the timings: they are read at 3-frame resolution, so ±0.1 s.

### Gaps
- I did not watch the clips at speed in a player; motion judgments come from frame sequences.
- I could not separate the cv2.inpaint fill from defocused, magnified B foreground on mismatch_2 (the blurred thumb and arm at frames 9–36); I named the smear without attributing it.
- mismatch_3_c2 frames 60–89 and mismatch_3_c1-nosit frames 0–40 were seen only on the contact sheet. The c2 step spike at frame 35 was not inspected.
- No colour or flicker measurement over the holds; no check of the page's resolved numbers against the renderer's code.
