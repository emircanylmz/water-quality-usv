"""Minimal keyboard-only ground control client."""

from __future__ import annotations

import argparse
from typing import Optional, Sequence

from usv_monitoring.config import GroundStationConfig
from usv_monitoring.keyboard_control import KeyboardCommandController


def main(argv: Optional[Sequence[str]] = None) -> None:
    import serial

    defaults = GroundStationConfig.from_env()
    parser = argparse.ArgumentParser(description="USV keyboard telemetry controller")
    parser.add_argument("--port", default=defaults.port)
    parser.add_argument("--baud", type=int, default=defaults.baud)
    args = parser.parse_args(argv)

    serial_port = serial.Serial(args.port, args.baud)
    try:
        KeyboardCommandController(serial_port, verbose=False).run()
    finally:
        try:
            serial_port.write(b"x")
        finally:
            serial_port.close()


if __name__ == "__main__":
    main()
