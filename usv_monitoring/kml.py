"""KML generation for geo-referenced sensor measurements."""

from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple

import pandas as pd

KML_NS = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NS)


def ph_color(value: float) -> str:
    if value < 6.5:
        return "ff0000ff"
    if value <= 8:
        return "ff00ff00"
    return "ffff0000"


def turbidity_color(value: float) -> str:
    if value <= 20:
        return "ff00ff00"
    if value <= 50:
        return "ff00ffff"
    return "ff0000ff"


def temperature_color(value: float) -> str:
    if value < 15:
        return "ffff0000"
    if value <= 25:
        return "ff00ff00"
    return "ff0000ff"


def half_spans_degrees(latitude: float, half_size_m: float) -> Tuple[float, float]:
    """Return latitude/longitude spans for an approximately square polygon."""

    latitude_span = half_size_m / 111_320.0
    longitude_scale = math.cos(math.radians(latitude))
    if abs(longitude_scale) < 1e-9:
        raise ValueError("Cannot construct a longitude span at the poles")
    longitude_span = half_size_m / (111_320.0 * longitude_scale)
    return latitude_span, longitude_span


def _sub(parent: ET.Element, name: str, text: str = "") -> ET.Element:
    element = ET.SubElement(parent, f"{{{KML_NS}}}{name}")
    element.text = text
    return element


def write_kml(
    filename: Path,
    name: str,
    rows: Iterable[Dict[str, object]],
    value_column: str,
    color_function: Callable[[float], str],
    half_size_m: float = 4.0,
) -> None:
    root = ET.Element(f"{{{KML_NS}}}kml")
    document = _sub(root, "Document")
    _sub(document, "name", name)

    for row in rows:
        latitude = float(row["lat"])
        longitude = float(row["lon"])
        value = float(row[value_column])
        latitude_span, longitude_span = half_spans_degrees(
            latitude, half_size_m
        )

        placemark = _sub(document, "Placemark")
        _sub(placemark, "name", f"{value_column}: {value:g}")
        description = (
            f"time={row.get('time', '')}, status={row.get('status', '')}, "
            f"lat={latitude:.7f}, lon={longitude:.7f}"
        )
        _sub(placemark, "description", description)
        style = _sub(placemark, "Style")
        poly_style = _sub(style, "PolyStyle")
        _sub(poly_style, "color", color_function(value))
        polygon = _sub(placemark, "Polygon")
        outer = _sub(polygon, "outerBoundaryIs")
        ring = _sub(outer, "LinearRing")
        coordinates = [
            (longitude - longitude_span, latitude - latitude_span),
            (longitude + longitude_span, latitude - latitude_span),
            (longitude + longitude_span, latitude + latitude_span),
            (longitude - longitude_span, latitude + latitude_span),
            (longitude - longitude_span, latitude - latitude_span),
        ]
        _sub(
            ring,
            "coordinates",
            "\n" + "\n".join(f"{lon},{lat},0" for lon, lat in coordinates) + "\n",
        )

    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = filename.with_name(f".{filename.name}.tmp")
    ET.ElementTree(root).write(
        temporary_path, encoding="utf-8", xml_declaration=True
    )
    os.replace(temporary_path, filename)


def generate_kml_maps(
    workbook: Path, output_directory: Path, half_size_m: float = 4.0
) -> Tuple[Path, Path, Path]:
    frame = pd.read_excel(workbook)
    if "temperature" in frame.columns and "temp" not in frame.columns:
        frame = frame.rename(columns={"temperature": "temp"})

    required = {"lat", "lon", "ph", "turbidity", "temp"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Workbook is missing columns: {', '.join(missing)}")

    frame = frame.dropna(subset=["lat", "lon"])
    output_directory = Path(output_directory)
    specifications = (
        ("ph.kml", "pH Haritası", "ph", ph_color),
        ("turbidity.kml", "Bulanıklık Haritası", "turbidity", turbidity_color),
        ("temperature.kml", "Sıcaklık Haritası", "temp", temperature_color),
    )

    outputs = []
    for filename, title, column, color_function in specifications:
        output = output_directory / filename
        rows = frame.dropna(subset=[column]).to_dict(orient="records")
        write_kml(
            output,
            title,
            rows,
            column,
            color_function,
            half_size_m=half_size_m,
        )
        outputs.append(output)

    return tuple(outputs)
