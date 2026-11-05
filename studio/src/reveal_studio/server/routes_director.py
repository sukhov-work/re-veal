"""The director flow's routes (builder D's list from wave 2 on), spliced into server/routes.ROUTES after the shared rows
and before the two fallback rows, so a row here answers before the fallbacks' 404. Empty in the slice of 2026-11-05.

A row: route._r(method, pattern, fn) with fn(handler, match, body); a job route starts with route.JOB and loads its
job first (load_job), as the shared rows do.
"""

from __future__ import annotations

from reveal_studio.server.route import Route

ROUTES: list[Route] = []
