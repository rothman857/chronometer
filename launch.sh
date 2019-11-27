#!/bin/sh
# This script checks for a update before running the chronometer.
# Add the folling line to /etc/rc.local (before 'exit(0)'
#
# sudo -H -u pi sh /full/path/to/launcher.sh &
#
# exit(0)

# Wait for internet connection
while :
do
  sleep 1
if (nc -zw1 google.com 80); then
    echo "Device is online."
    break
  else
    echo "Waiting for network..."
  fi
done

# Pull most recent code
script_dir="$(dirname $0)"
cd $script_dir
git pull

python3 chronometer.py
