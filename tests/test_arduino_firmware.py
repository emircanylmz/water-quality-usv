from pathlib import Path

SKETCH = (
    Path(__file__).resolve().parents[1]
    / "arduino"
    / "water_quality_usv"
    / "water_quality_usv.ino"
)


def test_gps_uses_mega_hardware_serial_and_tinygpsplus():
    source = SKETCH.read_text(encoding="utf-8")

    assert "#include <TinyGPS++.h>" in source
    assert "Serial1.begin(GPS_BAUD)" in source
    assert "gps.encode(Serial1.read())" in source
    assert "gps.location.isValid()" in source
    assert "gps.location.age()" in source


def test_firmware_emits_complete_geo_referenced_packet():
    source = SKETCH.read_text(encoding="utf-8")

    for field in ("LAT=", ",LON=", ",PH=", ",TURB=", ",STATUS=", ",TEMP="):
        assert f'Serial.print("{field}")' in source
    assert 'Serial.println("GPS_NO_FIX")' in source
