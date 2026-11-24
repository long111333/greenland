"""Run deterministic firmware tests with g++ (no Arduino connected)."""
from pathlib import Path
import subprocess
import sys

firmware = Path(__file__).resolve().parents[1]
host = firmware / "test" / "host"
includes = ["-I", str(host), "-I", str(firmware / "include"), "-I", str(firmware / "src")]
groups = {
    "test_safety": ["controllers/ServoController.cpp", "controllers/StepperController.cpp",
                    "controllers/SortingController.cpp", "safety/SafetyManager.cpp", "sensors/LoadCellSensor.cpp"],
    "test_io": ["communication/SerialProtocol.cpp", "sensors/ColorSensor.cpp", "sensors/UltrasonicSensor.cpp", "safety/MemoryMonitor.cpp", "sensors/LoadCellSensor.cpp"],
    "test_loadcell": ["sensors/LoadCellSensor.cpp"],
}
json_include = firmware / ".pio" / "libdeps" / "uno" / "ArduinoJson" / "src"
accel_include = firmware / ".pio" / "libdeps" / "uno" / "AccelStepper" / "src"
groups["test_actual_stepper"] = ["controllers/StepperController.cpp", str(accel_include / "AccelStepper.cpp")]
for name, sources in groups.items():
    output = host / (name + ".exe")
    actual_flags = ["-DARDUINO=10819", "-I", str(accel_include)] if name == "test_actual_stepper" else []
    command = ["g++", "-std=c++17", "-Wall", "-Wextra", *actual_flags, *includes,
               "-I", str(json_include), str(host / (name + ".cpp")),
               *(str(firmware / "src" / source) for source in sources), "-o", str(output)]
    if sys.platform == "win32":
        command.append("-static")
    subprocess.run(command, check=True)
    subprocess.run([str(output)], check=True)
