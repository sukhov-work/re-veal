# The studio build routine (the package under `studio/`; owner rulings of 2026-10-21, 2026-11-04 and 2026-11-05)

Read `.claude/conventions/studio.md` first (the layout, the rules, the gates). This file holds
the routine a studio change follows and the routing of the subagents. `STUDIO.md` is the design
of record; its §9 lists the phases with their acceptance checks; its §13 records the package.

## What a studio change is
| Change | Tier | Reads | Gate |
|---|---|---|---|
| a hint sentence, a chip, a knob's default from the script | Quick | the registry module | `make qa` (the prose test covers the sentence) |
| a stage, a panel, a route, a view (one module and its test) | Standard | `conventions/studio.md`, `STUDIO.md §2–§5`, the neighbouring module | `make qa` + `make test`; the routine below before his eye |
| a new flow (align, pair, director), a change to the runner's rules or the job folder layout, a change to the research script a stage runs | Deep | `STUDIO.md` whole, the registry, `loops.md`, `contracts.md`'s studio section | `make qa` + `make test` + `make acceptance`; the routine below; a DECISIONS line with `[revert: …]` |

The old script `scripts/research/studio.py` is retired (2026-11-05); a studio change lands in the
package only. A research script gains a default-off flag at most, proved byte-identical on the
default path before and after (`loops.md`, `research/2026-11-04/loopseq_flags.md`); nothing
enters `reveal.py` or `transitions.py` without the owner's word (invariant 7, T68).

## The routine before his eye (every UI change; the order matters)
1. **Build** in the package with tests alongside; `make qa` green; `make test` green on this
   laptop (the integration layer needs the main venv).
2. **Acceptance drive** (an Opus 5.5 subagent at max effort): the checks of `STUDIO.md §9` for
   the phase, scripted against the served page. The page is driven by Playwright against a
   headless Chrome on port 9222, the API by `curl`. Each check is PASS or FAIL with the observed
   value. The durable form is `studio/tests/acceptance/`, marked `acceptance`. The server under
   test runs on a free port with its own lock path (`--lock`), never on the owner's 8380.
3. **Fable review** (a Fable 5.1 subagent, read-only): the served surface and the diff are read
   against the hard constraints: 127.0.0.1 only, no connection, originals untouched, subprocesses
   only, the job folder as state, the review gates, the never-overwrite rule, restart
   reconciliation. The review gives a verdict per constraint with evidence, in the shape of
   `research/2026-11-04/a1_review.md`.
4. **Critique** (an Opus 5.5 subagent): impeccable's `critique` method on the served page, with
   the engine's detector at three viewports:
   `IMPECCABLE_BIN=/Users/yevhens/Projects/ai/impeccable/skill/scripts/bin/darwin-arm64/impeccable DO_NOT_TRACK=1 impeccable detect --no-advisory --viewport 2560x1440 http://127.0.0.1:<port>/`,
   then `1440x900` and `1280x800`. The score out of 40 is read against the previous one (the comp
   24, A1 26). 0 anti-patterns is the bar before his eye. `audit`, `harden` and `clarify` run at a
   phase close; `polish` runs last or not at all (his 2026-10-20 "bare in terms of polishing").
5. **Prose**: every sentence the page shows and every text of the session passes the no-slop
   pass (`.claude/rules/prose.md`); the prose test pins the hints.
6. **Fix or record**: every finding is fixed the same session or lands in
   `references/tracked-backlog.md` with its reason; a contested behaviour is the owner's call and
   rides the handover's questions (T77 is the worked example).
   A critique that lists more than a few items gets a fix round. One Opus 5.5 subagent runs it on
   its own port and headless Chrome, from a brief that lists every item by its source. Its report
   re-runs the gates, the acceptance, the detector and a keyboard drive on the final tree.
   `research/2026-11-05/a2_fixes.md` is the worked example (37 of 39 items; what it left became
   backlog rows).
7. **Record**: the DECISIONS line carries the checks' results with numbers, the detector's count,
   the critique's score and the md5 that reproduced. `STUDIO.md §13` gains a dated paragraph.
   `studio/ARCHITECTURE.md` changes when a module moved; `contracts.md` changes when a route or a
   shape changed. The handover's watches name the a2 md5 through the package and the detector at 0.

## Routing
The main thread writes the briefs, integrates, runs the gates and writes every record. Opus 5.5
subagents at max effort build, drive and critique; a Fable 5.1 subagent reviews. Waves of at most
three subagents; each writes its report under `benchmarks/runs/<date>/studio/agents/<name>.md`
and runs the no-slop pass on it; the main thread copies the reports to
`.claude/claude-docs/research/<date>/` with a provenance header before the commit. Two
subagents never own the same file: a brief names the files each owns and marks the shared ones
Edit-only.

## Watches a studio session leaves in the handover
- The a2 render through the package gives md5 c302623f293eacd069218fd7518e0967 from a new job of
  the angel stills with the recorded lock windows (the A1 acceptance anchor, `STUDIO.md §9`).
- The three jobs of 2026-11-04 are listed, and the adopted one opens with its grade text.
- The detector reports 0 anti-patterns at the three viewports.
- `make qa` is green with its counts; the GitHub workflow is green on the last push.

## What phase B taught the routine (2026-11-06)
- A flow is built in waves: one generalization slice first, alone and green, with a snapshot test of the incumbent path pinned before the first edit (`tests/test_loop_snapshot.py`, never regenerated); then the flow builders in parallel on disjoint files, each with a fake script under `tests/fakes/`; then the drive, the review and the critique in one wave; then one fix round. The design note that fixes the shared shapes (`research/2026-11-05/b_design.md`) comes before the slice.
- An acceptance anchor is re-measured from the record's argv (`render.json`, `stage.json`) before it is pinned: the workbench's md5 carried two knobs its report never named (DECISIONS 2026-11-05 eighth and ninth lines).
- Every long chain runs under `caffeinate -i`: this laptop sleeps on battery and a frozen wait expires on wake (four sleeps on 2026-11-05 stalled the drives). One rendering drive at a time on the tree (T88, T119).
- The wave-3 agents read the builders' reports and the design note, not the session; the critique's score (26 of 40 for B, 28 for A2) is read against the previous one, and the fix round takes every P1 and P2 and the one-line minors.
