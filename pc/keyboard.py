"""PC-side keyboard control with an Arduino diagnostic monitor."""

from __future__ import annotations

import argparse
import threading
import time
from typing import Optional, Sequence

from usv_monitoring.config import GroundStationConfig
from usv_monitoring.keyboard_control import KeyboardCommandController
from usv_monitoring.protocol import parse_tagged_sensor_line


def monitor_serial(serial_port: object, stop_event: threading.Event) -> None:
    buffer = ""
    while not stop_event.is_set():
        try:
            waiting = getattr(serial_port, "in_waiting", 0)
            if waiting:
                data = serial_port.read(waiting).decode(errors="ignore")
                buffer += data.replace("\r", "")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    fields = parse_tagged_sensor_line(line)
                    if fields:
                        print("Sensör:", fields)
            time.sleep(0.01)
        except Exception as exc:
            if not stop_event.is_set():
                print(f"Seri okuma hatası: {exc}")
            time.sleep(0.1)


def main(argv: Optional[Sequence[str]] = None) -> None:
    import serial

    defaults = GroundStationConfig.from_env()
    parser = argparse.ArgumentParser(description="USV keyboard and sensor monitor")
    parser.add_argument("--port", default=defaults.port)
    parser.add_argument("--baud", type=int, default=defaults.baud)
    args = parser.parse_args(argv)

    serial_port = serial.Serial(
        args.port, args.baud, timeout=defaults.timeout_seconds
    )
    stop_event = threading.Event()
    reader = threading.Thread(
        target=monitor_serial, args=(serial_port, stop_event), daemon=True
    )
    reader.start()
    try:
        KeyboardCommandController(serial_port).run()
    finally:
        stop_event.set()
        try:
            serial_port.write(b"x")
        finally:
            serial_port.close()


if __name__ == "__main__":
    main()
