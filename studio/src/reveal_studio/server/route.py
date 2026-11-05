"""A route row and the helpers every route list builds its rows with: the shared table (server/routes.py) and each
flow's list (server/routes_pair.py, server/routes_director.py), which the table splices before its two fallbacks."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from reveal_studio.fs import Json

if TYPE_CHECKING:
    from reveal_studio.server.handler import Handler

RouteFn = Callable[["Handler", "re.Match[str]", Json], None]
JOB = r"^/api/jobs/([^/]+)"
"""The prefix of a job's routes: group 1 is the job id, which the route loads first."""


@dataclass(frozen=True)
class Route:
    method: str
    pattern: re.Pattern[str]
    fn: RouteFn
    name: str


def _r(method: str, pattern: str, fn: RouteFn) -> Route:
    return Route(method, re.compile(pattern), fn, f"{method} {fn.__name__}")
