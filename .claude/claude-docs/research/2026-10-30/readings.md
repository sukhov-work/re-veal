<!-- Provenance: written by an Opus 5.5 subagent (the readings, round 3) of the Claude Code session of 2026-10-30 (the Halloween loops; DECISIONS 2026-10-30 round 3); copied verbatim from benchmarks/runs/2026-10-30/halloween/agents/readings/report.md (sha256 9a3f3a32704614d1; the values in readings/readings.json beside it) on the owner's standing order of 2026-10-17. The anchor and box readings for round 3: the talk's wand ends and six more anchors (±2–10 px), the teleporting woman's two boxes and her border with the leopard-mask man, the ghoul's hat-and-head boxes and the rise point behind the man's shoulder (the final JSON names the shoulder's outer corner (470,548) and keeps the shoulder top (530,500); the round-3 plans used the earlier reading, a rise straight up from x 530). A research artifact: the readings were used as given; their error bars are the author's. -->

# Readings, round 3 (2026-10-30): talk, group-teleport, zeke-back

Two of the four "static" talk anchors moved between k0 and k1: the top-hat crown moved by (+23, +18) and the witch-hat tip by (-55, -11). The talk wand reads within ±5 px only in k0; its k1 ends carry ±6-10 px.
All values are in canvas pixels of each sequence's registered stills and are in `readings.json`, each with a ±px error.
The cane grip moved by (-2, -2) and the ceiling lamp by (+3, -3), so registration on the background agrees to about 3 px.

## How I read them
I read every value from cv2 crops at 2-4x with a 25 px or 10 px grid, saved in `readings/crops/`, and checked it numerically:
- talk wand, k0: a line fit of the tan shaft pixels (HSV hue 9-22, x 450-585) gives the axis y = 760 - 0.39(x - 465); I read the ends on that axis from `talk_k0_knob.png` and `talk_k0_handle2.png`.
- talk wand, k1: I diffed k1 against k0 (`talk_k1_diff.png`), where the streak shows clearly, and measured its left and right edges per row; the streak centre line runs (544,526) (531,580) (520,610) (493,640) (462,710). Rows below y 630 are mixed with her arm, so I read the lower end from `talk_k1_bot2.png`.
- Other talk anchors: dark-pixel crown extents per row (hat), the rightmost dark pixel (witch-hat tip), the top of the black blob (cane), and the lamp ellipse centroid. Template matching confirmed the cane (0.987) and lamp (0.99+). On the hat crown, template matching slid along the straight top edge (it returned -23 px in x against my +23 px), so I did not use it there.
- Teleport ear tops come from the first magenta row (178 in k0, 197 in k1). Zeke box edges come from dark-pixel (<55) extents per column and row.

## Talk wand (the values that need ±5 px)
| point | k0 | k1 | ± (k0, k1) |
|---|---|---|---|
| handle end | (423,777) | (455,730) | 8, 10 |
| knob tip on the axis | (652,687) | (553,501) | 5, 6 |
| knob ball centre | (636,691) | (547,516) | 4, 8 |

The handle end is the least certain point. In k0 its last few px lie under her fingers; the visible tan tip is at (422,780). In k1 the streak's visible centre line enters her fist at (458,722) ±6. Setting the k0 wand length (246 px) along the streak puts the end at (455,730). The k1 streak is 236 px long visibly and bends slightly, with the slope dx/dy going from -0.35 near the top to -0.44 near the fist. For the k1 knob tip I rejected the diff's first rows at y 484-488: in raw k1 pixels the wall runs to y 488, the man's dark shoulder edge starts at 491 (it moved about 3 px between stills, which is what the diff picked up), and the streak's tan tint starts at y 497-503.

## Ambiguous points
- Teleport k1: her right boot toe reaches x 544, in front of the leopard-mask man's legs, while her upper body ends at 440-447. The k1 box is therefore wider than her torso. The shoulder border (440) includes her bag strap; her jacket alone ends at 420.
- Zeke: the ghoul's left jacket edge (x0 ≈ 424 in k1, 417 in k4) touches the girl's dark hair below y 620, which is why the error there is ±8. The red-white cloth at (840-930, 720-780) is left out of both ghoul boxes because I could not tell whose it is. The k4 sleeve bottom (730) is ±10 because of a shadow next to that cloth.
- Zeke rise point (470,548) ±10: a hat rising straight up from behind the man first shows where his outline is lowest within the hat's x span (about 440-620). That is the outer corner of his right shoulder, on the viewer's left. The shoulder top (530,500) is stored as `shoulder_top_k1` in case the director wants the hat over the shoulder top instead. In k1 the ghoul's hand covers the shoulder top, so I estimated the shoulder line from its visible ends, (508,502) and (464,560).
- Zeke head-and-hat boxes end at x 605, where the crown meets the man's hair. The k4 sleeve bottom carries ±15 because the dark scan reaches y 759 at x 880, which I read as shadow.

```json
{
 "units": "canvas pixels of each sequence's registered stills (x right, y down)",
 "date": "2026-10-30",
 "talk": {
  "canvas": [
   1140,
   1910
  ],
  "anchors": [
   {
    "label": "wand handle end (k0: the stick's end in her hands; k1: streak centre line extended to the k0 wand length, inside her fist)",
    "pt": [
     423,
     777,
     455,
     730
    ],
    "err": [
     8,
     10
    ],
    "note": "k0 end partly hidden under her fingers, read from a line fit of the tan shaft (x 450-585) plus the visible tip at (422,780). k1: visible streak centre enters the fist at (458,722) +-6; the k0 wand length (246 px) puts the end ~9 px further, (455,730)."
   },
   {
    "label": "wand knob tip (far end on the wand axis)",
    "pt": [
     652,
     687,
     553,
     501
    ],
    "err": [
     5,
     6
    ],
    "note": "k0 axis y = 760 - 0.39*(x-465), knob ball centre (636,691). k1: top of the streak at the centre of its width, read from raw k1 pixels: wall down to y 488, the man's dark shoulder edge at 491, the streak's tan tint starts at 497-503 for x 540-555. The diff scan's first rows at y 484-488 come from his shoulder edge shifting ~3 px between stills, not from the wand, so I rejected them. Streak centre line (544,526) (531,580) (520,610) (493,640) (462,710)."
   },
   {
    "label": "wand knob ball centre",
    "pt": [
     636,
     691,
     547,
     516
    ],
    "err": [
     4,
     8
    ]
   },
   {
    "label": "top hat: crown top, centre of the crown width (NOT static: his head moved)",
    "pt": [
     655,
     272,
     678,
     290
    ],
    "err": [
     4,
     4
    ]
   },
   {
    "label": "witch hat tip (NOT static: she turned; k1 tip motion-blurred)",
    "pt": [
     465,
     410,
     410,
     399
    ],
    "err": [
     3,
     8
    ]
   },
   {
    "label": "cane handle: top of the black grip above his fist",
    "pt": [
     863,
     1056,
     861,
     1054
    ],
    "err": [
     3,
     3
    ]
   },
   {
    "label": "wall/ceiling point: left end of the lower ceiling lamp ellipse",
    "pt": [
     415,
     153,
     418,
     150
    ],
    "err": [
     3,
     3
    ]
   },
   {
    "label": "ceiling lamp ellipse centroid (pixels > 235)",
    "pt": [
     527,
     153,
     530,
     150
    ],
    "err": [
     2,
     2
    ]
   }
  ]
 },
 "teleport": {
  "canvas": [
   1870,
   1278
  ],
  "box_k0": {
   "xyxy": [
    1499,
    178,
    1759,
    1050
   ],
   "err": [
    4,
    2,
    3,
    3
   ],
   "note": "top = pink ears (first magenta row 178-179); left = her left hand at the belt (1499,490), boots reach only 1522; right = her left elbow (1759,~445); bottom = boot soles."
  },
  "box_k1": {
   "xyxy": [
    259,
    197,
    544,
    1015
   ],
   "err": [
    3,
    2,
    4,
    3
   ],
   "note": "left = her right sleeve (259,452); right = toe of her forward boot (544,1007), in front of the leopard-mask man's legs; her upper body ends at 440-447."
  },
  "border_x_k1": {
   "shoulder": {
    "x": 440,
    "y": 375,
    "err": 4,
    "note": "includes her brown bag strap over the shoulder; the olive jacket itself ends at 420; read at y 375, on the upper arm just below the shoulder top (~y 340)"
   },
   "hip": {
    "x": 447,
    "y": 515,
    "err": 5,
    "note": "her hand on her hip; her body/belt without the hand ends ~440"
   }
  },
  "bag_k1": {
   "xyxy": [
    282,
    560,
    417,
    728
   ],
   "err": [
    4,
    5,
    4,
    4
   ],
   "note": "bag body and its short handles; right edge is the metal clip/strap at 417 (body alone ends ~400); the long shoulder strap running up to (440,375) is excluded."
  }
 },
 "zeke": {
  "canvas": [
   1186,
   1874
  ],
  "ghoul_box_k1": {
   "xyxy": [
    424,
    276,
    945,
    700
   ],
   "err": [
    8,
    3,
    3,
    8
   ],
   "head_and_hat_xyxy": [
    440,
    276,
    605,
    472
   ],
   "note": "x0 = his dark jacket left of the man's shoulder (~y 600; the girl's hair is dark below y 620 and limits the reading), hat brim reaches 440; x1 = his left sleeve showing past the man's left arm (945, ~y 640); y1 = bottom of that sleeve (x 915). Hands on the man's shoulders at x 500-600 and 735-780, y 460-515. The red-white cloth at (840-930, 720-780) is excluded: owner unclear. head_and_hat x1 = 605 is where the crown meets the man's hair (read from the crop), not a free edge."
  },
  "man_box_k1": {
   "xyxy": [
    460,
    250,
    890,
    540
   ],
   "err": [
    5,
    5,
    6,
    10
   ],
   "hair_top": [
    680,
    250
   ],
   "hair_wisps_top_y": 248,
   "head_x": [
    602,
    770
   ],
   "shoulder_line": {
    "left_top": [
     508,
     502
    ],
    "left_edge": [
     464,
     560
    ],
    "right_top": [
     840,
     490
    ],
    "right_edge": [
     882,
     560
    ]
   },
   "note": "occluding outline: hair top 250, head 602-770, shoulder tops ~500 on both sides (both under the ghoul's hands), jacket outer edges 464 / 882 at y 560. Box bottom 540 = where the shoulder slope reaches the outer edge."
  },
  "rise_point_k1": {
   "pt": [
    470,
    548
   ],
   "err": 10,
   "rule": "a hat rising straight up from behind the man first shows where his outline is lowest (largest y) within the hat's x span (~440-620)",
   "note": "the outer corner of his right shoulder (viewer's left), where the shoulder slope (508,502) -> (464,560) meets the jacket's outer edge. The ghoul's hand covers the shoulder top in k1."
  },
  "ghoul_box_k4": {
   "xyxy": [
    412,
    281,
    913,
    730
   ],
   "err": [
    4,
    3,
    4,
    15
   ],
   "head_and_hat_xyxy": [
    412,
    281,
    605,
    472
   ],
   "note": "x0 = hat brim (412,440); jacket left ~417 at y 580; x1 = his left sleeve (913, ~y 645); y1 = sleeve bottom 730 at x 895-905, less certain (shadow near the red cloth). head_and_hat x1 = 605 is where the crown meets the man's hair (read from the crop), not a free edge. The dark column scan at x 880 reaches y 759; I read that as shadow beside the red cloth, hence +-15 on y1."
  },
  "shoulder_top_k1": {
   "pt": [
    530,
    500
   ],
   "err": 10,
   "note": "top of the same shoulder, midway between the neck (~600) and the outer edge (~464); the alternative if the hat is meant to appear over the shoulder top rather than at its corner."
  }
 },
 "crops": "readings/crops/*.png (grid 25 px unless named *_handle/_knob/_top/_bot/_cane/_border/_left/_right/_hairtop/_lshoulder/_rsleeve, which use 10 px; yellow lines every 4 grid steps, labelled)"
}```
