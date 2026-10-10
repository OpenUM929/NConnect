"""Queue a monitor turn through the running app server, never a second writer."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


class Rpc:
    def __init__(self) -> None:
        control = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "app-server-control/app-server-control.sock"
        self.proxy = None
        self.socket = None
        if hasattr(socket, "AF_UNIX"):
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect(str(control))
            self.reader = self.socket.makefile("rb")
        else:
            command = shutil.which("codex.cmd")
            if not command:
                raise RuntimeError("codex.cmd missing")
            self.proxy = subprocess.Popen(["cmd.exe", "/d", "/c", command, "app-server", "proxy", "--sock", str(control)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            assert self.proxy.stdout
            self.reader = self.proxy.stdout
        key = base64.b64encode(os.urandom(16)).decode()
        self._send_bytes(("GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Key: " + key + "\r\n\r\n").encode())
        status = self.reader.readline()
        headers = {}
        while line := self.reader.readline():
            if line == b"\r\n":
                break
            name, value = line.decode().split(":", 1)
            headers[name.lower()] = value.strip()
        expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if b" 101 " not in status or headers.get("sec-websocket-accept") != expected:
            self.close()
            raise RuntimeError("App-server WebSocket upgrade rejected: " + status.decode().strip())
        self.counter = 0
        self.call("initialize", {"clientInfo": {"name": "nconnect_monitor", "version": "1"}, "capabilities": {"experimentalApi": True}})
        self.send({"method": "initialized"})

    def _exact(self, size: int) -> bytes:
        data = self.reader.read(size)
        if len(data) != size:
            raise RuntimeError("App-server connection closed")
        return data

    def _send_bytes(self, data: bytes) -> None:
        if self.socket:
            self.socket.sendall(data)
        else:
            assert self.proxy and self.proxy.stdin
            self.proxy.stdin.write(data)
            self.proxy.stdin.flush()

    def _frame(self, payload: bytes, opcode: int = 1) -> None:
        size = len(payload)
        header = bytes([0x80 | opcode])
        header += bytes([0x80 | size]) if size < 126 else (bytes([0x80 | 126]) + struct.pack("!H", size) if size < 65536 else bytes([0x80 | 127]) + struct.pack("!Q", size))
        mask = os.urandom(4)
        self._send_bytes(header + mask + bytes(value ^ mask[index % 4] for index, value in enumerate(payload)))

    def receive(self) -> dict[str, Any]:
        chunks = bytearray()
        while True:
            first, second = self._exact(2)
            size = second & 127
            if size == 126:
                size = struct.unpack("!H", self._exact(2))[0]
            elif size == 127:
                size = struct.unpack("!Q", self._exact(8))[0]
            if size > 8 * 1024 * 1024:
                raise RuntimeError("Unexpectedly large app-server frame")
            if second & 128:
                raise RuntimeError("Invalid masked server frame")
            payload = self._exact(size)
            opcode = first & 15
            if opcode == 8:
                raise RuntimeError("App-server WebSocket closed")
            if opcode == 9:
                self._frame(payload, 10)
                continue
            if opcode == 10:
                continue
            if opcode not in (0, 1):
                raise RuntimeError("Unexpected app-server frame type")
            chunks.extend(payload)
            if first & 128:
                return json.loads(chunks)

    def send(self, value: dict[str, Any]) -> None:
        self._frame(json.dumps(value, ensure_ascii=False).encode("utf-8"))

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.counter += 1
        request_id = self.counter
        self.send({"id": request_id, "method": method, "params": params})
        while True:
            value = self.receive()
            if value.get("id") != request_id:
                continue
            if "error" in value:
                raise RuntimeError(f"{method}: {value['error']}")
            return value["result"]

    def close(self) -> None:
        # Close only our connection; never stop the app server or writer.
        self.reader.close()
        if self.socket:
            self.socket.close()
        if self.proxy:
            if self.proxy.stdin:
                self.proxy.stdin.close()
            try:
                self.proxy.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proxy.terminate()
                self.proxy.wait(timeout=3)


def dispatch(rpc: Any, thread_id: str, prompt: str, message_id: str, probe: bool = False) -> dict[str, Any]:
    thread = rpc.call("thread/read", {"threadId": thread_id, "includeTurns": False})["thread"]
    if probe:
        return {"state": "PROBE_OK", "thread_id": thread_id, "status": thread.get("status")}
    pending = rpc.call("thread/queue/list", {"threadId": thread_id})
    # Do not pile up monitor requests while a long continuation owns the thread.
    entries = pending.get("data", pending.get("items", pending.get("queuedSubmissions", [])))
    existing = next((item for item in entries if item.get("clientUserMessageId", "").startswith("nconnect-monitor-")), None)
    if existing:
        submission = existing
    else:
        result = rpc.call("thread/queue/add", {"threadId": thread_id, "clientUserMessageId": message_id, "input": [{"type": "text", "text": prompt}]})
        submission = result.get("queuedSubmission", result.get("submission", result))
    status = thread.get("status", {})
    active = status.get("type") == "active" if isinstance(status, dict) else status == "active"
    not_loaded = status.get("type") == "notLoaded" if isinstance(status, dict) else status == "notLoaded"
    state = "QUEUED_WHILE_ACTIVE"
    if not active:
        if not_loaded:
            rpc.call("thread/resume", {"threadId": thread_id})
        # The host may consume the queue automatically on resume or turn completion.
        # Never treat that race as a failed delivery or re-add the same request.
        remaining = rpc.call("thread/queue/list", {"threadId": thread_id}).get("data", [])
        if any(item["id"] == submission["id"] for item in remaining):
            try:
                rpc.call("thread/queue/start", {"threadId": thread_id, "queuedSubmissionId": submission["id"]})
            except RuntimeError:
                after = rpc.call("thread/queue/list", {"threadId": thread_id}).get("data", [])
                if any(item["id"] == submission["id"] for item in after):
                    raise
        state = "DISPATCHED"
    return {"state": state, "thread_id": thread_id, "submission_id": submission.get("id"), "report_delivered": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    now = datetime.now()
    slot = now.replace(minute=(now.minute // 30) * 30, second=0, microsecond=0)
    prompt = (
        "[30-minute scheduled monitor] 사용자 요청에 따른 자동 확인입니다. "
        "tools/pc2_hourly_monitor_prompt.md의 최신 H1 우선순위를 따르세요. "
        "현재 실제 학습/평가/영상/회수 진행률과 차단을 확인해 이 대화에 한국어로 보고하고, "
        "A077 완료 시 회수·검증·판독·commit/push 후 H1 H-A001 기존 결과 판독과 조건부 "
        "1000iter 탐색으로 이어가세요. 완료한 학습/P0 반복 금지, 추가 Go2 삽입 금지. "
        "파일 기록만으로 보고를 대체하거나 일반 진행 승인을 다시 묻지 마세요."
    )
    rpc = Rpc()
    try:
        print(json.dumps(dispatch(rpc, args.thread_id, prompt, "nconnect-monitor-" + slot.isoformat(), args.probe), ensure_ascii=False))
    finally:
        rpc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
