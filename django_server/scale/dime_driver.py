import paho.mqtt.client as mqtt
import time
import simplejson as json
from django.core.exceptions import ObjectDoesNotExist
import sensors.models
# switch these lines to change brokers
#BROKER_SERVER = "m2m.eclipse.org"
#BROKER_SERVER = "dime.smartamerica.io"
BROKER_SERVER = "iqueue.ics.uci.edu"

class DimeDriver:
    """
    Module for encapsulating the MQTT client for publishing and subscribing.
    """

    _client_instance = None
    _client_looping = False

    @staticmethod
    def _on_message(mosq, obj, msg):
        # lazy imports to fix circular importing stuff
        import analytics.tasks

        #TODO: wrap in debug
        if 'test' in msg.topic or 'demo' in msg.topic:
            print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

        # extract event data
        event = msg.topic.split('/')
        try:
            device = sensors.models.Device.objects.get(device_id=event[2])
        except ObjectDoesNotExist:
            device = sensors.models.Device.objects.create(device_id=event[2])
        event_type = event[4]
        if event[5] != 'json':
            print('Unsupported payload format %s' % event[5])

        try:
            data = json.loads(str(msg.payload))
        except ValueError as e:
            print("ERROR parsing JSON payload: %s" % msg.payload)
            print(e)
            return

        try:
            source_event = sensors.models.SensedEvent.objects.get(pk=data['d']['source_event'])
        except:
            source_event = None

        #TODO: get from DB if already created?
        event = sensors.models.SensedEvent(device=device,
                                           event_type=event_type,
                                           data=data,
                                           source_event=source_event)

        #TODO: remove this when we keep DB clean
        if 'demo' in msg.topic or 'explosive_gas' in msg.topic:
            event.save()
        analytics.tasks.analyze(event)

    @staticmethod
    def _on_disconnect(mosq, obj, rc):
        print("disconnected, rc: " + str(rc))

        # theoretically, Paho will handle reconnecting...
        #DimeDriver._client_instance = None
        #mosq.loop_stop()
        #DimeDriver._client_looping = False
        ## reconnect and subscribe again
        #rc = DimeDriver.subscribe()
        #print("reconnecting: " + str(rc))

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
        if not ret:
            print("Publishing error: %d" % ret)
        return ret

    @staticmethod
    def publish_event(event):
        DimeDriver.publish("iot-1/d/%s/evt/%s/json" % (event.device_id, event.event_type), json.dumps(event.data))

    @staticmethod
    def publish_alert(alert):
        """
        Converts an Alert object into a SensedEvent message since that's the unified interface
        for publishing messages via DIME
        """
        #TODO: combine with publish_event since Alert should be a Child class of SensedEvent
        event = alert.source_event
        data = event.data
        #TODO: handle this via model field
        data['d']['source_event'] = event.pk
        data['d']['response'] = alert.response
        #TODO: escalated status?
        #TODO: contact?

        event.event_type = sensors.models.EMERGENCY_EVENT
        event.data = data

        DimeDriver.publish_event(event)

    @staticmethod
    def subscribe(topic="iot-1/d/+/evt/+/json", qos=0):
        client = DimeDriver._get_client()
        ret = client.subscribe(topic, qos)
        if not DimeDriver._client_looping:
            DimeDriver._client_looping = True
            client.loop_start()
        return ret

    @staticmethod
    def _get_client():
        if DimeDriver._client_instance is None:
            #DimeDriver._client_instance = mosquitto.Mosquitto()
            DimeDriver._client_instance = mqtt.Client()
            DimeDriver._client_instance.on_message = DimeDriver._on_message
            DimeDriver._client_instance.on_connect = DimeDriver._on_connect
            DimeDriver._client_instance.on_disconnect = DimeDriver._on_disconnect
            DimeDriver._client_instance.on_publish = DimeDriver._on_publish
            DimeDriver._client_instance.on_subscribe = DimeDriver._on_subscribe
            print 'connecting... %d' % DimeDriver._client_instance.connect(BROKER_SERVER, 1883, 60)
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
    import sys
    print 'args:', sys.argv

    for i in range(10):
        DimeDriver.publish('iot-1/d/kyle2/evt/smoke/json', 'blahblahpayload %i' % i)

    #sleep for a bit to see messages show up before we quit
    time.sleep(10)
