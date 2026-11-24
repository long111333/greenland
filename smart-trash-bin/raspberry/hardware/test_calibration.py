import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from calibrate_color import run_calibration


class ColorSource:
    references = [(506, 235, 259), (179, 305, 516), (193, 466, 341), (230, 384, 386)]

    def __init__(self, overlap=False, clear=1000):
        self.position = 0
        self.overlap = overlap
        self.clear = clear
        self.requests = []

    def get_status(self):
        self.requests.append("GET_STATUS")
        return {"state": "INIT", "homed": False}

    def get_color(self):
        self.requests.append("GET_COLOR")
        r, g, b = self.references[0 if self.overlap else self.position]
        return {"r": r, "g": g, "b": b, "clear": self.clear, "healthy": True}

    def confirm(self, prompt):
        for index, color in enumerate(("RED", "BLUE", "GREEN", "BLACK")):
            if f"Place {color} " in prompt:
                self.position = index
        return "y"


class CalibrationTests(unittest.TestCase):
    def exercise(self, source):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "calibration.json"
            with patch("builtins.input", side_effect=source.confirm), patch("calibrate_color.time.sleep"), patch("builtins.print"):
                result = run_calibration(source, path, samples=5)
            report = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(all(command in ("GET_STATUS", "GET_COLOR") for command in source.requests))
        return result, report

    def test_four_distinct_colors_create_candidate_without_motion(self):
        passed, report = self.exercise(ColorSource())
        self.assertTrue(passed)
        self.assertEqual(len(report["colors"]), 4)
        self.assertEqual(report["failed_training_samples"], 0)

    def test_identical_markers_are_rejected(self):
        passed, report = self.exercise(ColorSource(overlap=True))
        self.assertFalse(passed)
        self.assertGreater(report["failed_training_samples"], 0)

    def test_dim_marker_stops_capture(self):
        passed, report = self.exercise(ColorSource(clear=99))
        self.assertFalse(passed)
        self.assertIn("Clear below 100", report["error"])


if __name__ == "__main__":
    unittest.main()
