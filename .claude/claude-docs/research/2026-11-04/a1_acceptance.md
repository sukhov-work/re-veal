<!-- Provenance: written by an Opus 5.5 subagent (the acceptance drive of the studio's phase A1 per STUDIO.md §9, through the served page in headless Chrome by the Playwright MCP and curl against the API, 22:22–22:50) of the Claude Code session of 2026-11-04 (the studio phase A1 build; DECISIONS 2026-11-04 sixth line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/a1_acceptance.md (sha256 01ebfc4da0bad943) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). 13 of 15 checks passed; the two fails (the 2× mode at 1.27×, a placeholder at 3.9:1) and the five medium defects were fixed by the main thread at 22:57 (DECISIONS 2026-11-04 sixth line). A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

## Findings: A1 acceptance drive

Result: 13 of the 15 checks pass and 2 fail. Check 8 fails on the 2× mode only. Check 14 fails on one detector finding, a placeholder at 3.9:1 contrast.

Scope: the brief's 15 checks for the studio's first build phase (A1 in STUDIO.md section 9), driven on 2026-11-04 from 22:22 to 22:50. I drove the page at http://127.0.0.1:8380/ in headless Chrome through Playwright, and used `curl` for API codes.

Names used below:
- "the adopted job" is `loop_angel_20261104-220708`, the angel run folder `benchmarks/runs/2026-11-04/angel` adopted as a job.
- "my job" is `loop_angel_20261104-223204`, created by check 3 from `/Users/yevhens/Downloads/Telegram Desktop/angel-portrait`.
- "the old server" is pid 6616, started 22:23:03; it served checks 1 to 12.
- "the new file" is `scripts/research/studio.py` with md5 5e8109dcc6837544c2d329a637b3c7a4, on disk since 22:37:05; it served checks 13 to 15.

Action asked: fix the five medium defects (the `.part` candidates, the 1:1 clipping, the 2× scale, the frozen poll, the prep move) before the owner's eye.

### Verdicts

| # | check | verdict | evidence |
|---|---|---|---|
| 1 | the shell loads | PASS | 0 console errors at load; the rail lists `loop_angel_20261104-220708` and `loop_angel_20261104-220719`; acc_01_shell.jpg |
| 2 | the adopted job, graded | PASS | Strip: registration done "467 inl.", render "5 full, 3 drafts; unjudged: a1, a2, a3, a4, a5", page "md5 72dadc4f…", grades ungraded. The iframe shows the 2026-11-04 page with 5 videos. After the save the chip reads "graded". The API's rounds[0].grade.text equals the verbatim text (Python `==`); page_md5 72dadc4f5ea4db16152fe0c7062a3f94. acc_02_adopted.jpg, acc_03_graded.jpg |
| 3 | a new job from the form | PASS | My job appeared in the rail and opened. `ls -la`: raw/angel/01.jpg and 02.jpg are symlinks to the two originals. job.json holds sha256 c0bb68c6… and b2a1dd82…. acc_04_new.jpg |
| 4 | registration from the inspector | PASS | Knobs set: ref 0, depth_maps on, the recorded lock windows. The tile went running, then done in 4.0 s. `cmp` of k0.png, k1.png, depth_k0.npy, depth_k1.npy against the session's files: all identical. prep.json frames[1]: "sift+magsac + lock", 467 inliers, shift [-4.93, 11.48], crop [29, 0, 1395, 1770]. The panel lists each window's offset and correlation. acc_05_registration.jpg |
| 5 | readers from the inspector | PASS | k0: 3 faces, focus 51.6. k1: 2 faces, focus 73.3. Lab distance above 14 on 30.2 % of the pair, above 30 on 13.4 %. acc_06_readers.jpg |
| 6 | the full a2 render | PASS | The tile read "running 15/50 frames" at 2.1 s and "running 41/50 frames" in acc_07_running.jpg. Done in 63.0 s. md5_mp4 c302623f293eacd069218fd7518e0967; script_md5 and rife_version present; the record lists loop.mp4 with that md5. A second a2 got HTTP 409 "…/angel/a2 exists: choose another name". |
| 7 | the 960 draft a2d | PASS | Progress 15/50 to 49/50 frames, then the encode; done in 21.0 s under drafts/angel/a2d/. Its card chip reads "draft 960". acc_08a_draft_running.jpg, acc_08_draft.jpg |
| 8 | the viewer on a2 | FAIL (2× only) | Present: the scrubber (0 to 49), the 49-point step series, the 0.3 bar, 24 violet bands, the cursor. After 15 ArrowRight presses: f15, violet outline, chip "generated t 0.0927". Shift moved ten (15, 25, 15). Space played 25 frames in about 1 s and paused. 2× renders at 1.269×, not 2×. The mark wrote owner_frames/full_a2_f0015.json with the note; a red marker sits at f15. acc_09_viewer_f15.jpg, acc_09b_viewer_2x.jpg, acc_10_marked.jpg |
| 9 | hints | PASS | Popovers opened on the draft knob, the seam_step measure and the render tile. `GET /api/registry` has 86 hint keys. On the 8 panels, no `?` popover says "no hint recorded" (0 gaps). acc_11_hint.jpg |
| 10 | the skeptic request | PASS | requests/skeptic_20261104-224015.json holds a2 with md5 c302623f…, the brief and the f15 mark. `studio.py requests` printed it at 6 s old ("1 open request(s)"). The rail showed "waiting 0 s". acc_12_request.jpg |
| 11 | the page gate | PASS | Without the override: HTTP 409 naming "a2 (unjudged: no skeptic verdict for this candidate)", and no index.html, page.md5, round or record. With the override: index.html md5 45c8bbec0e9e2088216383a343e08162 equals page.md5. The footer prints "Override: built on his word with a2 (…) (2026-11-04T22:40:53)."; round 1 opened; the rail reads "round 1 ungraded". acc_13_page_refused.jpg, acc_14_page_built.jpg |
| 12 | the round gate | PASS | The full a1 got HTTP 409 "round 1 has no grade text: …". The draft a1d (480) ran in 7.0 s. After "mark ungraded by his word" the full a1 ran in 67.0 s with md5 1068c289b5fe782fd21579f825c0d77f. acc_15_round_gate.jpg |
| 13 | a restart during a render | PASS | a2r: the old server ignored SIGINT and stopped on SIGTERM; child 24331 kept running. Server 24645 logged "still runs after a restart; re-attached"; the record ended done, 6 outputs, note "finished after a restart…". a2l: after `kill -9 -- -25090` and a restart, the record became lost with its reason. Neither record stayed running or pending. |
| 14 | the detector | FAIL | One finding at 2560x1440 and the same one at 1440x900, exit 2: [low-contrast] placeholder "what you see at this frame", 3.9:1 (need 4.5:1), #757575 on #141618. |
| 15 | every panel at 2560×1440 | PASS | acc_16_import, acc_16_registration, acc_16_readers, acc_16_plan, acc_16_render, acc_16_skeptic, acc_16_page, acc_16_grades (.jpg). Plan a2_breath020 saved with 1 change, /effects/0/z from 0.018 to 0.02, words "test of the plan editor". Its from_sha256 aef637f0… equals the frozen file's sha256. |

### Defects

Format: [severity] where · what happened · how to reproduce · classification. Ranked by severity; every studio defect is still in the new file (checked by grep).

1. [medium] `candidates()` in studio.py · A render's `.part` folder is listed as a candidate once measure.json lands in it, before the rename. The panel auto-selected `a2.part`, whose requests returned HTTP 400. The viewer stayed empty under "a render is full|draft/<name>" until I clicked a2. The poll repeated the request: 25 console errors from `a2.part`, `a1.part` and `a1d.part`. · Run a full render on a job with no candidate; watch the console during the encode and measure phases. · my-change
2. [medium] the viewer's frame box (`.frame`: align-items center, overflow auto) · At 1:1 the top 515 px of the 1770 px frame cannot be scrolled into view; at 2× the lost band is 753 screen px. That band holds the ring light's top arc. · Open a2, press 1:1, scroll the frame box to its top; the image top sits 515 px above the box. · my-change
3. [medium] the viewer's 2× mode (`.frame img` shrinks as a flex item) · The image gets width 2732 px and pixelated rendering, but it renders 1734 px wide: 1.269×. · Press 2×, then read `getBoundingClientRect().width` of `#frameImg`. · my-change
4. [medium] the page's poll (`openJob()` has no catch) · One failed fetch during a server restart ("TypeError: Failed to fetch") ends the poll for good. The strip kept "running 46/50 frames" and the rail "running" for a finished record until I reloaded. · Open a job, restart the server, wait 10 s. · my-change
5. [medium] a registration rerun under the new file · The rerun moves the old prep, with keys.jpg and readers/, to in/angel_prev_20261104-224918. Both pages of my job link in/angel/keys.jpg, which now returns 404. Round 1's page survives only as stages/20261104-224913_page/previous_index.html. The rerun was accepted while a page build on the same prep was still running. · Build a page, rerun registration with the same knobs, open the page. · my-change
6. [low] the mark field's placeholder colour · The CSS sets no ::placeholder colour, so Chrome's #757575 sits on #141618 at 3.9:1, under the 4.5:1 bar. · Run `impeccable detect --no-advisory` at either viewport. · my-change
7. [low] the step plot (SVG) · The caption line (y 116 to 130) overlaps the frame-number ticks (y 119 to 133). The setting preserveAspectRatio="none" also stretches the text sideways. · Open any render in the viewer; acc_10_marked.jpg shows both. · my-change
8. [low] the render panel's layout · With 1 full render and 1 draft listed, the scrubber starts at y 1450 and the plot at y 1481 in a 1440 px viewport. The frame and the axis share the screen only after a scroll. · Open my job's render panel at 2560×1440 and leave the default scroll. · my-change
9. [low] the message line (`S.msg` is global) · "round 1 graded…" from the adopted job showed in my job's panel. The HTTP 400 message stayed after a good selection. The plan's "saved …" line showed on the render panel. · Act in one panel, then open another panel or job. · my-change
10. [low] the page's copy and stage state · The import panel says the symlinks sit "under in/raw"; they sit under raw/angel/. The mark button reads "mark f as a fault". The rail says "round 1 ungraded" where the strip says "ungraded by his word". A new job opens on the stage used last (grades). · Open each panel; mark a round ungraded. · my-change
11. [low] the records' wall times · The records keep whole-second timestamps, so the readers tile reads "0.0 s" and every wall time carries ±1 s. · Run the readers stage. · my-change
12. [low] the "unchanged" rule of STUDIO.md section 4 (its failure code C4) · No code implements it. My registration rerun gave byte-identical k0.png, k1.png and depth maps, and the tile said nothing. prep.json differs on every rerun because it carries its date. · Rerun registration with the same knobs. · my-change
13. [low] the plan provenance · Every plan saved from the page records author "owner". My agent's save of a2_breath020 carries author "owner" and my words "test of the plan editor". · Save any plan from the plan panel. · my-change
14. [low] the `.part` folder of a lost record · The a2l record left drafts/angel/a2l.part with a partial 265,655-byte loop.mp4 and a 262,144-byte loop.gif. · Kill a render's process group, then restart the server. · my-change
15. [infra] the server's launch mode · A server started with `nohup … &` from a non-interactive shell ignores SIGINT. `kill -INT` stopped neither pid 6616 nor pid 24645 within 1 s; SIGTERM did, so the "stopped" log line never printed. · Start the server with the brief's command, then send `kill -INT`. · infra
16. [infra] the detector's browser · The impeccable binary launched Google Chrome 156. During the 1440x900 pass its processes connected to 172.217.117.4:443, 209.85.202.138:443 and 34.104.35.123:80. The studio page holds no external URL. · Run the detector while `lsof` watches its process tree. · infra
17. [infra] the Playwright viewport · The emulated viewport fell back to 2560×1353 between acc_02 and acc_03, so acc_03 to acc_06 are 2560×1353. I re-applied 2560×1440 from acc_07 on. · Not reproduced; the cause is UNVERIFIED. · infra

### Numbers

- Render md5s (loop.mp4): a2 full c302623f293eacd069218fd7518e0967; a1 full 1068c289b5fe782fd21579f825c0d77f; a2d (960) 3d453980f80eff43014646a6f65398a6; a1d (480) ef9453e51675409d1aa5dce51a621995; a2r (480) 2955c25c2611565b3ee57d2d081f8669.
- Prep md5s, identical to the session's by `cmp`: k0.png ccdb458cc6f25c5440640136e2862877; k1.png 558688ea70079c924092838738f5caa1; depth_k0.npy be5f197b14139379a68bf778378f7203; depth_k1.npy abc016300ed337e4e653cba82599b08f.
- Page md5s: the adopted job 72dadc4f5ea4db16152fe0c7062a3f94, unchanged at the end; my job's round 1 45c8bbec0e9e2088216383a343e08162; my job's round 2 60867571a3c7d36069c74fefb1810fcd.
- Script md5s: loop_seq.py eba20856bdccd17bbfedde0d7ae17b08, equal to script_md5 in every measure.json; studio.py 5e8109dcc6837544c2d329a637b3c7a4 since 22:37:05.
- Readers, k0: faces [299, 695, 313, 386] 0.935, [783, 629, 300, 365] 0.931, [616, 1087, 114, 114] 0.758; focus 51.6; grey mean 109.6; clipped 0 high, 287,417 low; depth mean 0.269.
- Readers, k1: faces [770, 630, 291, 373] 0.934, [287, 694, 311, 396] 0.932; focus 73.3; grey mean 115.3; clipped 40,645 high, 285,583 low; depth mean 0.287.
- Readers, the pair k0 to k1: Lab distance above 14 on 0.3021 of the pixels, above 30 on 0.1343.
- Registration, frames[1]: 467 inliers of 751 matches; window offsets (6.14, -12.59), (4.7, -10.9), (3.96, -10.97); correlations 0.992, 0.993, 0.976; shift [-4.93, 11.48].
- Wall times of the full renders: a2 63.0 s (render_s 57.7); a1 67.0 s (render_s 61.0).
- Wall times of the stages before rendering: registration 4.0 s; readers 0.0 s; round 1 page 0.0 s.
- Wall times of the drafts: a2d 21.0 s; a1d 7.0 s; a2r 8.0 s across the restart; a2l lost at 7.0 s.
- Progress seen on the tile: a2 full 15/50 frames at 2.1 s, 17/50 at 8.4 s, 41 to 49/50 frames, 20/50 effects, 0/50 encode, 50/50 encode, 50/50 measure. a2d 15 to 49/50 frames, 0/50 and 50/50 encode. a1d 19, 25, 43, 49/50 frames, 0/50 encode, 50/50 measure. a1 full 15/50 frames at 2.4 s.
- a2 measures: 50 frames; step_max 4.091 at f43; seam_step 1.536; generated_share 0.48; f15 at t 0.0927 with dexp 0.0027.
- Playback: 50 image loads in 2.0 s, 25 per second.
- Restart A (a2r): started 22:45:11.9; SIGTERM stopped the old server at 22:45:17.5; server 24645 answered at 22:45:19.0.
- Restart B (a2l): started 22:45:59.9; server 24645 stopped at 22:46:05.5; the child group was killed at 22:46:06.3; server 25473 answered at 22:46:07.4.
- Console errors before the first reload: 30. Of these, 25 came from the `.part` candidates, 3 from expected HTTP 409 refusals and 2 from the restart.

### Screenshots

All in `benchmarks/runs/2026-11-04/studio/shots/`, JPEG at css scale.
- 2560×1440: acc_01_shell.jpg, acc_02_adopted.jpg, acc_07_running.jpg, acc_08a_draft_running.jpg, acc_08_draft.jpg, acc_09_viewer_f15.jpg, acc_09b_viewer_2x.jpg, acc_10_marked.jpg.
- 2560×1440: acc_11_hint.jpg, acc_12_request.jpg, acc_13_page_refused.jpg, acc_14_page_built.jpg, acc_15_round_gate.jpg.
- 2560×1440: acc_16_import.jpg, acc_16_registration.jpg, acc_16_readers.jpg, acc_16_plan.jpg, acc_16_render.jpg, acc_16_skeptic.jpg, acc_16_page.jpg, acc_16_grades.jpg.
- 2560×1353, after the viewport reset: acc_03_graded.jpg, acc_04_new.jpg, acc_05_registration.jpg, acc_06_readers.jpg. acc_04 also shows the adopted job's message in my job's panel.

### Confidence: 85%

The verdicts rest on files, md5s and HTTP codes read by command. The main doubt is the code change at 22:37:05: checks 1 to 12 ran the old server, whose code I could not hash.

### Gaps

- The code changed under the drive. The old server (started 22:23:03) served checks 1 to 12; the new file served checks 13 to 15. Every defect above is still in the new file (grep).
- Not driven: cancel from the inspector; the adopt form (the adopted job already existed); a failed or refused stage.
- Not driven: a skeptic answer, so no verdict chip, no judged md5 and no "unjudged after a fix" state were seen.
- The playback rate is measured by the frame counter and the image loads, not by eye. The 2560x1440 detector pass watched only the detector's own sockets.
- I ran two extra probes during check 15 on my job: a round-2 page with the override, and a registration rerun. The new file accepted both (HTTP 202).
- Those probes left my job with round 2 ungraded, which blocks its next full render. They also left a new prep and stale readers.
- Plan a2_breath020 in my job is a test artifact. Its author "owner" and its words "test of the plan editor" are mine, not his.
- On the adopted job I wrote only round 1's grade text, inside its studio folder. No file under benchmarks/runs/2026-11-04/angel is newer than 22:20; its index.html md5 is still 72dadc4f….
- The job `loop_angel_20261104-220719` changed during my drive (records 222628 to 222844, from another actor). I did not touch it.
- End state: the server listens on 127.0.0.1:8380 as pid 25473, which is in the pid file. Nothing listens on 8390.
