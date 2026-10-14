"""Local HTTP server that serves the interface and the API it uses.

It only listens on 127.0.0.1, checks the Host header (against DNS rebinding)
and every /api request needs the random token generated at start-up, so other
web pages cannot use it."""

from __future__ import annotations

import json
import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import bcsfe
from bcsfe import core

from . import __version__, settings
from .bridge import bridge
from .i18n import t
from .jobs import BusyError, JobRunner
from .session import Session, SessionError

mimetypes.add_type("font/otf", ".otf")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("application/javascript", ".js")

# The interface only loads its own files and never needs inline scripts.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    ),
}


class AppState:
    def __init__(self, web_dir: Path, token: str, session: Session) -> None:
        self.web_dir = web_dir.resolve()
        self.token = token
        self.session = session
        self.runner = JobRunner(bridge)
        self.last_seen = time.time()
        self.page_seen = False  # the interface has made at least one request
        self.bye_at: float | None = None
        self.shutdown_event = threading.Event()
        self.port = 0

    def touch(self) -> None:
        self.last_seen = time.time()
        self.page_seen = True
        self.bye_at = None

    # ----------------------------------------------------------------- tasks
    def start(self, title: str, func: Any, kind: str = "feature") -> dict[str, Any]:
        job = self.runner.start(title, func, kind)
        return {"ok": True, "job": job.to_dict()}

    def state(self, since: int) -> dict[str, Any]:
        job = self.runner.current
        logs, nxt = bridge.log.since(since)
        return {
            "session": self.session.info(),
            "job": job.to_dict() if job else None,
            "prompt": bridge.current_prompt(),
            "waiting_file": bridge.waiting_file_dialog,
            "logs": logs,
            "next": nxt,
        }

    def home(self) -> dict[str, Any]:
        doc = core.SaveFile.get_save_path()
        return {
            "gui_version": __version__,
            "bcsfe_version": bcsfe.__version__,
            "documents_save": doc.exists(),
            "documents_path": doc.to_str(),
            "saves_dir": core.SaveFile.get_saves_path().to_str(),
            "data_dir": core.Path.get_data_folder().to_str(),
            "country_codes": core.CountryCode.get_all_str(),
            "language": settings.current["language"],
            "languages": settings.LANGUAGES,
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "BCSFE-GUI"
    sys_version = ""
    app: AppState  # set when the server is created

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    # --------------------------------------------------------------- helpers
    def _send(self, code: int, body: bytes, ctype: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data: Any, code: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8", {"Cache-Control": "no-store"})

    def _error(self, message: str, code: int = 400) -> None:
        self._json({"ok": False, "error": message}, code)

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        port = self.app.port
        return host in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _token_ok(self) -> bool:
        return self.headers.get("X-Token") == self.app.token

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, 5_000_000))
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    # ---------------------------------------------------------------- routes
    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        if not self._host_ok():
            return self._error(t("host_not_allowed"), 403)
        url = urlparse(self.path)
        if url.path.startswith("/api/"):
            if not self._token_ok():
                return self._error(t("invalid_token"), 403)
            return self._api_get(url.path, parse_qs(url.query))
        return self._static(url.path)

    def do_POST(self) -> None:
        if not self._host_ok():
            return self._error(t("host_not_allowed"), 403)
        url = urlparse(self.path)
        if url.path == "/api/bye":
            # sendBeacon cannot set headers, so the token travels in the URL.
            if parse_qs(url.query).get("t", [""])[0] == self.app.token:
                self.app.bye_at = time.time()
            return self._json({"ok": True})
        if not url.path.startswith("/api/") or not self._token_ok():
            return self._error(t("invalid_token"), 403)
        try:
            self._api_post(url.path, self._body())
        except BusyError as exc:
            self._error(str(exc), 409)
        except SessionError as exc:
            self._error(str(exc), 400)

    def _static(self, path: str) -> None:
        if path in ("", "/"):
            path = "/index.html"
        target = (self.app.web_dir / path.lstrip("/")).resolve()
        if self.app.web_dir not in target.parents and target != self.app.web_dir:
            return self._error(t("not_found"), 404)
        if not target.is_file():
            return self._error(t("not_found"), 404)
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        cache = "max-age=86400" if "/assets/" in path else "no-cache"
        self._send(200, target.read_bytes(), ctype, {"Cache-Control": cache})

    def _api_get(self, path: str, query: dict[str, list[str]]) -> None:
        app = self.app
        app.touch()
        s = app.session
        try:
            if path == "/api/state":
                since = int(query.get("since", ["0"])[0] or 0)
                return self._json(app.state(since))
            if path == "/api/home":
                return self._json(app.home())
            if path == "/api/menu":
                return self._json({"ok": True, "menu": s.menu()})
            if path == "/api/overview":
                return self._json({"ok": True, "overview": s.overview(), "info": s.info()})
            if path == "/api/cats":
                return self._json({"ok": True, **s.cats_state()})
        except SessionError as exc:
            return self._error(str(exc), 400)
        return self._error(t("unknown_route"), 404)

    def _api_post(self, path: str, body: dict[str, Any]) -> None:
        app = self.app
        app.touch()
        s = app.session

        if path == "/api/heartbeat":
            return self._json({"ok": True})
        if path == "/api/answer":
            ok = bridge.answer(int(body.get("id", -1)), body.get("value"))
            return self._json({"ok": ok})
        if path == "/api/cancel":
            bridge.cancel_prompt()
            return self._json({"ok": True})
        if path == "/api/stop":
            if app.runner.busy():
                bridge.request_abort()
            return self._json({"ok": True})
        if path == "/api/quit":
            app.shutdown_event.set()
            return self._json({"ok": True})

        if path == "/api/load":
            method = body.get("method")
            if method == "file":
                return self._json(app.start(t("job_open_file"), s.load_from_file_dialog, "load"))
            if method == "path":
                p = str(body.get("path") or "")
                return self._json(app.start(t("job_open_file"), lambda: s.load_from_path(p), "load"))
            if method == "documents":
                return self._json(app.start(t("job_documents"), s.load_from_documents, "load"))
            if method == "json":
                return self._json(app.start(t("job_json"), s.load_from_json, "load"))
            if method == "adb":
                return self._json(app.start(t("job_adb"), s.load_from_adb, "load"))
            if method == "codes":
                tc = str(body.get("transfer_code") or "")
                cc_code = str(body.get("confirmation_code") or "")
                cc = str(body.get("cc") or "")
                if not tc.strip() or not cc_code.strip():
                    return self._error(t("codes_required"))
                return self._json(app.start(t("job_codes"), lambda: s.load_from_codes(tc, cc_code, cc), "load"))
            return self._error(t("unknown_load_method"))

        if path == "/api/settings":
            language = str(body.get("language") or "")
            if language not in settings.LANGUAGES:
                return self._error(t("invalid_language"))
            if app.runner.busy():
                return self._error(t("wait_task"), 409)
            settings.set_language(language)
            s.language_changed()
            return self._json({"ok": True, "home": app.home()})

        if path == "/api/close":
            if app.runner.busy():
                return self._error(t("wait_task"), 409)
            s.close()
            return self._json({"ok": True})

        if path == "/api/feature":
            feat_path = [str(x) for x in body.get("path") or []]
            if not feat_path:
                return self._error(t("missing_feature"))
            s.require_save()
            title = s.feature_title(feat_path)
            return self._json(app.start(title, lambda: s.run_feature(feat_path)))

        if path == "/api/editor":
            option = str(body.get("option") or "")
            titles = {
                "config": "job_config",
                "update_external": "job_update_external",
                "manage_game_data": "job_game_data",
            }
            if option not in titles:
                return self._error(t("unknown_option"))
            return self._json(app.start(t(titles[option]), lambda: s.run_editor_option(option), "editor"))

        if path == "/api/cats/meta":
            s.require_save()
            return self._json(app.start(t("job_cat_meta"), s.load_cat_meta, "cats_meta"))

        if path == "/api/cats/action":
            action = str(body.get("action") or "")
            ids = [int(x) for x in body.get("ids") or []]
            params = body.get("params") or {}
            title = str(body.get("title") or t("job_cats"))
            s.require_save()
            return self._json(app.start(title, lambda: s.cat_action(action, ids, params), "cats"))

        return self._error(t("unknown_route"), 404)


def create_server(app: AppState, port: int = 0) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"app": app})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True
    app.port = server.server_address[1]
    return server
