"""Prepare this project's USB adapter before avrdude opens its bootloader session."""
import time
import serial

Import("env")


def prepare_upload(source, target, env):
    if env.subst("$UPLOAD_PROTOCOL") != "arduino":
        return
    if not env.subst("$UPLOAD_PORT"):
        env.AutodetectUploadPort()
    port_name = env.subst("$UPLOAD_PORT")
    baudrate = int(env.GetProjectOption("monitor_speed", 115200))
    print(f"Draining stale serial data and resetting {port_name} before upload")
    # This sends no application commands. Busy ports fail clearly; no process is killed.
    with serial.Serial(port_name, baudrate, timeout=0.03, write_timeout=0.5) as port:
        deadline = time.monotonic() + 0.3
        while time.monotonic() < deadline:
            port.read(256)
        port.reset_input_buffer()
        port.dtr = False
        time.sleep(0.05)
        port.dtr = True


env.AddPreAction("upload", prepare_upload)
