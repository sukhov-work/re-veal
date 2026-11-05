"""The lock file names PyPI and nothing else.

The lock of 2026-11-05 once carried a work mirror's URLs, copied from the laptop's shell by `uv lock`;
the GitHub runner could not resolve that host, and the package's dependency management must not depend
on the machine that locked it. Mutation that fails the test: one `registry =` or `url =` line pointing at
another host.
"""

from __future__ import annotations

import re
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "uv.lock"
ALLOWED_HOSTS = {"pypi.org", "files.pythonhosted.org"}
URL_RE = re.compile(r"https?://([^/\s\"']+)")


def test_the_lock_names_only_pypi_hosts() -> None:
    text = LOCK.read_text()
    hosts = {m.group(1) for m in URL_RE.finditer(text)}
    assert hosts, "the lock holds no URL at all; the lock file is not the one uv wrote"
    assert hosts <= ALLOWED_HOSTS, f"the lock names other hosts: {sorted(hosts - ALLOWED_HOSTS)}"


def test_the_project_pins_pypi_as_its_default_index() -> None:
    toml = (LOCK.parent / "pyproject.toml").read_text()
    block = re.search(r"\[\[tool\.uv\.index\]\]\n(?:.*\n){1,4}", toml)
    assert block, "pyproject.toml has no [[tool.uv.index]] block"
    assert 'url = "https://pypi.org/simple"' in block.group(0)
    assert "default = true" in block.group(0)
