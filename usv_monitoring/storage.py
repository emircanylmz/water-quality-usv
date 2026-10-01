"""Durable Excel storage that preserves records from earlier sessions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pandas as pd

from .protocol import SensorRecord

COLUMNS = ["time", "lat", "lon", "ph", "turbidity", "status", "temp"]


class ExcelMeasurementStore:
    """Append measurements and atomically replace the XLSX output on flush."""

    def __init__(self, path: Path, flush_every: int = 1) -> None:
        self.path = Path(path)
        self.flush_every = max(1, flush_every)
        self._pending: List[SensorRecord] = []
        self._frame = self._load_existing()

    def _load_existing(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame(columns=COLUMNS)

        frame = pd.read_excel(self.path)
        if "temperature" in frame.columns and "temp" not in frame.columns:
            frame = frame.rename(columns={"temperature": "temp"})
        missing = [column for column in COLUMNS if column not in frame.columns]
        if missing:
            raise ValueError(
                f"{self.path} is missing required columns: {', '.join(missing)}"
            )
        return frame[COLUMNS]

    @property
    def count(self) -> int:
        return len(self._frame) + len(self._pending)

    def append(self, record: SensorRecord) -> None:
        self._pending.append(record)
        if len(self._pending) >= self.flush_every:
            self.flush()

    def flush(self) -> None:
        if not self._pending:
            return

        pending_frame = pd.DataFrame(
            [record.as_dict() for record in self._pending], columns=COLUMNS
        )
        if self._frame.empty:
            combined = pending_frame
        else:
            combined = pd.concat([self._frame, pending_frame], ignore_index=True)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_name(f".{self.path.stem}.tmp.xlsx")
        combined.to_excel(temporary_path, index=False, engine="openpyxl")
        os.replace(temporary_path, self.path)

        self._frame = combined
        self._pending.clear()

    def close(self) -> None:
        self.flush()
