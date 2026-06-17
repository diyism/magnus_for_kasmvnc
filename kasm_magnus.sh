DISPLAY=:2 xrandr --output VNC-0 --mode 1920x1080
nohup ./magnus --to-display=:2 --zoomlevel=1.5 >/dev/null 2>&1 &
./bt300/receiver.py
