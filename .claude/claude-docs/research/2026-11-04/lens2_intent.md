<!-- Provenance: written by an Opus 5.5 subagent (skeptic lens 2, the owner's intent and the operator's failures, on STUDIO.md) of the Claude Code session of 2026-11-04 (the studio design; DECISIONS 2026-11-04 second line); copied verbatim from benchmarks/runs/2026-11-04/studio/agents/lens2_intent.md (sha256 3aeca58796ae1436) on the owner's standing order of 2026-10-17 ("record useful researches … as persistent documents"). His order clause by clause (loops answered in phase A, the rest deferred; no-slop, "flexibly adapt" and general sequences unanswered at the time), the twelve failures against the mechanisms (five without one), the missing requirements, the shapes that did not fit (the Halloween round, the 7-still repaint, a refused pair, a clip), his taste (one grade text per round), the decisions already answered. STUDIO.md §12 records what changed. A research artifact: its claims carry the author's own confidence and gaps; not re-verified at the copy. -->

---
reader: the main thread of the 2026-11-04 UI design session and the next session's builder; cold
shape: report
---
## Findings: lens 2 (intent)

Verdict: STUDIO.md answers his order for the loop flow and defers most of the rest. Phase A (the next session) delivers loops only. Pair transitions, the director flow, Reveal's own features, the models panel, the Strix Halo box and photo-to-video all wait for phases B to D. Three clauses of his order have no answer at all: the no-slop pass, "flexibly adapt" (suggestions by match or mismatch), and "general sequences" beyond the loop grammar. Five of the twelve operator failures have no mechanism: a fix that changed nothing (C4), nothing played at speed (C5), an unasked candidate on the page (C7), a knob against a ruling (C8), and knobs piling up per pair (C11). The page endpoint does not enforce the skeptic gate that Track B §E4 asks for. The first thing he will do is grade the two ungraded pages. No path exists for that, because the studio cannot open a run folder made before it existed.

Asked of the main thread: the three changes at the end. Open question for him: the skeptic bypass (§7 b).

Terms. "The box" is the Strix Halo machine reached by `ssh strix`. "Skeptic pass" is an Opus 5.5 subagent that reviews every candidate before he sees a page. "Phase A to D" are the rows of STUDIO.md §9. "Cn", "Vn", "Tn", "Rn" are rows of `trackB_distill.md` §C and §E. "The workbench" is `scripts/research/director_ui.py`. Every line reference is to STUDIO.md unless another file is named.

### 1. His words, clause by clause

| Clause (2026-11-04 order) | Where answered | Verdict |
|---|---|---|
| enrich the UI tool | §0, §8 option A: a new `studio.py` that replaces the workbench's page | answered |
| an additional mode, or more tweaks | §2: four flows in one shell; the loop is the added flow | answered |
| loops | §2 loop rows; §9 phase A | answered |
| general sequences | only through `loop_seq.py`. §1 caps a sequence at 2–6 stills. The 7-still repaint path (`chain_luma.py --variant draw`, `benchmarks/2026-10-09-fabra-boxes.md` stage 6) and the sequence stitch (EXPLORATION_PLAN UI4) are absent or in phase D | partial |
| full control over everything | §2 registry and §3 inspector over the loop SCHEMA keys. Track A gap 2 lists knobs no surface reaches: 23 global-only `CFG` keys in `reveal.py`, six `transitions.py` spec fields, and `loop_seq.py --set` taking top-level keys only. STUDIO.md does not tell him which knobs stay out of reach | partial |
| expand the main transitions UI we built before | §9 phase B rebuilds the workbench's panels; §10.4 retires the workbench. He said "expand"; the design chose "replace" | deferred (B), and replaced instead of expanded |
| convenient and efficient | §3 shell, the keyboard, the copyable command. No check measures time or clicks against the session's own run (angel `prep` 6 s, a2 render about 60 s, NEXT_SESSION §1) | partial |
| expose all the tools | §2 registry; for the loop flow only in phase A | partial; the rest deferred (B–D) |
| show visually all the processes | the stage strip (§2, DESIGN.md "the stage strip"). Session-side work appears only as an answer file: the planner prompt and its sha256, the director track and the record step (sheet, DECISIONS line) have no tile | partial |
| let me tune them | inspector knobs and "rerun from here" (§2, §3, §5 `run` with `from`) | answered for loops; deferred for the rest |
| every transition and loop | loops in A, pair and director in B, align in C | deferred (B, C) |
| regardless of match / mismatch | mismatch_3 is phase B's check. His 2026-10-20 "analysis on how much mismatch, suggestions for given cases" has no panel: `suggest` occurs 0 times in STUDIO.md. EXPLORATION_PLAN UI3 had "the suggestions panel from the tooling list filtered by the relation" and STUDIO.md drops it without saying so | deferred (B), suggestions missing |
| flexibly adapt and handle | none. He picks the flow before import (`POST /api/jobs {flow, …}`). A refused pair shows "refused" and the reason (§1) and offers no route to the flow that would take it | missing |
| external and internal models | §2 "readers" in A (depth, faces, mattes, layers); the models panel and the box in D | partial; the box deferred (D) |
| optional halo box support for the flows | §5 `/api/box`, §10.7, phase D: keyframe and plate kinds only. If "halo box" meant the angel's glow box instead, annotations with `role: glow` cover it in A (§4). The box reading is the likely one, given "external and internal models" in the same sentence [INFERRED] | deferred (D) |
| original reveal features | §2 align rows, phase C | deferred (C) |
| impeccable pass | §6: detector, `audit`, `harden`, `clarify`, `polish` | answered |
| no-slop pass | `no-slop` occurs 0 times in STUDIO.md; nothing applies it to the UI's copy (chip words, refusals, help lines) | missing |
| (2026-10-20) photo to video and back | phase D, "the video endpoints (UI4)"; `job.json` `inputs` has no clip kind | deferred (D) |

### 2. The twelve failures

| Cn | Mechanism in STUDIO.md | Verdict |
|---|---|---|
| C1 windows off the object | windows drawn on the still as annotations (§4 `role: lock`); `prep --windows` draws them on `windows.jpg` with dx, dy per fit (§7) | prevented, if the lock knob takes drawn boxes only and offers no free-text coordinate field (STUDIO.md does not say) |
| C2 stale watch md5 | `script_md5` in `render.json` (§4, §7) | partial: the md5 names the script, but the script's bytes at that md5 are not kept. Seasons s6 (5ec0fe31) shows exactly this case: the md5 is known and no code reproduces it. Copy the script into the job folder by md5, or record the git commit plus a dirty flag |
| C3 fixes shown unjudged | `judged_md5` against the current md5 gives the chip "unjudged after a fix" (§4) | partial: the chip only displays the state. `POST /api/jobs/<id>/page` (§5) builds a page with unjudged renders on it; Track B §E4's rule "a page is offered only after a skeptic answer file exists for the shown md5s" is not enforced |
| C4 a fix that changed nothing | none | missing: on a rerun, compare the new mp4 md5 with the parent render's and show the chip "identical to <rid>" |
| C5 drafts and crops hid defects; nothing played at speed | the draft chip (§4) | missing: the viewer scrubs JPEGs by index (§3), with no play at 25 fps and no record that anyone played it. `at speed` occurs 0 times. §10.5 also recommends grading drafts, against `loops.md §2.3` ("a 640 px draft shows nothing a skeptic can judge") |
| C6 he saw renders before the page | a draft is a draft in its folder name and its chip (§4) | prevented, given that the studio shows everything by design |
| C7 an unasked or NOT READY candidate shown as a peer | none: the page endpoint takes `{order, notes}` | missing: the page lists NOT READY and unrequested candidates under their own heading, or leaves them off |
| C8 a knob broke a recorded ruling | none: the knob schema has name, type, range, default and sentence (§2); `ruling` occurs 0 times | missing: a rulings table in the registry, each row a forbidden value with his words and date (`hole_reveal` true, `carry` above 0, holds on inner stills, n ≥ 4 on a big move, 30 fps gif; `loops.md §3–§5`). A ruling warns, and he may override it |
| C9 plans without provenance | the provenance block on every saved plan (§4) | prevented; add the planner prompt's sha256 when the session writes the plan |
| C10 exposure step not read before an effect | the import tile shows exposure and focus differences (§2) | partial: shown, but nothing links it to the `glow` knob |
| C11 pair-specific knobs piling up | the changed-from-default weight (§3) | partial: no count of changed knobs per plan, no warning, no re-render of the accepted pieces when a script default changes |
| C12 recording traps | argv built by the server removes the heredoc trap (§5); `page` with `order` (§5) | partial: `--ref 0` is not defaulted when two fits are compared (`loops.md §8`), and the page's order is not required to come from `candidates/` |

### 3. Requirements coverage (missing or partial only)

- §E4, the skeptic gate on the page: not enforced. Fix: `POST /page` refuses, or labels "unjudged", every candidate whose `judged_md5` differs from its md5.
- V7, frame source tags: only generated frames are marked "each with its t" (§2 loop render row). Add the hold, blend and snap tags from `frames.json`.
- V11, parked rounds: rejected fits are listed; parked rounds (`round<N>/`, angel `round1a/`) have no place in the §4 data model. Add `rounds/<n>/` or a `parked` state per candidate.
- R3, grades saved before the next render: nothing enforces the order. Fix: a `run` on a job with an open page and no picks file asks for the grades first.
- T1, every SCHEMA key: Track A §Gaps 1 and 3 found that `matte: {"all": true}` crashes every method except plain `rife` (`loop_seq.py` L488) and that `breath.depth_k` does nothing without `parallax` (L1442), and that SCHEMA.md and the code disagree on three keys. A form generated from SCHEMA.md will offer all of these. STUDIO.md names none (`bug` occurs 0 times). Add them to §7, fixed or guarded.
- §F: "bands moving at once per frame" and the generated share are missing from the `measure` command (§7).
- §E5, the box: `strix_keyframe.sh` defaults to `MODEL=qwen`, which is Qwen-Image-Edit-2511 Q4_K_M (script lines 11, 50). His standing rule is no 4-bit quants (the memory file `no-4bit-quants.md`). `remote_queue.json` items carry no model field (§4). Fix: a model field on each item, pinned to the Q8 or bf16 models, with Q4 refused.

### 4. Overfitting

The loop flow fits the angel and the seasons. These four cases do not fit as written.

| Case | What would not fit | Fix |
|---|---|---|
| Halloween, 10 sequences of 2–6 stills, 24 candidates on one page, four rounds (`loops.md §2.5`: "One page, every candidate") | a job is one folder with one page (§4); "round" is only a number in the rail (§3). Ten sequences would make ten jobs and ten pages | a round object above jobs: several jobs, one page, one grade text |
| The boxes repaint, 7 stills, one gradual clip with a long end hold (fabra sheet stages 5–6) | §1 caps stills at 6; `chain_luma.py --variant draw` is in no flow; the seam measure assumes a loop | no upper bound on stills; a "sequence clip" flow or a `chain_luma` stage; the seam measure skipped for a one-way clip |
| A mismatch pair | phase B only; no suggestion panel; a refusal from Reveal (exit 2) is a dead end | a refused tile offers the flows that accept the pair (pair class B, director) |
| Photo to video (UI4) | `inputs: [{path, sha256, exif}]` has stills only; no frame-extraction stage | `inputs[].kind: still or clip`, plus a frame index per endpoint |

The §9 phase A check uses the angel only, with three windows known in advance. Keep it, and add one drive on a sequence the design was not written around (§6).

### 5. His taste

- The grade form. `candidates.<name>.{grade, words}` (§3) splits his grade per candidate. He grades a round in one short text that crosses candidates and carries the next order: "all ugly except s4"; "good keep s6 it is perfect, now want to experiment …" (PRODUCT.md line 17; NEXT_SESSION "Owner orders"). Fix: one verbatim text box per round, saved first; per-candidate marks optional. The director's checkbox form (`director_picks_11.json`) stays for director rounds.
- Polish. His 2026-10-20 words: "you can still keep it highly technical and bare in terms of polishing, this is simply to speed up our iterations". Phase A runs five impeccable passes on top of a full redesign, inside a session with a 70 % chance of fitting (§11). Run the detector once; run `polish` last and drop it if time runs out. Dense tables, monospace data and copyable command lines are what he asked for.
- Waiting. A request file waits for a session that may not be running. The skeptic pass takes 5–6 minutes (`loops.md §7`). A "waiting" chip with an age and no one watching is a pause he did not ask for. Fix: the session writes a heartbeat file; the chip says "no session watching" when it is stale.
- Nothing in the visual design reads as "junky" or "cardboard"; those words were about clips (`loops.md §3`). DESIGN.md's neutral grey suits judging photographs. His eye on the first screen decides.

### 6. The acceptance checks

The §9 checks are the builder's proof: a Playwright drive that re-renders a2 to its known md5. His first screen will be different. The angel page (md5 72dadc4f) and the seasons round 4 are both ungraded (NEXT_SESSION §0), so he will open them to grade. Their folders under `benchmarks/runs/2026-11-04/angel/` have no `job.json` or `stage.json`, and STUDIO.md has no "adopt a run folder" path. Add to phase A:

1. Adopt the angel run folder as a job, with its five candidates, the skeptic verdicts and the page md5; grade it with one round text.
2. Apply "20 % faster" to a candidate and show the frame counts that changed.
3. Play a render at 25 fps in the viewer.
4. Reproduce seasons s6 (mp4 md5 5908af3d…, NEXT_SESSION §1) through the studio, to show the accepted piece survives.
5. Drive one held-out sequence: a Halloween sequence with a declared cut (`--cut`), or a pair Reveal refuses. Show the refused chip, a failed render's chip, and the C3, C4 and C7 rules firing.

### 7. The decisions

Already answered; do not re-ask him:
- §10.1, the engine download: his order names the impeccable repository, and the standing order says "fetch anything you need" (NEXT_SESSION "Standing order").
- §10.6, a headless Claude Code process: STUDIO.md itself says his 2026-10-21 answer (a request file) stands.
- §10.5 Q5, grading drafts: `loops.md §2.3` and failure C5 already answer it. Make the recommendation "full size for the page; drafts labelled and never on the page", not "yes".
- §10.3, PRODUCT.md's three questions: the file was written from his orders, and `loops.md §1` says "ask nothing up front that the first page can answer". Let the first screen correct the file.
- §10.2 stays a question, but cite "bare in terms of polishing".

Missing, needed before the build:
- (a) The port. §0 and §8 say "a new port", but the studio takes 8379, which is the workbench's default (`director_ui.py` line 1140). The workbench stays live through phases A and B, so the two cannot run together. Pick another port, such as 8380.
- (b) The skeptic bypass. "Full control" suggests he may build a page from his own renders without a skeptic pass. The standing order says a page goes through the skeptic first. STUDIO.md does not decide; he does.
- (c) Retire or expand. He said "expand the main transitions UI". Retiring the workbench (§10.4) needs his explicit yes.
- (d) Out-of-reach knobs. "Full control over everything" includes the `CFG` and `TCFG` keys that only a code change exposes (Track A gap 2). T68 says nothing enters either tool without his word. Ask whether a default-off per-job override flag may enter `reveal.py` and `transitions.py`, or whether those knobs stay out.

### The three changes STUDIO.md needs most (ranked)

1. Enforce the review gates in the data model and endpoints. The page refuses or labels unjudged and NOT READY candidates (C3, C7, §E4). A rerun with an unchanged md5 says so (C4). The rulings table warns on a ruled value (C8). Add a round object above jobs so the Halloween shape fits.
2. Meet his first screen. Add a path that adopts the existing run folders (angel, seasons round 4) and a single verbatim grade text per round. Add a play at 25 fps.
3. Clear the pre-build defects in §7 and §10. Fix or guard the two `loop_seq.py` bugs the form would expose, pin the box queue off Q4 models, move the studio off port 8379, and drop the questions he has already answered.

### Confidence: 75%

Every finding comes from text read on 2026-11-04. The sources: STUDIO.md, PRODUCT.md, DESIGN.md, Track A, B and C, `loops.md`, NEXT_SESSION_PROMPT.md, EXPLORATION_PLAN UI rows, the backlog rows, `strix_keyframe.sh` lines 11–50, `director_ui.py` line 1140, the fabra sheet stages 5–6. Nothing was run.

### Gaps

- UNVERIFIED: whether the workbench and the studio would ever run at the same time in practice. The port clash holds only if they do.
- UNVERIFIED: whether `chain_luma.py --variant draw` still runs with the current code. It goes through `reveal.run_alignment`, which the studio must not import (it would run as a subprocess).
- The "halo box" reading is inferred; both readings are listed in §1.
- Not read: `ui_design.md` in full, the skeptic reports, the DECISIONS lines beyond what Track B quotes.
- The no-slop cold read (pass step 6) was not run on this report; the pattern scan and counts were done by hand.
