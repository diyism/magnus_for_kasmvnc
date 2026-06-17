# BT-300 head pose mouse bridge

This folder contains a small Android sender for Epson Moverio BT-300 and a
Debian receiver.

The sender uses Android's standard `SensorManager` motion APIs. It reads
`TYPE_GYROSCOPE` and sends raw angular velocity (`gx`, `gy`, `gz`) over UDP to
Debian.

## Build the APK

```bash
cd bt300
./build.sh
```

The output APK is:

```text
bt300/build/bt300-headmouse-debug.apk
```

Install it on the BT-300:

```bash
adb install -r build/bt300-headmouse-debug.apk
```

## Run the Debian receiver

On Debian, listening on all interfaces:

```bash
cd bt300
DISPLAY=:0 ./receiver.py --host 0.0.0.0 --port 39500
```

The default mode maps gyroscope angular velocity to relative mouse movement.
Small sensor drift is ignored with a deadzone; the default is `0.03 rad/s`.
The receiver defaults to `--x-axis gz --y-axis gx`, but BT-300 axis mapping may
need adjustment depending on how the device reports its gyroscope axes.

Useful receiver options:

```bash
DISPLAY=:0 ./receiver.py --yaw-gain 120 --pitch-gain 120
DISPLAY=:0 ./receiver.py --x-axis gy --y-axis gx
DISPLAY=:0 ./receiver.py --x-axis gz --y-axis gx --invert-y
DISPLAY=:0 ./receiver.py --deadzone 0.05
DISPLAY=:0 ./receiver.py --mode scroll --scroll-threshold 8
```

## Android app settings

Default target:

```text
192.168.0.12:39500
```

Change it in the app UI if Debian has a different IP.

## Notes

Android documents gyroscope motion sensors through the standard sensor API.
BT-300 should expose its gyroscope through the same Android API path.
