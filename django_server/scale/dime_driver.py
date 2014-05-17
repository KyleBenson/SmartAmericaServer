import mosquitto


def on_disconnect(mosq, obj, rc):
    print("disconnected: " + str(rc))

def on_connect(mosq, obj, rc):
    #mosq.subscribe("$SYS/#", 0)
    print("rc: "+str(rc))

def on_message(mosq, obj, msg):
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

def on_publish(mosq, obj, mid):
    print("published: "+str(mid))

def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mosq, obj, level, string):
    print(string)

class DimeDriver:
    __instance = None

    def __init__(self):
        if DimeDriver.__instance is None:
            DimeDriver.__instance = mosquitto.Mosquitto("SmartAmericaSCALE")

            DimeDriver.__instance.on_message = on_message
            DimeDriver.__instance.on_connect = on_connect
            DimeDriver.__instance.on_disconnect = on_disconnect
            DimeDriver.__instance.on_publish = on_publish
            DimeDriver.__instance.on_subscribe = on_subscribe

            print 'connecting...'
            DimeDriver.__instance.connect("dime.smartamerica.io", 1883, 60)
            DimeDriver.__instance.subscribe("iot-1/d/+/evt/+/json", 0)
            print 'connected!'
            #DimeDriver.__instance.loop_forever()

    def publish(self, topic, payload):
        return DimeDriver.__instance.publish(topic, payload)

if __name__ == '__main__':
    driver = DimeDriver()
    driver.publish('iot-1/d/kyle/evt/test/json', 'blahblahpayload')

    driver = DimeDriver()
    driver.publish('iot-1/d/kyle2/evt/test/json', 'blahblahpayload')
