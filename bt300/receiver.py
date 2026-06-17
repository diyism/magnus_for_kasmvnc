#!/usr/bin/env python3
import argparse
import json
import socket
import subprocess
import sys
import time


def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def display_geometry():
    try:
        out = run(["xdotool", "getdisplaygeometry"])
        width, height = out.split()[:2]
        return int(width), int(height)
    except Exception:
        return 1920, 1080


def clamp(value, low, high):
    return max(low, min(high, value))


def axis_value(pose, name):
    return float(pose[name])


def apply_deadzone(value, deadzone):
    if abs(value) < deadzone:
        return 0.0
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=39500)
    parser.add_argument("--mode", choices=["gyro", "relative", "scroll"],
                        default="gyro")
    parser.add_argument("--x-axis", choices=["gx", "gy", "gz"],
                        default="gz",
                        help="incoming gyro axis used for horizontal movement")
    parser.add_argument("--y-axis", choices=["gx", "gy", "gz"],
                        default="gx",
                        help="incoming gyro axis used for vertical movement")
    parser.add_argument("--invert-x", action="store_true")
    parser.add_argument("--invert-y", action="store_true")
    parser.add_argument("--yaw-gain", type=float, default=120.0,
                        help="pixels per rad/s for horizontal gyro movement")
    parser.add_argument("--pitch-gain", type=float, default=120.0,
                        help="pixels per rad/s for vertical gyro movement")
    parser.add_argument("--deadzone", type=float, default=0.03,
                        help="ignore angular velocity below this rad/s")
    parser.add_argument("--scroll-threshold", type=float, default=8.0,
                        help="pitch degrees needed per scroll tick")
    parser.add_argument("--rate", type=float, default=60.0,
                        help="max xdotool updates per second")
    args = parser.parse_args()

    screen_w, screen_h = display_geometry()
    center_x = screen_w // 2
    center_y = screen_h // 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"listening on {args.host}:{args.port}, screen {screen_w}x{screen_h}",
          flush=True)

    last_update = 0.0
    last_yaw = None
    last_pitch = None
    scroll_accum = 0.0

    while True:
        data, addr = sock.recvfrom(2048)
        try:
            pose = json.loads(data.decode("utf-8"))
            x_axis = axis_value(pose, args.x_axis)
            y_axis = axis_value(pose, args.y_axis)
            if args.invert_x:
                x_axis = -x_axis
            if args.invert_y:
                y_axis = -y_axis
        except Exception as exc:
            print(f"bad packet from {addr}: {exc}", file=sys.stderr)
            continue

        now = time.monotonic()
        if now - last_update < 1.0 / args.rate:
            continue
        last_update = now

        x_axis = apply_deadzone(x_axis, args.deadzone)
        y_axis = apply_deadzone(y_axis, args.deadzone)

        if args.mode == "gyro":
            dx = int(x_axis * args.yaw_gain)
            dy = int(y_axis * args.pitch_gain)
            if dx or dy:
                subprocess.call(["xdotool", "mousemove_relative",
                                 "--", str(dx), str(dy)])
        elif args.mode == "relative":
            if last_yaw is not None and last_pitch is not None:
                dx = int((x_axis - last_yaw) * args.yaw_gain)
                dy = int((y_axis - last_pitch) * args.pitch_gain)
                if dx or dy:
                    subprocess.call(["xdotool", "mousemove_relative",
                                     "--", str(dx), str(dy)])
            last_yaw = x_axis
            last_pitch = y_axis
        else:
            scroll_accum += y_axis
            if scroll_accum > args.scroll_threshold:
                subprocess.call(["xdotool", "click", "5"])
                scroll_accum = 0.0
            elif scroll_accum < -args.scroll_threshold:
                subprocess.call(["xdotool", "click", "4"])
                scroll_accum = 0.0


if __name__ == "__main__":
    main()
