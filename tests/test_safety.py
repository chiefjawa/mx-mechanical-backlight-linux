import unittest
from types import SimpleNamespace
from unittest.mock import patch

import mx_mechanical_backlight as tool


class SafetyTests(unittest.TestCase):
    def test_rejects_out_of_range_and_uneven_delays(self):
        for value in ("0", "7201", "31", "abc"):
            with self.assertRaises(Exception):
                tool.seconds(value)

    @patch.object(tool, "_find_device")
    @patch.object(tool, "_receivers_and_devices")
    def test_rejects_wrong_or_ambiguous_keyboard(self, receivers, find_device):
        receivers.return_value = [object()]
        wrong = SimpleNamespace(name="MX Mechanical Mini", wpid="B367", serial="abc")
        find_device.return_value = [wrong]
        with self.assertRaises(RuntimeError):
            tool.find_keyboard(None)

        first = SimpleNamespace(name="MX Mechanical", wpid="B366", serial="abc", ping=lambda: True)
        second = SimpleNamespace(name="MX Mechanical", wpid="B366", serial="def", ping=lambda: True)
        find_device.return_value = [first, second]
        with self.assertRaises(RuntimeError):
            tool.find_keyboard(None)
        self.assertIs(tool.find_keyboard("abc"), first)

    @patch.object(tool.configuration, "persister")
    @patch.object(tool, "Backlight")
    def test_failed_readback_does_not_update_saved_settings(self, backlight, persister):
        old = SimpleNamespace(enabled=1, mode=1, dho=6, dhi=6, dpow=60)
        new = SimpleNamespace(enabled=1, mode=1, dho=1440, dhi=6, dpow=1440)
        old.write = lambda: b""
        backlight.side_effect = [old, old, new]
        with self.assertRaises(RuntimeError):
            tool.set_delays(object(), dict.fromkeys(tool.FIELDS, 7200))
        persister.assert_not_called()


if __name__ == "__main__":
    unittest.main()
