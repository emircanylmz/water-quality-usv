"""Telemetry parsing for both the deployed report format and legacy logger format."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


class TelemetryParseError(ValueError):
    """Raised when a line looks like telemetry but contains invalid values."""


@dataclass(frozen=True)
class SensorRecord:
    time: str
    lat: float
    lon: float
    ph: Optional[float]
    turbidity: Optional[int]
    status: str
    temp: Optional[float]

    @classmethod
    def now(
        cls,
        lat: float,
        lon: float,
        ph: Optional[float],
        turbidity: Optional[int],
        status: str,
        temp: Optional[float],
    ) -> "SensorRecord":
        return cls(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            lat=lat,
            lon=lon,
            ph=ph,
            turbidity=turbidity,
            status=status,
            temp=temp,
        )

    def as_dict(self) -> Dict[str, object]:
        return {
            "time": self.time,
            "lat": self.lat,
            "lon": self.lon,
            "ph": self.ph,
            "turbidity": self.turbidity,
            "status": self.status,
            "temp": self.temp,
        }

    def warnings(self) -> List[str]:
        warnings = []
        if not -90 <= self.lat <= 90:
            warnings.append("latitude is outside -90..90")
        if not -180 <= self.lon <= 180:
            warnings.append("longitude is outside -180..180")
        if self.ph is not None and not 0 <= self.ph <= 14:
            warnings.append("pH is outside 0..14")
        if self.turbidity is not None and self.turbidity < 0:
            warnings.append("turbidity is negative")
        if self.temp is not None and not -55 <= self.temp <= 125:
            warnings.append("temperature is outside the DS18B20 range")
        return warnings


def _optional_float(value: str) -> Optional[float]:
    value = value.strip()
    return None if value in {"", "?"} else float(value)


def _optional_int(value: str) -> Optional[int]:
    value = value.strip()
    return None if value in {"", "?"} else int(float(value))


def _record_from_data_csv(line: str) -> SensorRecord:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 7:
        raise TelemetryParseError("DATA packet must contain 7 comma-separated fields")
    if parts[1] == "?" or parts[2] == "?":
        raise TelemetryParseError("DATA packet has no GPS fix")
    try:
        return SensorRecord.now(
            lat=float(parts[1]),
            lon=float(parts[2]),
            ph=_optional_float(parts[3]),
            turbidity=_optional_int(parts[4]),
            status=parts[5],
            temp=_optional_float(parts[6]),
        )
    except ValueError as exc:
        raise TelemetryParseError("DATA packet contains a non-numeric value") from exc


def _parse_key_value_fields(line: str) -> Dict[str, str]:
    fields = {}
    for token in re.split(r"[,|]", line):
        match = re.match(r"\s*([A-Za-z_]+)\s*[=:]\s*(.*?)\s*$", token)
        if match:
            fields[match.group(1).upper()] = match.group(2)
    return fields


def parse_measurement_line(line: str) -> Optional[SensorRecord]:
    """Parse one complete geo-referenced measurement.

    Supported formats:
    - ``DATA,lat,lon,ph,turbidity,status,temp`` (legacy logger)
    - ``LAT=...,LON=...,PH=...,TURB=...,STATUS=...,TEMP=...`` (field report)

    Non-measurement status lines return ``None``. Lines that look like a
    measurement but are malformed raise ``TelemetryParseError``.
    """

    stripped = line.strip()
    if not stripped or stripped.upper() in {"GPS_NO_FIX", "GPS NO FIX"}:
        return None

    if stripped.upper().startswith("DATA,"):
        return _record_from_data_csv(stripped)

    fields = _parse_key_value_fields(stripped)
    if not fields or not ({"LAT", "LON"} & fields.keys()):
        return None

    required = {"LAT", "LON", "PH", "TURB", "STATUS", "TEMP"}
    missing = sorted(required - fields.keys())
    if missing:
        raise TelemetryParseError(f"Key/value packet is missing: {', '.join(missing)}")
    if fields["LAT"] == "?" or fields["LON"] == "?":
        raise TelemetryParseError("Key/value packet has no GPS fix")

    try:
        return SensorRecord.now(
            lat=float(fields["LAT"]),
            lon=float(fields["LON"]),
            ph=_optional_float(fields["PH"]),
            turbidity=_optional_int(fields["TURB"]),
            status=fields["STATUS"],
            temp=_optional_float(fields["TEMP"]),
        )
    except ValueError as exc:
        raise TelemetryParseError("Key/value packet contains a non-numeric value") from exc


def parse_tagged_sensor_line(line: str) -> Dict[str, str]:
    """Parse non-GPS Arduino diagnostic lines without treating them as log rows."""

    return _parse_key_value_fields(line)


def looks_like_arduino_telemetry(payload: bytes) -> bool:
    text = payload.decode("utf-8", errors="ignore").upper()
    return any(
        marker in text
        for marker in ("GPS_NO_FIX", "PH:", "PH=", "DATA,", "TEMP:", "TEMP=")
    )
