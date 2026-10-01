"""Minimal SBUS frame decoding, including frame-loss and failsafe flags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

SBUS_FRAME_LENGTH = 25
SBUS_START_BYTE = 0x0F


@dataclass(frozen=True)
class SBusFrame:
    channels: Tuple[int, ...]
    frame_lost: bool
    failsafe: bool

    @property
    def signal_ok(self) -> bool:
        return not self.frame_lost and not self.failsafe


def _raw_to_pwm(raw_value: int) -> int:
    pwm = int(((raw_value - 172) * 1000 / 1639) + 1000)
    return max(1000, min(2000, pwm))


def decode_sbus_frame(data: bytes, channel_count: int = 3) -> SBusFrame:
    if len(data) != SBUS_FRAME_LENGTH or data[0] != SBUS_START_BYTE:
        raise ValueError("Invalid SBUS frame")
    if not 1 <= channel_count <= 16:
        raise ValueError("channel_count must be between 1 and 16")

    channels = []
    for channel in range(channel_count):
        raw_value = 0
        bit_start = channel * 11
        for bit in range(11):
            byte_index = 1 + ((bit_start + bit) // 8)
            bit_index = (bit_start + bit) % 8
            if data[byte_index] & (1 << bit_index):
                raw_value |= 1 << bit
        channels.append(_raw_to_pwm(raw_value))

    flags = data[23]
    return SBusFrame(
        channels=tuple(channels),
        frame_lost=bool(flags & (1 << 2)),
        failsafe=bool(flags & (1 << 3)),
    )
