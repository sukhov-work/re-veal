# Research documents of 2026-10-18 (round 10; copied from the gitignored run folder `benchmarks/runs/2026-10-17/agents/` under the owner's standing order of 2026-10-17: "record useful researches … as persistent documents")

Each file is the subagent's report verbatim with a provenance header on top (the source path and its sha256). The claims carry the author's own confidence and gaps sections; nothing was re-verified at the copy. The prose rule's detect pass (`.claude/rules/prose.md`) was run as a reading of each file; the patterns found are listed, not fixed, because the texts are the record of what the subagents wrote.

| File | What it is | Author | Folded into | Detect |
|---|---|---|---|---|
| `matte_report.md` | ViTMatte small as the soft-matte model: the API read from the installed source, the trimap rule, 140 mattes on six photos with wall times and band numbers, the lattice trimap, the reading contract for the renderer | an Opus 5.5 subagent (Track M, soft mattes) | `TRANSITIONS.md §13.17` item 1, the tooling list (readers), backlog T43 | none found |
| `keyframes_r10.md` | Ten FLUX.3 image klein distilled runs on the box for the café man and the window pane: prompts, references, run facts, the screen per keyframe (faces, hands, what changed), the four that passed and the six that failed | an Opus 5.5 subagent (Track K, the box) | `§13.17` item 3, the tooling list (helpers), backlog T40, T41 | none found |
| `planner_r10.md` | The round-10 planner's notes: what each plan kept and changed against his round-9 grades, what the schema could not express, and the `vacated_first` sign it caught in the renderer before any render | an Opus 5.5 subagent (the planner) | `§13.17` item 4 | none found |
| `skeptic_r10.md` | The frame-by-frame first pass on the first full-size round-10 renders: the faults by frame number with measurements (the fill share, the halo's red levels, the streak contrast), against round 9; it led to six renderer fixes and a re-render | an Opus 5.5 subagent (the skeptic, first pass) | `§13.17` item 5 | none found |
| `skeptic_r10b.md` | The second pass on the re-render: each first-pass fault gone, reduced or unchanged, the new faults, and the verdict against the first render and round 9; the page's fault texts quote it | an Opus 5.5 subagent (the skeptic, second pass) | `§13.17` item 5, the page `director_r10/notes.json` | none found |

The living tooling list is `../director-tooling.md`; its rows dated 2026-10-18 come from these files.
