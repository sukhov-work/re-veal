"""The registry's entry builders, shared by every flow module: a knob (`K`), a hint (`H`) and the hints' merge.

A flow module (registry/loop.py, pair.py, director.py) and a hints module (hints.py, hints_pair.py,
hints_director.py) import these from here, never from one another, so a flow module imports no other flow's.
"""

from __future__ import annotations

from typing import Any


def K(
    key: str,
    typ: str,
    default: Any,
    what: str,
    flag: str | None = None,
    choices: list[str] | None = None,
    rng: list[float] | None = None,
) -> dict[str, Any]:
    """A knob: the literal key, its type, default and sentence, the script flag it becomes, its choices and range.

    The types: int, float, str, bool, list (names, joined by commas into one flag), plan (job:<name> or
    frozen:<name>), object (a JSON object: one `<flag> k=<json>` per key, keys in sorted order; runner/argv.py)."""
    return {"key": key, "type": typ, "default": default, "what": what, "flag": flag, "choices": choices, "range": rng}


def H(
    what: str,
    default: Any = None,
    rng: list[float] | None = None,
    stage: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """A hint: the sentence, and the default, range, reading stage and source when they exist."""
    d: dict[str, Any] = {"what": what}
    if default is not None:
        d["default"] = default
    if rng is not None:
        d["range"] = rng
    if stage:
        d["stage"] = stage
    if source:
        d["source"] = source
    return d


def merge_hints(*tables: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """One table from the flows' hint tables, in their order; a key in two tables raises ValueError naming it, so a
    duplicate fails the import (and every test) instead of one flow's sentence silently replacing another's."""
    out: dict[str, dict[str, Any]] = {}
    for table in tables:
        twice = sorted(set(out) & set(table))
        if twice:
            raise ValueError(f"hint keys in two flows' tables: {twice}")
        out.update(table)
    return out
