# Halloween loops (2026-10-30): the owner's ten photo sequences as looped clips

Sources: `~/Pictures/halloween 2026/gifs/<seq>/raw/*.jpg` (2–6 developed JPGs per sequence, 2682–6192 px, the ARW and XMP files ignored; read only, never copied). Outputs (gitignored): `benchmarks/runs/2026-10-30/halloween/` (the registered stills under `in/<seq>/`, the candidates under `<seq>/<cN>/`, the page `index.html`, the subagent reports under `agents/`, the round-1 candidates that were rebuilt under `round1/`). Tool: `scripts/research/loop_seq.py` (prep · render · page); plans: `scripts/research/plans/loops/`. Grades: none yet (the page opened in his browser at the end of the session).

## Registration (`loop_seq.py prep`; SIFT + MAGSAC to frame 0, chained SIFT, ECC seeded by the chain, a cut for a frame that cannot be registered)
| seq | stills | canvas frame | methods (inliers or ECC cc) | common crop |
|---|---|---|---|---|
| evgen-npc | 3 | 2 | sift 464, 275 | 1242×1908 |
| evgen-thug | 6 | 1 | sift 75, 72, 86; k4 and k5 cuts (a plain wall; the subject fills the frame; ECC locked onto him: scale 0.78, a masked ECC 0.51) | 1200×1794 |
| group-teleport | 2 | 1 | sift 420 | 1870×1278 |
| group1 | 2 | 0 | sift 443 | 1896×1266 |
| nose | 2 | 0 | sift 141 | 1266×1890 |
| sveta-head | 2 | 1 | sift 93 | 1156×1836 |
| talk | 2 | 0 | sift 265 | 1140×1910 |
| wand | 2 | 0 | sift 99 | 1388×1890 |
| zeke-back | 5 | 1 | sift 89, 175, 181, 181 | 1186×1874 |
| zeke-bite | 2 | 0 | ECC cc 0.56 (the second still is whole-frame motion blur; 8 SIFT inliers) | 1098×1792 |

The camera was handheld: 0.5–3 % shifts and up to 3 % scale between shots (the registration probe on 1200 px proxies, 2026-10-30).

## Round 2 candidates (the page of 2026-10-30, md5 3c69dc169b2b8f9b5bcf073de9f436a2; the talk loop re-rendered byte-identical (mp4 2ecbe778…, gif 94d14d6b…); the other 23 were not re-run)
| seq | cand | frames | s | canvas | methods | effects | generated | dexp max | step mean | step max | seam | md5 mp4 | md5 gif | gif MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| evgen-npc | c1 | 49 | 1.96 | 1242x1908 | rife | breath | 0.429 | 0.0468 | 1.693 | 2.83 | 1.441 | 0110654b | 8eaacea8 | 3.5 |
| evgen-npc | c2 | 49 | 1.96 | 1242x1908 | morph | breath | 0.0 | 0.0 | 1.732 | 3.033 | 1.799 | 456fb6b7 | 57b092e1 | 3.5 |
| evgen-npc | c3 | 28 | 1.12 | 1242x1908 | cut | - | 0.0 | 0.0 | 0.852 | 8.637 | 5.499 | 56defaaa | a6e10b88 | 0.4 |
| evgen-thug | c1 | 57 | 2.28 | 1200x1794 | cut+rife | - | 0.14 | 0.1065 | 3.414 | 51.542 | 49.641 | a7be7f5a | 13f09957 | 1.2 |
| evgen-thug | c2 | 75 | 3.0 | 1200x1794 | cut+rewind+rife | - | 0.107 | 0.1065 | 4.972 | 51.542 | 1.142 | 98f1cf17 | 8a72967d | 1.8 |
| evgen-thug | c3 | 54 | 2.16 | 1200x1794 | cut+rife | - | 0.111 | 0.1065 | 3.58 | 51.541 | 49.642 | 980f9e9b | 444fba29 | 1.1 |
| group-teleport | c1 | 44 | 1.76 | 1870x1278 | cut+teleport | - | 0.0 | 0.0 | 2.754 | 57.128 | 25.599 | 3fb9c81e | 383cc740 | 0.6 |
| group-teleport | c2 | 54 | 2.16 | 1870x1278 | teleport | breath | 0.444 | 0.0471 | 3.306 | 7.676 | 5.635 | f554fa23 | 5b7d71b2 | 5.6 |
| group1 | c1 | 48 | 1.92 | 1896x1266 | rife | breath | 0.5 | 0.0494 | 3.358 | 8.822 | 2.003 | e63e21cd | 372e3066 | 5.0 |
| group1 | c2 | 60 | 2.4 | 1896x1266 | cut | - | 0.0 | 0.0 | 0.48 | 28.066 | 28.065 | 1ceb6739 | 3bc03e09 | 0.3 |
| group1 | c3 | 44 | 1.76 | 1896x1266 | morph | - | 0.0 | 0.0 | 2.407 | 6.516 | 3.416 | 30ec5727 | 16668325 | 2.7 |
| nose | c1 | 33 | 1.32 | 1266x1890 | rife | breath | 0.364 | 0.0408 | 6.046 | 10.055 | 2.524 | 1b41e96a | 9fbc77b9 | 3.1 |
| nose | c2 | 48 | 1.92 | 1266x1890 | rife | - | 0.292 | 0.0397 | 1.003 | 5.78 | 2.245 | 9a398764 | 54d4851d | 1.5 |
| sveta-head | c1 | 36 | 1.44 | 1156x1836 | rife | breath | 0.556 | 0.0423 | 1.888 | 3.106 | 1.4 | c2c6c85e | ec5216dd | 2.6 |
| sveta-head | c2 | 34 | 1.36 | 1156x1836 | rife | - | 0.471 | 0.0418 | 1.298 | 3.633 | 2.375 | 7ba3e417 | 31b94813 | 1.6 |
| talk | c1 | 28 | 1.12 | 1140x1910 | rife | breath | 0.286 | 0.0501 | 2.849 | 5.315 | 1.725 | 74d23241 | 21d132ec | 2.2 |
| talk | c2 | 42 | 1.68 | 1140x1910 | rife | - | 0.405 | 0.0514 | 1.172 | 5.933 | 1.576 | 8722e63b | 9b457ee9 | 1.4 |
| wand | c1 | 28 | 1.12 | 1388x1890 | rife | breath | 0.571 | 0.0311 | 2.768 | 5.073 | 1.501 | ace1f768 | 65e1f81e | 2.5 |
| wand | c2 | 35 | 1.4 | 1388x1890 | rife | - | 0.371 | 0.0319 | 1.235 | 7.799 | 1.448 | 91c89865 | c71594f9 | 1.2 |
| zeke-back | c1 | 78 | 3.12 | 1186x1874 | dissolve+rife | breath | 0.282 | 0.0589 | 1.923 | 8.445 | 9.007 | c9ed26e8 | cf0cc02e | 6.1 |
| zeke-back | c2 | 79 | 3.16 | 1186x1874 | rife+teleport | breath | 0.468 | 0.06 | 2.313 | 9.156 | 1.515 | 7c6e24a9 | 50879418 | 6.1 |
| zeke-back | c3 | 72 | 2.88 | 1186x1874 | cut+rife | - | 0.306 | 0.0589 | 1.261 | 29.631 | 23.783 | 557c2028 | 46fd33fb | 2.0 |
| zeke-bite | c1 | 27 | 1.08 | 1098x1792 | rife | breath | 0.222 | 0.0932 | 6.721 | 24.093 | 8.027 | 1d5328d9 | 49516e9e | 2.4 |
| zeke-bite | c2 | 27 | 1.08 | 1098x1792 | cut | breath | 0.0 | 0.0 | 4.854 | 45.823 | 45.417 | c279cdf5 | 1254aebf | 2.2 |

Round-1 and rebuilt candidates moved to `round1/`: evgen-thug_c1 05ad668f; evgen-thug_c2 bf7d9b1d; evgen-thug_c3_r2 c98df8de; group-teleport_c1 17ae26b6; group-teleport_c1_r2 f451d90d; group-teleport_c1_r2b f451d90d; group-teleport_c1_r2c f451d90d; group-teleport_c1_r2d a124b2e7; talk_c1 2ecbe778; zeke-bite_c1 49856f2b

Columns: generated = the share of frames with RIFE pixels inside the change matte; dexp max = rule 7's double-exposure share (the largest over the generated frames); step = the mean absolute difference between consecutive decoded frames; seam = the last frame against the first (a declared cut back shows as a large seam). Round 1's twelve candidates (page md5 31a2d93b…) went through the skeptic's first pass (`research/2026-10-30/skeptic.md`): 1 READY, 4 READY WITH A NOTE, 7 NOT READY; the five rebuilt in place are under `round1/` with the md5s above, plus the renders replaced after the skeptic's second pass (`evgen-thug_c3_r2` c98df8de…; the teleport c1 four times, f451d90d… twice, a124b2e7…, until the box reached her boots: the person matte's threshold 30 missed the tan boots against the grey floor, 24 reaches them, and the largest-component rule dropped them until parts of at least 2 % were kept).

Skeptic pass 2 (`research/2026-10-30/skeptic2.md`, on the 16 changed or new candidates): READY zeke-back c3, zeke-bite c2, group1 c2, evgen-npc c3, sveta-head c2, nose c2; READY WITH A NOTE evgen-thug c1 and c2 (a yellow tint on his face at frame 12), wand c2 (the hat and handle blended at 11–12, 29–30); NOT READY group-teleport c1 (her boots stayed standing; fixed after the pass as above, not re-judged) and c2 (box rectangles, a doubled boot), evgen-thug c3 (the blur leg's RIFE doubled the pumpkin again; a cut now, not re-judged), zeke-back c2 (the pair doubles at 16–17, 74–75), zeke-bite c1 (one ghost frame per leg), talk c1 and c2 (the wand as two sticks; T63), group1 c3 (as c1). The skeptic did not play any clip at speed.

## Owner grades
Round 2 (2026-10-30, verbatim): "Review and required fixes: 
First of all overall , all loop with more than two frames are too discrtete, the transitions in-between inner frames must be fluid , seamless and not like 1-2 (small pause) 2-3 etc. Second , no flashes, no double pokes, nothing jerky. Next , will give feedback per item: 
1) group-teleport - c2 , but do not beam , this looks like cardbard cut out very cheap and photoshop-style , should be like super swift fluid lateral  move   from one side to another , with remaining people nicely morphing 
2) evgen-thug - c2 but  more fluid , slower in the begiining with big speed ramp up for last 3 frames
3) zeke-back - c2 , but with  all genearal issues mentioned above, also make man in cylinder appear in more sinister and natural way ( in second frame) from behind the back of main person with glasses. Same jerky blocky transitions between frames misses single fluid flow  
4) zeke-bite - c1 almost good, a bit more fluide ( with same speed ) 
5) talk - c1 but more fluid , no breathing effect
6) wand - c1 , alnost just a 20% faster and slightly more natural girl transition
7) group1 - c1 almost there, a 30% faster, no breathing
8) evgen-npc - c1 but with general fixes metnitoned above, this oe is severely discreet and blocky, visible frame transtions, must be very natural and fluid resembe npc selection idle animation in games, breathing effect is fine here"
(sveta-head and nose: no grade given.)

Round 3 (2026-10-30, verbatim): "group-teleport - c2: round 3b is bad very dirty, just dissolbe morph person into background and do inverse in destination , all other people and stay as you have in latest version of c2. also whole scene 20% faster
zeke-back - c2: round 3b is ugly and has lots of artifacts between frame 1 and 2 , insead do a more immediat snap from 1 to 2 frame like in c3 but more fluid and with slight motion blur  and then nice gradual single clean  motion animation ( currently still in steps between frames )  
All else is good as is"

## Round 3 (2026-10-30, from his grades above; the final page md5 6f1ec2c73bdef4a098e138b064138904)
The general rule he stated became a renderer mechanism: a `through` chain passes several stills under ONE global speed profile (`weights` per segment, `soft` slows near a still without stopping; no inner holds). The teleport became a lateral `slide` (her cutout in flight with a motion blur, crossfading between her two poses; underneath, RIFE between the two stills with her removed: her old spot from the other still, her new spot a wall-and-floor fill from the rows above and below). The ghoul became a `rise` (his hat-and-head cutout from the second still rises from behind the man's shoulder, occluded by the man's own GrabCut matte; the pair settle by RIFE). GrabCut mattes (`grabcut_matte`) where a colour threshold failed; the readings of a subagent (`research/2026-10-30/readings.md`) gave the boxes and the wand anchors.

Eight candidates re-rendered (the round-2 renders under `round2/`): evgen-npc c1 (a continuous 45-frame cycle, the breath kept), evgen-thug c2 (34 generated frames under an accelerating profile through the five stills, the gun held, the rewind; the unregistered last two stills make the draw a fast zoom-in, steps 25–47), zeke-back c2 (the rise over 18 frames, a 30-frame creep through the three closer stills, the sink), zeke-bite c1 (four in-betweens each way, sine), talk c1 (six up, eight back, sine, no breath), wand c1 (22 frames, sine, the breath kept), group1 c1 (34 frames, sine, no breath), group-teleport c2 (the slide, 16 frames each way, her flight over the middle half). The anchored morph for the talk (eight hand anchors, `round2/talk_c3_anchors_failed`, md5 91efc7bc…) doubled both people at mid-swing (frames 13–16, 28–31) and is off the page: the DIS flow on this pair degrades to a dissolve of the bodies and the anchors move only the wand's field (T63 stays open).

| seq | cand | frames | s | canvas | methods | effects | generated | dexp max | step mean | step max | seam | md5 mp4 | md5 gif | gif MB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| evgen-npc | c1 | 45 | 1.8 | 1242x1908 | chain:rife | breath | 0.978 | 0.0469 | 1.76 | 2.881 | 1.458 | 1a3ed0c5 | beb150e1 | 3.3 |
| evgen-npc | c2 | 49 | 1.96 | 1242x1908 | morph | breath | 0.0 | 0.0 | 1.732 | 3.033 | 1.799 | 456fb6b7 | 57b092e1 | 3.5 |
| evgen-npc | c3 | 28 | 1.12 | 1242x1908 | cut | - | 0.0 | 0.0 | 0.852 | 8.637 | 5.499 | 56defaaa | a6e10b88 | 0.4 |
| evgen-thug | c1 | 57 | 2.28 | 1200x1794 | cut+rife | - | 0.14 | 0.1065 | 3.414 | 51.542 | 49.641 | a7be7f5a | 13f09957 | 1.2 |
| evgen-thug | c2 | 85 | 3.4 | 1200x1794 | chain:rife+rewind | - | 0.424 | 0.111 | 4.819 | 29.666 | 1.002 | 88d6efaa | 87bdde43 | 4.2 |
| evgen-thug | c3 | 54 | 2.16 | 1200x1794 | cut+rife | - | 0.111 | 0.1065 | 3.58 | 51.541 | 49.642 | 980f9e9b | 444fba29 | 1.1 |
| group-teleport | c1 | 44 | 1.76 | 1870x1278 | cut+teleport | - | 0.0 | 0.0 | 2.754 | 57.128 | 25.599 | 3fb9c81e | 383cc740 | 0.6 |
| group-teleport | c2 | 56 | 2.24 | 1870x1278 | slide | - | 0.571 | 0.0529 | 3.023 | 8.383 | 2.072 | ec81bddb | 04da4dcf | 3.6 |
| group1 | c1 | 34 | 1.36 | 1896x1266 | rife | - | 0.471 | 0.0469 | 2.983 | 11.594 | 1.943 | 1ade90b8 | afb0f4e2 | 2.0 |
| group1 | c2 | 60 | 2.4 | 1896x1266 | cut | - | 0.0 | 0.0 | 0.48 | 28.066 | 28.065 | 1ceb6739 | 3bc03e09 | 0.3 |
| group1 | c3 | 44 | 1.76 | 1896x1266 | morph | - | 0.0 | 0.0 | 2.407 | 6.516 | 3.416 | 30ec5727 | 16668325 | 2.7 |
| nose | c1 | 33 | 1.32 | 1266x1890 | rife | breath | 0.364 | 0.0408 | 6.046 | 10.055 | 2.524 | 1b41e96a | 9fbc77b9 | 3.1 |
| nose | c2 | 48 | 1.92 | 1266x1890 | rife | - | 0.292 | 0.0397 | 1.003 | 5.78 | 2.245 | 9a398764 | 54d4851d | 1.5 |
| sveta-head | c1 | 36 | 1.44 | 1156x1836 | rife | breath | 0.556 | 0.0423 | 1.888 | 3.106 | 1.4 | c2c6c85e | ec5216dd | 2.6 |
| sveta-head | c2 | 34 | 1.36 | 1156x1836 | rife | - | 0.471 | 0.0418 | 1.298 | 3.633 | 2.375 | 7ba3e417 | 31b94813 | 1.6 |
| talk | c1 | 34 | 1.36 | 1140x1910 | rife | - | 0.412 | 0.0516 | 0.808 | 3.468 | 1.497 | 80920e0e | 72718426 | 1.0 |
| talk | c2 | 42 | 1.68 | 1140x1910 | rife | - | 0.405 | 0.0514 | 1.172 | 5.933 | 1.576 | 8722e63b | 9b457ee9 | 1.4 |
| wand | c1 | 22 | 0.88 | 1388x1890 | rife | breath | 0.636 | 0.0315 | 3.253 | 5.472 | 1.62 | 7878d441 | 7ff3211c | 2.1 |
| wand | c2 | 35 | 1.4 | 1388x1890 | rife | - | 0.371 | 0.0319 | 1.235 | 7.799 | 1.448 | 91c89865 | c71594f9 | 1.2 |
| zeke-back | c1 | 78 | 3.12 | 1186x1874 | dissolve+rife | breath | 0.282 | 0.0589 | 1.923 | 8.445 | 9.007 | c9ed26e8 | cf0cc02e | 6.1 |
| zeke-back | c2 | 87 | 3.48 | 1186x1874 | chain:rife+rise | - | 0.667 | 0.0667 | 1.943 | 8.048 | 3.953 | 96031b82 | 1584e4cd | 4.7 |
| zeke-back | c3 | 72 | 2.88 | 1186x1874 | cut+rife | - | 0.306 | 0.0589 | 1.261 | 29.631 | 23.783 | 557c2028 | 46fd33fb | 2.0 |
| zeke-bite | c1 | 26 | 1.04 | 1098x1792 | rife | breath | 0.231 | 0.0932 | 6.992 | 24.882 | 7.501 | 47fd25da | 5fdcc120 | 2.4 |
| zeke-bite | c2 | 27 | 1.08 | 1098x1792 | cut | breath | 0.0 | 0.0 | 4.854 | 45.823 | 45.417 | c279cdf5 | 1254aebf | 2.2 |

Earlier renders: round 2's under `round2/`: evgen-npc_c1 0110654b; evgen-thug_c2 98f1cf17; group-teleport_c2 f554fa23; group-teleport_c2_r3a 6858ef18; group1_c1 e63e21cd; talk_c1 74d23241; talk_c3_anchors_failed 91efc7bc; wand_c1 ace1f768; zeke-back_c2 7c6e24a9; zeke-back_c2_r3a 110c26e4; zeke-bite_c1 1d5328d9. Round 3's first renders, replaced after the third pass, under `round3/`: evgen-thug_c2 ec238115; group-teleport_c2 921be08e; zeke-back_c2 dbc7be88; zeke-back_c2_3b 91a26ee0; zeke-bite_c1 382c824e

Skeptic pass 3: READY evgen-npc c1 (a single face, hand and pumpkin throughout; the last leg about 1.5× faster); READY WITH A NOTE wand c1 (the hat tip and handle blended one frame per leg), group1 c1 (two tridents and the see-through glove at 12–13 and 30, T66), evgen-thug c2 leaning NOT READY (the double pumpkin back at 29–32 through the chain's blur-to-belly leg; one-frame stalls at 27 and 35; the draw in three steps of 25–47 levels reads as a snap zoom on stills); NOT READY zeke-back c2 (the ghoul pasted in front of the man's chest at 14–22, his face a flat patch at 26–30, a pop at 32, the same at the sink), zeke-bite c1 (four in-betweens doubled the ghost at 14–15 and 24–25), talk c1 (the wand at 15–16 and 28–29, T63), group-teleport c2 (a pale halo at her landing 24–26 and 52–54, a dark edge at 27 and 55, a see-through smear mid-flight). The skeptic played no clip at speed. Four fixes applied after the pass and NOT re-judged (round 3b): the ghoul by the colour matte (hat and face) with the man's GrabCut matte down to his chest and a shorter rise; the slide's mattes eroded by 0.4 % of the width and the flight blur at 0.45 of her speed; the thug's blur-to-belly leg weighted to a jump inside the chain and the last two legs given about five frames; the bite back to three in-betweens with the sine ease. The round-3 renders they replace are under `round3/`.

## Round 4 (2026-10-30, from his round-3 grades above; the final page md5 d84820d716774baf0c6457c30bf8aa9a)
Two candidates re-rendered, everything else "good as is". group-teleport c2: the slide's `mode: dissolve` (she fades out in place over the first 55 % of the segment and fades in at the destination over the last 55 %; the others morph underneath by RIFE between the stills with her removed; her destination filled column by column from the wall above and the floor below, then from the first still's own wall where it shows one), GrabCut mattes on both sides with the door strip excluded, no erosion, holds 10 and 13 in-betweens each way: 46 frames (1.84 s, 18 % shorter than 56), step mean 2.184, max 5.123 at 10, seam 2.745, mp4 44fd0e9c…, gif e030a7f2… (3.1 MB). zeke-back c2: a `snap` (a 3-frame blend with a vertical motion blur of up to 2.2 % of the height, nothing generated) into the still with the ghoul, one linear-speed creep through the three closer stills (36 generated frames, the first leg given half of them, no frame within 4 % of a still), the hold, a 3-frame snap back: 67 frames (2.68 s), step mean 1.904, max 10.352 at 14, seam 9.215, mp4 4be39328…, gif fbef43a8… (3.7 MB). Earlier round-4 renders under `round4/` (the first pair the skeptic judged, then the teleport's second and third); the round-3b renders under `round3/`.

Skeptic pass 4 (`research/2026-10-30/skeptic4.md`, the two candidates): both NOT READY. group-teleport c2 did what he asked (she fades out at the right over 10–16 and in at the left over 16–22; 18 % shorter) but carried a pale halo along her outline in every dissolve frame, a dark stroke from her shoulder to her knee at 42–45, a piece of her forearm left at her old spot, a grey square on her chest at 19–22 and 33–35; the leopard-mask man doubles at 35–37 in the base he asked to keep. zeke-back c2 got the snap right (the ghoul behind the man, one face each) but the creep stalled after the snap under the sine ease (steps 0.00–0.04 at 15–18), stopped a frame at each middle still (0.26, 0.15) and slowed 2.5× after the second still. Fixes applied after the pass and NOT re-judged: the dissolve's cutout multiplied by its matte once instead of twice (the halo), GrabCut mattes on both sides (the stroke and the forearm), a linear profile with the first leg given half the frames and no frame within 4 % of a still (the creep's steps now 2.0–3.2 then 0.7–1.8, one dip to 0.29), the snap's blur 2.2 %. The first round-4 renders are under `round4/`. The skeptic played no clip at speed. After the pass the teleport was rendered three more times from the main thread's own full-size crops (the door strip excluded, the fill from the first still's wall, the erosion removed); a faint lighter rim along her edge remains while she fades; the skeptic did not see these renders.
