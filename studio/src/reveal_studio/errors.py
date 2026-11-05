"""The one exception for a request the studio refuses: an operator-readable message, an HTTP code and extra fields."""

from __future__ import annotations

from typing import Any


class StudioError(Exception):
    """A refusal the page shows as it is: `str(e)` is the message, `code` the HTTP status, `extra` more JSON keys."""

    def __init__(self, msg: str, code: int = 400, extra: dict[str, Any] | None = None) -> None:
        super().__init__(msg)
        self.code = code
        self.extra: dict[str, Any] = extra or {}
