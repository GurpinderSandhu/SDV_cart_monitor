# Made by: Gurpinder Sandhu
# Version: 1.1

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from functools import partial
from twisted.internet import reactor, ssl
from twisted.internet.defer import inlineCallbacks

import threading
import json
import time
from FetchAPIData import *

#------------------RELATIVE PATH TO FILES-----------------------#
config_json_path = "./config.json"
#---------------------------------------------------------------#

robot_departure_buffer = 0
global_json = {'place': 0,'change_to': 0}
spots = []

def init_spots(place_id):
    tmp_spot = {'place': place_id, 'id': None, 'robot_id': None}
    spots.append(tmp_spot)

def load_places():
	global robot_departure_buffer
	try:
		with open(config_json_path) as json_file:
			data = json.load(json_file)
			robot_departure_biffer = data["robot_departure_buffer"]
			for place in data:
				if not isinstance(data[place], list):
					continue
				init_spots(getID(place))
	except IOError:
		print('No config.json file found. Please run \"python cart_monitor.py -s \'Place Group Name\'\"')
		sys.exit()

class Component(ApplicationSession):
    topics = ('v2.containers','v2.places.traffic')

    def _subscribe(self, topic):
        return self.subscribe(partial(self.on_event, topic), topic)

    @inlineCallbacks
    def onJoin(self, details):
        print('connected')
        for topic in self.topics:
            sub = yield self._subscribe(str(topic))
            print("subscribed to {0}\nsub id: {1}".format(topic, sub.id))

    def on_event(self, topic, *args, **kwargs):
	# API provides all the information through 'args'
	# We convert it to a list
        arg = list(args)
        event_type = arg[0]
        json_list = arg[1]

        if topic == self.topics[0]:
	    # The first item in the list lets us know whether it is showing
	    # the initial state or providing an update 
            for spot in spots:
                # Setting the Initial ID
                if event_type == 'all':
                    for i in json_list:
                        if i['place'] == spot['place']:
                            spot['id'] = i['id']
                    print(spot)
                if event_type == 'updated':
                    # For loop accounts for situation where goes from colour to white, and robot has not left completely yet
                    if spot['robot_id'] == json_list[0]['robot'] and json_list[0]['state'] == "DROPPING_OFF":
                        global_json['place'] = spot['place']
                        global_json['change_to'] = 0
                        # Robot has a place to go, but adding delay to give it time to fully leave ROI, then update socket.json
                        timer = threading.Timer(robot_departure_buffer,writeJSON)
                        timer.start
                        print("Robot on the move")
                        spot['robot_id'] = None
                        
                    # Check if API set cart as arrived or departed and let "CartMonitor.py" know through "socket.json"
                    if json_list[0]['id'] == spot['id']:
                       print("recieved update for place: {}".format(spot['place']))
                       print("corresponding id {}".format(spot['id']))
                       # ID matches and it shows that the place is None, therefore its going to white
                       if json_list[0]['place'] == None:
                          print("{}: Colour --> White".format(spot['place']))
                          spot['robot_id']=json_list[0]['robot']
                          print("Cart picked up, no location")
                       else:
                          print("{}: Colour --> Colour".format(spot['place']))
                          global_json['place']=spot['place']
                          global_json['change_to']= 1
                          print(global_json)
                          writeJSON()
                    elif json_list[0]['place'] == spot['place']:
                       # ID does not match but place is in our interest. Update the ID.
                       spot['id'] = json_list[0]['id']
                       print("{}: White --> Colour".format(spot['place']))
                       global_json['place']=spot['place']
                       global_json['change_to']=1
                       print(global_json)
                       writeJSON()

    def onDisconnect(self):
        print('disconnected')
        if reactor.running:
            reactor.stop()

def startWebsocket():
    load_places()
    host_name = '10.35.33.55'
    cert_path = False
    
    url = u'wss://{}/api/fleet/wamp/'.format(host_name)
    if cert_path:
        with open(cert_path) as cert_file:
            cert = ssl.Certificate.loadPEM(cert_file.read())
        cert_options = ssl.optionsForClientTLS(host_name, cert)
    else:
        # Warning: This disables SSL verifiation
        cert_options = ssl.CertificateOptions(verify=False)

    runner = ApplicationRunner(url, realm=u'default', ssl=cert_options)
    runner.run(Component)

# Write an outfile that indicates which place has changed to what state: 0 (cart to no-cart), 1 (no-chart to cart)
def writeJSON():
    with open('socket.json', 'w') as outfile:
        json.dump(global_json,outfile)

while True:
    startWebsocket()
    time.sleep(5)
