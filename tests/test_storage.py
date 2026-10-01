from pathlib import Path

import pandas as pd

from usv_monitoring.protocol import SensorRecord
from usv_monitoring.storage import ExcelMeasurementStore


def record(second: int) -> SensorRecord:
    return SensorRecord(
        time=f"2026-01-01 00:00:{second:02d}",
        lat=38.7,
        lon=35.5,
        ph=7.2,
        turbidity=20,
        status="CLEAR",
        temp=19.5,
    )


def test_store_preserves_existing_rows_between_sessions(tmp_path: Path):
    output = tmp_path / "measurements.xlsx"

    first_session = ExcelMeasurementStore(output)
    first_session.append(record(1))
    first_session.close()

    second_session = ExcelMeasurementStore(output)
    second_session.append(record(2))
    second_session.close()

    frame = pd.read_excel(output)
    assert len(frame) == 2
    assert list(frame["time"]) == [
        "2026-01-01 00:00:01",
        "2026-01-01 00:00:02",
    ]


def test_store_accepts_legacy_temperature_column(tmp_path: Path):
    output = tmp_path / "legacy.xlsx"
    pd.DataFrame(
        [
            {
                "time": "2026-01-01 00:00:01",
                "lat": 38.7,
                "lon": 35.5,
                "ph": 7.2,
                "turbidity": 20,
                "status": "CLEAR",
                "temperature": 19.5,
            }
        ]
    ).to_excel(output, index=False)

    store = ExcelMeasurementStore(output)
    store.append(record(2))
    store.close()

    frame = pd.read_excel(output)
    assert "temp" in frame.columns
    assert len(frame) == 2
