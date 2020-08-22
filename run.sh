#!/bin/bash

#function stopScript() {
#        sudo kill -9 $CARTMONITOR
#        sudo kill -9 $WEBSOCKET
#        echo "Processes Killed"
#        exit
#}


/home/pi/.virtualenvs/py3/bin/python /home/pi/python_scripts/SDV/rev3/SDV_Container_Monitor_Service/CartMonitor.py &
#CARTMONITOR=$!

/home/pi/.virtualenvs/py3/bin/python /home/pi/python_scripts/SDV/rev3/SDV_Container_Monitor_Service/Websocket.py &
#WEBSOCKET=$!

#echo $CARTMONITOR
#echo $WEBSOCKET

echo 'Bash script started'

while true;
do
	echo  ""
	#trap stopScript SIGINT SIGTERM SIGKILL
done
