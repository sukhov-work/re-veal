# Reveal: Internal Handoff

Audience: engineers and AI agents continuing this tool. The operator doc is
README.md. Source of truth for behavior is reveal.py (v1.5.0, ~2,500 lines,
single file by design, mirroring organize.py/viewer.py). Written 2026-07-10
at the end of the founding build session; extended the same day (v1.1.0:
user-selectable matching modes; v1.2.0-1.3.0: phase-3 residual redesigned
after the first field defect; v1.3.1: confidence rescored on
scene-independent evidence after the first real-pair validation; v1.4.0:
learned matcher executed for the first time, and consequently replaced;
v1.5.0: that matcher made genuinely offline). Design research lives in
the
companion report "Before/After Photo Aligner: Design-Ready Technical Report"
(same thread); this doc records what was actually built and verified.

Relationship to the media-organizer project: standalone tool, separate venv,
shared conventions only (single-file Python, stdlib HTTP server bound to
127.0.0.1, ./setup.sh + ./run.sh operator surface, plain-language README,
pinned requirements with verified arm64 wheels, assertion harness, VERSION
discipline, evidence-labeled engineering communication).

## 1. What this is

A local web tool that aligns photo B (after) onto photo A (before) of the
same subject shot days apart from roughly the same spot, then presents the
pair behind a comparison slider, with export of the aligned stills and a
wipe/fade transition video. All three build phases from the design report
shipped in v1.0.0: classical pipeline (phase 1), learned-matcher fallback
(phase 2, optional install), bounded residual flow (phase 3, auto-gated).

## 2. Invariants

1. **Localhost only.** The server binds 127.0.0.1. No exceptions.
2. **Originals are never modified.** Uploads are copied into the job dir;
   all outputs are new files there.
3. **BEFORE is the reference frame.** B is always warped onto A, never the
   reverse. Every geometric quantity is expressed B->A.
4. **Convergence is judged on inlier statistics, not pixel similarity.**
   The changed region legitimately differs; MAGSAC++ inliers ignore it by
   construction. Pixel metrics (peripheral SSIM, edge overlap) are computed
   on the static periphery only, and only for display/validation. Do not
   optimize against them.
5. **The residual field is low-order by construction.** Phase 3 applies
   only a robustly fitted 20-parameter (2D cubic) field: it structurally
   cannot content-chase or wobble, needs no masks or ramps, and treats the
   subject like the scene (the subject's lens distortion is as real as
   the wall's). Samples come from the gradient-supported static periphery;
   Huber IRLS plus a fit-vs-flow re-admission pass handle misclassified
   displacement; a field exceeding the 6 work-px cap anywhere is rejected
   whole, never clipped; the far-periphery SSIM gate decides keeping; off
   entirely in loose mode. Never reintroduce spatially masked dense flow:
   both dense interpolation and every masked/feathered variant bend
   subjects (field defect #1, section 5a).
6. **Degradation is graceful.** rawpy, pillow-heif, imageio-ffmpeg, and
   torch/kornia are optional layers; absence produces a plain message
   (`check` shows the full matrix), never a crash.
7. **Operator surface stays ./setup.sh + ./run.sh + the page.** Engineer
   features go into the CLI (`align`, `check`) or constants, not the UI.

## 2a. Matching modes (v1.1.0)

Every job carries a mode; `profile(mode)` overlays CFG.

- **reshot** (default): unchanged v1.0.0 behavior; the strict
  deliberate-re-shot prior.
- **loose**: for similar-but-different pairs (another person in the same
  scene, two look-alike objects in different scenes). Overrides: ratio
  0.82, min_matches 8, MAGSAC threshold 5 px, min_inliers 12, good_rmse
  4 px, corner shift <= 0.80 diag, area ratio [0.2, 5.0], ECC trust 24 px,
  residual flow OFF (invariant 5: flow on different subjects chases
  content), manual sliders +-15% shift / +-15 deg / +-30% size / doubled
  keystone, learned matcher consulted always (not only below-bar), and a
  4-DOF similarity fallback: `estimateAffinePartial2D` competes on every
  match set (methods tagged '+sim'); candidate ranking prefers ones that
  pass the stop bar, homography over similarity on ties, so 8 DOF wins
  only when actually supported. Similarity-model results are ECC-refined
  with MOTION_AFFINE, not homography, to avoid reintroducing the overfit.

Mode travels as a multipart field on upload (unknown values fall back to
reshot), is echoed in status along with the slider limits (the frontend
adopts them, nothing is hardcoded twice), reaches the CLI as
`align --mode loose`, and the failure screen offers a one-click loose
retry when a strict job fails. Note the same-scene subject-swap case
passes in strict mode already (background anchors it, harness check 58);
loose exists for the cross-scene and large-transform cases.

## 3. Pipeline

decode -> working copies (1600 px long edge) -> estimate -> refine ->
measure -> interactive render (2000 px source, 1400 px preview JPEG) ->
export (full res stills, videos at fixed target sizes).

### 3.1 Decode
Pillow (+pillow-heif) for JPEG/PNG/HEIC with `ImageOps.exif_transpose` and
ICC->sRGB via ImageCms when a profile is embedded (iPhone Display P3).
rawpy for DNG/ARW with `postprocess(use_camera_wb=True, output_bps=8)`;
rawpy applies the camera flip itself, so EXIF orientation is deliberately
NOT re-applied to RAW output (double-rotation trap).

### 3.2 Estimation chain (working resolution, grayscale)
1. SIFT (8k features) -> ratio 0.75 -> `findHomography(USAC_MAGSAC, 2.0 px)`.
2. If SIFT missing/weak: ORB same route. Best candidate wins on
   (inliers, -rmse).
3. If below the stop bar and torch+kornia importable: DISK keypoints +
   LightGlue matcher (kornia, 1024 px cap, 2048 features, CPU; MPS
   deliberately not used because op-coverage gaps can corrupt results
   silently). Candidates from different matchers are then arbitrated on
   peripheral SSIM, NOT on inlier count (see section 5b).
4. If nothing: phase-correlation translation seed -> ECC rescue
   (accepted only at rho > 0.35 and sane).
5. Sanity gate on every candidate: convex warped quad, area ratio in
   [0.45, 2.2], max corner shift <= 0.40 of the A diagonal. This encodes
   the "deliberate re-shot" prior and rejects degenerate homographies from
   repetitive-texture mismatches.
6. ECC refinement (`MOTION_HOMOGRAPHY`, 120 iters), masked to the static
   scene since v1.2.0: a preliminary changed-region estimate from the
   feature homography is transported to the B frame and passed as ECC's
   inputMask, so a large repainted subject cannot bias the photometric
   refine (side effect: rho now reads static-scene agreement; on the demo
   pair it rose from 0.906 to 0.999). Callers without color images get the
   unmasked path unchanged. Note the convention
   trap that cost a bug during the build: findTransformECC's warp maps
   TEMPLATE(A) coords into INPUT(B) coords (it is applied with
   WARP_INVERSE_MAP), so it is seeded with inv(H) and the result is
   inverted back. Refinement is discarded if it drifts > 12 work-px from
   the feature solution (trust region) or fails to converge.

**Stop metric (primary):** inliers >= 30 AND inlier reprojection
RMSE <= 2.0 px at working resolution -> `metrics.passed`. The UI shows a
soft warning below the bar but still lets the user proceed and hand-tune.

### 3.3 Coordinate transport
`scale_h(H, sA, sB)` with sA/sB = target/source scale factors per frame:
H_target = D(sA) @ H @ D(1/sB). The founding session shipped this inverted
once; the harness now pins it with a ground-truth transport assertion
(check 19). Manual tuning composes AFTER the automatic H, in the A frame,
about the A center: translation/rotation/scale/keystone; params are
resolution-independent fractions so the same params render identically at
preview and export resolution.

### 3.3a Residual field (phase 3, v1.3.0 architecture)
DIS flow provides SAMPLES only. Sample set: static periphery, gradient
support (Sobel magnitude vs its own 75th percentile: textureless pixels
carry no flow evidence), outside the changed mask, >= 2000 required,
subsampled to <= 20k. Fit: 10-term 2D cubic per component, 3-iteration
Huber IRLS (delta 1 px), light ridge on quadratic/cubic terms against
corner extrapolation. Second pass re-admits "changed" pixels whose DIS
flow agrees with the fit within 1 px: residual DISPLACEMENT gets
misclassified as change (a shifted grille diffs strongly), and those are
the strongest-signal samples; content-chasing flow is incoherent and
stays excluded, so the fit itself is the discriminator. Rejection: median
sample magnitude outside (0.4, 9) px, or fitted field exceeding 6 px
anywhere in the valid region (clipping would reintroduce gradients).
Keeping: far-periphery SSIM gain >= 0.01, as before.

### 3.4 Changed region, periphery, metrics
Per-channel mean/std-normalized abs-diff (max over channels: a repaint can
change hue at constant luminance, which killed the first grayscale version
in harness check 21), Otsu threshold, morphology, interior hole filling
(v1.2.0: enclosed 'unchanged' islands inside a repainted subject are
detection misses and leak the periphery into the subject), 21 px
dilation -> `changed`. `peripheral` = valid overlap, eroded 15 px, minus changed.
Displayed: confidence 0-100 = (70% rmse term + 30% inliers/75 term), times
0.6 when the found homography is NOT a local maximum of peripheral
similarity (geometry and pixels disagreeing is a real red flag). Anchor
count, drift px, changed %.

**Do not put a pixel-similarity scale back into the score.** Two were tried
and both are scene-dependent, i.e. not comparable across pairs, which is
the whole job of a 0-100 score (v1.3.1, measured on the first real pair):
(a) ABSOLUTE peripheral SSIM has a ceiling set by texture, sensor noise,
JPEG and resampling, none of which alignment can fix. Real photographs cap
near 0.55 even when perfectly aligned (Yevhen's box pair: 0.551 at 0.74 px
rmse, 458 inliers); synthetic scenes reach 0.89. The old /0.85 divisor came
from synthetic data and docked every real pair by ~15 points. (b) The SSIM
PEAK SHARPNESS (relative drop under a 3 px perturbation) cancels that
ceiling but is confounded by texture density in the opposite direction: a
perfectly aligned smooth synthetic scene measures 0.016 and a textured real
one 0.263, so scoring on it punishes clean scenes. Both survive in
metrics.json as diagnostics; only the local-max BOOLEAN is robust.
Also note `edge_overlap` is blind below ~4 px (its Canny mask is dilated
3 px: 0.919 at perfect alignment, 0.915 at a 4 px error). It is a coarse
sanity check, never a precision metric.

### 3.5 Exposure match
Masked Reinhard in Lab: per-channel (mean, std) transfer computed on the
static periphery at working resolution, applied at any resolution, gains
clamped to [0.4, 2.5], blended by a 0-100 strength. Auto-enabled at
strength 70 when the peripheral luminance Bhattacharyya distance > 0.05.
Warp-then-match order (statistics on truly corresponding pixels).

### 3.6 Crop
Largest axis-aligned rectangle inside the warped-valid mask: exact
O(HW) histogram+stack maximal-rectangle on a <=700 px copy of the mask,
mapped back with a conservative inset; dimensions forced even for yuv420p.

### 3.7 Video
numpy frame compositing piped to the imageio-ffmpeg bundled binary as
rawvideo -> libx264 crf 18 yuv420p +faststart. Timeline: hold, cosine-eased
sweep, hold; wipe has a feathered seam (12 px at 1080 width, scaled); fade
is a plain crossfade. Aspects: 4:5, 9:16, 16:9, 1:1 (cover-crop), original
(capped 1920). The design report's ffmpeg xfade filtergraph was NOT used:
piping frames gives easing and the feathered seam with less filtergraph
fragility, one decision the build deliberately changed from the report.

## 4. HTTP surface

Stdlib ThreadingHTTPServer. Python 3.13 removed `cgi` (PEP 594), so
multipart/form-data is parsed by a hand-rolled binary-safe parser
(`parse_multipart`), body capped at 2 GiB. Routes:
GET / | GET /api/job/{id}/status | GET /api/job/{id}/img/{before|after} |
GET /api/job/{id}/download/{before|after_aligned|video} |
POST /api/job (multipart) | POST /api/job/{id}/tune (JSON, clamped) |
POST /api/job/{id}/export (JSON). Job ids are 16-hex, regex-gated (kills
traversal); downloads only from a fixed allow-list. Alignment and export
run in daemon threads; the page polls status. Tune re-renders in-request
(~0.3-1 s at preview scale).

Full-resolution originals stay in RAM per job (a 61 MP pair ~0.4 GB;
fine on the 36 GB target, and jobs die with the process).

## 5. Frontend

One embedded HTML string, vanilla JS (~10 KB, node --check'ed), no build
step, no external requests. Slider = clip-path inset driven by a CSS
custom property; pointer events, keyboard arrows, one automatic eased
sweep on first ready (skipped under prefers-reduced-motion). During drag
of shift/rotate/size the after layer gets a CSS-transform approximation of
the delta vs the last rendered params; release POSTs tune and swaps in the
authoritative render. Aesthetic: darkroom (deep umber, amber safelight
accent, the pair matted like a print); deliberately NOT the cream+
terracotta default look.

## 5a. Field defect #1: wavy subject edges (fixed in v1.2.0)

Reported on a real pair (graffiti-covered box -> painted mural, full-subject
repaint): straight box edges came out wobbly in after_aligned.jpg. Root
cause chain, reproduced deterministically before fixing (harness 63-65):
changed-mask holes on real repaints (both paint jobs alias in normalized
channel space) -> static periphery leaks inside the subject -> DIS flow
content-chases between the two paintings, and its smoothness term bleeds
those vectors into nearby textureless pixels -> the SSIM keep-gate scores
partly on the leaked region, approving the artifact -> capped 6 work-px
vectors (~15 px at full res) bend the subject edges. Four fixes, each
closing one link: (1) interior hole filling in the changed mask; (2)
gradient-weighted flow voting (textureless pixels carry no flow evidence
and must not vote); (3) the keep-gate measures far periphery only (eroded
25 px, away from changed boundaries); (4) subject rigidification, replacing
suppression. Three designs were built and rejected against reproductions before the
final one: a feathered kill zone and a distance-ramp attenuation both
MANUFACTURE wobble (any spatially varying attenuation of a legitimate
smooth correction bends straight structures crossing the gradient), and
per-subject rigidification (constant vector per changed-cluster hull)
protected subjects but starved them and misclassified-displacement areas
of legitimate correction, and its blend ramp could still land on
undetected subject borders. The final v1.3.0 design replaces dense flow
application entirely with a fitted low-order field (section 3.3a), which
dissolves the subject/scene distinction: a 20-parameter field cannot
chase or wobble anywhere. Measured: subject-edge wobble (quadratic-
residual metric) 8.5 px worst-case before, 0.09-0.12 px after, with the
field matching template-matched ground-truth residual within 0.25 px.
Measurement lessons that cost real time, recorded so the next agent does
not repay them: an edge detector whose window spans two parallel
structures, or an unsigned detector on a two-sided border, fabricates
5-12 px of fake wobble; use signed single-transition tracking and judge
wobble as residual from a fitted quadratic, never from a line (a smooth
lens arc is legitimate). Residual cost of a kept field: one extra
bilinear resample, microscopic softening, no geometric change.

## 5b. The learned matcher: first execution (v1.4.0)

Shipped in v1.1.0 and never once run until 2026-07-13, three releases
later. Executing it found four things, all of which are why unexercised
code is a liability rather than a feature:

1. **kornia fetches LoFTR over plain HTTP** from a personal academic page
   (`http://cmp.felk.cvut.cz/~mishkdmy/models/loftr_outdoor.ckpt`), an
   unauthenticated download of a pickled checkpoint fed to
   `torch.hub.load_state_dict_from_url`. DISK and LightGlue come over
   HTTPS from github (cvlab-epfl/disk, cvg/LightGlue releases).
2. **kornia's LoFTR mishandles non-multiple-of-8 inputs.** Its
   fine-matching stride is `hw0_f[0] // hw0_c[0]` (fine_preprocess.py:62)
   and its keypoint x-scale is `hw0_i[0] / hw0_c[0]`
   (coarse_matching.py:286): both derive from the HEIGHT alone. The old
   `prep()` resized to `round(w*s)`, essentially never a multiple of 8.
3. **The learned path could never be tested here**, because the weights
   are unreachable from the sandbox. It shipped unverified for three
   releases behind a try/except that would have turned any failure into a
   silent `None`, i.e. a 2 GB dependency that quietly does nothing.
4. **A latent crash, dormant since v1.1.0**: when the learned matcher
   returns points that every sanity gate rejects, `max(candidates)` ran on
   an empty list. It only surfaced the moment torch was installed.

So LoFTR is out and DISK+LightGlue is in, verified end to end.

**Inlier count is not comparable across matchers, and this is the sharp
edge.** Measured on Yevhen's real pair: SIFT 458 inliers -> peripheral
SSIM 0.566; DISK+LightGlue 408 inliers -> 0.429. The old ranking picked
the larger inlier count, so a slightly denser learned result would have
won and silently produced a visibly worse alignment. `_arbitrate()` now
scores every cross-matcher candidate by peripheral SSIM against one fixed
mask and picks the visual winner (on that pair: sift 0.566, learned 0.536,
orb 0.485 -> sift).

**It earns its keep on exactly one class.** On a low-texture, repetitive,
heavily relit wall, SIFT finds no usable match at all and DISK+LightGlue
returns 1227 inliers at 0.3 px corner error (harness 77). On rich texture
it is slower and worse than SIFT, which is fine: it is a fallback, and the
arbiter keeps it from winning when it should not.

Runtime: 15 s at 768 px and 34 s at 1280 px on 4 sandbox CPU threads;
expect materially less on the M3 Pro's 10 performance cores [INFERRED].

**Offline contract (v1.5.0).** Three holes were closed:
1. **Model files live in the project**, at `models/hub/checkpoints`
   (`_pin_torch_home()` forces `TORCH_HOME` there). They previously landed
   in the global `~/.cache/torch`, which does not travel with the project
   and which any cache cleaner can delete. Copy the project folder to
   another machine and the learned matcher still works, with no network.
2. **The runtime never downloads.** `_learned_models()` refuses to
   construct anything unless `models/MANIFEST.json` says warmup already
   ran and verified, and only `cmd_warmup` sets `_ALLOW_DOWNLOAD`. A
   missing file produces a clear "run ./setup.sh --learned", not a silent
   network call that hangs on a plane.
3. **Warmup PROVES it, rather than assuming it.** Downloading the
   checkpoints only exercises model CONSTRUCTION. Warmup additionally runs
   a real forward pass on a synthetic textured pair, so any file fetched
   lazily at INFERENCE is fetched at setup instead, where it can fail
   loudly. It then records every file's size and sha256 in the manifest,
   which `check` verifies (deep=True re-hashes).

Verified end to end by harness 81: with `socket.socket` and
`socket.create_connection` both patched to raise, the models cold-load from
`./models` and return 658 matches. Total footprint: 2 files, 52 MB
(depth-save.pth 4.4 MB, disk_lightglue 47.6 MB).

## 6. Decision log

| # | Decision | Rejected alternative | Why |
|---|---|---|---|
| 1 | Inlier stats as stop metric; pixel metrics peripheral-only | edge-map similarity as optimization target | Content legitimately changes; edges of the changed subject would fight the optimizer. Design report section 2 |
| 2 | BEFORE as reference, warp AFTER | warp both to a mean frame | One resampled image, before stays pristine, simpler mental model |
| 3 | ECC seeded from features, trust-regioned | ECC from identity; pure feature H | ECC needs an init; trust region caught real divergence on the unrelated-pair test |
| 4 | Color-aware change detection (max over channels) | grayscale diff | Equal-luminance repaints leaked 12% into the periphery (harness 21 failure) |
| 5 | Residual flow auto-gated on measured SSIM gain, capped 6 px | always-on dense flow | Small-parallax brief; unbounded flow morphs content |
| 6 | Frames-piped video render | ffmpeg xfade filtergraph | Easing + feathered seam controllable in numpy; no input-mismatch fragility |
| 7 | Confidence weighted to precision (45% rmse) | inlier-count-heavy blend | A visually perfect sparse-scene alignment scored 64; recalibrated to 88 on the same demo |
| 8 | Constants, no settings.yaml | operator-editable config | Every knob a user needs is a UI slider; zero-config keeps the tool disposable |
| 9 | Learned matcher = LoFTR on CPU, optional install | DISK+LightGlue; MPS | Detector-free helps exactly the failure class (low texture); CPU avoids silent MPS wrong-results risk; base install stays ~200 MB |
| 10 | Full-res originals in RAM per job | re-decode per render | 61 MP ARW decode is seconds; tuning must feel instant; RAM budget fits |
| 11 | Modes as CFG overlay profiles, strict default untouched | loosening the defaults | The strict prior IS the product for the main purpose; loose is opt-in with an explicit retry path |
| 12 | 4-DOF similarity fallback competing in the ladder (loose only) | homography-only; always-similarity | Few sketchy cross-content matches: 8 DOF overfits outlier structure a rigid model shrugs off; ranking lets the data decide |
| 13 | Residual flow hard-off in loose mode | auto-gate only | The SSIM gate measures the periphery; on cross-scene pairs the periphery itself differs, so the gate is blind there |
| 14 | Fill interior holes of the changed mask | trust Otsu output | A repainted physical object is contiguous; holes are detection misses that leak the periphery into the subject (field defect #1) |
| 15 | Gradient-weighted flow voting | uniform periphery weight | Textureless pixels inherit DIS smoothness-term bleed (often content-chasing) and must not vote |
| 16 | Subject rigidification: constant vector per changed-cluster hull | feathered kill zone; distance-ramp attenuation | Both rejected designs manufacture wobble: spatially varying attenuation of a smooth correction bends straight structures; a constant field cannot |
| 17 | ECC masked to the static scene (inputMask from prelim changed estimate) | unmasked ECC + trust region | Photometric stages must never see the changed subject; trust region caps damage but does not remove bias |
| 18 | Fitted low-order residual field, DIS as samples only | dense flow + rigidification (v1.2.0) | Low-order cannot chase or wobble; masks/ramps in the applied field either bend subjects or starve corrections (three designs rejected empirically) |
| 19 | Fit-vs-flow re-admission of "changed" samples | trust the changed mask | Residual displacement masquerades as change; excluding it starves the fit of its strongest-signal corner samples; coherence with the fit is the discriminator |
| 20 | Whole-field rejection over the cap | per-pixel clipping | Clipping reintroduces spatial gradients, i.e. the wobble mechanism |
| 21 | Confidence on geometry only (rmse + inliers) x local-max penalty | raw SSIM term (v1.0-1.3.0); SSIM peak-sharpness term | Both pixel-similarity scales are scene-dependent in OPPOSITE directions (texture ceiling vs texture-driven peak sharpness); only rmse, inliers and the local-max boolean compare across pairs |
| 22 | Learned matcher = DISK + LightGlue | LoFTR (v1.1.0-1.3.1) | LoFTR's weights come over plain HTTP from a personal page, kornia mishandles non-multiple-of-8 inputs, and the path was untestable and therefore untested for three releases |
| 23 | Cross-matcher arbitration on peripheral SSIM | ranking by inlier count | Inlier counts do not compare across detectors: the learned matcher scored 408 inliers / 0.429 SSIM against SIFT's 458 / 0.566, so a denser learned result would have won with a worse alignment |
| 24 | Weights pre-fetched by ./setup.sh --learned | lazy download on first use | A silent network call mid-job breaks the "fully local" promise and fails at the worst moment; setup-time download fails loudly and keeps every real run offline |
| 25 | TORCH_HOME pinned to <project>/models | the default global ~/.cache/torch | The project must be self-contained: a global cache does not travel with the folder and any cleaner can delete it, after which the runtime would silently re-download |
| 26 | Warmup runs a real forward pass, not just a download | construct the models and assume | Construction only proves the CHECKPOINTS resolve; only inference proves nothing else is fetched lazily. Any hidden fetch then happens at setup, loudly |
| 27 | Runtime refuses to download (manifest-gated) | let torch.hub fetch on demand | A job that quietly waits on the network is worse than one that says "run setup": offline is a promise, not a best effort |

## 7. Harness (harness.py, 82 checks, all passing in-sandbox)

Coverage: multipart parser binary-safety (1-5); decode router incl. EXIF
orientation, HEIC roundtrip, rawpy routing + absence, bad types (6-11);
geometry recovery vs a known ground-truth homography with exposure change
and a changed-content patch: <1.5 px corner error, inliers, RMSE, ECC
(12-16); ORB path and clean failure on unrelated images (17-18); scale
transport (19); changed/peripheral masks vs the injected patch (20-21);
exposure match closing the luma gap >=80% (22-23); crop validity (24-25);
full pipeline to ready + auto-exposure + confidence (26-29); manual
compose exactness (30-32); residual guard (33); headless CLI + real mp4
verified via cv2.VideoCapture: size, fps, duration (34-37); real HTTP
round-trip: upload, poll, previews, tune + clamp, export, download
headers, 404s, traversal shapes, bad upload type, and the 127.0.0.1 bind
(38-51); mode profiles and mode-aware clamps (52-53); similarity
estimator vs a known transform with 30% outliers (54); affine ECC path
(55); the three calibrated mode scenarios: a big-scale look-alike that
strict refuses and loose aligns at 0.5 px, a genuinely perturbed similar
object (different palette, text, proportions) that aligns in loose only,
and a same-scene subject swap that passes in strict (56-58); a loose job
end-to-end with residual forced off and limits in status (59); HTTP mode
round-trip, loose tune ranges, unknown-mode fallback (60-62); field defect
#1 regressions: hole filling; no-added-wobble contract (signed-edge,
quadratic-residual metric) on a full-repaint and a sparse-change pair
whose radial residual (k1 2.5e-8) survives homography absorption and
exercises the fitted path; masked-ECC convergence; the unmasked
back-compat path; fitted field vs template-matched ground truth at 4
probes (<=1 px); whole-field rejection of an over-cap residual (63-69);
confidence monotonicity, the >=90 floor for an excellent real alignment,
the local-max penalty, absence of any SSIM term, local-max discrimination
of a 7 px offset, sharpness declining on a tiny periphery, and the
diagnostics reaching metrics.json (70-76); and the learned matcher
(77-79, skipped cleanly when torch is absent): the low-texture repetitive
rescue that SIFT cannot do, arbitration preferring the visually better
candidate over one claiming 1000x the inliers, and the checksummed weight
cache; plus the offline contract (80-82): model files inside the project
rather than a global cache, a full cold-load-and-match with EVERY socket
patched to raise, and the runtime refusing to download mid-job when the
manifest is gone.

Honest gaps, same class as the organizer's: no real HEIC-from-iPhone, DNG,
or ARW file has ever been decoded in a test (rawpy is exercised via a
fake); the learned path has never executed (no torch in the sandbox); all
runtime numbers below are from a Linux sandbox, not the M3 Pro; no real
before/after photo pair has been through it yet.

## 8. Verified facts and measurements

- Wheels on PyPI for macosx arm64 cp311-cp313, checked 2026-07-10
  [VERIFIED via PyPI JSON]: numpy 2.2.6, opencv-python-headless 5.0.0.93
  (abi3, needs numpy>=2), Pillow 12.3.0, pillow-heif 1.4.0 (needs
  Pillow>=11.1, python>=3.10), rawpy 0.27.0 (cp310-cp314), imageio-ffmpeg
  0.6.0 (bundles ffmpeg; no brew dependency), torch 2.13.0
  (macosx_14_0), kornia 0.8.3 (pure python, needs python>=3.11 -> setup.sh
  requires 3.11+).
- SIFT patent expired 2020; in main opencv module since 4.4 [VERIFIED].
- cgi/cgi.FieldStorage removed in Python 3.13 (PEP 594) [VERIFIED]; hence
  the hand-rolled multipart parser.
- Sandbox timings (Linux x86_64 container, 1600 px working copies)
  [VERIFIED in-harness]: full pipeline on a 1600x1200 pair ~6 s wall
  (SIFT+match ~5 s of it); tune re-render ~0.4 s; 3 s 1080x1080 video
  ~4 s. M3 Pro numbers unmeasured [INFERRED: same order].
- Synthetic ground-truth recovery: 0.5-0.6 px corner error at estimation
  resolution; 1.5 px when transported from half resolution [VERIFIED].

## 9. Risks and open questions, ranked

1. **First real pair validated (2026-07-13), the rest are not.** Yevhen's
   graffiti-to-mural box pair: sift, 458 inliers, 0.74 px rmse, rho 0.946,
   residual declined, box edge straight to 0.54 px RMS against the camera
   original's 0.62 px (the v1.1 output that triggered the defect report
   measured 4.08 px). The 2 px / 30-inlier stop bar held up; the
   confidence formula did not, and was rebuilt (decision 21). Still
   unvalidated: HEIC-from-iPhone, DNG, ARW, landscapes, and any pair where
   the residual field actually fires (this one declined it).
2. **Repetitive metal-box texture** may defeat SIFT on real pairs; that is
   exactly the learned-fallback case. If it triggers often, promote LoFTR
   install from optional to default.
3. **Crop-rect jumping during tuning**: the inscribed rectangle is
   recomputed per render, so big manual shifts change the crop and the
   image size visibly. Accepted for v1; fix would pin the rect from the
   auto pass and shrink-only.
4. **Memory with two 61 MP RAW pairs in flight**: ~1 GB. Jobs are never
   evicted until process exit. Add LRU eviction if multi-pair sessions
   become the norm.
5. **rawpy vs very new Sony bodies**: LibRaw lags new cameras; a failing
   ARW decodes nowhere else in this tool (the organizer's exiftool preview
   trick is not a dependency here). Mitigation: export JPEG from the
   camera app for the affected body.
6. **The learned path is now exercised and offline-proven** (v1.4.0-1.5.0,
   harness 77-82). What remains unverified: it has never run on Apple
   Silicon, only on x86 CPU, and its M3 Pro runtime is [INFERRED], not
   measured. Note also that `models/` is deliberately NOT in the shipped
   zip: warmup fetches it, so a fresh unzip on an air-gapped machine needs
   the folder copied across by hand.
7. **Kept residual flow costs one extra bilinear resample** (microscopic
   softening of the after image, no geometric effect). If Svitlana's
   pixel-peeping ever flags it, render the homography and the flow in a
   single remap (compose the maps) instead of sequentially.
8. **Loose mode trusts the user.** With gates this wide, a confident-
   looking but wrong fit is possible on repetitive content; the UI copy
   explicitly tells the user the numbers mean less there and to trust
   their eyes. Do not widen the strict profile in response to loose-mode
   feedback.

## 10. Runbooks

```
./setup.sh [--learned]            # once
./run.sh [--port 8400]            # serve http://127.0.0.1:8378
source .venv/bin/activate
python reveal.py check            # dependency matrix
python reveal.py align B.jpg A.jpg --out out/ --video --aspect 9:16
python harness.py                 # Gate 1; the check count lives in section 7
```

Working conventions for future agents: identical to the organizer's
HANDOFF.md section 13 (anchored edits with MISS detection, py_compile,
harness before shipping behavior, VERSION bump minor/patch, zip + loose
files every shipped turn, web-verify versioned facts, evidence labels,
anti-slop prose, scope discipline).

## 11. Amendments (dated rows; the sections above are the founding text and are not rewritten)

| Date | Amendment | Where recorded |
|---|---|---|
| 2026-09-13 | This file moved from the repo root to `.claude/claude-docs/HANDOFF.md` (owner: "migrate and adjust as needed"). Citations of the form `HANDOFF.md §N` keep the short name. Section 10's runbook said "51 assertions" while section 7 said 82; the runbook now points at section 7 (backlog T7 closed). | DECISIONS 2026-09-13 |
| 2026-09-13 | Invariant 5's ban on dense or masked flow applied to pixels is scoped to the ALIGNMENT output (`after_aligned.jpg`, the slider, the metrics). A second tool, `transitions.py` (design of record `TRANSITIONS.md`), animates the change between two photos and uses dense fields as the transition's motion. Reveal's pixels are untouched: neither module imports the other. Owner: "dense-flow decision - ok". | DECISIONS 2026-09-13 |
| 2026-09-13 | Decision 9 (no MPS) stands for Reveal. For the transitions tool the device for model stages (dense matcher, generative) is decided per slice by measurement against a CPU run on a fixture; the deterministic tier stays on the CPU. Owner: "lets try to speed up all stages ( at reasonable degree ) … without compromising quality". | DECISIONS 2026-09-13; EXPLORATION_PLAN §TR |
| 2026-09-13 | **First real HEIC decoded and aligned.** Section 7 and section 9.1 say no real HEIC had ever been decoded in a test. On 2026-09-13 the fixture pair `match_1` (two iPhone HEIC files, 6048×8064, EXIF orientation 1, embedded ICC profile, 1.9 s decode each) went through `reveal.py align --mode reshot`: sift, 368 inliers, 0.74 px rmse, ECC rho 0.998, peripheral SSIM 0.849, residual declined, changed 10.4 %, confidence 95, 7.7 s wall on the M3 Pro. A JPEG with EXIF orientation 6 (`match_5_S`) decoded upright as well. Real-pair-VERIFIED for HEIC; DNG and ARW remain untested on real files. | DECISIONS 2026-09-13; `fixtures/MANIFEST.md`; `benchmarks/runs/2026-09-13/` (local) |
| 2026-09-13 | **Roster pair re-measured on the owner's laptop.** The graffiti-box pair of section 9.1 is fixture `match_4`. `align --mode reshot` here (OpenCV 5.0.0, M3 Pro): sift, 481 inliers, 0.79 px rmse, rho 0.946, peripheral SSIM 0.539, residual declined, changed 28.3 %, confidence 94, 5.0 s. Section 9.1 recorded 458 inliers and 0.74 px in the Linux sandbox on 2026-07-13; no estimation code changed between the two runs, so the difference is the environment. The box-edge straightness metric (0.54 px RMS) was not re-measured; the CLI does not compute it. The five `mismatch` fixtures are refused by strict mode with the plain message, as designed. | DECISIONS 2026-09-13 late; `fixtures/MANIFEST.md`; `benchmarks/2026-09-13-real-pairs.md` |
