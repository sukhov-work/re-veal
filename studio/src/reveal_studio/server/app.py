"""The App (the settings, the script's flags, the runner and the registry) and the server bound to 127.0.0.1 only."""

from __future__ import annotations

import threading
import webbrowser
from dataclasses import dataclass, field
from http.server import ThreadingHTTPServer
from typing import Any

from reveal_studio.config import Settings
from reveal_studio.fs import log, rel
from reveal_studio.jobs.store import job_dirs, studio_dir
from reveal_studio.registry.flows import FLOWS
from reveal_studio.runner.argv import ScriptFlags, probe_script_flags
from reveal_studio.runner.lock import take_lock
from reveal_studio.runner.process import Runner
from reveal_studio.server.handler import Handler

HOST = "127.0.0.1"


@dataclass
class App:
    """What one server holds: no module-level state; the handler reads it as `self.server.app`."""

    settings: Settings
    flags: ScriptFlags
    runner: Runner
    flows: dict[str, Any] = field(default_factory=lambda: FLOWS)

    @classmethod
    def build(cls, settings: Settings, flags: ScriptFlags | None = None) -> App:
        """An App with the flags probed from the script's --help unless given."""
        flags = probe_script_flags(settings) if flags is None else flags
        return cls(settings=settings, flags=flags, runner=Runner(settings, flags))


class StudioServer(ThreadingHTTPServer):
    """A threading HTTP server on 127.0.0.1 at the settings' port, holding the App."""

    daemon_threads = True

    def __init__(self, app: App) -> None:
        self.app = app
        super().__init__((HOST, app.settings.port), Handler)


def serve(settings: Settings, second: bool = False) -> int:
    """Takes the tree's lock, probes the script, reconciles every running record, then serves until interrupted."""
    lock_fh = take_lock(settings, second)
    app = App.build(settings)
    app.runner.reconcile_all()
    httpd = StudioServer(app)
    url = f"http://{HOST}:{settings.port}/"
    log(
        f"{settings.ui_version}: serving {url} (jobs under {rel(studio_dir(settings), settings.root)}; "
        f"{len(job_dirs(settings))} job(s) found)"
    )
    if settings.open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        running = [(rid, p.pid) for rid, p in app.runner.procs.items()]
        log(
            f"stopped; {len(running)} child process(es) keep running and are reconciled at the next start"
            + (f": {running}" if running else "")
        )
    finally:
        lock_fh.close()
    return 0
