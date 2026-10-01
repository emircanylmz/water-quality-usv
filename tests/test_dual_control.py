from raspberry.dual_control import DualControlSystem


class FakeSerial:
    def __init__(self):
        self.writes = []

    def write(self, payload):
        self.writes.append(payload)

    def flush(self):
        return None


def test_direct_command_updates_cache_and_mode_change_forces_stop():
    controller = DualControlSystem()
    controller.arduino_ser = FakeSerial()
    controller.last_arduino_command = "x"

    assert controller.send_to_arduino_direct(b"w")
    assert controller.last_arduino_command == "w"

    controller.ch1 = 1800
    controller.determine_control_mode()

    assert controller.control_mode == "RC"
    assert controller.arduino_ser.writes == [b"w", b"x"]
    assert controller.last_arduino_command == "x"


def test_safe_sender_can_force_a_duplicate_stop():
    controller = DualControlSystem()
    controller.arduino_ser = FakeSerial()
    controller.last_arduino_command = "x"

    assert controller.send_to_arduino_safe("x", force=True)
    assert controller.arduino_ser.writes == [b"x"]
