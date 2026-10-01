import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from usv_monitoring.kml import half_spans_degrees, ph_color, write_kml


def test_square_spans_compensate_for_longitude_scale():
    latitude_span, longitude_span = half_spans_degrees(38.7, 4.0)
    north_south = latitude_span * 111_320
    east_west = longitude_span * 111_320 * math.cos(math.radians(38.7))
    assert north_south == pytest.approx(4.0)
    assert east_west == pytest.approx(4.0)


def test_writes_valid_kml_with_closed_polygon(tmp_path: Path):
    output = tmp_path / "ph.kml"
    write_kml(
        output,
        "pH Haritası",
        [
            {
                "time": "2026-01-01 00:00:00",
                "lat": 38.7,
                "lon": 35.5,
                "ph": 7.2,
                "status": "CLEAR",
            }
        ],
        "ph",
        ph_color,
    )

    root = ET.parse(output).getroot()
    namespace = {"k": "http://www.opengis.net/kml/2.2"}
    coordinate_text = root.findtext(".//k:coordinates", namespaces=namespace)
    coordinates = coordinate_text.strip().splitlines()
    assert len(coordinates) == 5
    assert coordinates[0] == coordinates[-1]
