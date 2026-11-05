"""One server per tree: the lock file names the port and pid of the server that holds it.

Two servers on one tree would reconcile the same record twice; `--second` lets a review run another one knowingly.
"""

from __future__ import annotations

import fcntl
import os
from typing import TextIO

from reveal_studio.config import Settings
from reveal_studio.errors import StudioError
from reveal_studio.fs import log, now_iso, rel


class LockHeld(StudioError):
    """Another server holds the lock file and `--second` was not given."""


def take_lock(settings: Settings, second: bool) -> TextIO:
    """An exclusive flock on the settings' lock file, its text rewritten to `port P pid N since T`.

    The returned handle holds the lock for as long as it stays open. Raises LockHeld when another server holds
    it, unless `second`; a second server keeps the first one's text.
    """
    lock = settings.lock_path
    lock.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock, "a+")  # noqa: SIM115  # 2026-11-05: the handle stays open for the server's life; closing it releases the lock
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.seek(0)
        who = fh.read().strip()
        if not second:
            fh.close()
            raise LockHeld(
                f"another studio holds {rel(lock, settings.root)} ({who}); "
                "stop it, or pass --second for a review server",
                409,
            ) from None
        log(f"a second server beside {who} (--second): a record can be reconciled by both")
        return fh
    fh.seek(0)
    fh.truncate()
    fh.write(f"port {settings.port} pid {os.getpid()} since {now_iso()}\n")
    fh.flush()
    return fh
