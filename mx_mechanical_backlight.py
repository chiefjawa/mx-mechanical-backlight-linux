#!/usr/bin/env python3
"""Set the MX Mechanical's persistent backlight delays through Solaar."""

import argparse
import sys

try:
    from logitech_receiver.exceptions import FeatureCallError
    from logitech_receiver.hidpp20 import Backlight
    from solaar import configuration
    from solaar.cli import _find_device, _receivers_and_devices
except ImportError as exc:
    raise SystemExit("Solaar is required. Install the Solaar package for your Linux distribution.") from exc


MODEL_NAME = "MX Mechanical"
MODEL_WPID = "B366"
MAX_SECONDS = 7200
FIELDS = ("hands_out", "hands_in", "powered")


def seconds(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer number of seconds") from exc
    if number < 5 or number > MAX_SECONDS or number % 5:
        raise argparse.ArgumentTypeError("must be a multiple of 5 from 5 to 7200 seconds")
    return number


def find_keyboard(serial):
    receivers = list(_receivers_and_devices())
    if not receivers:
        raise RuntimeError("No Solaar-compatible receiver or keyboard was found")
    devices = [
        device
        for device in _find_device(receivers, MODEL_NAME.lower())
        if device.name == MODEL_NAME
        and str(device.wpid).upper() == MODEL_WPID
        and (serial is None or str(device.serial or "").upper() == serial.upper())
        and device.ping()
    ]
    if len(devices) != 1:
        raise RuntimeError(
            f"Expected one connected {MODEL_NAME} (WPID {MODEL_WPID}); found {len(devices)}. "
            "Wake the keyboard, or use --serial if more than one is connected."
        )
    return devices[0]


def state(device):
    light = Backlight(device)
    return {
        "enabled": bool(light.enabled),
        "mode": light.mode,
        "hands_out": light.dho * 5,
        "hands_in": light.dhi * 5,
        "powered": light.dpow * 5,
    }


def show(values):
    mode = {0: "enabled", 1: "automatic", 2: "temporary manual", 3: "manual"}.get(
        values["mode"], f"unknown ({values['mode']})"
    )
    print(f"Backlight: {mode if values['enabled'] else 'disabled'}")
    print(f"Hands away: {values['hands_out']} seconds")
    print(f"Hands near: {values['hands_in']} seconds")
    print(f"Charging: {values['powered']} seconds")


def set_delays(device, desired):
    before = state(device)
    light = Backlight(device)
    if not light.enabled:
        light.enabled = 1
        light.mode = 1  # Automatic, so the keyboard still uses its light sensor.
    light.dho = desired["hands_out"] // 5
    light.dhi = desired["hands_in"] // 5
    light.dpow = desired["powered"] // 5

    if all(before[field] == desired[field] for field in FIELDS) and before["enabled"]:
        print("Already set:")
        show(before)
        return

    if light.write() is None:
        raise RuntimeError("The keyboard did not acknowledge the backlight update")

    after = state(device)
    if not after["enabled"] or any(after[field] != desired[field] for field in FIELDS):
        raise RuntimeError(f"Readback differs from the requested values: {after}")

    # Solaar reapplies saved settings when it starts, so keep its config in sync.
    saved = configuration.persister(device)
    if saved is not None:
        saved["backlight"] = after["mode"]
        for field in FIELDS:
            saved[f"backlight_duration_{field}"] = after[field]

    print("Saved and verified:")
    show(after)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="select one keyboard if several MX Mechanicals are connected")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show current settings without changing them")
    set_command = commands.add_parser("set", help="save new delays to the keyboard")
    set_command.add_argument("--hands-out", type=seconds, default=MAX_SECONDS)
    set_command.add_argument("--hands-in", type=seconds, default=MAX_SECONDS)
    set_command.add_argument("--powered", type=seconds, default=MAX_SECONDS)
    args = parser.parse_args(argv)

    try:
        device = find_keyboard(args.serial)
        if args.command == "status":
            show(state(device))
        else:
            set_delays(
                device,
                {"hands_out": args.hands_out, "hands_in": args.hands_in, "powered": args.powered},
            )
    except (FeatureCallError, OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
