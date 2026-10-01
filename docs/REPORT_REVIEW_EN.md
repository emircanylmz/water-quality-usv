# Graduation-report review

[Türkçe](REPORT_REVIEW_TR.md) | [Main README](../README.en.md)

Reviewed report: **Unmanned Surface Vehicle for Water-Quality Analysis**, 40 PDF pages, January 2026. The PDF is not copied into the repository because its final page contains personal contact and address information.

## Strengths

- The environmental-monitoring purpose, three-layer architecture, and low-cost objective are clear.
- Arduino, Raspberry Pi, and ground-computer responsibilities are conceptually separated.
- Associating pH, turbidity, temperature, and GPS in one observation is the correct system goal.
- Combining RC and computer control addresses a practical field need.
- The report includes separate hardware, microcontroller, Raspberry Pi, and ground-station diagrams.
- It explicitly acknowledges that the collected dataset was too small for the planned machine-learning work.

## Critical report-to-repository differences

| Topic | Report | Repository source | Required action |
| --- | --- | --- | --- |
| GPS | NEO-6M and `TinyGPSPlus`; Arduino reads GPS | No GPS code in `arduino/water_quality_usv/water_quality_usv.ino` | Archive the deployed firmware or revise the report to match the available sketch. |
| Serial packet | `LAT=...,LON=...,PH=...,TURB=...,STATUS=...,TEMP=...` | Arduino emits `PH:...,CAL:...,TURB:...,TEMP:...`; old logger expected `DATA,...` | Logger now accepts both geo-referenced formats; the GPS-free sketch cannot create a complete record. |
| Motor electronics | SimonK 30A ESC and `Servo.writeMicroseconds()` | `ENA/ENB`, `IN1..IN4`, `digitalWrite/analogWrite` | Identify the physical variant; do not flash incompatible motor firmware. |
| Temperature pin | Not made explicit in the report | OneWire on `D1` | Verify the Mega TX0 conflict against physical wiring. |
| Storage layout | Claims separate pH, turbidity, and temperature files | Uses one `all_sensors.xlsx` | Revise the report to document the combined schema. |
| KML library | Claims `simplekml` | Generates XML manually | Report and source must describe one implementation; the new module uses the standard XML API. |
| Map geometry | Describes each observation as a point/placemark | Produces colored polygons/squares | Document polygon dimensions and color thresholds. |
| Baud rate | Algorithm lists a single 9600 rate | Arduino link is 9600; radio/ground link is 57600 | Separate the two links in a communication table. |

## Scientific-method and data-quality gaps

1. **Calibration is not reproducible.** Buffer values, temperature, date, slope/offset, and the reference instrument are absent.
2. **Two pH formulas exist.** The repository computes both `7 + ((2.5 - V) / 0.18)` and `-5.70V + 21.34`; the report must identify the formula used for results.
3. **Turbidity has no unit.** Values such as `19`, `32`, and `96` are not identified as raw ADC, percent, or NTU.
4. **CLEAR/CLOUDY/DIRTY is undefined.** Thresholds, units, and scientific basis are missing.
5. **Tests are qualitative only.** There is no reference measurement, sample count, mean error, standard deviation, repeatability, or confidence interval.
6. **Negative pH data are unexplained.** Current sample data include negative pH and require calibration/ADC-supply investigation.
7. **Clock provenance is unclear.** The timestamp source and time zone are not documented.
8. **GPS quality is absent.** Satellite count, HDOP, fix age, accuracy, and fix-loss behavior are not logged.
9. **Communication performance is unmeasured.** Packet loss, latency, range, and reconnection time are absent.
10. **No power budget.** Battery capacity, mean/peak current, and expected runtime are missing.
11. **Water/electrical safety is underspecified.** Waterproofing, feedthroughs, corrosion, fusing, physical emergency stop, and Li-Po controls are not measurable requirements.
12. **The low-cost claim is not quantified.** No bill of materials or total cost is provided.

## Software and safety claims

- The report correctly intends to stop on mode changes, but the old command cache could suppress that stop. The new version forces the transition stop.
- “Unknown commands stop motors” only helps when a new byte arrives. The old Arduino code could continue its last movement after total link loss; a watchdog has been added.
- SBUS failsafe and frame-loss flags were not handled in the report or old code. The new decoder handles both.
- The old logger could overwrite earlier Excel sessions. The new store loads existing data and uses atomic replacement.
- USB detection contained `or True`, causing the first USB device to be accepted as Arduino. Detection now requires recognizable telemetry.

## Writing and visual-layout issues

- The English abstract page still uses the placeholder title “BİTİRME ÖDEVİ BAŞLIĞI İNGİLİZCE.”
- Several Turkish words are collapsed together by typesetting.
- The abbreviations list inserts spaces inside `GPS`, `IMU`, `PC`, `PWM`, `SBUS`, and `UART`.
- Algorithm 2.1 and its caption are visually crowded/overlapping.
- The hardware “block diagram” is a detailed wiring image with labels too small for print. Use a separate block diagram and pin table.
- Code listings have expanded character spacing and reduced readability.
- The serial screenshot is important protocol evidence and should also be written as a formal packet grammar.
- Verify DOI, page ranges, and complete metadata for every reference.
- Do not publish the résumé page's phone number, email, and address in a public repository.

## Recommended report tables

1. Bill of materials, unit prices, and total cost
2. Pin map and electrical voltage levels
3. Serial links and packet formats
4. Sensor model, unit, range, resolution, and calibration coefficients
5. Reference-measurement error and repeatability
6. Telemetry loss, latency, and range
7. Battery current and runtime
8. Field conditions, date, weather, water condition, and GPS quality
9. Known limitations and safety risks

## Recommended English title

**Unmanned Surface Vehicle for Water-Quality Analysis**

## Conclusion

The report communicates the objective and high-level architecture, but scientific validation, safety behavior, and traceability between source versions and field hardware are insufficient. The most valuable next record is a tagged field release that freezes the exact Arduino, Raspberry Pi, and ground-computer versions used together.
