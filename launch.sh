while ! ping -c 1 -W 1 8.8.8.8 do
    echo "Waiting for network..."
    sleep 1
done
. chronometer.py