#!/usr/bin/python
import math, random, json, time
import paho.mqtt.client as mqtt

TOPIC = "iot-1/d/demo/evt/alert"
eventTypes = [
  "smoke",
  "flood",
  "power loss"
]

responses = [
  "unconfirmed",
  "confirmed",
  "rejected"
]
persons = [
    {
        "name": "Charles Fracchia",
        "phone": "+1 (582) 653-8393",
        "email": "fracchia@mit.edu"
    },
    {
        "name": "Kyle Benson",
        "phone": "+1 (949) 619-9248",
        "email": "kyleedwardbenson@gmail.com"
    },
    {
        "name": "Shawnna Utzinger",
        "phone": "+1 (617) 253-0000",
        "email": "Shawnna@Utzinger.com"
    },
    {
        "name": "Melda Igo",
        "phone": "+1 (617) 253-0000",
        "email": "Melda@Igo.com"
    },
    {
        "name": "Latrisha Sabado",
        "phone": "+1 (617) 253-0000",
        "email": "Latrisha@Sabado.com"
    },
    {
        "name": "Kara Barrientez",
        "phone": "+1 (617) 253-0000",
        "email": "Kara@Barrientez.com"
    },
    {
        "name": "Maryjo Waggener",
        "phone": "+1 (617) 253-0000",
        "email": "Maryjo@Waggener.com"
    },
    {
        "name": "Aurore Phegley",
        "phone": "+1 (617) 253-0000",
        "email": "Aurore@Phegley.com"
    },
    {
        "name": "Emelia Hunt",
        "phone": "+1 (617) 253-0000",
        "email": "Emelia@Hunt.com"
    },
    {
        "name": "Virgilio Puglisi",
        "phone": "+1 (617) 253-0000",
        "email": "Virgilio@Puglisi.com"
    },
    {
        "name": "Xiomara Gagnon",
        "phone": "+1 (617) 253-0000",
        "email": "Xiomara@Gagnon.com"
    },
    {
        "name": "Lakeesha Wilcoxen",
        "phone": "+1 (617) 253-0000",
        "email": "Lakeesha@Wilcoxen.com"
    },
    {
        "name": "Deane Herrera",
        "phone": "+1 (617) 253-0000",
        "email": "Deane@Herrera.com"
    },
    {
        "name": "Garth Thon",
        "phone": "+1 (617) 253-0000",
        "email": "Garth@Thon.com"
    },
    {
        "name": "Denyse Laven",
        "phone": "+1 (617) 253-0000",
        "email": "Denyse@Laven.com"
    },
    {
        "name": "Keven Lukes",
        "phone": "+1 (617) 253-0000",
        "email": "Keven@Lukes.com"
    },
    {
        "name": "Ronni Rehn",
        "phone": "+1 (617) 253-0000",
        "email": "Ronni@Rehn.com"
    },
    {
        "name": "Laronda Wheaton",
        "phone": "+1 (617) 253-0000",
        "email": "Laronda@Wheaton.com"
    },
    {
        "name": "Leonardo Souliere",
        "phone": "+1 (617) 253-0000",
        "email": "Leonardo@Souliere.com"
    },
    {
        "name": "Anabel Seiler",
        "phone": "+1 (617) 253-0000",
        "email": "Anabel@Seiler.com"
    },
    {
        "name": "Elwanda Lollis",
        "phone": "+1 (617) 253-0000",
        "email": "Elwanda@Lollis.com"
    },
    {
        "name": "Arlena Fontanez",
        "phone": "+1 (617) 253-0000",
        "email": "Arlena@Fontanez.com"
    },
    {
        "name": "Twila Mayo",
        "phone": "+1 (617) 253-0000",
        "email": "Twila@Mayo.com"
    },
    {
        "name": "Arie Haverly",
        "phone": "+1 (617) 253-0000",
        "email": "Arie@Haverly.com"
    },
    {
        "name": "Eli Hagans",
        "phone": "+1 (617) 253-0000",
        "email": "Eli@Hagans.com"
    },
    {
        "name": "Gwen Magruder",
        "phone": "+1 (617) 253-0000",
        "email": "Gwen@Magruder.com"
    },
    {
        "name": "Jacquelin Sereno",
        "phone": "+1 (617) 253-0000",
        "email": "Jacquelin@Sereno.com"
    },
    {
        "name": "Savannah Outen",
        "phone": "+1 (617) 253-0000",
        "email": "Savannah@Outen.com"
    },
    {
        "name": "Coleman Gingras",
        "phone": "+1 (617) 253-0000",
        "email": "Coleman@Gingras.com"
    },
    {
        "name": "Analisa Pilon",
        "phone": "+1 (617) 253-0000",
        "email": "Analisa@Pilon.com"
    },
    {
        "name": "Oralia Durfey",
        "phone": "+1 (617) 253-0000",
        "email": "Oralia@Durfey.com"
    },
    {
        "name": "Lanny Craghead",
        "phone": "+1 (617) 253-0000",
        "email": "Lanny@Craghead.com"
    },
    {
        "name": "Maximo Edmisten",
        "phone": "+1 (617) 253-0000",
        "email": "Maximo@Edmisten.com"
    },
    {
        "name": "Freida Odom",
        "phone": "+1 (617) 253-0000",
        "email": "Freida@Odom.com"
    },
    {
        "name": "Luciano Burdine",
        "phone": "+1 (617) 253-0000",
        "email": "Luciano@Burdine.com"
    },
    {
        "name": "Mafalda Pickett",
        "phone": "+1 (617) 253-0000",
        "email": "Mafalda@Pickett.com"
    },
    {
        "name": "Elois Zollinger",
        "phone": "+1 (617) 253-0000",
        "email": "Elois@Zollinger.com"
    },
    {
        "name": "Everett Turnipseed",
        "phone": "+1 (617) 253-0000",
        "email": "Everett@Turnipseed.com"
    },
    {
        "name": "Arturo Warnick",
        "phone": "+1 (617) 253-0000",
        "email": "Arturo@Warnick.com"
    },
    {
        "name": "Daina Dziedzic",
        "phone": "+1 (617) 253-0000",
        "email": "Daina@Dziedzic.com"
    },
    {
        "name": "Deedra Coldwell",
        "phone": "+1 (617) 253-0000",
        "email": "Deedra@Coldwell.com"
    },
    {
        "name": "Keshia Overmyer",
        "phone": "+1 (617) 253-0000",
        "email": "Keshia@Overmyer.com"
    },
    {
        "name": "Olimpia Hose",
        "phone": "+1 (617) 253-0000",
        "email": "Olimpia@Hose.com"
    },
    {
        "name": "Narcisa Palko",
        "phone": "+1 (617) 253-0000",
        "email": "Narcisa@Palko.com"
    },
    {
        "name": "Albert Peirce",
        "phone": "+1 (617) 253-0000",
        "email": "Albert@Peirce.com"
    },
    {
        "name": "Lucile Capobianco",
        "phone": "+1 (617) 253-0000",
        "email": "Lucile@Capobianco.com"
    },
    {
        "name": "Jenae Baize",
        "phone": "+1 (617) 253-0000",
        "email": "Jenae@Baize.com"
    },
    {
        "name": "Bryanna Marin",
        "phone": "+1 (617) 253-0000",
        "email": "Bryanna@Marin.com"
    },
    {
        "name": "Les Fickes",
        "phone": "+1 (617) 253-0000",
        "email": "Les@Fickes.com"
    },
    {
        "name": "Meagan Paulk",
        "phone": "+1 (617) 253-0000",
        "email": "Meagan@Paulk.com"
    },
    {
        "name": "Josh Duppstadt",
        "phone": "+1 (617) 253-0000",
        "email": "Josh@Duppstadt.com"
    },
    {
        "name": "Clarita Counter",
        "phone": "+1 (617) 253-0000",
        "email": "Clarita@Counter.com"
    }
]

def on_connect(mosq, obj, rc):
  """docstring for on_connect"""
  pass
  print "Connected to MQTT broker !"

def on_disconnect(mosq, obj, rc):
  print("Disconnected from MQTT Broker !")

def on_message(mosq, obj, msg):
  """docstring for on_message"""
  pass
  print("Message received on topic "+msg.topic+" with QoS "+str(msg.qos)+" and payload "+msg.payload)

mqttc = mqtt.Client("python_sub")
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.connect("dime.smartamerica.io",1883,60)

i = 0
alertsSent = []
while i<15:
  person = persons[random.randrange(0,len(persons))]
  person['location'] = {
    "lat" : 39.070 + float(random.randrange(0,250))/1000,
    "lng" : -77.400 + float(random.randrange(0,330))/1000
  }
  alertJSON = {
    "d" : {
      "source_event" : random.randrange(0,1000),
      "response" : "unconfirmed",
      "event" : eventTypes[random.randrange(0,len(eventTypes))],
      "value" : "0x%s" % random.randrange(0,99),
      "person" : person
    }
  }
  alertsSent.append(alertJSON)
  print "Publishing: %s" % alertJSON
  mqttc.publish(TOPIC, json.dumps(alertJSON))
  i = i+1
  time.sleep(1)

time.sleep(10)
i = 0
while i<8:
  ranIndex = random.randrange(0,len(alertsSent))
  chosenAlert = alertsSent[ranIndex]
  print "Chosen Alert: %s" % chosenAlert
  chosenAlert['d']['response'] = responses[random.randrange(1,len(responses))]
  print "Sending new response: %s" % chosenAlert['d']['response']
  print "Publishing update: %s" % chosenAlert
  mqttc.publish(TOPIC, json.dumps(chosenAlert))
  alertsSent.pop(ranIndex)
  i=i+1
  time.sleep(random.randrange(3,12))

