#!/bin/bash
# This script checks for a update before running the chronometer.
# Call this script from /etc/rc.local (with a trailing '&') to
# automatically update the chronometer on reboot

# Wait for internet connection
while :
do
  sleep 1
if (nc -zw1 google.com 80); then
    echo "Found network"
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
