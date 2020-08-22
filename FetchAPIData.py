# Made by: Gurpinder Sandhu
# Version: 1.1

import json
import requests

requests.packages.urllib3.disable_warnings()

config_json_path = "./config.json"
URL_BASE = 'https://10.35.33.55'
PARAMS = {'accept': 'application/json'}

def readURLBase():
    global URL_BASE
    try:
        with open(config_json_path) as json_file:
            data = json.load(json_file)
            URL_BASE = data["URL_BASE"]
    except:
        print("No config file found.")

def _getPlaceGroupJson():
    readURLBase()
    URL = URL_BASE + "/api/fleet/v1/place_groups/?offset=0&ordering=name"
    response = requests.get(url=URL, verify=False, params=PARAMS)

    if response.status_code == 200:
        return(response.json())
    else:
        print(response.status_code)

def getPlaceGroupList():
    master_list = _getPlaceGroupJson()

    place_groups = []
    for place_group in master_list:
        place_groups.append(place_group["name"])
    return place_groups

def getPlacesList(place_group_name):
    master_list = _getPlaceGroupJson()
    names = {}
    for i in master_list:
        if i["name"] == place_group_name:
            for j in i["places"]:
                names[j["name"]] = j["id"]
    return(names)

def getID(name):
    master_list = _getPlaceGroupJson()
    places = []
    for i in master_list:
        for place in i["places"]:
            if place["name"] == name:
                return(place["id"])

def getStatus(name):
    ID = getID(name)
    URL = URL_BASE + "/api/fleet/v1/places/" + str(ID+"/")
    
    response = requests.get(url=URL, verify=False, params=PARAMS)

    if response.status_code == 200:
        lst = response.json()
    else:
        print(response.status_code)

    if lst["container"] != None:
        return(True)
    else:
        return(False)
