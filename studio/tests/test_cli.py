"""The CLI: `check` prints the resolved settings (exit 1 when something is missing), `requests` lists the open requests,
`serve` refuses a held lock, and `python -m reveal_studio` is the same command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from reveal_studio.cli import main
from reveal_studio.config import Settings
from reveal_studio.fs import Json, md5_file
from reveal_studio.jobs.grades import write_request
from reveal_studio.runner.lock import take_lock

ENV = (
    "REVEAL_STUDIO_ROOT",
    "REVEAL_STUDIO_PY",
    "REVEAL_STUDIO_PORT",
    "REVEAL_STUDIO_LOCK",
    "REVEAL_STUDIO_RUNS_DATE",
    "REVEAL_STUDIO_LAYERS_DIR",
    "REVEAL_STUDIO_MATTES_DIR",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ENV:
        monkeypatch.delenv(k, raising=False)


def test_check_prints_the_resolved_settings(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "--root", str(root), "--port", "8391"]) == 0
    out = capsys.readouterr().out
    assert f"python        {root.resolve()}/.venv/bin/python (exists)" in out
    assert f"loop_seq      scripts/research/loop_seq.py md5 {md5_file(root / 'scripts/research/loop_seq.py')}" in out
    assert "serves        http://127.0.0.1:8391/" in out
    assert "script flags  progress yes, frames yes, readers yes" in out
    assert "frozen plans  scripts/research/plans/loops (1 plans)" in out


def test_check_prints_the_flow_paths_and_a_missing_one_leaves_the_exit_code(
    root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every path of the pair and director flows gets a row with its md5 or count. Mutation: a missing transitions.py
    or layer root counted into the exit code (check then answers 1 on a tree that runs the loop) turns this red."""
    (root / "transitions.py").unlink(missing_ok=True)
    (root / "scripts/research/director_page.py").unlink(missing_ok=True)
    fx = root / "fixtures"
    fx.mkdir(exist_ok=True)
    for name in ("pa_1_S.jpg", "pa_1_F.png", "pb_2_S.jpg", "MANIFEST.md"):  # pb_2 lacks its _F: not a pair
        (fx / name).write_bytes(b"x")
    layers = root / "benchmarks/runs/2026-09-28/layers_v3"
    for photo in ("pa_1_S", "pa_1_F", "_candidates"):  # a folder starting with _ is no photo
        (layers / photo).mkdir(parents=True)
        (layers / photo / "layers.json").write_text("{}")
    assert main(["check", "--root", str(root), "--mattes-dir", str(root / "nowhere")]) == 0
    out = capsys.readouterr().out
    assert f"transitions   {root.resolve()}/transitions.py (MISSING)" in out
    assert f"reveal        reveal.py md5 {md5_file(root / 'reveal.py')}" in out
    assert f"director page {root.resolve()}/scripts/research/director_page.py (MISSING)" in out
    assert "fixtures      fixtures (1 pairs)" in out
    assert "layers        benchmarks/runs/2026-09-28/layers_v3 (2 photo folders with layers.json)" in out
    assert f"mattes        {root.resolve()}/nowhere (MISSING)" in out


def test_check_exits_1_when_the_main_venv_is_missing(
    root: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REVEAL_STUDIO_PY", str(root / "no-venv" / "python"))
    assert main(["check", "--root", str(root)]) == 1
    out = capsys.readouterr().out
    assert "no-venv/python (MISSING: the main venv" in out and "script flags  not probed" in out


def test_check_exits_1_naming_the_missing_root_file(
    root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (root / "reveal.py").unlink()
    assert main(["check", "--root", str(root)]) == 1
    assert "has no reveal.py" in capsys.readouterr().err
    assert main(["check", "--root", str(tmp_path / "absent")]) == 1
    assert "is not a folder" in capsys.readouterr().err


def test_requests_lists_an_open_request(
    settings: Settings, root: Path, job: tuple[Path, Json], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["requests", "--root", str(root)]) == 0
    assert capsys.readouterr().out == "no open requests\n"
    d, j = job
    write_request(settings, d, j, "plan", {"brief": "a slower first leg", "candidates": []})
    assert main(["requests", "--root", str(root)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split() == ["0", "s", j["id"], out[0].split()[3], "plan:", "a", "slower", "first", "leg"]
    assert out[0].split()[3].startswith(f"{j['root']}/requests/plan_")
    assert out[-1] == "1 open request(s); the oldest 0 min"


def test_serve_refuses_a_held_lock(settings: Settings, root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    fh = take_lock(settings, second=False)
    try:
        code = main(
            [
                "serve",
                "--root",
                str(root),
                "--lock",
                str(settings.lock_path),
                "--port",
                str(settings.port),
                "--no-browser",
            ]
        )
        assert code == 1
        assert "another studio holds" in capsys.readouterr().err
    finally:
        fh.close()


def test_python_m_reveal_studio_is_the_same_command(root: Path) -> None:
    p = subprocess.run(
        [sys.executable, "-m", "reveal_studio", "check", "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0, p.stderr
    assert p.stdout.startswith("reveal-studio 0.2.0\n")
    v = subprocess.run([sys.executable, "-m", "reveal_studio", "--version"], capture_output=True, text=True, timeout=60)
    assert v.stdout.strip() == "reveal-studio 0.2.0"
