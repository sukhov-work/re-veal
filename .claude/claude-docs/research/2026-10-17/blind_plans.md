<!-- Provenance: written 2026-10-17 by an Opus 5.5 subagent (afternoon) of the Claude Code session of that day (the round-8/9 session; DECISIONS 2026-10-17), copied verbatim from benchmarks/runs/2026-10-17/agents/blind_plans.md (sha256 6d7cdaaee76cf040) on the owner's order; folded into `TRANSITIONS.md §13.6`. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

# Transition plans: three blind pairs, 3 s each

Conventions. All windows are normalised time t in [0, 1] (t = 1 is 3.0 s). Boxes are [x0, y0, x1, y1] in the canvas pixels of elements.json. Box coordinates I derived from the proxies use the mapping I inferred from the table: each proxy is cover-scaled to the canvas and centre-cropped. That inference rests on matching the detected sun, flag and trunk boxes to the proxies; it is UNVERIFIED against the renderer's own canvas code.

---

## Pair 1: sunset behind a bridge -> Andromeda galaxy with a satellite streak

### What I see in the two photos

A is a portrait telephoto sunset. A large orange sun sits behind a two-level road bridge, with a thin bright deck line and a dark truss below it. Lamp posts stand on the bridge as silhouettes, and the sun's reflection makes a vertical column of orange ripples on dark water. The 1920x1080 canvas is a centre band of the portrait frame, so the canvas cuts off the top of the sun. Sun centre is about (992, 132) with radius about 276 px; the deck runs across y 250-300, the truss across y 385-590, and the reflection column spans about [712, 720, 1272, 1080]. B is a landscape astrophoto of the Andromeda galaxy: an orange core near (955, 515), an inclined disk tilted about +20 degrees (down to the right) with a dark dust lane below-left of the core, a star field, and one thin straight satellite or meteor streak. The streak runs from (0, 920) to (1920, 245), about -19 degrees, and passes just below the core. Both photos share one structure: an orange luminary on a dark red-black field, crossed just below its centre by a thin bright line, with a dark band under that line. Detections I would not trust: in B, "sun" ids 3, 4, 6 and 7 are one object (the galaxy core); "wall" 9 is a star; "meteor streak" 5 at [589,491,680,560] sits on the dust lane and is probably not a streak. The galaxy disk and the dust lane are not detected, so I use boxes: disk about [240, 290, 1870, 880], dust lane about [320, 400, 1253, 747]. In A, "tree" 30 and 31 and "earth" 37 are the dark far shoreline under the bridge; "animal" 38 is a small bird on the water at the far left.

### Concept 1 (ranked first): the bridge tilts into the streak and the reflection becomes the galaxy

```json
{
  "idea": "The sun sinks and cools into the galaxy core while the bridge deck pivots -19 degrees about it and thins into the satellite streak, the dark truss below it becomes the dust lane, and the orange reflection column on the water rotates up and spreads out into the inclined galaxy disk, its ripple glints becoming stars.",
  "relation": "themed",
  "anchors": [
    {"a_element_id": 4, "b_box": [830, 429, 1091, 595], "how": "sun disc centre (992,132) to galaxy core centre (955,515); radius 276 -> ~130 px"},
    {"a_element_id": 16, "b_element_id": 2, "how": "deck line endpoints (0,~275) and (1919,~275) to streak endpoints (0,920) and (1920,245); MLS line anchors at 5 evenly spaced points"},
    {"a_element_id": 29, "b_box": [320, 400, 1253, 747], "how": "truss band (dark) to dust lane (dark), principal axes matched"},
    {"a_box": [712, 720, 1272, 1080], "b_box": [240, 290, 1870, 880], "how": "reflection column luminance mass to galaxy disk luminance mass; column axis (vertical) to disk major axis (+20 deg)"},
    {"a_element_id": 1, "b_element_id": 1, "how": "sky to space by colour statistics only, no geometry"}
  ],
  "container": null,
  "camera": {"kind": "pullback", "fixed_point": "luminary centre, travelling from (992,132) to (955,515) under the same ease", "ease": "smootherstep", "parallax": "off"},
  "transforms": [
    {"a_element_id(s)": [4], "b_element_id(s)": [3, 4, 6, 7], "by": "morph_to", "window": [0.0, 0.85], "note": "disc keeps a hard limb until t=0.5, then the limb softens into the core's glow profile; the sun drops 383 px, which reads as the end of the sunset"},
    {"a_element_id(s)": [16, 17], "b_element_id(s)": [2], "by": "mls", "window": [0.10, 0.75], "note": "pivot about the luminary, -19 deg; line width tapers to the streak's 2-3 px; deck cars (14, 15, 18) ride the line and shrink to points on it"},
    {"a_element_id(s)": [29, 21, 24, 30, 31, 37], "b_box": [320, 400, 1253, 747], "by": "morph_to", "window": [0.15, 0.85], "note": "all dark horizontal structure under the deck condenses into the dust lane"},
    {"a_box": [712, 720, 1272, 1080], "b_box": [240, 290, 1870, 880], "by": "morph_to", "window": [0.20, 0.90], "note": "optimal transport of the column's brightness mass; the column lifts off the water and fans into the ellipse"},
    {"a_element_id(s)": [36], "b_element_id(s)": [1], "by": "move_to", "window": [0.30, 0.95], "note": "the brightest ripple glints (top 0.5% luminance) are moved as blobs onto the brightest B stars, matched by rank and nearest position"},
    {"a_element_id(s)": [2, 3, 6, 8, 9, 11], "b_element_id(s)": [1], "by": "move_to", "window": [0.10, 0.60], "note": "lamp posts collapse along their length to their tops, which land on bright stars"},
    {"a_element_id(s)": [1, 5, 10, 12, 36], "b_element_id(s)": [1], "by": "colour", "window": [0.0, 1.0], "note": "red sky and water drift to the near-black of space with a slight green-brown cast in the disk area"}
  ],
  "finish": "From t=0.8 every carried element is within a few px of its B position; the remaining star field completes through a reveal ordered by brightness (brightest first), each star on a 3-frame ramp, and the last frame is B's pixels.",
  "helper": null,
  "knobs": ["deck_pivot_window (when the bridge tilts relative to the sun's drop)", "glint_to_star_fraction (how many water glints become stars vs. dissolve into the disk mass)", "limb_soften_t (how long the sun keeps a hard edge)"],
  "surprise": 4,
  "risk": "crossfade: the disk is diffuse, so the optimal-transport morph of the column into it can read as a dissolve if the column's mass does not visibly travel; keep the column's shape coherent until t=0.6. invention: none, every bright point in the end state is a B star."
}
```

### Concept 2: the horizon winds up into a spiral

```json
{
  "idea": "A divergence-free swirl centred on the sun winds A's horizontal strata (sky, deck line, truss, shoreline, water column) into a spiral, which is then squashed into the galaxy's inclined ellipse as the swirl unwinds onto B's dust lane and streak.",
  "relation": "themed",
  "anchors": [
    {"a_element_id": 4, "b_box": [830, 429, 1091, 595], "how": "swirl centre travels from the sun centre to the galaxy core"},
    {"a_element_id": 29, "b_box": [320, 400, 1253, 747], "how": "the wound-up truss band is the arm that ends as the dust lane"},
    {"a_element_id": 16, "b_element_id": 2, "how": "the deck is the one stratum the swirl does not catch: it stays straight and only rotates, ending as the streak"}
  ],
  "container": null,
  "camera": {"kind": "zoom", "fixed_point": "swirl centre", "ease": "ease-in-out cubic, zoom 1.0 -> 0.8 -> 1.0", "parallax": "off"},
  "transforms": [
    {"a_element_id(s)": [21, 29, 30, 31, 37, 36], "b_box": [240, 290, 1870, 880], "by": "log_polar", "window": [0.0, 0.55], "note": "swirl angle peaks at ~270 deg at the core, falling off with radius"},
    {"a_element_id(s)": [21, 29, 30, 31, 37, 36], "b_box": [240, 290, 1870, 880], "by": "morph_to", "window": [0.45, 0.90], "note": "the spiral is affinely flattened to B's disk axis ratio (~0.35) and its texture carried onto the disk"},
    {"a_element_id(s)": [16], "b_element_id(s)": [2], "by": "mls", "window": [0.20, 0.80]},
    {"a_element_id(s)": [4], "b_element_id(s)": [3, 4, 6, 7], "by": "morph_to", "window": [0.0, 0.85]},
    {"a_element_id(s)": [1, 5, 10, 12], "b_element_id(s)": [1], "by": "colour", "window": [0.0, 1.0]}
  ],
  "finish": "The swirl is zero by t=0.8; residual mismatch inside the disk is closed by the optimal-transport morph, stars complete by a brightness-ordered reveal.",
  "helper": null,
  "knobs": ["swirl_peak_angle", "flatten_start_t", "deck_immunity (0 = the deck is swirled too, 1 = only rotated)"],
  "surprise": 5,
  "risk": "invention: at peak swirl the smeared strata can look like a made-up texture that exists in neither photo; cap the angle so bridge girders stay legible. crossfade: same disk-dissolve risk as concept 1."
}
```

---

## Pair 2: crowd behind a fence at a brick-wall bar -> shirtless friends on green sofas in a glass lounge

### What I see in the two photos

A is an evening outdoor bar terrace seen through a chain-link fence. Behind it, a white brick wall carries a wall-mounted air-conditioner unit, two large wooden spoked cart wheels plus a small one, a Ukrainian flag (blue over yellow), a painted landscape mural with green hills, cave-art-style figures on a pillar, and hanging string-light garlands. About twenty people stand close together. In the centre, a man in a yellow shirt raises one finger and a man in black raises an open hand. Wooden slatted benches fill the foreground. B is a daytime covered lounge. Hundreds of hanging wooden sticks form the ceiling. On a dark left wall hang a red painting and a blue line-drawing painting, and a glass wall on the right looks onto pine trees. Eight shirtless men sit on green-cushioned sofas with grey woven-rope frames on a wooden plank deck, with a hookah. The front centre man makes a V-sign and the right man points. The photos are unrelated in place and light; the shared themes are a group of friends, raised-hand gestures, pictures on a wall, wood, and a grid (the fence mesh in A, the woven chair frames in B). Detections I would not trust: in A, "fan" 3 [1179,160,1879,825] is the two cart wheels (left wheel about [1180,177,1572,569], right wheel about [1500,408,1892,800]); "fan" 5 is the AC unit; "palm" 11 and 14, "sun" 12 and "animal" 7, 10 and 34 are painted mural details; "building" 2 is the brick wall; thin "person" boxes 55, 58, 59 and 64 at bench height are probably bench rails. In B, "ceiling" 1 is the hanging sticks; the paintings are not detected (red about [0,227,155,661], blue about [200,261,528,640]); "bottle" 20 is the hookah; "wall" 13 is mostly the right sofa and window frame.

### Concept 1 (ranked first): the bar sits down

```json
{
  "idea": "Everything in A takes a seat: the flag splits so its blue band glides left to become the blue painting while its yellow band and the hanging garlands rise into the wooden-stick ceiling, the cart wheels spin, slow down and stretch into the pine trunks behind the glass, the fence mesh slides down and tightens into the woven sofa frames, and the five central people walk and sink into the five matching seated men (raised hand to V-sign, raised finger to the reclining man's gesture) while the rest of the crowd sinks behind the rising sofa backs.",
  "relation": "themed",
  "anchors": [
    {"a_element_id": 9, "b_box": [200, 261, 528, 640], "how": "flag blue band (upper half of id 9) to the blue painting; quad corners"},
    {"a_box": [1104, 735, 1516, 901], "b_element_id": 1, "how": "flag yellow band to the stick ceiling, spread along x by optimal transport"},
    {"a_box": [1180, 177, 1572, 569], "b_element_id": 8, "how": "left wheel hub to trunk id 8 base; spokes to trunk axis"},
    {"a_box": [1500, 408, 1892, 800], "b_element_id": 11, "how": "right wheel hub to trunk id 11"},
    {"a_element_id": 20, "b_element_id": 39, "how": "fence mesh corners to chair-frame corners (ids 39, 43, 35 woven areas), MLS"},
    {"a_element_id": 13, "b_element_id": 31, "how": "raised open hand to V-sign hand; head to head; centre front"},
    {"a_element_id": 16, "b_element_id": 21, "how": "yellow-shirt man raising a finger to the reclining man with the raised hand"},
    {"a_element_id": 31, "b_element_id": 28, "how": "denim-shirt man on the right to the pointing man on the right"},
    {"a_element_id": 27, "b_element_id": 15, "how": "left man to the grey-T-shirt man on the left"},
    {"a_element_id": 32, "b_element_id": 14, "how": "second-left man to the man beside him"}
  ],
  "container": null,
  "camera": {"kind": "none", "fixed_point": "frame centre", "ease": "smootherstep", "parallax": "off"},
  "transforms": [
    {"a_element_id(s)": [9], "b_box": [200, 261, 528, 640], "by": "morph_to", "window": [0.05, 0.70], "note": "blue band only; travels ~950 px left and grows to the painting's aspect; the B line drawing emerges by edge-distance reveal inside the moving matte from t=0.5"},
    {"a_element_id(s)": [9, 16], "b_element_id(s)": [1], "by": "morph_to", "window": [0.10, 0.75], "note": "yellow band and the yellow shirt's colour mass rise to the ceiling; the shirt's geometry stays with its person (colour transfer on the person layer), only the yellow lifts"},
    {"a_box": [1180, 177, 1892, 800], "b_element_id(s)": [7, 8, 11], "by": "log_polar", "window": [0.0, 0.40], "note": "wheels spin up to one turn and decelerate"},
    {"a_box": [1180, 177, 1892, 800], "b_element_id(s)": [7, 8, 11], "by": "morph_to", "window": [0.35, 0.80], "note": "spokes stretch vertically into trunks; brick around them brightens to the glass/sky by colour transfer"},
    {"a_element_id(s)": [20, 18, 19, 26, 43], "b_element_id(s)": [39, 43, 35], "by": "mls", "window": [0.15, 0.80], "note": "mesh descends and its diamond cells contract into the rope weave"},
    {"a_element_id(s)": [13, 16, 31, 27, 32], "b_element_id(s)": [31, 21, 28, 15, 14], "by": "move_to", "window": [0.10, 0.70], "note": "people walk to seats; heads and hands are MLS anchors so gestures track"},
    {"a_element_id(s)": [13, 16, 31, 27, 32], "b_element_id(s)": [31, 21, 28, 15, 14], "by": "morph_to", "window": [0.45, 0.90], "note": "surface: noise-ordered patch reveal inside each moving matte, clothes give way to skin and shorts"},
    {"a_element_id(s)": [21, 22, 24, 29, 33, 35, 38, 39, 40, 44, 47, 48, 49, 51], "b_element_id(s)": [30, 39, 43, 35], "by": "move_to", "window": [0.20, 0.75], "note": "remaining crowd sinks straight down behind the sofa backs, which rise from below as an occluding layer"},
    {"a_element_id(s)": [66, 68, 69, 70], "b_element_id(s)": [48, 51, 55, 54], "by": "morph_to", "window": [0.25, 0.90], "note": "bench slats rotate into deck planks; seat tops take the green cushion colour"},
    {"a_element_id(s)": [2], "b_element_id(s)": [6, 3], "by": "colour", "window": [0.0, 1.0], "note": "brick wall: left part darkens to B's wall, right part brightens to the window"}
  ],
  "finish": "From t=0.8 each carried element sits on its B matte; the last mismatch (faces, small objects, the hookah) closes by a noise-ordered reveal inside the B mattes, finished by t=1.",
  "helper": {"what it generates": "one keyframe at t=0.5: B's lounge with A's five central people already seated in the five B seats, clothes still A's", "what it must keep": "B's room, sofas, ceiling and paintings unchanged and every person drawn from A or B; no added people or props"},
  "knobs": ["crowd_sink_depth (how far the extra people sink before the sofa backs cover them)", "wheel_spin_turns", "flag_split_time (when blue and yellow separate)"],
  "surprise": 4,
  "risk": "crossfade: the face surface change on five people is the weakest link; if the patch reveal is too fine it reads as a double exposure, so use coarse patches aligned to facial landmarks. cutout: people walking as rigid mattes read as 2D cut-outs; they need MLS limb warps and depth ordering against the rising sofa backs. invention: the helper keyframe must be checked for added hands or faces."
}
```

### Concept 2: through the painted hills into the window

```json
{
  "idea": "The camera pushes into A's small landscape mural; inside it the painted green hills and blue sky are carried onto B's real pines and sky, and the camera then pulls back out of B's glass wall into the lounge, so the mural turns out to be the window.",
  "relation": "themed",
  "anchors": [
    {"a_box": [829, 514, 1064, 794], "b_element_id": 3, "how": "mural quad to window quad (B [584,0,1919,737]); hill line to the tree-line base, painted sky to the sky gaps"}
  ],
  "container": {"in": "B", "element_ids": [3], "rim": "quad"},
  "camera": {"kind": "zoom", "fixed_point": "mural centre (946,654) in A, then window centre (1250,370) in B", "ease": "ease-in quint into the mural to t=0.45, ease-out quint pull-back from t=0.55", "parallax": "depth"},
  "transforms": [
    {"a_box": [829, 514, 1064, 794], "b_element_id(s)": [10, 7, 8, 11, 12], "by": "morph_to", "window": [0.30, 0.70], "note": "painted hills to foliage mass, painted sky to sky; brushwork texture carried by optimal transport"},
    {"a_element_id(s)": [2], "b_element_id(s)": [1, 6], "by": "colour", "window": [0.0, 0.45], "note": "the brick framing the mural darkens toward B's wall tone before it leaves frame"},
    {"a_element_id(s)": [13, 16], "b_element_id(s)": [31, 21], "by": "move_to", "window": [0.0, 0.40], "note": "the two raised hands drift into the mural edge as the camera passes them, so A's gestures lead the eye in"}
  ],
  "finish": "The pull-back ends on B's own frame at t=0.8; the last 20% is camera settle only, with the depth dolly unwinding parallax to zero.",
  "helper": {"what it generates": "a 4x upscale plate of A's mural crop", "what it must keep": "the mural's composition and colours; no new shapes"},
  "knobs": ["zoom_depth (how far into the mural before the swap)", "swap_window", "pullback_parallax"],
  "surprise": 3,
  "risk": "pan-over-dissolve: the swap happens while the frame is filled by a texture, which is a zoom hiding a cut; it holds only if the hills visibly become trees. invention: the mural is ~235x280 px in canvas, so the push needs the upscale helper, and an upscaler can add brush detail."
}
```

---

## Pair 3: man in yellow jacket peeking from behind a tree -> friends at a café, one holding up a phone

### What I see in the two photos

A shows a man in a bright yellow jacket peeking out from behind a tree trunk on the left. His hands are clasped at chest height and he looks sideways toward the right; the background is soft green and orange bokeh. The trunk occupies x 0-200, the face is near (280, 167) and the clasped hands about [175, 367, 385, 556]. B is a phone snapshot at a café. A man on the left in a navy T-shirt (face about [0, 278, 189, 578]) holds up a phone in his right hand: hand and phone about [206, 278, 433, 800], phone body about [311, 280, 358, 456]. A woman in green peeks from behind that raised hand (face about [189, 383, 300, 500]), and a woman in black on the right smiles at the camera (face about [450, 294, 544, 428]). Behind them are a monstera plant, a cream brick wall with painted birds, a dried palm-thatch canopy, yellow drain pipes (about [78, 0, 183, 156]) and a yellow planter. The shared motif is a person peeking from behind a vertical occluder: in A the man peeks past the trunk, in B the woman peeks past the raised hand. A's clasped hands and B's raised hand also occupy almost the same canvas region. Detections I would not trust: in A, "wall" 6 is the bright bokeh at the right edge, not a wall. In B, "galaxy core" 13 is the phone's edge or camera; "animal" 5, 6, 8 and 9 are painted birds; "building" 2 is the brick wall and window.

### Concept 1 (ranked first): the peek is passed on

```json
{
  "idea": "The trunk turns into the man on the left, the clasped rubbing hands rise and open into the hand holding up the phone (same place, new surface), the peeking face slides down behind that hand and becomes the woman peeking in B, and the yellow jacket comes apart into every yellow thing in B: the drain pipes, the planter and the painted birds.",
  "relation": "themed",
  "anchors": [
    {"a_box": [175, 367, 385, 556], "b_box": [206, 278, 433, 800], "how": "knuckles to knuckles, fingertips to the fingertips around the phone; MLS with ~8 pairs"},
    {"a_element_id": 1, "b_element_id": 10, "how": "trunk silhouette (near, disparity 0.90) to the left man's head and shoulders (nearest in B, 0.51); trunk's right edge to the man's profile"},
    {"a_box": [210, 60, 390, 270], "b_box": [189, 383, 300, 500], "how": "A face to the peeking woman's face: eyes, nose, mouth landmarks"},
    {"a_element_id": 3, "b_box": [78, 0, 183, 156], "how": "jacket collar and shoulders to the drain pipes"},
    {"a_box": [300, 560, 420, 660], "b_element_id": 21, "how": "jacket cuff with its black label to the yellow planter"},
    {"a_element_id": 5, "b_element_id": 3, "how": "green bokeh to the monstera leaves"}
  ],
  "container": null,
  "camera": {"kind": "dolly", "fixed_point": "the hands (280,460), which keep their place", "ease": "smootherstep", "parallax": "depth"},
  "transforms": [
    {"a_box": [175, 367, 385, 556], "b_box": [206, 278, 433, 800], "by": "mls", "window": [0.0, 0.70], "note": "hands unclasp, the right hand lifts and its fingers close around where the phone will be"},
    {"a_box": [175, 367, 385, 556], "b_box": [206, 278, 433, 800], "by": "morph_to", "window": [0.40, 0.90], "note": "phone body emerges from the gap between the fingers by an edge-distance reveal inside the hand matte"},
    {"a_element_id(s)": [1], "b_element_id(s)": [10], "by": "morph_to", "window": [0.10, 0.85], "note": "bark to navy cotton and skin; the trunk keeps its left-side place, so it reads as the tree turning round"},
    {"a_box": [210, 60, 390, 270], "b_box": [189, 383, 300, 500], "by": "move_to", "window": [0.15, 0.65], "note": "the face drops ~270 px and shrinks, staying behind the rising hand layer so it is always peeking"},
    {"a_box": [210, 60, 390, 270], "b_box": [189, 383, 300, 500], "by": "morph_to", "window": [0.45, 0.90]},
    {"a_element_id(s)": [3], "b_element_id(s)": [21, 5, 6, 8, 9], "by": "morph_to", "window": [0.20, 0.85], "note": "optimal transport of the yellow mass into the pipes, planter and painted birds; whatever yellow remains is handed to colour transfer on the cream wall"},
    {"a_element_id(s)": [3], "b_element_id(s)": [15, 11, 22], "by": "colour", "window": [0.30, 0.90], "note": "jacket area not taken by yellow objects takes on the green and black clothes of the two women"},
    {"a_element_id(s)": [2, 4, 5, 6, 7], "b_element_id(s)": [2, 3, 12], "by": "morph_to", "window": [0.0, 0.80], "note": "bokeh gains focus into leaves, thatch and brick by an edge-distance reveal"}
  ],
  "finish": "By t=0.8 the hand, the left man and the peeking face are on their B mattes; the right woman (id 11) completes last through a noise-ordered reveal inside her matte, sourced from the jacket's right half that already sits there, so the last frame is B.",
  "helper": {"what it generates": "one keyframe at t=0.5: B's scene with the left man still bark-textured and the centre woman's face half A's face", "what it must keep": "B's layout, the hand and phone, the women and all background objects; no new person, object or yellow item"},
  "knobs": ["face_drop_start (when the peeking face starts to slide behind the hand)", "yellow_split_ratio (share of the jacket going to objects vs. to wall colour)", "trunk_to_man_window"],
  "surprise": 5,
  "risk": "crossfade: the face-to-face change is the most likely double exposure; drive it by landmarks with a coarse noise reveal, never by alpha. invention: the A photo is a widely shared meme of a real person; the transition only reuses its pixels, but the helper must not generate a new face. cutout: the descending face is a matte moving over B and must stay occluded by the hand layer the whole way."
}
```

### Concept 2: the meme goes into the phone

```json
{
  "idea": "A pulls back and shrinks into the phone the man in B is holding up, as if he had just shown the picture to the women, while the parts of A that leave the phone's outline turn into the B elements at the same positions (trunk into the left man, jacket yellow into the planter and pipes).",
  "relation": "themed",
  "anchors": [
    {"a_box": [0, 0, 602, 800], "b_box": [311, 280, 358, 456], "how": "A's frame corners to the phone body's four corners (quad, foreshortened)"},
    {"a_element_id": 1, "b_element_id": 10, "how": "the trunk strip that falls outside the phone outline is carried to the left man"},
    {"a_element_id": 3, "b_element_id": 21, "how": "jacket parts outside the outline to the planter and pipes"}
  ],
  "container": {"in": "B", "element_ids": [], "box": [311, 280, 358, 456], "rim": "quad"},
  "camera": {"kind": "pullback", "fixed_point": "the phone centre (334,368)", "ease": "ease-out cubic", "parallax": "depth"},
  "transforms": [
    {"a_element_id(s)": [1], "b_element_id(s)": [10], "by": "morph_to", "window": [0.10, 0.75]},
    {"a_element_id(s)": [3], "b_element_id(s)": [21, 5, 6, 8, 9], "by": "morph_to", "window": [0.15, 0.80]},
    {"a_box": [175, 367, 385, 556], "b_box": [206, 278, 433, 800], "by": "mls", "window": [0.20, 0.80], "note": "A's hands are the last part outside the phone; they become the fingers holding it"},
    {"a_box": [0, 0, 602, 800], "b_box": [311, 280, 358, 456], "by": "colour", "window": [0.70, 1.0], "note": "inside the quad, A darkens to the phone's black back by a brightness-ordered reveal (brightest last)"}
  ],
  "finish": "From t=0.8 the quad holds a darkening thumbnail of A; it reaches the phone's own pixels at t=1.",
  "helper": null,
  "knobs": ["phone_quad_tilt (how much foreshortening the shrinking frame takes)", "outside_carry_strength (how much of A outside the outline is carried vs. left to B)", "darken_start_t"],
  "surprise": 4,
  "risk": "cutout: a shrinking rectangle over B is a picture-in-picture, the shape the client calls cheap 2D work, unless the carried parts visibly leave the rectangle and become B elements. invention: the phone shows its back, so A 'on the phone' is a story the photo does not show; the quad must end on the phone's real pixels."
}
```
