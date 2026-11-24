"""Guided hardware test. Physical observations are distinct from software replies."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def run_guided(client, report_path):
    report = {"started_at": datetime.now(timezone.utc).isoformat(),
              "positions": {1: "RED", 2: "BLUE", 3: "GREEN", 4: "BLACK"},
              "steps": [], "passed": False}

    def confirm(prompt):
        if input(prompt + " [y/N]: ").strip().lower() != "y":
            raise RuntimeError("Operator did not confirm; test stopped")

    def step(name, action, check, observation=None):
        record = {"name": name, "software_passed": False, "physical_passed": None}
        if name.startswith("SORT "):
            record["start_position"] = client.latest_status.get("position")
        report["steps"].append(record)
        started = time.monotonic()
        try:
            response = action()
            record["response"] = response
            record["software_passed"] = bool(check(response))
            if not record["software_passed"]:
                raise RuntimeError(f"Unexpected result at {name}: {response}")
            if observation:
                confirm(observation)
                record["physical_passed"] = True
            print(f"PASS: {name}")
            return response
        finally:
            record["elapsed_s"] = round(time.monotonic() - started, 3)

    try:
        print("Guided physical test: no trash initially; external motor power and clear mechanism required.")
        print("This test will move both servos and the tube ONLY after you confirm the motion stage.")
        step("Boot status", client.get_status,
             lambda r: r.get("state") == "INIT" and r.get("homed") is False,
             "Confirm no automatic movement occurred on boot/connect")
        # Read-only calibration exercise before the first explicit actuator command.
        for position, name in report["positions"].items():
            confirm(f"With the tube stationary and coils released, place the {name} marker at the sensor")
            time.sleep(1.2)
            step(f"Color {name}", client.get_color,
                 lambda r, p=position: r.get("healthy") is True and r.get("position") == p)

        confirm("Clear the mechanism and authorize CLOSE_GATE followed by HOME")
        step("Close gate", client.close_gate, lambda r: r.get("status") == "COMPLETE",
             "Did both servos close together, in the correct direction, without binding")
        step("HOME", client.home, lambda r: r.get("status") == "COMPLETE",
             "Did the tube stop at RED and remain stopped with the gate closed")
        step("Ready status", client.get_status,
             lambda r: r.get("state") == "IDLE" and r.get("homed") is True and r.get("position") == 1)

        for sequence in ([1, 2, 3, 4, 1], [1, 3, 2, 4, 1]):
            for target in sequence:
                confirm(f"Clear the mechanism and authorize SORT {target} ({report['positions'][target]})")
                step(f"SORT {target}", lambda p=target: client.sort(p),
                     lambda r, p=target: r.get("status") == "COMPLETE" and r.get("position") == p,
                     "Correct marker/compartment; motor stopped before opening; both servos opened, held, then closed")
                step("After SORT", client.get_status,
                     lambda r, p=target: r.get("state") == "IDLE" and r.get("homed") is True and r.get("position") == p)
        report["passed"] = True
    except (Exception, KeyboardInterrupt) as exc:
        report["error"] = str(exc) or "Interrupted by operator"
        print(f"Test stopped: {report['error']}")
        # Once a workflow fails, cancel outstanding motion; never auto-close or retry.
        try:
            report["stop_response"] = client.stop()
        except Exception as stop_error:
            report["stop_error"] = str(stop_error)
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["messages"] = list(client.messages)
        trace_checks = []
        for record in report["steps"]:
            if not record["name"].startswith("SORT ") or "response" not in record:
                continue
            ident = record["response"].get("id")
            states = [entry["message"].get("to") for entry in report["messages"]
                      if entry["direction"] == "RX" and entry["message"].get("type") == "STATE_CHANGE"
                      and entry["message"].get("id") == ident]
            phases = ["VERIFY_POSITION", "OPENING", "HOLDING", "CLOSING", "COMPLETE"]
            if record.get("start_position") != record["response"].get("position"):
                phases.insert(0, "ROTATING")
            record["expected_states"] = phases
            expected = iter(phases)
            wanted = next(expected, None)
            for state in states:
                if state == wanted:
                    wanted = next(expected, None)
            record["observed_states"] = states
            record["trace_complete"] = wanted is None
            trace_checks.append(record["trace_complete"])
        report["trace_complete"] = bool(trace_checks) and all(trace_checks)
        report["trace_note"] = "STATE_CHANGE is diagnostic and may drop under load; observations and terminal responses are recorded separately."
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report saved: {path.resolve()}")
    return report["passed"]
