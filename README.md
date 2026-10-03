# MX Mechanical backlight timeout on Linux

The Logitech MX Mechanical can save a longer keyboard backlight timeout than its short default. This tool sets the hands-away, hands-near, and charging delays to **two hours** and checks what the keyboard saved. It does not make the light permanently on.

Tested with a full-size MX Mechanical (WPID `B366`, firmware `RBK 71.03.B0021`) connected through a Logi Bolt receiver on Linux with Solaar 1.1.20. The setting is stored on the keyboard, so the tool does not need to keep running. Other models and firmware versions have not been tested.

## Use it

Install [Solaar](https://github.com/pwr-Solaar/Solaar) from your Linux distribution, connect and wake the keyboard, then run:

```sh
python3 mx_mechanical_backlight.py status
python3 mx_mechanical_backlight.py set
python3 mx_mechanical_backlight.py status
```

The `set` command enables automatic backlighting if it was disabled. It otherwise leaves the lighting mode alone. You can choose shorter delays in five-second steps:

```sh
python3 mx_mechanical_backlight.py set --hands-out 300 --hands-in 300 --powered 300
```

To restore the defaults measured on our test keyboard:

```sh
python3 mx_mechanical_backlight.py set --hands-out 30 --hands-in 30 --powered 300
```

Run `status` before changing anything if you want a record of your own defaults. If you have two full-size MX Mechanicals connected, use `--serial` before the command to select one; find its serial with `solaar show`.

## Limits

- Two hours is the maximum documented by the [HID++ backlight protocol](https://openlogi.org/hidpp/features/x1982-backlight). The keyboard can still turn lighting off in a bright room or at low battery.
- A longer timeout uses more battery. This tool makes a persistent device setting, so there is no background process to stop.
- Solaar 1.1.20's normal UI and CLI limit these delays to 600 seconds even though its [source acknowledges the two-hour maximum](https://github.com/pwr-Solaar/Solaar/blob/master/lib/logitech_receiver/settings_templates.py). This tool uses Solaar's device library to save and read back the larger value. Solaar's own UI may not display an out-of-range value correctly.
- Solaar is an independent Linux project, not Logitech software. The code uses its Python internals, which can change in future releases.

## How it works

The tool checks for exactly one connected full-size MX Mechanical (WPID `B366`). It sends one HID++ `BACKLIGHT2` configuration update through Solaar, reads the setting back, and updates Solaar's saved configuration so a later Solaar launch does not restore an older timeout. It does not need root access or contact a network service, and it does not transmit device identifiers.
