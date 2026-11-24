import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from arduino_client import ArduinoError

from test_loadcell import (calibrate, calculate_calibration, collect_samples,
                           validate_weight, write_project_calibration)


class LoadCellCalibrationTests(unittest.TestCase):
    def test_old_firmware_fails_before_prompt_or_write(self):
        client = Mock()
        client.get_status.return_value = {"state": "INIT"}
        client.get_weight.side_effect = ArduinoError("GET_WEIGHT id=20: INVALID_COMMAND")
        with patch("builtins.input") as prompt:
            with self.assertRaisesRegex(ArduinoError, "Upload this project's HX711 firmware"):
                calibrate(client, 170)
            prompt.assert_not_called()
        client.set_scale.assert_not_called()

    def test_positive_and_negative_factor_in_counts_per_kg(self):
        positive = calculate_calibration([100000] * 20, [200000] * 20, 200)
        self.assertEqual(positive["offset"], 100000)
        self.assertEqual(positive["factor"], 500000)
        negative = calculate_calibration([100000] * 20, [0] * 20, 200)
        self.assertEqual(negative["factor"], -500000)
        validate_weight(negative, [0] * 10)

    def test_invalid_signal_or_mass_is_rejected(self):
        for mass in (0, -200, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                calculate_calibration([1000] * 20, [2000] * 20, mass)
        with self.assertRaisesRegex(ValueError, "Span below"):
            calculate_calibration([1000] * 20, [1020] * 20, 200)
        with self.assertRaisesRegex(ValueError, "saturated"):
            calculate_calibration([1000] * 20, [8388607] * 20, 200)

    def test_vibration_and_bad_independent_check_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unstable"):
            calculate_calibration([1000, 2000] * 10, [4000, 5000] * 10, 200)
        result = calculate_calibration([1000] * 20, [101000] * 20, 200)
        with self.assertRaisesRegex(ValueError, "Independent verification"):
            validate_weight(result, [121000] * 10)

    def test_generated_files_leave_other_configuration_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = root / "firmware/include/config.h"
            config.parent.mkdir(parents=True)
            config.write_text("HOME_SPEED=600;", encoding="utf-8")
            result = calculate_calibration([1000] * 20, [101000] * 20, 200)
            paths = write_project_calibration(result, root)
            self.assertEqual(config.read_text(), "HOME_SPEED=600;")
            self.assertIn("FACTOR=500000.0f", paths[0].read_text())
            self.assertIn("OFFSET=1000", paths[0].read_text())
            self.assertTrue(json.loads(paths[1].read_text())["calibrated"])

    def test_collects_only_fresh_healthy_samples(self):
        client = Mock()
        client.get_weight.side_effect = [
            {"healthy": True, "raw": number * 10, "sample_seq": number}
            for number in (1, 1, 2, 3, 4, 5)]
        with patch("test_loadcell.time.sleep"), patch("builtins.print"):
            self.assertEqual(collect_samples(client, 5), [10, 20, 30, 40, 50])

    def test_complete_calibration_saves_device_then_project_without_motion(self):
        client = Mock()
        client.get_status.return_value = {"state": "INIT"}
        client.get_weight.return_value = {"calibrated": True, "factor": 500000.0, "offset": 1000}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("builtins.input", side_effect=["y", "y"]), patch("builtins.print"), patch("test_loadcell.time.sleep"), patch(
                    "test_loadcell.collect_samples", side_effect=[[1000] * 20, [101000] * 20, [101000] * 10]):
                result = calibrate(client, 200, 20, root)
            client.set_scale.assert_called_once_with(500000.0, 1000)
            self.assertTrue(result["device_eeprom_saved"])
            self.assertTrue((root / "firmware/include/loadcell_calibration.h").exists())
            self.assertEqual([call[0] for call in client.mock_calls], ["get_status", "get_weight", "get_weight", "set_scale", "get_weight"])

    def test_failed_verification_never_writes_device_or_files(self):
        client = Mock()
        client.get_status.return_value = {"state": "INIT"}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("builtins.input", side_effect=["y", "y"]), patch("builtins.print"), patch("test_loadcell.time.sleep"), patch(
                    "test_loadcell.collect_samples", side_effect=[[1000] * 20, [101000] * 20, [151000] * 10]):
                with self.assertRaises(ValueError):
                    calibrate(client, 200, 20, root)
            client.set_scale.assert_not_called()
            self.assertFalse((root / "firmware/include/loadcell_calibration.h").exists())


if __name__ == "__main__":
    unittest.main()
