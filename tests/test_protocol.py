import pytest

from usv_monitoring.protocol import (
    TelemetryParseError,
    looks_like_arduino_telemetry,
    parse_measurement_line,
)


def test_parses_legacy_data_packet():
    record = parse_measurement_line(
        "DATA,38.7009,35.5295,7.45,19,CLOUDY,9.3"
    )
    assert record is not None
    assert record.lat == pytest.approx(38.7009)
    assert record.ph == pytest.approx(7.45)
    assert record.turbidity == 19
    assert record.status == "CLOUDY"


def test_parses_field_report_key_value_packet():
    record = parse_measurement_line(
        "LAT=38.743804,LON=35.468315,PH=7.29,TURB=32,"
        "STATUS=CLOUDY,TEMP=19.87"
    )
    assert record is not None
    assert record.lon == pytest.approx(35.468315)
    assert record.temp == pytest.approx(19.87)


def test_ignores_gps_status_and_diagnostic_lines():
    assert parse_measurement_line("GPS_NO_FIX") is None
    assert parse_measurement_line("PH:7.2,CAL:7.1,TURB:Temiz,TEMP:20") is None


def test_gps_no_fix_identifies_arduino_during_port_detection():
    assert looks_like_arduino_telemetry(b"GPS_NO_FIX\r\n")


def test_rejects_incomplete_measurement_candidate():
    with pytest.raises(TelemetryParseError, match="missing"):
        parse_measurement_line("LAT=38.7,LON=35.5,PH=7.2")


def test_flags_out_of_range_values_without_dropping_field_data():
    record = parse_measurement_line(
        "DATA,38.7009,35.5295,-1.74,32,CLOUDY,20.4"
    )
    assert record is not None
    assert "pH is outside 0..14" in record.warnings()
