"""Convert the combined measurement workbook into three KML overlays."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from usv_monitoring.kml import generate_kml_maps


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="USV XLSX to KML converter")
    parser.add_argument("--input", type=Path, default=Path("all_sensors.xlsx"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument(
        "--half-size-m",
        type=float,
        default=4.0,
        help="Half of each square side length in metres (default: 4)",
    )
    args = parser.parse_args(argv)

    outputs = generate_kml_maps(
        args.input, args.output_dir, half_size_m=args.half_size_m
    )
    print("KML üretildi:", ", ".join(str(path) for path in outputs))


if __name__ == "__main__":
    main()
