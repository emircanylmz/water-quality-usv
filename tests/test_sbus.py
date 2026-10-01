import pytest

from usv_monitoring.sbus import decode_sbus_frame


def make_frame(raw_channels, flags=0):
    frame = bytearray(25)
    frame[0] = 0x0F
    for channel, raw_value in enumerate(raw_channels):
        start = channel * 11
        for bit in range(11):
            if raw_value & (1 << bit):
                byte_index = 1 + ((start + bit) // 8)
                bit_index = (start + bit) % 8
                frame[byte_index] |= 1 << bit_index
    frame[23] = flags
    return bytes(frame)


def test_decodes_first_three_channels():
    frame = decode_sbus_frame(make_frame([172, 992, 1811]), channel_count=3)
    assert frame.channels[0] == 1000
    assert frame.channels[1] == pytest.approx(1500, abs=1)
    assert frame.channels[2] == 2000
    assert frame.signal_ok


@pytest.mark.parametrize("flags", [1 << 2, 1 << 3, (1 << 2) | (1 << 3)])
def test_marks_lost_or_failsafe_frames_unsafe(flags):
    frame = decode_sbus_frame(make_frame([992, 992, 992], flags=flags))
    assert not frame.signal_ok


def test_rejects_invalid_frame():
    with pytest.raises(ValueError):
        decode_sbus_frame(b"short")
