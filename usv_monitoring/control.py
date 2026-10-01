"""Pure control decisions shared by the Raspberry Pi controller and tests."""

from __future__ import annotations

from typing import Optional, Union

VALID_MOTION_COMMANDS = frozenset({"w", "a", "s", "d", "x"})


def select_control_mode(
    current_mode: str,
    selector_pwm: int,
    rc_threshold: int = 1700,
    computer_threshold: int = 1300,
) -> str:
    """Select RC/computer mode while retaining the original hysteresis band."""

    if selector_pwm > rc_threshold:
        return "RC"
    if selector_pwm < computer_threshold:
        return "COMPUTER"
    return current_mode


def command_from_channels(
    steering_pwm: int,
    throttle_pwm: int,
    dead_zone: int = 50,
    center: int = 1500,
) -> str:
    """Map the dominant RC stick axis to the existing one-byte command set."""

    steering_delta = steering_pwm - center
    throttle_delta = throttle_pwm - center

    if abs(steering_delta) < dead_zone and abs(throttle_delta) < dead_zone:
        return "x"

    if abs(throttle_delta) > abs(steering_delta):
        if throttle_delta > dead_zone:
            return "w"
        if throttle_delta < -dead_zone:
            return "s"
    else:
        if steering_delta > dead_zone:
            return "d"
        if steering_delta < -dead_zone:
            return "a"

    return "x"


def last_motion_command(command: Union[str, bytes]) -> Optional[str]:
    """Return the last valid motion byte in a direct telemetry payload."""

    if isinstance(command, bytes):
        text = command.decode("utf-8", errors="ignore")
    else:
        text = command

    for character in reversed(text):
        if character in VALID_MOTION_COMMANDS:
            return character
    return None
