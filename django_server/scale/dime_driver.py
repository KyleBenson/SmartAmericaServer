import mosquitto, thread, time, os
from twilio.rest import TwilioRestClient

#BROKER_SERVER = "dime.smartamerica.io"
BROKER_SERVER = "m2m.eclipse.org"

class DimeDriver:
    """
    Module for encapsulating the MQTT client for publishing and subscribing.
    """

    _client_instance = None
    _client_looping = False

    @staticmethod
    def _on_message(mosq, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        #TODO: remove all possible/confirmed instances, that should be a field
        if 'smoke' in msg.topic:
            DimeDriver.publish(msg.topic.replace('smoke', 'possible_fire'), str(msg.payload))
        elif 'possible_fire' in msg.topic:
            client = TwilioRestClient()
            message = client.messages.create(to="+1%s" % os.environ.get("PHONE_NUMBER"), body="Possible fire detected in your home!  Respond with HELP for immediate assistance or OKAY to cancel this alert.", _from="+13024070223")
            DimeDriver.publish(msg.topic.replace('possible_fire', 'confirmed_fire'), str(msg.payload))

    @staticmethod
    def _on_disconnect(mosq, obj, rc):
        print("disconnected, rc: " + str(rc))
        DimeDriver._client_instance = None
        mosq.loop_stop()

    @staticmethod
    def _on_connect(mosq, obj, rc):
        #mosq.subscribe("$SYS/#", 0)
        print("connected, rc: "+str(rc))

    @staticmethod
    def _on_publish(mosq, obj, mid):
        print("published: "+str(mid))

    @staticmethod
    def _on_subscribe(mosq, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    @staticmethod
    def _on_log(mosq, obj, level, string):
        print(string)

    @staticmethod
    def publish(topic, payload):
        client = DimeDriver._get_client()
        ret = client.publish(topic, payload)
        #may have to disconnect and reconnect each time: DimeDriver._dispose_client(client)
        return ret

    @staticmethod
    def subscribe(topic="iot-1/d/+/evt/+/json", qos=0):
        client = DimeDriver._get_client()
        ret = client.subscribe(topic, qos)
        if not DimeDriver._client_looping:
            DimeDriver._client_looping = True
            client.loop_start()

    @staticmethod
    def _get_client():
        if DimeDriver._client_instance is None:
            print 'connecting...'
            DimeDriver._client_instance = mosquitto.Mosquitto("SmartAmericaSCALE" + str(time.time()))
            DimeDriver._client_instance.connect(BROKER_SERVER, 1883, 60)
            DimeDriver._client_instance.on_message = DimeDriver._on_message
            DimeDriver._client_instance.on_connect = DimeDriver._on_connect
            DimeDriver._client_instance.on_disconnect = DimeDriver._on_disconnect
            DimeDriver._client_instance.on_publish = DimeDriver._on_publish
            DimeDriver._client_instance.on_subscribe = DimeDriver._on_subscribe
        return DimeDriver._client_instance

    @staticmethod
    def _dispose_client(client):
        client.disconnect()
        #TODO: figure out why _on_disconnect doesn't get called!
        DimeDriver._client_looping = None
        DimeDriver._client_instance = None
        client.loop_stop()

if __name__ == '__main__':
    DimeDriver.subscribe('iot-1/d/kyle2/#')
    DimeDriver.subscribe('iot-1/d/7831c1d1c734/#')
    for i in range(10):
        DimeDriver.publish('iot-1/d/kyle2/evt/smoke/json', 'blahblahpayload %i' % i)

    #sleep for a bit to see messages show up before we quit
    time.sleep(10)