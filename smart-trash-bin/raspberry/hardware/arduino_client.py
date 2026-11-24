"""USB JSON Lines client. No automatic motion retries; one receiver + heartbeat."""
from __future__ import annotations

import json
import logging
import threading
import time
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import serial
from serial.tools import list_ports

LOG = logging.getLogger(__name__)


class ArduinoError(RuntimeError):
    pass


@dataclass
class _Pending:
    event: threading.Event = field(default_factory=threading.Event)
    result: dict[str, Any] | None = None
    error: Exception | None = None
    accepted: bool = False


class ArduinoClient:
    def __init__(self, port: str | None = None, *, baudrate: int = 115200,
                 reset_wait: float = 2.0, command_timeout: float = 75.0):
        self.port, self.baudrate = port, baudrate
        self.reset_wait, self.command_timeout = reset_wait, command_timeout
        self._serial = None
        self._reader = None
        self._running = threading.Event()
        self._write_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._motion_lock = threading.Lock()
        self._pending: dict[int, _Pending] = {}
        self._next_id = 0
        self._ready = False
        self._uncertain = False
        self.latest_status: dict[str, Any] = {}
        self._last_rx = 0.0
        self.messages = deque(maxlen=2048)
        self._heartbeat_enabled = threading.Event()
        self._heartbeat_enabled.set()
        self.invalid_lines = 0
        self._last_invalid_log = float("-inf")
        self.last_link_error = None

    def connect(self):
        if self._running.is_set():
            return self.latest_status
        self.disconnect()
        port = self.port
        if port is None:
            candidates = [p.device for p in list_ports.comports()
                          if p.vid in (0x2341, 0x2A03, 0x1A86)]
            if len(candidates) != 1:
                raise ArduinoError("Specify port explicitly; no unique Arduino USB port found")
            port = candidates[0]
        self._serial = serial.Serial(port, self.baudrate, timeout=0.05, write_timeout=0.5)
        # Uno commonly resets on DTR. Never restore local homed state after opening USB.
        self._ready = False
        self._uncertain = False
        self.latest_status = {}
        self.messages.clear()
        self._heartbeat_enabled.set()
        # Some USB adapters deliver buffered fragments during reset. Drain them
        # while the board boots, rather than leaving them queued for the parser.
        self._serial.reset_input_buffer()
        startup_deadline = time.monotonic() + self.reset_wait
        while time.monotonic() < startup_deadline:
            self._serial.read(128)
        self._serial.reset_input_buffer()
        self.invalid_lines = 0
        self._last_invalid_log = float("-inf")
        self._last_rx = time.monotonic()
        self._running.set()
        self._reader = threading.Thread(target=self._read_loop, name="arduino-rx", daemon=True)
        self._reader.start()
        try:
            # Only retry a read-only handshake, never a motion command.
            for attempt in range(3):
                try:
                    status = self.get_status()
                    break
                except TimeoutError:
                    if attempt == 2 or not self._running.is_set():
                        raise
                    LOG.warning("Status handshake timed out; retrying read-only GET_STATUS")
            LOG.info("Connected %s; state=%s; explicit HOME required", port, status.get("state"))
            self.last_link_error = None
            return status
        except Exception:
            self.disconnect()
            raise

    def disconnect(self):
        self._running.clear()
        self._ready = False
        self._fail_pending(ArduinoError("Disconnected; verify mechanism and HOME again"))
        if self._reader and self._reader is not threading.current_thread():
            self._reader.join(timeout=1.5)
        self._reader = None
        if self._serial:
            self._serial.close()
            self._serial = None

    def _fail_pending(self, error):
        with self._pending_lock:
            for pending in self._pending.values():
                pending.error = error
                pending.event.set()

    def reconnect(self):
        """Explicitly reopen USB and query status; never replay motion or HOME."""
        self.disconnect()
        return self.connect()

    def _link_failed(self, error):
        if not self._running.is_set():
            return
        self.last_link_error = f"{type(error).__name__}: {error}"
        self._ready = False
        self._uncertain = True
        self._running.clear()
        self.messages.append({"time": time.monotonic(), "direction": "LINK_ERROR", "error": self.last_link_error})
        LOG.error("Serial link failed: %s. Previous motion outcome unknown; inspect mechanism and reconnect explicitly.", self.last_link_error)
        self._fail_pending(ArduinoError(f"Link lost: {self.last_link_error}; reconnect required; previous motion outcome unknown"))

    def _send(self, cmd, target=None, pending=None, params=None):
        # Allocate IDs and transmit under one lock so heartbeat cannot reorder IDs.
        with self._write_lock:
            if not self._running.is_set() or self._serial is None:
                raise ArduinoError("Not connected: STOP cannot be delivered over the failed link. Inspect mechanism, then use reconnect; do not retry previous motion blindly")
            self._next_id += 1
            if self._next_id > 2147483647:
                raise ArduinoError("ID range exhausted; restart Arduino and reconnect")
            request = {"id": self._next_id, "cmd": cmd}
            if target is not None:
                request["target"] = target
            if params:
                request.update(params)
            if pending is not None:
                with self._pending_lock:
                    self._pending[self._next_id] = pending
            data = (json.dumps(request, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
            try:
                if self._serial.write(data) != len(data):
                    raise ArduinoError("Partial serial write; command outcome unknown")
            except Exception as error:
                if pending is not None:
                    with self._pending_lock:
                        self._pending.pop(request["id"], None)
                self._link_failed(error)
                raise ArduinoError(f"Serial write failed: {error}; reconnect required; command was not retried") from error
            LOG.debug("TX %s", request)
            self.messages.append({"time": time.monotonic(), "direction": "TX", "message": request.copy()})
            return request["id"]

    def _read_loop(self):
        buffer = bytearray()
        dropping = False
        last_heartbeat = time.monotonic()
        try:
            while self._running.is_set():
                now = time.monotonic()
                if self._heartbeat_enabled.is_set() and now - last_heartbeat >= 1.0:
                    self._send("GET_STATUS")
                    last_heartbeat = now
                chunk = self._serial.read(128)
                for byte in chunk:
                    if byte == 10:
                        if not dropping and buffer:
                            try:
                                msg = json.loads(buffer)
                            except (ValueError, UnicodeDecodeError):
                                self._invalid_line(buffer)
                            else:
                                if isinstance(msg, dict):
                                    self._receive(msg)
                        buffer.clear()
                        dropping = False
                    elif len(buffer) >= 512:
                        buffer.clear()
                        dropping = True
                    elif not dropping:
                        buffer.append(byte)
                if time.monotonic() - self._last_rx > 4.5:
                    raise ArduinoError("No valid response; link lost")
        except Exception as exc:
            self._link_failed(exc)

    def _invalid_line(self, data):
        self.invalid_lines += 1
        preview = bytes(data[:160])
        self.messages.append({"time": time.monotonic(), "direction": "RX_INVALID",
                              "raw_hex": preview.hex(), "length": len(data)})
        LOG.debug("Invalid serial line (%d bytes): %r", len(data), preview)
        now = time.monotonic()
        if now - self._last_invalid_log >= 1.0:
            self._last_invalid_log = now
            LOG.warning("Malformed serial JSON (total=%d), sample=%r; check startup/baud/firmware if persistent",
                        self.invalid_lines, preview)

    def _receive(self, msg):
        self._last_rx = time.monotonic()
        LOG.debug("RX %s", msg)
        self.messages.append({"time": time.monotonic(), "direction": "RX", "message": msg.copy()})
        if msg.get("type") == "STATE_CHANGE":
            LOG.info("State #%s: %s -> %s", msg.get("id"), msg.get("from"), msg.get("to"))
        if msg.get("type") == "TELEMETRY":
            self.latest_status = msg
            if not msg.get("homed") or msg.get("state") == "ERROR":
                self._ready = False
            if msg.get("bin_status") == "FULL":
                LOG.warning("Monitored compartment %s FULL", msg.get("monitored_bin"))
        with self._pending_lock:
            pending = self._pending.get(msg.get("id"))
            if pending is None:
                return
            if msg.get("status") == "ACCEPTED":
                pending.accepted = True
                LOG.info("Command %s ACCEPTED", msg["id"])
            elif msg.get("status") in ("COMPLETE", "ERROR") or msg.get("type") in ("TELEMETRY", "COLOR", "MOTION_DIAG", "WEIGHT"):
                pending.result = msg
                pending.event.set()

    def _request(self, cmd, target=None, timeout=None, params=None):
        pending = _Pending()
        request_id = self._send(cmd, target, pending, params)
        try:
            if not pending.event.wait(self.command_timeout if timeout is None else timeout):
                self._ready = False
                if cmd in ("GET_STATUS", "GET_COLOR", "GET_MOTION_DIAG", "GET_WEIGHT"):
                    raise TimeoutError(f"{cmd} id={request_id}: no reply; check serial port, 115200 baud and firmware; malformed lines={self.invalid_lines}")
                self._uncertain = True
                raise TimeoutError(f"{cmd} id={request_id}: outcome unknown; STOP, inspect, RESET_ERROR, CLOSE_GATE, HOME")
            if pending.error:
                raise pending.error
            result = pending.result
            if result.get("status") == "ERROR":
                raise ArduinoError(f"{cmd} id={request_id}: {result.get('error')}")
            return result
        except KeyboardInterrupt:
            self._ready = False
            self._uncertain = True
            raise
        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def _motion(self, cmd, target=None, params=None):
        if not self._motion_lock.acquire(blocking=False):
            raise ArduinoError("Another motion command is pending")
        try:
            if self._uncertain:
                raise ArduinoError("Previous outcome unknown; STOP and RESET_ERROR first")
            return self._request(cmd, target, params=params)
        finally:
            self._motion_lock.release()

    def home(self):
        self._ready = False
        result = self._motion("HOME")
        status = self.get_status()
        self._ready = bool(status.get("homed") and status.get("state") == "IDLE")
        if not self._ready:
            raise ArduinoError("HOME response received but ready state not confirmed")
        return result

    def sort(self, target):
        if type(target) is not int or not 1 <= target <= 4:
            raise ValueError("target must be an integer 1..4")
        if not self._ready:
            raise ArduinoError("Explicit successful HOME required in this connection")
        return self._motion("SORT", target)

    def open_gate(self):
        if not self._ready:
            raise ArduinoError("HOME required before opening")
        return self._motion("OPEN_GATE")

    def close_gate(self):
        return self._motion("CLOSE_GATE")

    def stop(self):
        # Bypass the motion lock: STOP must interrupt a waiting SORT/HOME.
        self._ready = False
        return self._request("STOP", timeout=3.0)

    def reset_error(self):
        result = self._request("RESET_ERROR", timeout=3.0)
        self._uncertain = False
        self._ready = False
        return result

    def get_status(self):
        return self._request("GET_STATUS", timeout=3.0)

    def get_color(self):
        return self._request("GET_COLOR", timeout=3.0)

    def test_stepper(self):
        """Fixed 1000-step baseline test; gate must be closed; HOME is invalidated."""
        self._ready = False
        return self._motion("TEST_STEPPER")

    def motion_diag(self):
        return self._request("GET_MOTION_DIAG", timeout=3.0)

    def get_weight(self):
        return self._request("GET_WEIGHT", timeout=3.0)

    def tare_weight(self):
        return self._motion("TARE_WEIGHT")

    def set_scale(self, factor, offset):
        if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not math.isfinite(factor) or not 1 < abs(factor) <= 1e12:
            raise ValueError("factor must be finite ADC counts/kg, 1 < abs(factor) <= 1e12")
        if type(offset) is not int or not -8388608 <= offset <= 8388607:
            raise ValueError("offset must be a signed 24-bit ADC count")
        return self._motion("SET_SCALE", params={"factor": factor, "offset": offset})

    def set_heartbeat(self, enabled: bool):
        """Fault-injection helper: RX stays active while automatic requests pause."""
        if enabled:
            self._heartbeat_enabled.set()
        else:
            self._heartbeat_enabled.clear()
        LOG.warning("Heartbeat %s", "ON" if enabled else "OFF; link timeout expected after HOME")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
