CartMonitor.py
-main script that setups all the configurations and monitors the spots with a camera, contains comparison logic to update API with realtime status

FetchAPIData.py
-contains methods to obtain information from FleetManager API

PostAPIData.py 
-contains methods to change statuses on FleetManager API

Websocket.py
-subscribes to websocket and creates socket.json to relay change events to CartMonitor.py

run.sh
-used to create the linux service  
