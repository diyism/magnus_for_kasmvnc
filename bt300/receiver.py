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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=39500)
    parser.add_argument("--mode", choices=["absolute", "relative", "scroll"],
                        default="absolute")
    parser.add_argument("--yaw-gain", type=float, default=38.0,
                        help="pixels per degree in absolute/relative modes")
    parser.add_argument("--pitch-gain", type=float, default=30.0,
                        help="pixels per degree in absolute/relative modes")
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
            yaw = float(pose["yaw"])
            pitch = float(pose["pitch"])
        except Exception as exc:
            print(f"bad packet from {addr}: {exc}", file=sys.stderr)
            continue

        now = time.monotonic()
        if now - last_update < 1.0 / args.rate:
            continue
        last_update = now

        if args.mode == "absolute":
            x = int(clamp(center_x + yaw * args.yaw_gain, 0, screen_w - 1))
            y = int(clamp(center_y + pitch * args.pitch_gain, 0, screen_h - 1))
            subprocess.call(["xdotool", "mousemove", str(x), str(y)])
        elif args.mode == "relative":
            if last_yaw is not None and last_pitch is not None:
                dx = int((yaw - last_yaw) * args.yaw_gain)
                dy = int((pitch - last_pitch) * args.pitch_gain)
                if dx or dy:
                    subprocess.call(["xdotool", "mousemove_relative",
                                     "--", str(dx), str(dy)])
            last_yaw = yaw
            last_pitch = pitch
        else:
            scroll_accum += pitch
            if scroll_accum > args.scroll_threshold:
                subprocess.call(["xdotool", "click", "5"])
                scroll_accum = 0.0
            elif scroll_accum < -args.scroll_threshold:
                subprocess.call(["xdotool", "click", "4"])
                scroll_accum = 0.0


if __name__ == "__main__":
    main()
