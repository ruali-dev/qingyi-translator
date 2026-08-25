from __future__ import annotations

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from .translator import TranslationError, TranslationResult


MAX_REQUEST_BYTES = 65_536


class ConnectorServer:
    def __init__(
        self,
        host: str,
        port: int,
        translate: Callable[[str], TranslationResult],
        events: queue.Queue[tuple[str, object]],
    ) -> None:
        self.host = host
        self.port = port
        self.translate = translate
        self.events = events
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path != "/health":
                    self._json(404, {"error": "not found"})
                    return
                self._json(200, {"ok": True, "name": "PaperTranslator"})

            def do_POST(self) -> None:  # noqa: N802
                if self.path != "/translate":
                    self._json(404, {"error": "not found"})
                    return
                if self.headers.get("Origin"):
                    self._json(403, {"error": "browser origins are not allowed"})
                    return
                content_type = self.headers.get("Content-Type", "").split(";", 1)[0]
                if content_type.lower() != "application/json":
                    self._json(415, {"error": "application/json required"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._json(400, {"error": "invalid content length"})
                    return
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    self._json(413, {"error": "request too large or empty"})
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    text = payload.get("text", "")
                    outer.events.put(("translation_started", text))
                    result = outer.translate(text)
                    outer.events.put(("translation", result))
                    self._json(200, {
                        "translation": result.translation,
                        "source": result.source,
                        "model": result.model,
                    })
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._json(400, {"error": "invalid json"})
                except TranslationError as exc:
                    outer.events.put(("translation_error", str(exc)))
                    self._json(422, {"error": str(exc)})
                except Exception:
                    outer.events.put(("translation_error", "翻译时发生未知错误"))
                    self._json(500, {"error": "internal error"})

            def _json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        self.server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(
            target=self.server.serve_forever, name="connector-server", daemon=True
        )
        self.thread.start()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
