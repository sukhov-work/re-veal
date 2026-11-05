"""Settings resolution: explicit args > environment > discovery > an error naming what is missing."""

from __future__ import annotations

from pathlib import Path

import pytest

from reveal_studio import __version__
from reveal_studio.config import BODY_CAP, DEFAULT_PORT, ConfigError, discover_root, resolve_settings


def test_explicit_root_derives_every_path(root: Path) -> None:
    s = resolve_settings(root=root, env={}, runs_date="2026-11-05")
    assert s.root == root.resolve()
    assert s.python == root.resolve() / ".venv/bin/python"
    assert s.loop_seq == root.resolve() / "scripts/research/loop_seq.py"
    assert s.runs == root.resolve() / "benchmarks/runs"
    assert s.frozen_plans == root.resolve() / "scripts/research/plans/loops"
    assert s.lock_path == root.resolve() / "benchmarks/runs/studio.lock"
    assert (s.port, s.runs_date, s.body_cap) == (DEFAULT_PORT, "2026-11-05", BODY_CAP)
    assert s.ui_version == f"reveal-studio {__version__}" == "reveal-studio 0.2.0"
    # the pair and director flows' paths (phase B, 2026-11-05). Mutation: a path read from the package's location,
    # or the director plans pointed at the loop's loops/ folder, turns this red.
    r = root.resolve()
    assert (s.transitions, s.reveal) == (r / "transitions.py", r / "reveal.py")
    assert (s.director_render, s.director_page) == (
        r / "scripts/research/director_render.py",
        r / "scripts/research/director_page.py",
    )
    assert (s.director_plans, s.fixtures) == (r / "scripts/research/plans", r / "fixtures")
    assert s.layers_dir == r / "benchmarks/runs/2026-09-28/layers_v3"  # director_render.py's own default
    assert s.mattes_dir == r / "benchmarks/runs/2026-10-17/mattes"


def test_the_layers_and_mattes_roots_take_the_flag_then_the_environment(root: Path, tmp_path: Path) -> None:
    """Mutation: the environment read before the flag, or a relative value read against the root instead of the
    working folder (the lock's rule), turns this red."""
    env = {"REVEAL_STUDIO_LAYERS_DIR": "env/layers", "REVEAL_STUDIO_MATTES_DIR": str(tmp_path / "env-mattes")}
    s = resolve_settings(root=root, env=env, cwd=tmp_path)
    assert (s.layers_dir, s.mattes_dir) == (tmp_path / "env/layers", tmp_path / "env-mattes")
    s2 = resolve_settings(root=root, env=env, cwd=tmp_path, layers_dir="flag/layers", mattes_dir="/abs/mattes")
    assert (s2.layers_dir, s2.mattes_dir) == (tmp_path / "flag/layers", Path("/abs/mattes"))
    assert not s2.layers_dir.exists()  # a missing root raises nothing: the loop flow runs without it


def test_env_beats_discovery_and_args_beat_env(root: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    (other / "benchmarks/runs").mkdir(parents=True)
    (other / "reveal.py").write_text("")
    (other / "AGENTS.md").write_text("")
    env = {
        "REVEAL_STUDIO_ROOT": str(other),
        "REVEAL_STUDIO_PY": "/opt/py/bin/python",
        "REVEAL_STUDIO_PORT": "8391",
        "REVEAL_STUDIO_LOCK": str(tmp_path / "env.lock"),
        "REVEAL_STUDIO_RUNS_DATE": "2026-01-02",
    }
    s = resolve_settings(env=env, cwd=root)
    assert s.root == other.resolve()
    assert str(s.python) == "/opt/py/bin/python"
    assert (s.port, s.lock_path, s.runs_date) == (8391, tmp_path / "env.lock", "2026-01-02")
    s2 = resolve_settings(
        root=root, python="/x/python", port=8392, lock=tmp_path / "arg.lock", runs_date="2026-03-04", env=env, cwd=root
    )
    assert s2.root == root.resolve()
    assert (str(s2.python), s2.port, s2.lock_path, s2.runs_date) == (
        "/x/python",
        8392,
        tmp_path / "arg.lock",
        "2026-03-04",
    )


def test_discovery_walks_up_from_the_working_folder(root: Path, tmp_path: Path) -> None:
    deep = root / "studio" / "src"
    deep.mkdir(parents=True)
    s = resolve_settings(env={}, cwd=deep, package_file=tmp_path / "nowhere" / "config.py")
    assert s.root == root.resolve()


def test_discovery_falls_back_to_the_package_location(root: Path, tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    pkg_file = root / "studio" / "src" / "reveal_studio" / "config.py"
    assert discover_root(elsewhere, pkg_file) == root.resolve()
    assert discover_root(elsewhere, None) is None


def test_no_root_found_names_both_markers(tmp_path: Path) -> None:
    lone = tmp_path / "lone"
    lone.mkdir()
    with pytest.raises(ConfigError, match=r"reveal\.py and AGENTS\.md") as e:
        resolve_settings(env={}, cwd=lone, package_file=lone / "x.py")
    assert "REVEAL_STUDIO_ROOT" in str(e.value)


def test_a_root_without_a_marker_names_the_missing_file(root: Path) -> None:
    (root / "AGENTS.md").unlink()
    with pytest.raises(ConfigError, match=r"has no AGENTS\.md") as e:
        resolve_settings(root=root, env={})
    assert "reveal.py" not in str(e.value).split("has no")[1].split(":")[0]


def test_a_missing_root_folder_is_named(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="is not a folder"):
        resolve_settings(root=tmp_path / "absent", env={})


@pytest.mark.parametrize("value", ["eighty", "0", "70000"])
def test_a_bad_port_from_the_environment_is_refused(root: Path, value: str) -> None:
    with pytest.raises(ConfigError, match="REVEAL_STUDIO_PORT"):
        resolve_settings(root=root, env={"REVEAL_STUDIO_PORT": value})
