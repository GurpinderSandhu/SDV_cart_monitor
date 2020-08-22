# Made by: Gurpinder Sandhu
# Version: 1.1

import json
import requests

config_json_path = "./config.json"

requests.packages.urllib3.disable_warnings()

URL_BASE = ""

PARAMS = {'accept': 'application/json', 'Content-Type': 'application/json'}

REQUEST_BODY = {
    "operation": "SET_CONTAINER",
    "place": None,
    "arguments":
    {
        "container":
        {
			"container_type": "OTTO100_CART",
			"container_empty": True
		}
	}
}

REQUEST_BODY_EMPTY = {
    "operation": "SET_CONTAINER",
    "place": None,
    "arguments":
    {
        "container": None
        }
}

def readURLBase():
    global URL_BASE
    try:
        with open(config_json_path) as json_file:
            data = json.load(json_file)
            URL_BASE = data["URL_BASE"]
    except:
        print("No config file found.")

def postPlaces(status, UID):
    readURLBase()
    URL = URL_BASE + "/api/fleet/v1/places/operations/"

    # Update JSON reqyest string with UID
    REQUEST_BODY["place"] = UID
    REQUEST_BODY_EMPTY["place"] = UID

    if (status == None):
        response = requests.post(url=URL, verify=False, params=PARAMS, json=REQUEST_BODY_EMPTY)
    elif (status != None):
        # Defaults to post Empty cart data
        response = requests.post(url=URL, verify=False, params=PARAMS, json=REQUEST_BODY)
        
    if response.status_code == 201:
        return(response.json())
    else:
        print(response.status_code)
