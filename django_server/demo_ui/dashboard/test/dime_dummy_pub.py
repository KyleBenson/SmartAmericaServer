import mosquitto
import random
import json
import time
from mosquitto import Mosquitto

dev_types = ['SheevaPlug','raspi']

events = ["SCALE_cold_temp_Sheeva",
	"SCALE_high_heat_Sheeva",
	"SCALE_potentialfire _Sheeva",
	"SCALE_small_shake_Sheeva",
	"SCALE_large_shake_Sheeva",
	"SCALE_small_aftershock_Sheeva",
	"SCALE_large_aftershock_Sheeva",
	"SCALE_gas_detected_RPi",
	"SCALE_dark_environment_RPi",
	"SCALE_motion_detected_RPi"]



def random_mac_address():
	mac = [ 0x00, 0x16, 0x3e,
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0xff),
		random.randint(0x00, 0xff) ]
	return ''.join(map(lambda x: "%02x" % x, mac))

def random_dev_type():
	dev_type = random.choice(dev_types)
	return dev_type

def random_position():
	lat = random.uniform(0, 90)
	lon = random.uniform(0, 180)

	pos = [lat, lon]

	return pos

def random_event():
	event = random.choice(events)

	return event

def random_priority():
	return random.randint(0, 15)

def random_topic():
	mac_address = random_mac_address()
	dev_type = random_dev_type()

	topic = "iot/d/" + mac_address + "/evt/" + dev_type + "/json"

	return topic

def random_message():
	msg_map = {}
	msg_map["event"] = random_event()
	msg_map["timestamp"] = time.time()
	
	pos_map = {}
	random_pos = random_position()
	pos_map["lat"] = str(random_pos[0])
	pos_map["lon"] = str(random_pos[1])
	
	msg_map["position"] = pos_map
	msg_map["prio_value"] = random_priority()

	if msg_map["prio_value"] < 4:
		msg_map["prio_class"] = "high"
	elif msg_map["prio_value"] > 7:
		msg_map["prio_class"] = "low"
	else:
		msg_map["prio_class"] = "medium"

	return json.dumps({"d": msg_map})

client = mosquitto.Mosquitto("Dummy Client")
client.connect("dime.smartamerica.io",1883,60)

client.loop()

while True:
	topic = random_topic()
	message = random_message()

	client.publish(topic, message, 1)

	print topic
	print message

	time.sleep(2)
