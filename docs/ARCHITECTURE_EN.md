# Architecture and code boundaries

[Türkçe](ARCHITECTURE_TR.md) | [Main README](../README.en.md)

This refactor keeps the proven field entry points while separating hardware-independent logic into small modules. `DualControl.py`, `xslx_logger.py`, `telemetry.py`, `keyboard.py`, and `xslx_to_kml.py` retain their original command names.

## Extracted classes and functions

| Component | New location | Reason for separation |
| --- | --- | --- |
| `DualControlConfig`, `GroundStationConfig` | `usv_monitoring/config.py` | Moves ports, baud rates, thresholds, and paths out of source while preserving field defaults. |
| `SensorRecord` | `usv_monitoring/protocol.py` | Defines one explicit measurement contract. |
| `parse_measurement_line()` | `usv_monitoring/protocol.py` | Supports both the report's `KEY=VALUE` and legacy `DATA,...` formats. |
| `select_control_mode()` | `usv_monitoring/control.py` | Tests hysteresis without serial hardware. |
| `command_from_channels()` | `usv_monitoring/control.py` | Pure RC-channel-to-motion mapping. |
| `decode_sbus_frame()` and `SBusFrame` | `usv_monitoring/sbus.py` | Separates bit decoding from failsafe/frame-loss decisions. |
| `ExcelMeasurementStore` | `usv_monitoring/storage.py` | Loads old records, appends new ones, and atomically replaces XLSX output. |
| `KeyboardCommandController` | `usv_monitoring/keyboard_control.py` | Reuses the `pynput` lifecycle in logger and control-only clients. |
| `generate_kml_maps()` | `usv_monitoring/kml.py` | Separates colors, geographic geometry, and XML generation from the CLI. |
| `DualControlSystem` | `DualControl.py` | Orchestrates hardware connections, threads, and system lifecycle. |

The boundary is intentionally conservative: the five field scripts were not replaced with a new framework. Only decisions that require testing were extracted.

## 1. Hardware architecture

```mermaid
flowchart LR
    subgraph Vehicle["Unmanned surface vehicle"]
        X8R["FrSky X8R"] --> LEVEL["SBUS inverter<br/>5 V - 3.3 V level shifter"]
        LEVEL -->|"UART / SBUS"| RPI["Raspberry Pi 4"]
        PH["pH sensor"] -->|"A0"| ARD["Arduino Mega 2560"]
        TURB["Turbidity sensor"] -->|"A1"| ARD
        TEMP["DS18B20"] -->|"D1 in repository sketch"| ARD
        GPS["NEO-6M GPS<br/>report field version"] -.-> ARD
        RPI <-->|"USB serial / 9600"| ARD
        ARD --> MOTORIF["Motor interface"]
        MOTORIF --> LEFT["Left motor"]
        MOTORIF --> RIGHT["Right motor"]
        RPI <-->|"USB serial / 57600"| RADIO1["Vehicle telemetry radio"]
        BAT["Li-Po battery"] --> ARD
        BAT --> RPI
        BAT --> MOTORIF
    end
    RADIO1 <-->|"433/915 MHz"| RADIO2["Ground telemetry radio"]
    RADIO2 <--> PC["Ground computer"]
```

Repository pin mapping: pH `A0`, turbidity `A1`, DS18B20 `D1`, motor enables `D9`/`D3`, and motor directions `D7`/`D6`/`D5`/`D4`.

**Critical item to verify:** `D1` is TX0 on an Arduino Mega. The current sketch uses it for both `Serial` and OneWire. If the working field build uses another UART, board, or sensor pin, update source and wiring together. This refactor did not guess a physical pin.

The report describes SimonK ESCs controlled through `Servo`, while the repository sketch uses `ENA/ENB` and `IN1..IN4`. Confirm the installed motor electronics before flashing the sketch.

## 2. Software deployment

```mermaid
flowchart TB
    subgraph ArduinoLayer["Arduino layer"]
        Sketch["sketch_sep15a.ino"] --> SensorRead["Sensor sampling and calibration"]
        Sketch --> MotorDrive["Motor commands and watchdog"]
    end
    subgraph PiLayer["Raspberry Pi layer"]
        Dual["DualControlSystem"] --> SBus["decode_sbus_frame"]
        Dual --> Decision["select_control_mode<br/>command_from_channels"]
    end
    subgraph GroundLayer["Ground-computer layer"]
        Logger["xslx_logger.py"] --> Protocol["parse_measurement_line"]
        Protocol --> Store["ExcelMeasurementStore"] --> Maps["generate_kml_maps"]
    end
    ArduinoLayer <-->|"command and sensor serial link"| PiLayer
    PiLayer <-->|"telemetry radio link"| GroundLayer
```

## 3. Control-mode state machine

```mermaid
stateDiagram-v2
    [*] --> COMPUTER
    COMPUTER --> RC: CH1 > RC threshold
    RC --> COMPUTER: CH1 < computer threshold
    COMPUTER --> COMPUTER: CH1 in hysteresis band
    RC --> RC: CH1 in hysteresis band
    COMPUTER --> COMPUTER: Forward telemetry command
    RC --> RC: Build command when SBUS is fresh
    RC --> RC: Send x on SBUS loss or failsafe
    COMPUTER --> RC: Forced x on transition
    RC --> COMPUTER: Forced x on transition
```

The previous mode is retained within `1300..1700`. Transition stops bypass command deduplication.

## 4. Command and telemetry sequence

```mermaid
sequenceDiagram
    actor Operator
    participant PC as Ground computer
    participant Radio as Telemetry pair
    participant Pi as Raspberry Pi
    participant Arduino
    participant Sensors as Sensors and GPS

    Operator->>PC: Press w/a/s/d
    PC->>Radio: One-byte motion command
    Radio->>Pi: Command
    alt Computer mode
        Pi->>Arduino: Forward command
    else RC mode
        Pi-->>PC: Ignore computer motion command
    end
    Arduino->>Sensors: Request measurements
    Sensors-->>Arduino: pH, turbidity, temperature, and GPS in field firmware
    Arduino->>Pi: Telemetry line
    Pi->>Radio: Forward line
    Radio->>PC: Telemetry line
    PC->>PC: Parse, warn, and atomically update XLSX
```

## 5. Arduino loop and safety

```mermaid
flowchart TD
    START(["Start"]) --> INIT["Initialize pins and sensors<br/>stop motors"]
    INIT --> LOOP{"Main loop"}
    LOOP --> RX{"Serial command available?"}
    RX -->|Yes| DRAIN["Process every buffered command"]
    RX -->|No| WATCH
    DRAIN --> WATCH{"Active motion older than 2 seconds?"}
    WATCH -->|Yes| STOP["Stop motors"]
    WATCH -->|No| DUE
    STOP --> DUE{"One-second sample due?"}
    DUE -->|No| LOOP
    DUE -->|Yes| SAMPLE["Sample pH and turbidity<br/>request DS18B20 temperature"]
    SAMPLE --> SEND["Send machine and diagnostic lines"]
    SEND --> LOOP
```

The watchdog prevents indefinite motion after a serial-link loss. A synchronous DS18B20 request may block the loop for hundreds of milliseconds; measure actual stop latency on the physical build.

## 6. Ground-station logging

```mermaid
flowchart TD
    OPEN["Open serial port and existing XLSX"] --> READ["Read line"]
    READ --> FORMAT{"Supported packet?"}
    FORMAT -->|No| READ
    FORMAT -->|Malformed candidate| WARN1["Report format warning and skip"] --> READ
    FORMAT -->|Yes| VALIDATE["Calculate range warnings"]
    VALIDATE --> APPEND["Combine old and new records"]
    APPEND --> TEMP["Write temporary XLSX"]
    TEMP --> REPLACE["Atomically replace original"]
    REPLACE --> READ
```

Out-of-range scientific data are retained for investigation instead of being silently changed.

## 7. Mapping pipeline

```mermaid
flowchart LR
    XLSX["all_sensors.xlsx"] --> SCHEMA["Normalize temp/temperature schema"]
    SCHEMA --> FILTER["Filter missing GPS or sensor values"]
    FILTER --> PHKML["ph.kml"]
    FILTER --> TURBKML["turbidity.kml"]
    FILTER --> TEMPKML["temperature.kml"]
    PHKML --> EARTH["Google Earth or KML viewer"]
    TURBKML --> EARTH
    TEMPKML --> EARTH
```

Longitude span is adjusted for latitude. The default `--half-size-m 4` creates an approximately eight-metre full square.

## 8. Class and module relationships

```mermaid
classDiagram
    class DualControlSystem {
        +detect_usb_ports()
        +connect_all()
        +parse_sbus_channels(data)
        +determine_control_mode()
        +calculate_rc_command()
        +send_to_arduino_safe(command, force)
        +start_system()
    }
    class DualControlConfig
    class GroundStationConfig
    class SBusFrame {
        +channels
        +frame_lost
        +failsafe
        +signal_ok
    }
    class SensorRecord {
        +warnings()
    }
    class ExcelMeasurementStore {
        +append(record)
        +flush()
        +close()
    }
    class KeyboardCommandController {
        +on_press(key)
        +on_release(key)
        +run()
    }
    DualControlSystem --> DualControlConfig
    DualControlSystem --> SBusFrame
    GroundStationConfig --> ExcelMeasurementStore
    KeyboardCommandController --> DualControlSystem : command path
    ExcelMeasurementStore --> SensorRecord
```

## Safety invariants

1. Every control-mode transition writes a forced `x` to the physical link.
2. SBUS failsafe, frame loss, or timeout changes RC motion to `x`.
3. Arduino stops motors after two seconds without a new motion command.
4. Partially opened serial connections are closed after connection failure.
5. USB auto-detection assigns Arduino only after recognizing readable telemetry.
6. Validation warnings never silently modify raw scientific observations.

These controls do not replace a physical emergency stop, fuse, correct ESC arming process, or operator supervision.
