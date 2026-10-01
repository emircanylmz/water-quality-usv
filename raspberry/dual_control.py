#!/usr/bin/env python3
"""Raspberry Pi dual-control bridge implementation.

The public script name and field defaults are preserved. Reusable decisions are
delegated to ``usv_monitoring`` so they can be tested without serial hardware.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional, Union

import serial
import serial.tools.list_ports

from usv_monitoring.config import DualControlConfig
from usv_monitoring.control import (
    command_from_channels,
    last_motion_command,
    select_control_mode,
)
from usv_monitoring.protocol import looks_like_arduino_telemetry
from usv_monitoring.sbus import decode_sbus_frame


class DualControlSystem:
    def __init__(
        self,
        x8r_port: Optional[str] = None,
        telemetry_port: Optional[str] = None,
        arduino_port: Optional[str] = None,
        config: Optional[DualControlConfig] = None,
        serial_factory: Callable[..., object] = serial.Serial,
        port_lister: Callable[[], object] = serial.tools.list_ports.comports,
    ) -> None:
        self.config = config or DualControlConfig.from_env()

        self.x8r_port = x8r_port or self.config.x8r_port
        self.telemetry_port = telemetry_port or self.config.telemetry_port
        self.arduino_port = arduino_port or self.config.arduino_port
        self.serial_factory = serial_factory
        self.port_lister = port_lister

        self.x8r_ser = None
        self.telemetry_ser = None
        self.arduino_ser = None

        self.ch1 = 1500
        self.ch2 = 1500
        self.ch3 = 1500

        self.control_mode = "COMPUTER"
        self.running = False
        self.last_arduino_command: Optional[str] = None
        self.last_sbus_frame_time = 0.0
        self.rc_signal_ok = False

        self.rc_threshold = self.config.rc_threshold
        self.computer_threshold = self.config.computer_threshold
        self.dead_zone = self.config.dead_zone
        self._arduino_write_lock = threading.Lock()

    def detect_usb_ports(self) -> None:
        """Identify Arduino by its sensor output; never accept a port unconditionally."""

        print("USB portları taranıyor...")
        usb_ports = []
        for port in self.port_lister():
            device_upper = port.device.upper()
            if "USB" in device_upper or "ACM" in device_upper or "/DEV/CU." in device_upper:
                usb_ports.append(port.device)
                print(f"Bulunan port: {port.device} - {port.description}")

        if len(usb_ports) < 2:
            print("En az 2 USB port bulunamadı; yapılandırılmış portlar kullanılacak.")
            return

        detected_arduino = None
        for port in usb_ports:
            test_serial = None
            try:
                print(f"{port} Arduino telemetrisi için test ediliyor...")
                test_serial = self.serial_factory(
                    port, self.config.arduino_baud, timeout=0.2
                )
                time.sleep(2.0)
                deadline = time.monotonic() + 1.5
                payload = bytearray()
                while time.monotonic() < deadline:
                    waiting = getattr(test_serial, "in_waiting", 0)
                    if waiting:
                        payload.extend(test_serial.read(waiting))
                        if looks_like_arduino_telemetry(bytes(payload)):
                            detected_arduino = port
                            break
                    time.sleep(0.05)
                if detected_arduino:
                    print(f"Arduino tespit edildi: {port}")
                    break
            except Exception as exc:
                print(f"{port} Arduino testi başarısız: {exc}")
            finally:
                if test_serial:
                    test_serial.close()

        remaining_ports = [port for port in usb_ports if port != detected_arduino]
        detected_telemetry = remaining_ports[0] if detected_arduino and remaining_ports else None

        if detected_arduino:
            self.arduino_port = detected_arduino
            print(f"Arduino portu otomatik atandı: {self.arduino_port}")
        if detected_telemetry:
            self.telemetry_port = detected_telemetry
            print(f"Telemetri portu otomatik atandı: {self.telemetry_port}")
        if not detected_arduino or not detected_telemetry:
            print("Portlar doğrulanamadı; yapılandırılmış portlar korunuyor.")

    def connect_all(self) -> bool:
        success = True

        try:
            self.x8r_ser = self.serial_factory(
                port=self.x8r_port,
                baudrate=self.config.x8r_baud,
                bytesize=serial.EIGHTBITS,
                parity=self.config.x8r_parity,
                stopbits=self.config.x8r_stopbits,
                timeout=0.001,
            )
            self.x8r_ser.reset_input_buffer()
            print(f"X8R bağlandı ({self.x8r_port})")
        except Exception as exc:
            print(f"X8R bağlantı hatası: {exc}")
            success = False

        try:
            self.telemetry_ser = self.serial_factory(
                self.telemetry_port, self.config.telemetry_baud, timeout=0.001
            )
            print(f"Telemetri bağlandı ({self.telemetry_port})")
        except Exception as exc:
            print(f"Telemetri bağlantı hatası: {exc}")
            success = False

        try:
            self.arduino_ser = self.serial_factory(
                self.arduino_port, self.config.arduino_baud, timeout=0.001
            )
            time.sleep(2.0)
            print(f"Arduino bağlandı ({self.arduino_port})")
        except Exception as exc:
            print(f"Arduino bağlantı hatası: {exc}")
            success = False

        return success

    def close_all(self) -> None:
        for connection in (self.x8r_ser, self.telemetry_ser, self.arduino_ser):
            if connection:
                try:
                    connection.close()
                except Exception as exc:
                    print(f"Seri port kapatma hatası: {exc}")

    def parse_sbus_channels(self, data: bytes) -> bool:
        try:
            frame = decode_sbus_frame(data, channel_count=3)
        except ValueError:
            return False

        if not frame.signal_ok:
            self.rc_signal_ok = False
            return False

        self.ch1, self.ch2, self.ch3 = frame.channels
        self.last_sbus_frame_time = time.monotonic()
        self.rc_signal_ok = True
        return True

    def rc_signal_is_fresh(self) -> bool:
        return self.rc_signal_ok and (
            time.monotonic() - self.last_sbus_frame_time
            <= self.config.sbus_timeout_seconds
        )

    def read_x8r_thread(self) -> None:
        buffer = bytearray()

        while self.running:
            try:
                if self.x8r_ser and self.x8r_ser.in_waiting > 0:
                    buffer.extend(self.x8r_ser.read(self.x8r_ser.in_waiting))

                    while len(buffer) >= 25:
                        start_index = buffer.find(0x0F)
                        if start_index == -1:
                            buffer.clear()
                            break
                        if start_index > 0:
                            buffer = buffer[start_index:]
                        if len(buffer) >= 25:
                            frame = bytes(buffer[:25])
                            buffer = buffer[25:]
                            self.parse_sbus_channels(frame)
                time.sleep(0.001)
            except Exception as exc:
                if self.running:
                    print(f"X8R okuma hatası: {exc}")
                time.sleep(0.01)

    def read_telemetry_thread(self) -> None:
        while self.running:
            try:
                if self.telemetry_ser and self.telemetry_ser.in_waiting > 0:
                    command = self.telemetry_ser.read(self.telemetry_ser.in_waiting)
                    if self.control_mode == "COMPUTER":
                        self.send_to_arduino_direct(command)
                time.sleep(0.001)
            except Exception as exc:
                if self.running:
                    print(f"Telemetri okuma hatası: {exc}")
                time.sleep(0.01)

    def read_arduino_thread(self) -> None:
        while self.running:
            try:
                if self.arduino_ser and self.arduino_ser.in_waiting > 0:
                    line = self.arduino_ser.readline().decode(errors="ignore").strip()
                    if line:
                        if self.telemetry_ser:
                            try:
                                self.telemetry_ser.write((line + "\n").encode())
                            except Exception as exc:
                                print(f"Telemetri gönderim hatası: {exc}")
                        print(f"\nArduino veri: {line}")
                time.sleep(0.01)
            except Exception as exc:
                if self.running:
                    print(f"Arduino okuma hatası: {exc}")
                time.sleep(0.1)

    def determine_control_mode(self) -> None:
        old_mode = self.control_mode
        self.control_mode = select_control_mode(
            current_mode=self.control_mode,
            selector_pwm=self.ch1,
            rc_threshold=self.rc_threshold,
            computer_threshold=self.computer_threshold,
        )

        if old_mode != self.control_mode:
            label = "BİLGİSAYAR" if self.control_mode == "COMPUTER" else "KUMANDA"
            print(f"\n{label} MODU AKTİF (CH1: {self.ch1})")
            # A mode transition is a safety boundary. Never deduplicate this stop.
            self.send_to_arduino_safe("x", force=True)

    def calculate_rc_command(self) -> str:
        return command_from_channels(
            steering_pwm=self.ch2,
            throttle_pwm=self.ch3,
            dead_zone=self.dead_zone,
        )

    def send_to_arduino_safe(
        self, command: Union[str, bytes], force: bool = False
    ) -> bool:
        if isinstance(command, bytes):
            command = command.decode("utf-8", errors="ignore")
        if not self.arduino_ser:
            return False
        if not force and command == self.last_arduino_command:
            return True

        try:
            with self._arduino_write_lock:
                self.arduino_ser.write(command.encode())
                self.arduino_ser.flush()
            self.last_arduino_command = command
            return True
        except Exception as exc:
            print(f"Arduino gönderim hatası: {exc}")
            return False

    def send_to_arduino_direct(self, command: bytes) -> bool:
        if not self.arduino_ser:
            return False
        try:
            with self._arduino_write_lock:
                self.arduino_ser.write(command)
                self.arduino_ser.flush()
            observed_command = last_motion_command(command)
            if observed_command:
                self.last_arduino_command = observed_command
            return True
        except Exception as exc:
            print(f"Arduino direkt gönderim hatası: {exc}")
            return False

    def get_command_text(self, command: str) -> str:
        return {
            "w": "İLERİ",
            "s": "GERİ",
            "d": "SAĞ",
            "a": "SOL",
            "x": "DUR",
        }.get(command, "?")

    def main_control_loop(self) -> None:
        print("\nDUAL CONTROL SİSTEMİ BAŞLADI")
        print("=" * 60)
        print(f"CH1 İleri (>{self.rc_threshold}): Kumanda Modu")
        print(f"CH1 Geri (<{self.computer_threshold}): Bilgisayar Modu")
        print("CH2: Sağ-Sol | CH3: İleri-Geri")
        print("Çıkmak için Ctrl+C\n")

        while self.running:
            self.determine_control_mode()

            if self.control_mode == "RC":
                rc_command = self.calculate_rc_command() if self.rc_signal_is_fresh() else "x"
                self.send_to_arduino_safe(rc_command)
                signal_text = "" if self.rc_signal_is_fresh() else " SBUS KAYIP"
                print(
                    f"\rkumanda CH1:{self.ch1:4d} CH2:{self.ch2:4d} "
                    f"CH3:{self.ch3:4d} -> '{rc_command}' "
                    f"{self.get_command_text(rc_command)}{signal_text}    ",
                    end="",
                    flush=True,
                )
            else:
                print(
                    f"\rbilgisayar COMPUTER MODE - CH1:{self.ch1:4d} "
                    "(Telemetri aktif)           ",
                    end="",
                    flush=True,
                )

            time.sleep(0.05)

    def start_system(self) -> bool:
        print("Dual Control System - X8R + Telemetri -> Arduino")
        print("=" * 60)

        if self.config.auto_detect_usb:
            self.detect_usb_ports()

        if not self.connect_all():
            print("Bağlantı hatası! Sistem durduruluyor.")
            self.close_all()
            return False

        print(
            f"Eşik değerleri: RC>{self.rc_threshold}, "
            f"Computer<{self.computer_threshold}"
        )
        print("Sistem hazır!")
        self.running = True

        threads = (
            threading.Thread(target=self.read_x8r_thread, daemon=True),
            threading.Thread(target=self.read_telemetry_thread, daemon=True),
            threading.Thread(target=self.read_arduino_thread, daemon=True),
        )
        for thread in threads:
            thread.start()

        try:
            time.sleep(1.0)
            self.main_control_loop()
        except KeyboardInterrupt:
            print("\n\nSistem durduruldu")
        finally:
            self.running = False
            self.send_to_arduino_safe("x", force=True)
            self.close_all()
        return True


# Backward-compatible name used by the original project.
Dual_Control_System = DualControlSystem


def main() -> None:
    DualControlSystem(config=DualControlConfig.from_env()).start_system()


if __name__ == "__main__":
    main()
