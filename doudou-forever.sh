until python3 doudou.py; do
	echo "doudou died ($?). A resurgent..." >> crash.log
	sleep 1
done
