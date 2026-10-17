<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (afternoon) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/skeptic_owner.md (sha256 4baef4706e04fb04) on the owner's order; folded into `TRANSITIONS.md §13.7`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Skeptic review of the §13 draft: the owner's eye and the other scenes (2026-10-17)

Verdict: the probe renders the camera half of the owner's two descriptions and none of the
transformation half. By the repo's own §11 definitions both clips are F2 (decoration without
transformation) plus a local crossfade, and the montages show the A frame as a rectangle standing in
B, a failure he has already rejected and the repo has parked. Two objections block: O1 and O4. Five
weaken the draft: O2, O3, O5, O6 and O7. Frame numbers below count the montages' 3×3 tiles from
1 (top left) to 9 (bottom right). "By my eye" marks my reading of a tile, not a measurement.

## (a) He will call it "2D decoration" or "a fancier crossfade" again

### O1. The probe is the zoom without the transformation, which is F2 by §11. Severity: blocks.
- Draft line (13.2): "What the two probes share with the owner's two sentences, and what they lack
  ... 'the bridge super fluidly transformed into part of galaxy sleeve' (absent ...)". Draft line
  (13.1 item 4): "The camera has been an option, never the transition".
- Evidence. §11 (TRANSITIONS.md:665–677) defines the goal the owner called "totally right" on
  2026-09-26: "a camera move is decoration, not the transition", and F2 is "decoration without
  transformation". The owner described these two pairs twice, and both times the transformation is
  the core and the camera is the frame around it:
  - mismatch_5 on 2026-09-27 (DECISIONS_ARCHIVE.md:80): "sun ... shrink and transform into andromeda
    bright center in B and the bridge itself rotate and become meteor streak". On 2026-10-17: "super
    out zoom **with nice layers and stuff** ... the bridge super fluidly tranformed into part of
    galaxy sleeve".
  - mismatch_3 on 2026-09-27 (same line): "people to tranfrom into other people from A group to B
    group ... removing ( tranforming ) background wall of A ( but again transforming and not just
    moving it as cheap 2d cutout!)".
- What the montages show:
  - mismatch_5 tiles 5–8: the bridge is a dark bar that only shrinks, and the sun is a disc with a
    dark ring that only shrinks.
  - mismatch_3 tiles 4–7: A's wall and crowd are one rigid rectangle that only shrinks behind the
    glass. That is A's wall "moving as a 2d cutout", the thing the owner excluded by name.
  - Nothing in either clip changes shape. The only A→B change is a dissolve (the mismatch_5 sky,
    5–75 % of the clip) and the luma reveal (the last 22 %).
- Change to the draft: state in 13.2's first line that the probe renders the camera half of his
  description and none of the transformation half, and that by §11 the clips are F2 until a
  transformation exists. Do not put the page to him as "is this the direction?" (13.8 Q1). Either
  hold the page until the minimum transformation of 13.4 item 2 exists (the bridge bent by the
  log-polar map toward the dust lane, A's crowd carried by `morph_to` onto B's group), or ask the
  narrower question "is the framing right, before the transformation is added?".

### O2. The montage shows the failures he already named, frame by frame. Severity: weakens (blocks if O1 is not fixed).
- Draft line (13.2): "Faults by my eye, not verdicts: a dark ring around the sun ...; the bridge
  stays a straight bar ...". The list leaves out the failures he has already graded.
- mismatch_5, tiles 2–3: A is a rectangle with a visible straight border floating in B's star field.
  This is the parked failure "the carried frame stands in the sky as a rectangle" (2026-09-29,
  NEXT_SESSION_PROMPT.md §8, line 461) and his "still at its core 2 separate pictures" (mismatch_1,
  2026-10-17).
- mismatch_5, tile 4: an oval vignette of A's red sky with two dark triangular notches at its top
  corners, set in the galaxy. By my eye this reads as a shaped dissolve.
- mismatch_5, tiles 5–8: a soft-edged bridge bar and a ringed disc floating over the galaxy. These
  match "crudely cut out of background with rough edges, looks like cheap 2d animated photoshop
  work" (T28, DECISIONS_ARCHIVE.md:155).
- mismatch_5, tiles 7–8: the sun disc and the core's glow are both visible. By my eye that is two
  objects at once (F1), the opposite of the page's claim that "the sun and the core are never two
  objects".
- mismatch_3, tiles 4–7: the pane has straight left and right edges beside B's trees (tile 4 near
  x≈90; tile 7 near x≈585). The crowd is at about the size of B's foreground men, so by my eye the
  pane reads as a poster on the glass, not a distant room. UNVERIFIED as his reading.
- mismatch_3, tile 8: the flag and the crowd are half-transparent over B's trees, a local double
  exposure. This is his "And still do crossfade in background" (mismatch_3, 2026-10-17).
- Change to the draft: add these frames to the fault list on the page and in 13.2, each tied to the
  owner phrase it matches. Add the parked "carried frame as a rectangle" item to 13.7 Risks as the
  first risk. A fix that keeps the photos' pixels: no visible A rectangle at any time. The rim
  should follow element mattes (sun, bridge, water as separate soft-matted layers) from frame 1,
  not a frame-shaped feather that widens.

### O3. "Every pixel from A or B" is presented as the success criterion; he grades the look. Severity: weakens.
- Draft line (13.0): "rendered both pairs in under 10 s each with every pixel from A or B and exact
  endpoints".
- Evidence. Every rejected round also passed `not_invented`: all 21 boxes in
  layered_picks_L7.json are ticked, and he still wrote "no improvement here". He grades
  "one picture" and "transforms". On mismatch_5 and mismatch_3, `one_picture` has been unticked on
  every automatic clip of round 7.
- Change to the draft: move render time and pixel provenance out of the Result paragraph. State
  instead which of the three boxes the probe is expected to earn: by my reading of O1 and O2,
  `not_invented` only.

## (b) It does not generalise to the other pairs or to the boxes

### O4. The draft claims "one mechanism" from two taste picks he called non-generalisable, and tests on pairs he has already described otherwise. Severity: blocks.
- Draft line (Result): "both descriptions are one mechanism that no round built". Draft line
  (13.6): "the planner on a pair the owner has not described (mismatch_2, mismatch_6 or
  mismatch_1)".
- Evidence on generalising:
  - mismatch_5 note, 2026-10-17: "very specific non -generalizable taste pick and core of the
    problem we are trying to solve!!!".
  - mismatch_3 note, 2026-10-17: "again, very specific art choice".
  - 2026-09-26: "be carefull also not to generalize" (DECISIONS.md:62).
  - The §11 amendment of 2026-09-27: "a hand-written score is the operator's tuning of a scene,
    never the proof that a mechanism works", and "per-pair mask rules count as tuning".
  - `nest_probe.py` branches on `if pair == "mismatch_5"` and on mismatch_3 (lines 136, 164, 197),
    with per-pair constants (the sky window, the 0.25 rim, the 13-px dilation). It is a hand score.
  - The page carries no automatic clip beside the hand clips. Every review page since 2026-09-27
    must carry one (§11 amendment, item 1).
- Evidence that the "undescribed" pairs are described:
  - mismatch_6 is described in time: clouds dissolve, the sky darkens, stars appear, buildings exit
    downward, trees and the AC unit enter (2026-09-26 late, §11). On 2026-09-27 he added "buildings
    this time transitioned to tree nicely ... i wish [clouds] just non-uniformly morphed into night
    sky parts".
  - mismatch_1, 2026-09-27: "building from A to transform into closest building in B and cloud in A
    naturally flow into cloud in B".
  - mismatch_4: "a LAYERED transition (sun → sun, skyline with depth, river, clouds materialising)"
    (2026-09-26, §11).
  - mismatch_2: "similar problem to mismatch_3" (2026-10-17) names the problem, not the fix. Treating
    it as a camera wish is my reading, and §12.25's reading item 5 already makes that leap.
- Where a nested camera has nothing to hold [INFERRED, none measured]:
  - mismatch_1 and mismatch_7 are the same city. Nesting a city inside the same city destroys the
    shared geometry he credited on mismatch_7 ("kept their shape correctly").
  - mismatch_4 is sun to sun at similar size, so the zoom ratio falls near 1 and the clip
    degenerates to a local dissolve. The sun-size ratio is UNVERIFIED.
  - mismatch_6 asks for a vertical, in-time score.
  - mismatch_2 has no window or container element in either photo by the fixture description
    (fixtures/MANIFEST.md:26). UNVERIFIED against the layer source.
- Change to the draft:
  - Replace "one mechanism" with "a framing the owner asked for on two pairs, which he labelled
    scene-specific".
  - Add an automatic nested clip to the page, produced by a pair-blind container and anchor rule,
    or state plainly that the page breaks the 2026-09-27 rule and ask him to waive it.
  - Correct 13.6's test pair: no pair in the set is undescribed. The test must be a new pair
    outside the seven (inventory D item 10: "No held-out pair exists"), or a described pair whose
    description is withheld from the planner, with his earlier note then compared against the
    planner's concept.

### O5. The box repaint plan conflicts with his closing word on the boxes, and it skips the ungraded `draw` variant. Severity: weakens.
- Draft lines (13.8 Q5): "a stroke-by-stroke repaint over the held, pinned plate for the next box
  session? Recommended: yes". (13.1 item 3): "a time-varying repaint, which none of the three is".
- Evidence:
  - The owner, 2026-10-17 (§12.24.9): "real life task experiment is done ... Do not redraw anything
    this is simply my feedback". No next box session exists.
  - The `draw` variant (§12.24.7–12.24.8) was built on his order for "really gradual and elaborate
    drawing process on those boxes". It is a soft per-pixel repaint front and is ungraded.
  - Stylized Neural Painting renders brush strokes. Reaching "B within ΔE 1" at the end needs a
    final blend to photo 7, which is a crossfade in the last frames [INFERRED]. The painterly look
    may fail his 2026-09-29 "realistic (for a given context)" ruling. UNVERIFIED.
- Change to the draft: recast Q5 as a capability question for future same-scene repaint pairs, not
  a box session. Name `draw` as the existing answer to the same wish and record it as ungraded. Keep
  the stroke route at rank "later", behind a ΔE test of the stroke renderer on photo 7 alone.

## (c) The director flow adds ceremony without changing what he sees

### O6. The planner picks among renderer actions that are all 2D, so the plan cannot change his verdict. Round 8's planner is the hand-scoring of rounds 4–5 under a new name. Severity: weakens.
- Draft lines (13.6): "Recommendation: round 8 uses the session's own model as the planner ...".
  (Stages 1–2): `layers` take an "action from §12.1"; `finish` is luma, melt, `morph_to` or helper.
- Evidence:
  - Every action in §12.1 and every finish listed has drawn a 2D or crossfade verdict: `move_to`
    "weird oval shape", `morph_to` "weird wavy pattern", luma "too crude and global", the camera
    "unnecessary pans".
  - The only new keys are `camera`, `container`, `crop_anchor` and `finish`, and their reference
    implementation is the O1/O2 probe.
  - The session model writing a score for a pair is how the rounds 4–5 hand scores were made. His
    2026-10-17 message is "we are stuck conceptually", and a planner choosing from the same
    vocabulary changes the clips he grades only through which rule is picked, not through what the
    renderer can draw.
  - The flow multiplies his grading load: 2–4 concepts per pair against the one or two clips per
    pair he grades now. No ruling bounds this, but he has graded about 340 clips with none accepted
    (§11).
- Change to the draft: order round 8 renderer-first. Build one transformation primitive (O1) and
  show it. Build the planner only when the renderer has an action he has not called 2D. Cut the
  `plan.json` schema to the keys a rendered concept actually used. Cap concepts at 2 per pair.
  Name the director flow as process, not as an answer to "stuck conceptually".

## (d) Contradictions with rulings in force

### O7. Rulings the draft crosses or leaves unrecorded. Severity: blocks until recorded, then cosmetic.
1. §11 "a camera move is decoration, not the transition" (owner-confirmed 2026-09-26), and "the
   cameras as a transition" on the parked list (NEXT_SESSION_PROMPT.md:461). The draft makes the
   camera the transition and names neither ruling. His 2026-10-17 notes arguably reopen it. That
   needs a dated DECISIONS line superseding the §11 sentence (AGENTS.md: reopening a parked item
   needs a new dated line), with `[revert: …]`. Change: add that line to 13.9 item 1 and cite both
   rulings in 13.1 item 4.
2. "Never full video generation" (2026-09-26). 13.4 item 5 handles Wan VACE correctly as a question
   for him. No change.
3. "A pick is not acceptance" (2026-09-14). 13.3's ranking reads picks as "positive verdicts"
   ("Seven carry a positive verdict") and 13.8 Q1 asks for a direction verdict on the probe.
   Change: label the ranking "closest picks, none accepted", and keep a separate "acceptable as-is"
   answer on the probe page.
4. "Do not overfit" (2026-09-27). 13.7 says "the primitive is general and the per-scene choice
   moves to the planner". The evidence in O4 says the primitive is per-pair code. Change: delete
   "the primitive is general" until a pair-blind run exists.
5. The 2026-10-17 verdicts sit in no DECISIONS line yet (inventory report, "Constraints
   discovered"). The draft cites "verbatim in DECISIONS 2026-10-17" in §12.25's header. Confirm
   that line exists before the section lands. UNVERIFIED by me.

## What the draft gets right
- It records the two descriptions verbatim, and it names its own gaps (no parallax, no
  bridge→arm, local finish) instead of hiding them.
- It holds every generative and network step out of both tools, and it routes VACE to the owner
  under the "never full video generation" ruling.
- 13.6's pass rule ("only if that concept is one he did not ask for and does not call 2D") is the
  right test. It needs a truly held-out pair (O4).

Confidence: 75 %. Frame readings are by my eye on 9-tile montages; I did not play the mp4s.
