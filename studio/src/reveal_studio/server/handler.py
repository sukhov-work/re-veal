"""The request handler: the Host check, the JSON body rules, file answers with Range, and errors as JSON.

Every answer carries `Cache-Control: no-store` except thumbnails and frames (their names carry an md5 or mtime).
A POST body must be `application/json` (a cross-site form cannot send that) and at most the settings' body cap.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from reveal_studio import __version__
from reveal_studio.errors import StudioError
from reveal_studio.fs import Json, inside, log
from reveal_studio.jobs.store import job_root
from reveal_studio.server import routes

if TYPE_CHECKING:
    from reveal_studio.server.app import App, StudioServer

JSON_CTYPE = "application/json; charset=utf-8"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".md": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".npy": "application/octet-stream",
    ".svg": "image/svg+xml",
}
STATIC_MIME = {**MIME, ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}


class Handler(BaseHTTPRequestHandler):
    server_version = f"reveal-studio/{__version__}"
    protocol_version = "HTTP/1.1"

    @property
    def app(self) -> App:
        return cast("StudioServer", self.server).app

    def log_message(self, *_args: Any) -> None:
        """Silent: the studio's own log lines go to stderr through fs.log."""

    def _send(self, code: int, body: Any, ctype: str = JSON_CTYPE, extra: dict[str, str] | None = None) -> None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode()
        elif isinstance(body, str):
            data = body.encode()
        else:
            data = body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _err(self, code: int, msg: str, extra: Json | None = None) -> None:
        self._send(code, {"error": msg, **(extra or {})})

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").strip()
        port = self.app.settings.port
        return host in (f"127.0.0.1:{port}", f"localhost:{port}", "127.0.0.1", "localhost")

    def _body(self) -> Json:
        n = int(self.headers.get("Content-Length") or 0)
        cap = self.app.settings.body_cap
        if n > cap:
            raise StudioError(f"the body is above {cap / (1024 * 1024):g} MB", 413)
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise StudioError("POST bodies are application/json (a cross-site form cannot send that)", 415)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        try:
            obj = json.loads(raw)
        except ValueError as e:
            raise StudioError(f"bad JSON: {e}", 400) from None
        if not isinstance(obj, dict):
            raise StudioError("the body is a JSON object", 400)
        return obj

    def _file(self, p: Path, cacheable: bool = False, static: bool = False) -> None:
        """The file, or the byte range a `Range: bytes=a-b` header asks for (206); 416 for a range outside it."""
        p = Path(p)
        if not p.is_file():
            return self._err(404, "no such file")
        ctype = (STATIC_MIME if static else MIME).get(p.suffix.lower(), "application/octet-stream")
        size = p.stat().st_size
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        code = 200
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            try:
                start = int(a) if a else max(0, size - int(b))
                end = int(b) if (b and a) else size - 1
            except ValueError:
                return self._err(416, "bad range")
            if start > end or start >= size:
                return self._err(416, "range out of file", {"size": size})
            end = min(end, size - 1)
            code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        # a thumbnail's name carries its md5 or mtime
        self.send_header("Cache-Control", "private, max-age=3600" if cacheable else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return None
        with open(p, "rb") as f:
            f.seek(start)
            left = length
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)
        return None

    def _safe_file(self, d: Path, job: Json, relpath: str) -> Path:
        """A path inside the job's run folder or the job folder; `..` and absolute paths are refused (403)."""
        if ".." in relpath.split("/") or relpath.startswith("/"):
            raise StudioError("forbidden", 403)
        for base in (job_root(self.app.settings, job), d):
            p = base / relpath
            if p.exists() and inside(p, base):
                return p
        raise StudioError("no such file", 404)

    def _handle(self, method: str) -> None:
        try:
            if not self._host_ok():
                return self._err(403, "the studio answers 127.0.0.1 only")
            path = self.path.split("?", 1)[0]
            body = self._body() if method == "POST" else {}
            routes.dispatch(self, method, path, body)
        except StudioError as e:
            self._err(e.code, str(e), e.extra)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # the reason reaches the page, never a silent 500
            log(f"{method} {self.path}: {type(e).__name__}: {e}")
            self._err(500, f"{type(e).__name__}: {e}")
        return None

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")
