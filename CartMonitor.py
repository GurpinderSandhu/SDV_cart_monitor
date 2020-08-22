#!/home/pi/.virtualenvs/py3/bin python
# Made by: Gurpinder Sandhu
# Version: 1.1

import os
import threading
import sys
import cv2
import numpy as np
import time
from datetime import datetime, timedelta
import json
import argparse
from FetchAPIData import *
from PostAPIData import *

#------------------RELATIVE PATH TO FILES-----------------------#
config_json_path = "./config.json"
detection_log_path = "./DetectionLog.txt"
error_log_path = "./ErrorLog.txt"
#---------------------------------------------------------------#

places = []
colour_bound_lower = np.array([167, 100, 100], dtype=np.uint8)
colour_bound_upper = np.array([187, 255, 255], dtype=np.uint8)
colour_threshold = 50
departure_wait_time = 5
arrival_wait_time = 5

class Place:
	def __init__(self, name, top_left_coord, bot_right_coord):
		self.name = name
		self.tlc = tuple(top_left_coord)
		self.brc = tuple(bot_right_coord)
		self.current_status = False
		self.last_status = False
		self.toggle_start_time = None

def log(place, status, fleet_status, time):
	log = open(detection_log_path,"a+")
	log.write("{}\t{}\t{}\t{}\t\n".format(place.name, status, fleet_status,time))
	log.close()

def error_log(message):
	e_log = open(error_log_path, "a+")
	e_log.write("{}\t".format(message))
	e_log.close()

def select_roi(nameID):
	roi_amount = nameID.keys()
	cap = cv2.VideoCapture(0)

	show_crosshair = False
	from_center = False

	_, frame = cap.read()
	cap.release()

	ref = {}

	#Run ROI Selector for each name
	for roi_name in roi_amount:
		img = frame.copy()
		cv2.putText(img, roi_name, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
		roi = cv2.selectROI(img, show_crosshair, from_center)

		ref[roi_name] = []
		ref[roi_name].append({
			'Top-Left-Coords': (roi[0], roi[1]),
			'Bot-Right-Coords': (roi[0]+roi[2], roi[1]+roi[3])
		})
	ref["colour_threshold"] = 50
	ref["departure_wait_time"] = 5
	ref["arrival_wait_time"] = 5
	ref["robot_departure_buffer"]= 10

	cv2.destroyAllWindows()

	with open(config_json_path, 'w') as output:
		json.dump(ref, output, indent=4)

	print('config.json file updated')

# Populate the 'places' global variable from json file
def load_places():
	try:
		with open(config_json_path) as json_file:
			data = json.load(json_file)
			for place in data:
				if not isinstance(data[place],list):
					continue
				places.append(Place(place, data[place][0]['Top-Left-Coords'], data[place][0]['Bot-Right-Coords']))
	except IOError:
		print('No config.json file found. Please run \"python cart_monitor.py -s \'Place Group Name\'\"')
		sys.exit()

# Takes a snapshot and updates Place Objects according to physical status
def monitor_spots():
	cap = cv2.VideoCapture(0)
	time.sleep(1)
	_, frame = cap.read()
	cap.release()

	for place in places:
        # Unpack ROI coordinates
		start_row, start_col = place.tlc
		end_row, end_col = place.brc
		crop = frame[start_col:end_col, start_row:end_row]
        
        # Detect Orange pixels
		hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
		mask = cv2.inRange(hsv, colour_bound_lower, colour_bound_upper)
		white_count = cv2.countNonZero(mask)

		# Check the instantaneous status of the cart
		if white_count > colour_threshold:
			place.current_status = True
		else:
			place.current_status = False


		# Detech when phsyical status changes
		if place.current_status != place.last_status:
			print("{}:\t STATUS CHANGED".format(place.name))
			
            # Begin timer countdown is not yet started
			if place.toggle_start_time == None:
				place.toggle_start_time = datetime.now()
				print("{}:\t TIMER STARTED".format(place.name))
			delta_time = (datetime.now() - place.toggle_start_time).seconds
			
            # Check if cart is departing
			if place.last_status:
				# If cart has been away for more than departure wait time
				if delta_time >= departure_wait_time:

					print("{}:\t TIMER EXCEEDED. DEPARTED".format(place.name))
					place.last_status = False
                    # Check against API
					compare(place, place.last_status)
					place.toggle_start_time = None
					log(place,"DEPARTED",getStatus(place.name),(datetime.now() - timedelta(seconds = departure_wait_time)))

			# Check if cart is arriving
			else:
				# If cart has been here for more than arrival wait time
				if delta_time >= arrival_wait_time:

					print("{}:\t TIMER EXCEEDED. ARRIVED".format(place.name))
					place.last_status = True
                    # Check against API
					compare(place, place.last_status)
					place.toggle_start_time = None
					log(place,"ARRIVED",getStatus(place.name),(datetime.now()- timedelta(seconds = arrival_wait_time)))

		# If in buffer period and state becomes the same again, turn off timer and change nothing
		if place.toggle_start_time != None and place.current_status == place.last_status:
			print("{}:\t TIMER CANCELLED".format(place.name))
			place.toggle_start_time = None

# Compares the physical status of a place with the API, and posts to API if different
def compare(place, status):
	api_status = getStatus(place.name)
    
	if(place.current_status != api_status):
		print("Post change to API")
		if(status == False):
			postPlaces(None, getID(place.name))
		else:
			postPlaces(True, getID(place.name))
	else:
		print("Status are the same. No change")

# Configures locations to monitor & region of interests
def initialize():
	ap = argparse.ArgumentParser()
	ap.add_argument('-s', '--setup', required=False, help='setup ROI for each slot', default=[])

	args = vars(ap.parse_args())
	place_group_name = args['setup']

    # If '-s' is not called then attempt to load ROIs from 'config.json'
	if len(place_group_name) == 0:
		print("Loading Places")
		load_places()
    # If '-s' is called but needs to be checked if Location is valid
	else:
		placesList = getPlacesList(place_group_name)


		if len(placesList) == 0:
			print("Place Group does not exist: Please select one of the following\n")
			for place_group in getPlaceGroupList():
				print("  {}".format(place_group))
			error_log("place group does not exist")
			sys.exit()
		else:
			select_roi(placesList)
			load_places()

    # Taking a snapshot to obtain initial state for each Place
	print("Starting up Camera")
	cap = cv2.VideoCapture(0)
	time.sleep(1)
	_, frame = cap.read()
	cap.release()

	print("Fetching Initial State")
	for place in places:
		start_row, start_col = place.tlc
		end_row, end_col = place.brc
		crop = frame[start_col:end_col, start_row:end_row]
		hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
		mask = cv2.inRange(hsv, colour_bound_lower, colour_bound_upper)
		white_count = cv2.countNonZero(mask)

		if white_count > colour_threshold:
			place.current_status = True
		else:
			place.current_status = False
		place.last_status = place.current_status
        
	print("Updating Initial State")
	for place in places:
		compare(place,place.last_status)

	print("Setup Complete -- Monitoring")
	while True:
		monitor_spots()
		readWebSocketTxt()

# Check for status updates from Websocket
def readWebSocketTxt():
	try:
        # Check if "socket.json" exists. If it does, then we received an update from Websocket
		if os.path.getsize("socket.json") > 0:
			with open("socket.json", 'r') as infile:
				data = json.load(infile)
				print(data['place'],data['change_to'])
				os.remove("socket.json")

				cap = cv2.VideoCapture(0)
				time.sleep(1)
				_, frame = cap.read()
				cap.release()
                
				for place in places:
                
					if (data['place'] == place.id):
						start_row, start_col = place.tlc
						end_row, end_col = place.brc
						crop = frame[start_col:end_col, start_row:end_row]
						hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
						mask = cv2.inRange(hsv, colour_bound_lower, colour_bound_upper)
						white_count = cv2.countNonZero(mask)

                        # If physical status does not match with received update, then post a change
						if white_count > colour_threshold:
							if data['change_to'] == 0:
								postPlaces(True, place.id)
								print("post to api to change to blue")
						else:
							if data['change_to'] == 1:
								postPlaces(None, place.id)
								print("post to api to change to none")
				
	except:
        # "socket.json" does not exist, therefore no update received from Websocket
		pass

# Program Starts Here
initialize()
