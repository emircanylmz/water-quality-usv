"""Environment-backed configuration with field-compatible defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DualControlConfig:
    """Raspberry Pi serial/control configuration.

    Defaults match the original field scripts. Every value can be overridden
    without editing source code.
    """

    x8r_port: str = "/dev/ttyAMA0"
    telemetry_port: str = "/dev/ttyUSB0"
    arduino_port: str = "/dev/ttyUSB1"
    x8r_baud: int = 100000
    telemetry_baud: int = 57600
    arduino_baud: int = 9600
    x8r_parity: str = "N"
    x8r_stopbits: float = 1.0
    rc_threshold: int = 1700
    computer_threshold: int = 1300
    dead_zone: int = 50
    sbus_timeout_seconds: float = 0.5
    auto_detect_usb: bool = True

    @classmethod
    def from_env(cls) -> "DualControlConfig":
        return cls(
            x8r_port=os.getenv("USV_X8R_PORT", cls.x8r_port),
            telemetry_port=os.getenv("USV_TELEMETRY_PORT", cls.telemetry_port),
            arduino_port=os.getenv("USV_ARDUINO_PORT", cls.arduino_port),
            x8r_baud=int(os.getenv("USV_X8R_BAUD", str(cls.x8r_baud))),
            telemetry_baud=int(
                os.getenv("USV_TELEMETRY_BAUD", str(cls.telemetry_baud))
            ),
            arduino_baud=int(os.getenv("USV_ARDUINO_BAUD", str(cls.arduino_baud))),
            x8r_parity=os.getenv("USV_X8R_PARITY", cls.x8r_parity).upper(),
            x8r_stopbits=float(
                os.getenv("USV_X8R_STOPBITS", str(cls.x8r_stopbits))
            ),
            rc_threshold=int(
                os.getenv("USV_RC_THRESHOLD", str(cls.rc_threshold))
            ),
            computer_threshold=int(
                os.getenv("USV_COMPUTER_THRESHOLD", str(cls.computer_threshold))
            ),
            dead_zone=int(os.getenv("USV_DEAD_ZONE", str(cls.dead_zone))),
            sbus_timeout_seconds=float(
                os.getenv("USV_SBUS_TIMEOUT", str(cls.sbus_timeout_seconds))
            ),
            auto_detect_usb=_env_bool("USV_AUTO_DETECT_USB", cls.auto_detect_usb),
        )


@dataclass(frozen=True)
class GroundStationConfig:
    """PC-side telemetry, logging, and output configuration."""

    port: str = "/dev/tty.usbserial-0001"
    baud: int = 57600
    timeout_seconds: float = 0.1
    workbook: Path = Path("all_sensors.xlsx")
    flush_every: int = 1
    keyboard_enabled: bool = True

    @classmethod
    def from_env(cls) -> "GroundStationConfig":
        return cls(
            port=os.getenv("USV_GROUND_PORT", cls.port),
            baud=int(os.getenv("USV_GROUND_BAUD", str(cls.baud))),
            timeout_seconds=float(
                os.getenv("USV_GROUND_TIMEOUT", str(cls.timeout_seconds))
            ),
            workbook=Path(os.getenv("USV_DATA_FILE", str(cls.workbook))),
            flush_every=max(1, int(os.getenv("USV_FLUSH_EVERY", str(cls.flush_every)))),
            keyboard_enabled=_env_bool(
                "USV_KEYBOARD_ENABLED", cls.keyboard_enabled
            ),
        )
