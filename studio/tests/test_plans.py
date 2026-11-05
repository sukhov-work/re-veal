"""Plans: validate_plan, plan_diff, save_plan's provenance and its never-rewrite rule, resolve_plan's grammar."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, read_json, sha256_file
from reveal_studio.jobs.plans import frozen_plans, plan_diff, plans_of, resolve_plan, save_plan
from reveal_studio.registry.schema import BY_PATH, validate_plan

from .conftest import FROZEN_PLAN


def test_validate_plan_accepts_the_frozen_plan() -> None:
    validate_plan(copy.deepcopy(FROZEN_PLAN))


@pytest.mark.parametrize(
    ("path", "drop", "plan", "message"),
    [
        ("timeline[*].method", "snap", {"timeline": [{"key": 0}, {"to": 1, "method": "snap"}]}, "method 'snap'"),
        ("timeline[*].ease", "sine", {"timeline": [{"key": 0}, {"to": 1, "ease": "sine"}]}, "ease 'sine'"),
        ("effects[*].kind", "glow", {"timeline": [{"key": 0}], "effects": [{"kind": "glow"}]}, "effects[0]: kind"),
    ],
)
def test_validate_plan_reads_its_lists_from_the_schema(
    monkeypatch: pytest.MonkeyPatch, path: str, drop: str, plan: Json, message: str
) -> None:
    validate_plan(plan)  # accepted with the schema's lists as they are
    entry = BY_PATH[path]
    monkeypatch.setitem(entry, "choices", [c for c in entry["choices"] or [] if c != drop])
    with pytest.raises(StudioError, match=re_escape(message)):
        validate_plan(plan)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"notes": "x"}, "unknown plan keys ['notes']"),
        ({"timeline": []}, "non-empty timeline"),
        ({"timeline": [{"hold": 3}]}, "timeline[0] is a hold"),
        ({"timeline": [{"key": 0, "hold": 2}, {"to": 1, "n": 2, "method": "warp"}]}, "method 'warp' is not one of"),
        ({"timeline": [{"key": 0, "hold": 2}, {"to": 1, "n": 2, "ease": "bounce"}]}, "ease 'bounce' is not one of"),
        ({"effects": [{"kind": "zoom"}]}, "effects[0]: kind is one of"),
        ({"matte": [14]}, "matte is an object"),
    ],
)
def test_validate_plan_refuses_with_the_known_list(change: Json, message: str) -> None:
    plan = {**copy.deepcopy(FROZEN_PLAN), **change}
    with pytest.raises(StudioError, match=message.replace("[", r"\[").replace("]", r"\]")) as e:
        validate_plan(plan)
    assert e.value.code == 400


def test_validate_plan_refuses_a_non_object() -> None:
    with pytest.raises(StudioError, match="a plan is a JSON object"):
        validate_plan([1, 2])


def test_a_transition_without_method_or_ease_takes_the_defaults() -> None:
    validate_plan({"timeline": [{"key": 0, "hold": 1}, {"to": 1, "n": 3}]})


def test_plan_diff_lists_changed_leaves_and_skips_provenance() -> None:
    old = copy.deepcopy(FROZEN_PLAN)
    new = copy.deepcopy(FROZEN_PLAN)
    new["timeline"][1]["n"] = 4
    new["timeline"].append({"key": 0, "hold": 1})
    new["crop"] = 0.75
    del new["gag"]
    new["provenance"] = {"author": "owner"}
    changes = plan_diff(old, new)
    assert {"path": "/timeline/1/n", "old": 2, "new": 4} in changes
    assert {"path": "/timeline/4", "old": None, "new": {"key": 0, "hold": 1}} in changes
    assert {"path": "/crop", "old": None, "new": 0.75} in changes
    assert {"path": "/gag", "old": "a test plan", "new": None} in changes
    assert not any(c["path"].startswith("/provenance") for c in changes)
    assert plan_diff(old, old) == []
    assert plan_diff(1, 2) == [{"path": "/", "old": 1, "new": 2}]


def test_plan_diff_stops_at_the_cap() -> None:
    old = {"a": list(range(10))}
    new = {"a": list(range(10, 20))}
    assert len(plan_diff(old, new, cap=3)) == 3


def test_save_plan_writes_provenance_and_never_rewrites(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    plan = copy.deepcopy(FROZEN_PLAN)
    plan["timeline"][1]["n"] = 5
    out = save_plan(settings, d, j, "tiny_v2", plan, "frozen:tiny_a1", "his words, verbatim")
    assert out["ref"] == "job:tiny_v2"
    assert out["changes"] == [{"path": "/timeline/1/n", "old": 2, "new": 5}]
    saved = read_json(d / "plans" / "tiny_v2.json")
    prov = saved["provenance"]
    assert prov["author"] == "owner"
    assert prov["words"] == "his words, verbatim"
    assert prov["from"] == "scripts/research/plans/loops/tiny_a1.json"
    assert prov["from_sha256"] == sha256_file(settings.frozen_plans / "tiny_a1.json")
    assert prov["ui_version"] == "reveal-studio 0.2.0"
    assert out["sha256"] == sha256_file(d / "plans" / "tiny_v2.json")
    with pytest.raises(StudioError, match="never overwritten") as e:
        save_plan(settings, d, j, "tiny_v2", plan)
    assert e.value.code == 409
    assert plans_of(settings, d)[0]["changes"] == 1
    assert plans_of(settings, d)[0]["words"] == "his words, verbatim"


def test_save_plan_refuses_a_bad_name_and_a_bad_plan(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    with pytest.raises(StudioError, match="a plan name is letters"):
        save_plan(settings, d, j, "../escape", FROZEN_PLAN)
    with pytest.raises(StudioError, match="unknown plan keys"):
        save_plan(settings, d, j, "ok_name", {**FROZEN_PLAN, "zoom": 1})
    assert not (d / "plans").exists()


def test_save_plan_without_a_source_records_no_changes(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    out = save_plan(settings, d, j, "fresh", FROZEN_PLAN)
    prov = read_json(d / "plans" / "fresh.json")["provenance"]
    assert (prov["from"], prov["changes"], out["changes"]) == (None, [], [])


def test_resolve_plan_grammar(settings: Settings, job: tuple[Path, Json]) -> None:
    d, j = job
    save_plan(settings, d, j, "mine", FROZEN_PLAN)
    assert resolve_plan(settings, d, "job:mine") == d / "plans" / "mine.json"
    assert resolve_plan(settings, None, "frozen:tiny_a1") == settings.frozen_plans / "tiny_a1.json"
    for ref, code, text in [
        ("tiny_a1", 400, "job:<name>"),
        (None, 400, "job:<name>"),
        ("frozen:../x", 400, "letters, digits"),
        ("disk:tiny_a1", 400, "job:<name> or frozen:<name>"),
        ("job:mine_none", 404, "no plan"),
        ("frozen:absent", 404, "no plan scripts/research/plans/loops/absent.json"),
    ]:
        with pytest.raises(StudioError, match=re_escape(text)) as e:
            resolve_plan(settings, d, ref)
        assert e.value.code == code, ref
    with pytest.raises(StudioError):
        resolve_plan(settings, None, "job:mine")  # a job plan needs the job


def test_frozen_plans_lists_the_tree_and_is_never_written(settings: Settings, job: tuple[Path, Json]) -> None:
    before = sha256_file(settings.frozen_plans / "tiny_a1.json")
    d, j = job
    save_plan(settings, d, j, "edit", FROZEN_PLAN, "frozen:tiny_a1", "x")
    rows = frozen_plans(settings)
    assert [r["ref"] for r in rows] == ["frozen:tiny_a1"]
    assert rows[0]["seq"] == "tiny"
    assert sha256_file(settings.frozen_plans / "tiny_a1.json") == before


def re_escape(text: str) -> str:
    import re

    return re.escape(text)
