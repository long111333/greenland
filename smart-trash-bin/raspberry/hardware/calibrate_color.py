"""Collect labeled GY-33 samples. Does not move actuators or edit firmware."""
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path


def run_calibration(client, report_path, samples=12):
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "colors": [], "valid": False,
              "max_distance": 0.07, "min_margin": 0.03}
    try:
        status = client.get_status()
        if status.get("state") not in ("INIT", "ERROR") or status.get("homed"):
            raise RuntimeError("Calibration requires stopped INIT/ERROR, not an active/homed mechanism")
        print("Read-only calibration: no CLOSE/HOME/SORT/STOP commands will be sent.")
        print("Keep lighting and sensor distance fixed. Place the actual marker at the sensor while stationary.")
        for position, name in enumerate(("RED", "BLUE", "GREEN", "BLACK"), 1):
            if input(f"Place {name} at sensor, confirm it is the actual marker [y/N]: ").strip().lower() != "y":
                raise RuntimeError("Calibration cancelled")
            readings = []
            for _ in range(samples):
                time.sleep(0.25)
                raw = client.get_color()
                if raw.get("healthy") is not True:
                    raise RuntimeError(f"{name}: sensor unhealthy; check GY-33/I2C")
                channels = [raw.get(key) for key in ("r", "g", "b")]
                if any(type(value) is not int or value < 0 for value in channels):
                    raise RuntimeError(f"{name}: invalid RGB response")
                total = sum(channels)
                if not total or raw.get("clear", 0) < 100:
                    raise RuntimeError(f"{name}: RGB sum zero or Clear below 100; adjust lighting first")
                normalized = [channel / total for channel in channels]
                readings.append({"raw": raw, "normalized": normalized})
                print(f"{name}: RGB={channels}, C={raw['clear']}, normalized="
                      + ", ".join(f"{v:.4f}" for v in normalized))
            reference = [sum(row["normalized"][i] for row in readings) / len(readings) for i in range(3)]
            spread = max(math.dist(row["normalized"], reference) for row in readings)
            report["colors"].append({"position": position, "name": name, "reference": reference,
                                     "max_sample_distance": spread, "samples": readings})
        references = [color["reference"] for color in report["colors"]]
        distances = [math.dist(references[a], references[b]) for a in range(4) for b in range(a + 1, 4)]
        report["minimum_reference_separation"] = min(distances)
        failures = 0
        for color in report["colors"]:
            for sample in color["samples"]:
                ranked = sorted((math.dist(sample["normalized"], ref), i + 1) for i, ref in enumerate(references))
                if ranked[0][1] != color["position"] or ranked[0][0] > 0.07 or ranked[1][0] - ranked[0][0] < 0.03:
                    failures += 1
        report["failed_training_samples"] = failures
        report["valid"] = failures == 0
        table = ",\n".join("  {" + ", ".join(f"{value:.6f}f" for value in ref) + "}" for ref in references)
        report["cpp_reference_table"] = "{\n" + table + "\n}"
        print("\nCandidate COLOR_REFERENCE (RED, BLUE, GREEN, BLACK):\n" + report["cpp_reference_table"])
        if not report["valid"]:
            print("NOT VALIDATED: colors overlap or samples vary too much under current thresholds. Check markers/lighting/distance.")
        else:
            print("All captured samples pass. Validate on new samples and background before updating config.h and uploading.")
    except (Exception, KeyboardInterrupt) as error:
        report["error"] = str(error) or "Interrupted"
        print(f"Calibration stopped: {report['error']}")
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Calibration report: {path.resolve()}")
    return report["valid"]
