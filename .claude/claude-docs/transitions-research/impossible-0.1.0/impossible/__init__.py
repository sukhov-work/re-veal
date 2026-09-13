"""
Impossible: dynamic, steerable transitions between two images or two video
clips (and, via sequences, between N of them).

ISOLATION CONTRACT (read before touching anything):
  * This package is a standalone feature that happens to live in the same
    repository as Reveal. It must NEVER import reveal.py, and reveal.py must
    never import it. Reveal's files (reveal.py, setup.sh, run.sh, README.md,
    HANDOFF.md, harness.py, requirements*.txt, VERSION) stay byte-identical
    when this package changes. Its own operator surface is
    setup-impossible.sh, the `impossible` CLI, impossible_harness.py, and
    the docs inside this folder.
  * A few pure helpers (image decode, Lab color transfer, SIFT+MAGSAC) were
    re-implemented here rather than imported, on purpose: coupling would
    let a Reveal change break this tool, or the reverse.
  * Model weights for this package live in impossible/models (project-local
    TORCH_HOME), never in a global cache, and are fetched only by
    `impossible warmup`, never mid-job. Same contract Reveal earned in v1.5.

Design: Reveal aligns two photos and hides the change; Impossible animates
the change. A deterministic, reproducible transition (correspondence + warp
+ color path) is always computed first. Generative models, when enabled,
may modify a bounded window of those frames (mask, budget, seed) and are
conditioned on them.
"""

VERSION = "0.1.0"
