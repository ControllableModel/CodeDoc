"""Minimal Language Server Protocol client (JSON-RPC over stdio).

Why hand-rolled: ``multilspy`` cannot be installed here (PyPI is unreachable
through this network), and only a handful of LSP messages are needed. The
protocol for what we use is small and stable, and writing it down makes the
dependency analysis auditable instead of hiding it behind a wrapper.

Supported surface
-----------------
``initialize`` / ``initialized`` / ``shutdown`` / ``exit``
``textDocument/didOpen``
``textDocument/documentSymbol``
``workspace/symbol``
``textDocument/prepareTypeHierarchy``   (class supertypes / subtypes)
``textDocument/prepareCallHierarchy``   (incoming / outgoing calls)
``textDocument/references``             (instantiation and reference sites)

Only synchronous request/response is implemented: the analysis is a batch job, so
notifications from the server are drained and discarded.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class LspError(RuntimeError):
    pass


class LspClient:
    """Synchronous LSP client for one server process."""

    def __init__(
        self,
        command: List[str],
        root: str,
        language_id: str = "python",
        timeout: float = 120.0,
        trace: bool = False,
        settings: Optional[Dict[str, Any]] = None,
        max_requests: Optional[int] = None,
    ) -> None:
        self.command = list(command)
        self.root = Path(root).resolve()
        self.language_id = language_id
        self.timeout = timeout
        self.trace = trace
        #: Server configuration pushed after initialization. Critical in
        #: practice: an unrestricted Pyright analyses the whole workspace on
        #: every query (observed: 2 GB RSS, 600 s CPU for a 24-file project).
        self.settings = settings or {}
        #: Safety valve so a misconfigured server cannot spin forever.
        self.max_requests = max_requests
        self.n_requests = 0
        self._proc: Optional[subprocess.Popen] = None
        self._next_id = 0
        self._opened: set = set()
        self._capabilities: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._buffer = b""

    # -- lifecycle ----------------------------------------------------------
    def start(self) -> "LspClient":
        env = dict(os.environ)
        env.setdefault("PYTHONIOENCODING", "utf-8")
        self._proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(self.root),
            env=env,
        )
        result = self.request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": self.root.as_uri(),
                "rootPath": str(self.root),
                "capabilities": {
                    "textDocument": {
                        "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                        "typeHierarchy": {"dynamicRegistration": False},
                        "callHierarchy": {"dynamicRegistration": False},
                        "references": {"dynamicRegistration": False},
                    },
                    "workspace": {"symbol": {"dynamicRegistration": False}},
                },
                "workspaceFolders": [
                    {"uri": self.root.as_uri(), "name": self.root.name}
                ],
            },
        )
        self._capabilities = (result or {}).get("capabilities", {})
        self.notify("initialized", {})
        if self.settings:
            self.notify("workspace/didChangeConfiguration", {"settings": self.settings})
        return self

    def stop(self) -> None:
        if not self._proc:
            return
        try:
            self.request("shutdown", None, allow_error=True)
            self.notify("exit", {})
        except Exception:
            pass
        try:
            self._proc.wait(timeout=10)
        except Exception:
            self._proc.kill()
        self._proc = None

    def __enter__(self) -> "LspClient":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()

    @property
    def capabilities(self) -> Dict[str, Any]:
        return self._capabilities

    # -- messaging ----------------------------------------------------------
    def _send(self, payload: Dict[str, Any]) -> None:
        if not self._proc or not self._proc.stdin:
            raise LspError("server is not running")
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        if self.trace:
            print(f"--> {payload.get('method') or payload.get('id')}", file=sys.stderr)
        self._proc.stdin.write(header + body)
        self._proc.stdin.flush()

    def notify(self, method: str, params: Any) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _read_message(self) -> Optional[Dict[str, Any]]:
        """Read one framed message; ``None`` when the stream closes."""
        if not self._proc or not self._proc.stdout:
            return None
        stream = self._proc.stdout
        length = None
        while True:
            line = stream.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":")[1])
        if length is None:
            return None
        body = stream.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    def request(self, method: str, params: Any, allow_error: bool = False) -> Any:
        self.n_requests += 1
        if self.max_requests is not None and self.n_requests > self.max_requests:
            raise LspError(
                f"request budget exhausted ({self.max_requests}); the server is not "
                "configured to answer within the analysis scope"
            )
        with self._lock:
            self._next_id += 1
            msg_id = self._next_id
            self._send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                message = self._read_message()
                if message is None:
                    raise LspError(f"server closed while waiting for {method}")
                if message.get("id") != msg_id:
                    # server-initiated request or stray notification
                    if "id" in message and "method" in message:
                        self._send({"jsonrpc": "2.0", "id": message["id"], "result": None})
                    continue
                if "error" in message:
                    if allow_error:
                        return None
                    raise LspError(f"{method} failed: {message['error']}")
                return message.get("result")
            raise LspError(f"timeout after {self.timeout}s waiting for {method}")

    # -- document helpers ---------------------------------------------------
    def open_document(self, path: str, text: Optional[str] = None) -> None:
        p = Path(path).resolve()
        if str(p) in self._opened:
            return
        if text is None:
            text = p.read_text(encoding="utf-8", errors="ignore")
        self.notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": p.as_uri(),
                    "languageId": self.language_id,
                    "version": 1,
                    "text": text,
                }
            },
        )
        self._opened.add(str(p))

    @staticmethod
    def position(line: int, character: int = 0) -> Dict[str, int]:
        """LSP positions are 0-based; our line numbers are 1-based."""
        return {"line": max(0, line - 1), "character": max(0, character)}

    def document_symbols(self, path: str) -> List[Dict[str, Any]]:
        self.open_document(path)
        result = self.request(
            "textDocument/documentSymbol",
            {"textDocument": {"uri": Path(path).resolve().as_uri()}},
            allow_error=True,
        )
        return result or []

    def prepare_type_hierarchy(self, path: str, line: int, character: int = 0) -> List[Dict[str, Any]]:
        self.open_document(path)
        result = self.request(
            "textDocument/prepareTypeHierarchy",
            {
                "textDocument": {"uri": Path(path).resolve().as_uri()},
                "position": self.position(line, character),
            },
            allow_error=True,
        )
        return result or []

    def supertypes(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.request("typeHierarchy/supertypes", {"item": item}, allow_error=True) or []

    def subtypes(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.request("typeHierarchy/subtypes", {"item": item}, allow_error=True) or []

    def prepare_call_hierarchy(self, path: str, line: int, character: int = 0) -> List[Dict[str, Any]]:
        self.open_document(path)
        result = self.request(
            "textDocument/prepareCallHierarchy",
            {
                "textDocument": {"uri": Path(path).resolve().as_uri()},
                "position": self.position(line, character),
            },
            allow_error=True,
        )
        return result or []

    def incoming_calls(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.request("callHierarchy/incomingCalls", {"item": item}, allow_error=True) or []

    def outgoing_calls(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.request("callHierarchy/outgoingCalls", {"item": item}, allow_error=True) or []

    def references(self, path: str, line: int, character: int = 0, include_declaration: bool = False) -> List[Dict[str, Any]]:
        self.open_document(path)
        result = self.request(
            "textDocument/references",
            {
                "textDocument": {"uri": Path(path).resolve().as_uri()},
                "position": self.position(line, character),
                "context": {"includeDeclaration": include_declaration},
            },
            allow_error=True,
        )
        return result or []
