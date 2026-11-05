"""A round: one page over the candidates, opened when the page is written, graded by his words (STUDIO.md §4).

open_round is the one way a round opens, whoever wrote the page: the Runner after a finished page record (the loop's
`loop_seq.py page`, the director's `director_page.py`), or the studio itself (the pair's page, a builtin stage).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from reveal_studio.fs import Json, log, md5_file, now_iso, write_json
from reveal_studio.jobs.candidates import rounds


def open_round(
    d: Path,
    page: Path,
    names: list[str],
    *,
    variants: list[str] | None = None,
    record: str | None = None,
    override: str | None = None,
) -> Json:
    """Opens the next round of job folder `d` on the written `page`: page.md5 beside the page, a copy of the page and
    rounds/<n>/round.json naming the candidates the page lists (`names`), the variants asked for ([] = every full
    render in name order), the record that wrote it (None for a page the studio wrote) and the override's text."""
    md5v = md5_file(page)
    (page.parent / "page.md5").write_text(md5v + "\n")
    n = len(rounds(d)) + 1
    (d / "rounds" / str(n)).mkdir(parents=True, exist_ok=True)
    shutil.copy2(page, d / "rounds" / str(n) / page.name)  # the round keeps its page; the root holds the latest
    r: Json = {
        "n": n,
        "at": now_iso(),
        "candidates": names,
        "variants": list(variants or []),
        "page_md5": md5v,
        "page": page.name,
        "record": record,
        "override": override or None,
        "grade": None,
        "ungraded_by_his_word": None,
    }
    write_json(d / "rounds" / str(n) / "round.json", r)
    log(f"{d.name}: round {n} opened on page md5 {md5v}")
    return r
