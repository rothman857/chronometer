#!/bin/bash
# Call this script from /etc/rc.local to update on reboot


# Wait for internet connection
while :
do
  sleep 1
#  if (ping -c 1 -W 1 8.8.8.8 > /dev/null); then
if (nc -zw1 google.com 80); then
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
