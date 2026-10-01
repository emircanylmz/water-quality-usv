# Field operation and safety guide

[Türkçe](OPERATIONS_TR.md) | [Main README](../README.en.md)

This document explains software operation; it does not replace electrical, battery, boating, or laboratory safety training.

## Before the first run

- Remove propellers or secure the vessel on a safe test stand.
- Confirm that the operator can reach a physical power disconnect.
- Check the Li-Po battery, fuse, ESC/motor-driver current limit, and cable ratings.
- Verify the Arduino model and motor interface. The report describes ESC/Servo control; the repository sketch uses direction/enable pins.
- On an Arduino Mega, verify the physical conflict between DS18B20 on `D1` and `Serial` TX0.
- Never connect 5 V SBUS directly to Raspberry Pi UART; verify the inverter and level shifter described by the report.
- In a dry test, verify `w`, `a`, `s`, `d`, key release, and power/telemetry loss behavior.

## Serial links

| Link | Default port | Baud | Content |
| --- | --- | --- | --- |
| X8R - Raspberry Pi | `/dev/ttyAMA0` | 100000 | SBUS |
| Ground telemetry - Raspberry Pi | `/dev/ttyUSB0` | 57600 | Computer commands and returned sensor data |
| Arduino - Raspberry Pi | `/dev/ttyUSB1` | 9600 | Motor commands and sensor lines |
| Ground-computer telemetry | `/dev/tty.usbserial-0001` | 57600 | Control and logging |

The default X8R framing remains `8N1` to preserve the proven script. If your standard SBUS adapter requires `8E2`:

```bash
export USV_X8R_PARITY=E
export USV_X8R_STOPBITS=2
```

On Linux, prefer stable `/dev/serial/by-id/...` paths over changing `/dev/ttyUSB*` numbers.

## Recommended startup order

1. With Arduino and motor power off, identify the ground telemetry port.
2. Load configuration on the Raspberry Pi.
3. Run `python -m raspberry.dual_control`.
4. Confirm that all three serial links open with the expected device names.
5. Run `python -m pc.xlsx_logger` on the ground computer.
6. Power Arduino and verify the first telemetry line and Excel row count.
7. With the vessel restrained, test the computer-mode stop behavior.
8. Enter RC mode and verify that motors stop during the transition.
9. Turn off the RC receiver and confirm stop within the SBUS timeout plus Arduino watchdog interval.
10. Only then perform a low-power water test.

## Emergency response

Priority order:

1. Release the keyboard key or send `x` in computer control.
2. Move the RC transmitter to its safe/stop state.
3. Disconnect physical motor power.
4. Stop software with `Ctrl+C`.

Software stop must not be the only safety layer.

## Data logging and quality checks

The logger accepts both formats:

```text
DATA,38.743804,35.468315,7.29,32,CLOUDY,19.87
LAT=38.743804,LON=35.468315,PH=7.29,TURB=32,STATUS=CLOUDY,TEMP=19.87
```

Before each field session:

- Record calibration against known pH buffers.
- State whether turbidity is raw ADC or NTU.
- Confirm GPS fix.
- Confirm date, time, and time zone.
- Take repeated stationary measurements.

After each field session:

- Copy the XLSX file to a read-only backup.
- Inspect negative pH, DS18B20 error values (`-127`, and sometimes `85`), and GPS jumps.
- Record packet counts, malformed packets, and run duration in a field log.
- Generate KML in a separate output directory.

```bash
python -m pc.xlsx_to_kml --input all_sensors.xlsx --output-dir maps/session-001
```

## Hardware-independent verification

```bash
python -m pytest
ruff check .
```

Automated tests cover telemetry parsing, control decisions, SBUS flags, Excel continuity, and KML XML/geometry. Real serial timing, radio range, motor stop latency, and on-water behavior still require field validation.
