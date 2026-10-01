"""Keyboard-to-serial command adapter with no import-time side effects."""

from __future__ import annotations

from typing import Any

from .control import VALID_MOTION_COMMANDS


class KeyboardCommandController:
    def __init__(self, serial_port: Any, verbose: bool = True) -> None:
        self.serial_port = serial_port
        self.verbose = verbose

    def on_press(self, key: Any) -> None:
        character = getattr(key, "char", None)
        if character in VALID_MOTION_COMMANDS - {"x"}:
            self.serial_port.write(character.encode("ascii"))
            if self.verbose:
                print("Gönderildi:", character)

    def on_release(self, _key: Any) -> None:
        self.serial_port.write(b"x")
        if self.verbose:
            print("DUR")

    def run(self) -> None:
        from pynput import keyboard

        with keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        ) as listener:
            listener.join()
