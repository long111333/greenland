"""Interactive hardware exercise; connecting alone does not move any actuator."""
import argparse
import json
import logging
import serial
from pathlib import Path
from serial.tools import list_ports

from arduino_client import ArduinoClient, ArduinoError


def main():
    parser = argparse.ArgumentParser(description="Smart Trash Bin USB console", allow_abbrev=False)
    parser.add_argument("--port", help="/dev/ttyACM0 or COM3; otherwise auto-detect")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--list-ports", action="store_true", help="List USB serial ports without opening them")
    parser.add_argument("--probe", action="store_true", help="Connect and read status/color; no motion commands")
    parser.add_argument("--guided", action="store_true", help="Guided physical workflow test with a JSON report")
    parser.add_argument("--calibrate-color", action="store_true", help="Read-only capture of four real color references; never moves actuators")
    parser.add_argument("--samples", type=int, default=12, help="Samples per color in calibration (5..100)")
    parser.add_argument("--calibration-report", default="test-reports/color-calibration.json")
    parser.add_argument("--report", default="test-reports/manual-test.json")
    parser.add_argument("--log-file", help="Save detailed TX/RX and state log")
    args = parser.parse_args()
    if args.list_ports:
        ports = list(list_ports.comports())
        for port in ports:
            print(f"{port.device}: {port.description} [{port.hwid}]")
        if not ports:
            print("No serial ports found. Connect Arduino with a USB data cable.")
        return
    if sum((args.probe, args.guided, args.calibrate_color)) > 1:
        parser.error("Choose --probe, --guided or --calibrate-color")
    if not 5 <= args.samples <= 100:
        parser.error("--samples must be 5..100")
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if args.debug else logging.INFO)
    handlers = [console]
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(level=logging.DEBUG, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(message)s")
    with ArduinoClient(args.port) as client:
        if args.probe:
            print(json.dumps({"status": client.get_status(), "color": client.get_color()}, indent=2))
            return
        if args.guided:
            from manual_test import run_guided
            if not run_guided(client, args.report):
                raise SystemExit(1)
            return
        if args.calibrate_color:
            from calibrate_color import run_calibration
            if not run_calibration(client, args.calibration_report, args.samples):
                raise SystemExit(1)
            return
        print("status | color | weight | tare | close | home | sort 1..4 | open | stop | reset | reconnect | test_stepper | diag | heartbeat on/off | quit")
        print("Positions: 1=RED, 2=BLUE, 3=GREEN, 4=BLACK. Ctrl+C sends STOP.")
        print("Before CLOSE/HOME: clear mechanism, inspect wiring and external power.")
        actions = {"status": client.get_status, "color": client.get_color,
                   "close": client.close_gate, "home": client.home,
                   "open": client.open_gate, "stop": client.stop,
                   "reset": client.reset_error, "diag": client.motion_diag,
                   "weight": client.get_weight, "tare": client.tare_weight}
        while True:
            try:
                command = input("> ").strip().split()
                if not command:
                    continue
                if command == ["quit"]:
                    break
                if command == ["reconnect"]:
                    print("Reopening USB may reset Uno. Motion and HOME will not be replayed.")
                    print(json.dumps(client.reconnect(), ensure_ascii=False))
                    continue
                if command == ["test_stepper"]:
                    print("This runs the fixed-step motor test at firmware-configured speed/acceleration, with sensors/serial active.")
                    if input("Mechanism clear, gate closed; authorize motion [y/N]: ").strip().lower() != "y":
                        continue
                    print(json.dumps(client.test_stepper()))
                    print(json.dumps(client.motion_diag()))
                    continue
                if len(command) == 2 and command[0] == "sort":
                    result = client.sort(int(command[1]))
                elif len(command) == 2 and command[0] == "heartbeat" and command[1] in ("on", "off"):
                    client.set_heartbeat(command[1] == "on")
                    continue
                elif len(command) == 1 and command[0] in actions:
                    result = actions[command[0]]()
                else:
                    print("Unknown command")
                    continue
                print(json.dumps(result, ensure_ascii=False))
            except KeyboardInterrupt:
                try:
                    print("\nSTOP:", client.stop())
                except Exception as error:
                    print(f"STOP could not be delivered: {error}")
            except EOFError:
                break
            except Exception as exc:
                print(f"ERROR: {exc}")


if __name__ == "__main__":
    try:
        main()
    except (ArduinoError, serial.SerialException, TimeoutError) as error:
        logging.error("%s", error)
        raise SystemExit(1)
