while ! ping -c 1 -W 1 8.8.8.8; do
    echo "Waiting for network..."
    sleep 1
done

script_dir="$(dirname $0)"
cd $script_dir
git pull
python3 chronometer.py
cd -
sleep 10
