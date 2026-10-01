"""PC-side ground-station logger and keyboard controller.

The historical filename is kept for compatibility. The module is now safe to
import; serial I/O starts only from ``main``.
"""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path
from typing import Optional, Sequence

from usv_monitoring.config import GroundStationConfig
from usv_monitoring.keyboard_control import KeyboardCommandController
from usv_monitoring.protocol import TelemetryParseError, parse_measurement_line
from usv_monitoring.storage import ExcelMeasurementStore


def run_logger(config: GroundStationConfig) -> None:
    import serial

    print("Porta bağlanılıyor:", config.port)
    serial_port = serial.Serial(
        config.port, config.baud, timeout=config.timeout_seconds
    )
    store = ExcelMeasurementStore(config.workbook, flush_every=config.flush_every)
    time.sleep(2.0)
    print("PORT AÇILDI")

    if config.keyboard_enabled:
        keyboard_controller = KeyboardCommandController(serial_port)
        threading.Thread(target=keyboard_controller.run, daemon=True).start()

    buffer = ""
    print("\nPC LOGGER + KLAVYE KONTROL AKTİF (CTRL+C ile çık)\n")

    try:
        while True:
            if serial_port.in_waiting > 0:
                data = serial_port.read(serial_port.in_waiting).decode(errors="ignore")
                buffer += data.replace("\r", "")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    print(line)

                    try:
                        record = parse_measurement_line(line)
                    except TelemetryParseError as exc:
                        print(f"Format hatası, atlandı: {exc}")
                        continue
                    if record is None:
                        continue

                    warnings = record.warnings()
                    if warnings:
                        print("Veri uyarısı:", "; ".join(warnings))
                    store.append(record)
                    print(f"KAYDEDİLDİ (Toplam: {store.count})")

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nProgram durduruldu")
    finally:
        store.close()
        try:
            serial_port.write(b"x")
        finally:
            serial_port.close()


def build_parser(defaults: GroundStationConfig) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="USV telemetri ve Excel logger")
    parser.add_argument("--port", default=defaults.port)
    parser.add_argument("--baud", type=int, default=defaults.baud)
    parser.add_argument("--output", type=Path, default=defaults.workbook)
    parser.add_argument("--flush-every", type=int, default=defaults.flush_every)
    parser.add_argument("--no-keyboard", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    defaults = GroundStationConfig.from_env()
    args = build_parser(defaults).parse_args(argv)
    config = GroundStationConfig(
        port=args.port,
        baud=args.baud,
        timeout_seconds=defaults.timeout_seconds,
        workbook=args.output,
        flush_every=max(1, args.flush_every),
        keyboard_enabled=defaults.keyboard_enabled and not args.no_keyboard,
    )
    run_logger(config)


if __name__ == "__main__":
    main()
