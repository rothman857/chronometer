#!/usr/bin/sh

#Wait for internet connection
while :
do
  sleep 1
  if (ping -c 1 -W 1 8.8.8.8 > /dev/null); then
    break
  else
  fi
done

#Pull most recent code
script_dir="$(dirname $0)"
cd $script_dir
git pull

python3 chronometer.py
