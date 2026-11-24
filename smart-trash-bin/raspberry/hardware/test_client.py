"""Offline protocol tests using a fake serial endpoint; no hardware movements."""
import json
import queue
import threading
import time
import unittest
from unittest.mock import patch
from serial import SerialTimeoutException

from arduino_client import ArduinoClient, ArduinoError


class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.rx = queue.Queue()
        self.requests = []
        self.homed = False
        self.hold_sort = False
        self.pending_sort = None
        self.position = 0
        self.color_position = 1
        self.scale_factor = 1.0
        self.scale_offset = 0
        self.scale_calibrated = False

    def reset_input_buffer(self):
        pass

    def close(self):
        pass

    def emit(self, message):
        self.rx.put((json.dumps(message) + "\n").encode())

    def write(self, data):
        request = json.loads(data)
        self.requests.append(request)
        command, ident = request["cmd"], request["id"]
        if command == "GET_STATUS":
            self.emit({"id": ident, "type": "TELEMETRY", "state": "IDLE" if self.homed else "INIT", "homed": self.homed, "position": self.position})
        elif command == "GET_COLOR":
            self.emit({"id": ident, "type": "COLOR", "r": 100, "healthy": True, "position": self.color_position})
        elif command == "GET_MOTION_DIAG":
            self.emit({"id": ident, "type": "MOTION_DIAG", "emitted_steps": 1000, "max_run_gap_us": 250})
        elif command == "GET_WEIGHT":
            self.emit({"id": ident, "type": "WEIGHT", "raw": 101000, "sample_seq": ident,
                       "healthy": True, "calibrated": self.scale_calibrated,
                       "factor": self.scale_factor, "offset": self.scale_offset, "weight_kg": 0.2})
        else:
            self.emit({"id": ident, "status": "ACCEPTED"})
            if command == "SET_SCALE":
                self.scale_factor, self.scale_offset = request["factor"], request["offset"]
                self.scale_calibrated = True
            if command == "HOME":
                self.homed = True
                self.position = 1
            if command == "TEST_STEPPER":
                self.homed = False
                self.position = 0
            if command == "STOP":
                self.homed = False
                if self.pending_sort:
                    self.emit({"id": self.pending_sort, "status": "ERROR", "error": "STOPPED"})
                    self.pending_sort = None
            if command == "SORT" and self.hold_sort:
                self.pending_sort = ident
            else:
                if command == "SORT":
                    self.position = request["target"]
                    previous = "IDLE"
                    for state in ("ROTATING", "VERIFY_POSITION", "OPENING", "HOLDING", "CLOSING", "COMPLETE"):
                        self.emit({"type": "STATE_CHANGE", "id": ident, "from": previous, "to": state})
                        previous = state
                self.emit({"id": ident, "status": "COMPLETE", "position": request.get("target", 1)})
        return len(data)

    def read(self, size):
        try:
            return self.rx.get(timeout=0.02)
        except queue.Empty:
            return b""


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSerial()
        self.patch = patch("arduino_client.serial.Serial", return_value=self.fake)
        self.patch.start()
        self.client = ArduinoClient("fake", reset_wait=0, command_timeout=0.3)
        self.client.connect()

    def tearDown(self):
        self.client.disconnect()
        self.patch.stop()

    def test_connect_is_read_only_and_requires_home(self):
        self.assertTrue(all(r["cmd"] == "GET_STATUS" for r in self.fake.requests))
        with self.assertRaises(ArduinoError):
            self.client.sort(1)

    def test_write_timeout_marks_link_failed_without_retry(self):
        self.client.home()
        with patch.object(self.fake, "write", side_effect=SerialTimeoutException("Write timeout")) as write:
            with self.assertRaisesRegex(ArduinoError, "command was not retried"):
                self.client.get_status()
            self.assertEqual(write.call_count, 1)
        self.assertFalse(self.client._running.is_set())
        self.assertFalse(self.client._ready)
        self.assertTrue(self.client._uncertain)
        self.assertIn("SerialTimeoutException", self.client.last_link_error)
        with self.assertRaisesRegex(ArduinoError, "STOP cannot be delivered"):
            self.client.stop()

    def test_reconnect_queries_status_without_motion_or_restoring_home(self):
        self.client.home()
        self.client._link_failed(SerialTimeoutException("Write timeout"))
        before = len(self.fake.requests)
        status = self.client.reconnect()
        self.assertEqual(status["state"], "IDLE")
        self.assertTrue(all(request["cmd"] == "GET_STATUS" for request in self.fake.requests[before:]))
        self.assertFalse(self.client._ready)
        with self.assertRaisesRegex(ArduinoError, "HOME required"):
            self.client.sort(2)

    def test_complete_and_target_validation(self):
        self.client.home()
        self.assertEqual(self.client.sort(3)["position"], 3)
        for invalid in (0, 5, True, 1.5, "2"):
            with self.assertRaises(ValueError):
                self.client.sort(invalid)

    def test_scale_configuration_and_weight_response(self):
        self.client.set_scale(-500000.0, 1000)
        data = self.client.get_weight()
        self.assertTrue(data["calibrated"])
        self.assertEqual(data["factor"], -500000)
        self.assertEqual(data["offset"], 1000)
        self.assertEqual(self.client.tare_weight()["status"], "COMPLETE")
        for factor in (float("nan"), float("inf"), 0, 1, True):
            with self.assertRaises(ValueError):
                self.client.set_scale(factor, 0)
        with self.assertRaises(ValueError):
            self.client.set_scale(10000, 8388608)

    def test_accepted_is_not_complete_and_no_retry(self):
        self.client.home()
        self.fake.hold_sort = True
        with self.assertRaises(TimeoutError):
            self.client.sort(2)
        self.assertEqual(sum(r["cmd"] == "SORT" for r in self.fake.requests), 1)
        with self.assertRaises(ArduinoError):
            self.client.close_gate()

    def test_stop_interrupts_pending_sort(self):
        self.client.home()
        self.fake.hold_sort = True
        errors = []
        def sort():
            try:
                self.client.sort(2)
            except ArduinoError as exc:
                errors.append(str(exc))
        thread = threading.Thread(target=sort)
        thread.start()
        deadline = time.monotonic() + 0.2
        while not self.fake.pending_sort and time.monotonic() < deadline:
            time.sleep(0.001)
        with self.assertRaises(ArduinoError):
            self.client.sort(3)
        self.assertEqual(self.client.stop()["status"], "COMPLETE")
        thread.join(timeout=1)
        self.assertTrue(errors and "STOPPED" in errors[0])

    def test_reset_telemetry_invalidates_local_home(self):
        self.client.home()
        self.fake.homed = False
        self.client.get_status()
        with self.assertRaises(ArduinoError):
            self.client.sort(1)

    def test_heartbeat_continues_during_command(self):
        self.client.home()
        self.fake.hold_sort = True
        self.client.command_timeout = 1.2
        before = len(self.fake.requests)
        with self.assertRaises(TimeoutError):
            self.client.sort(2)
        self.assertTrue(any(r["cmd"] == "GET_STATUS" for r in self.fake.requests[before:]))

    def test_heartbeat_can_pause_without_closing_receiver(self):
        self.client.set_heartbeat(False)
        before = len(self.fake.requests)
        time.sleep(1.1)
        self.assertTrue(self.client._running.is_set())
        self.assertEqual(len(self.fake.requests), before)
        self.assertEqual(self.client.get_color()["type"], "COLOR")
        self.client.set_heartbeat(True)

    def test_state_event_is_recorded_without_completing_request(self):
        self.client._receive({"type": "STATE_CHANGE", "id": 55, "from": "ROTATING", "to": "VERIFY_POSITION"})
        self.assertEqual(self.client.messages[-1]["message"]["to"], "VERIFY_POSITION")

    def test_stepper_baseline_does_not_require_home_and_invalidates_ready(self):
        self.client.home()
        self.assertEqual(self.client.test_stepper()["status"], "COMPLETE")
        self.assertEqual(self.client.motion_diag()["emitted_steps"], 1000)
        with self.assertRaises(ArduinoError):
            self.client.sort(2)

    def test_invalid_line_warnings_are_limited_and_raw_bytes_saved(self):
        with patch("arduino_client.LOG.warning") as warning:
            for _ in range(100):
                self.client._invalid_line(b'"g":262,"healthy":true}')
            self.assertEqual(warning.call_count, 1)
        self.assertEqual(self.client.invalid_lines, 100)
        self.assertEqual(self.client.messages[-1]["direction"], "RX_INVALID")
        self.assertEqual(bytes.fromhex(self.client.messages[-1]["raw_hex"]), b'"g":262,"healthy":true}')

    def test_read_only_timeout_does_not_mark_motion_uncertain(self):
        with patch.object(self.fake, "write", side_effect=lambda data: len(data)):
            with self.assertRaisesRegex(TimeoutError, "no reply"):
                self.client._request("GET_COLOR", timeout=0.02)
        self.assertFalse(self.client._uncertain)

    def test_startup_drains_old_fragments_before_handshake(self):
        self.client.disconnect()
        self.fake.rx.put(b'"g":262,"healthy":true}\n' * 30)
        self.client.reset_wait = 0.06
        self.client.connect()
        self.assertEqual(self.client.invalid_lines, 0)
        self.assertEqual(self.client.latest_status["state"], "INIT")

    def test_connect_retries_only_read_only_handshake(self):
        self.client.disconnect()
        with patch.object(self.client, "get_status", side_effect=[TimeoutError("boot"), {"state": "INIT"}]) as status:
            self.assertEqual(self.client.connect()["state"], "INIT")
            self.assertEqual(status.call_count, 2)

    def test_guided_cancel_writes_report_and_sends_stop(self):
        import tempfile
        from pathlib import Path
        from manual_test import run_guided
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.json"
            with patch("builtins.input", return_value="n"):
                self.assertFalse(run_guided(self.client, report))
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(data["passed"])
            self.assertEqual(data["stop_response"]["status"], "COMPLETE")
            self.assertTrue(any(r["cmd"] == "STOP" for r in self.fake.requests))
            self.assertFalse(any(r["cmd"] in ("SORT", "HOME", "CLOSE_GATE") for r in self.fake.requests))

    def test_guided_full_workflow_records_trace_and_physical_checks(self):
        import tempfile
        from pathlib import Path
        from manual_test import run_guided
        def confirm(prompt):
            for position, name in enumerate(("RED", "BLUE", "GREEN", "BLACK"), 1):
                if f"place the {name} marker" in prompt:
                    self.fake.color_position = position
            return "y"
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.json"
            with patch("builtins.input", side_effect=confirm), patch("manual_test.time.sleep", return_value=None):
                self.assertTrue(run_guided(self.client, report))
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(data["passed"] and data["trace_complete"])
            sorts = [step for step in data["steps"] if step["name"].startswith("SORT ")]
            self.assertEqual(len(sorts), 10)
            self.assertTrue(all(step["physical_passed"] and step["trace_complete"] for step in sorts))


if __name__ == "__main__":
    unittest.main()
