import mosquitto, thread, time
import sensors
from analytics import tasks
from django.core.exceptions import ObjectDoesNotExist
# switch these lines to change brokers
BROKER_SERVER = "m2m.eclipse.org"
BROKER_SERVER = "dime.smartamerica.io"

class DimeDriver:
    """
    Module for encapsulating the MQTT client for publishing and subscribing.
    """

    _client_instance = None
    _client_looping = False

    @staticmethod
    def _on_message(mosq, obj, msg):
        #TODO: wrap in debug
        if 'test' in msg.topic or 'demo' in msg.topic:
            print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        event = msg.topic.split('/')
        #TODO: create if not exists
        try:
            device = sensors.models.Device.objects.get(device_id=event[2])
        except ObjectDoesNotExist:
            device = sensors.models.Device(device_id=event[2])
            device.save()
        event_type = event[4]
        if event[5] != 'json':
            print('Unsupported payload format %s' % event[5])
        event = sensors.models.SensedEvent(device=device, event_type=event_type, data=str(msg.payload))
        event.save()
        tasks.analyze(event)

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
        print("Log:  %s" % string)

    @staticmethod
    def publish(topic, payload):
        client = DimeDriver._get_client()
        ret = client.publish(topic, payload)
        #may have to disconnect and reconnect each time: DimeDriver._dispose_client(client)
        return ret

    @staticmethod
    def publish_event(event):
        DimeDriver.publish("iot-1/d/%s/evt/%s/json" % (event.device_id, event.event_type), event.data)

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
            DimeDriver._client_instance = mosquitto.Mosquitto()
            print 'connecting... %d' % DimeDriver._client_instance.connect(BROKER_SERVER, 1883, 60)
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
    #DimeDriver.subscribe('iot-1/d/kyle2/#')
    #DimeDriver.subscribe('iot-1/d/7831c1d1c734/#')
    for i in range(10):
        DimeDriver.publish('iot-1/d/kyle2/evt/smoke/json', 'blahblahpayload %i' % i)

    #sleep for a bit to see messages show up before we quit
    time.sleep(10)
