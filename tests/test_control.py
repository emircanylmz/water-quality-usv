from usv_monitoring.control import (
    command_from_channels,
    last_motion_command,
    select_control_mode,
)


def test_mode_selection_keeps_hysteresis_band():
    assert select_control_mode("COMPUTER", 1800) == "RC"
    assert select_control_mode("RC", 1200) == "COMPUTER"
    assert select_control_mode("RC", 1500) == "RC"
    assert select_control_mode("COMPUTER", 1500) == "COMPUTER"


def test_rc_command_uses_dominant_axis_and_dead_zone():
    assert command_from_channels(1500, 1500) == "x"
    assert command_from_channels(1500, 1800) == "w"
    assert command_from_channels(1500, 1200) == "s"
    assert command_from_channels(1800, 1500) == "d"
    assert command_from_channels(1200, 1500) == "a"


def test_direct_payload_updates_command_cache_from_last_motion_byte():
    assert last_motion_command(b"w") == "w"
    assert last_motion_command(b"noise,wx") == "x"
    assert last_motion_command(b"telemetry") is None
