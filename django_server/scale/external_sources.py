from django.http import HttpResponse
from dime_driver import DimeDriver
import os, json, ctypes
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def sigfox(request):
    device_id = request.GET.get("id")
    timestamp = float(request.GET.get("time"))
    data = request.GET.get("data")
    signal = float(request.GET.get("snr"))
    response = "Your data from device %s at time %f is %s with strength %f" % (device_id, timestamp, data, signal)

    # the hacked smoke sensor only ever sends 4 hex digits
    #TODO: make that arduino program conform to our binary representation
    if len(data) < 7: #XXX
        sensor_type = 'smoke'
        # need to get in hex form first...
        #TODO: make smoke sensing system work with decimal values
        if not data.startswith('0x'):
            data = '0x' + str(data)

        event_type_original = sensor_type
        value_original = data
        priority_original = 10

    else:
        # Divided Sigfox message data into segments
        event_type_encoded = data[0:2]
        vd_encoded = data[2:6]
        value_encoded = data[6:22]
        priority_encoded = data[22]
        cb_encoded = data[23]

        # 1. Decode Type
        dirname, filename = os.path.split(os.path.abspath(__file__))
        type_file = open(dirname+"/"+"sigfox_event_types_server.json", "rt")
        type_stream = type_file.read()
        type_info = json.loads(type_stream)

        try:
            event_type_original = type_info[event_type_encoded]
        except KeyError:
            print "Unknown event: " + event_type_encoded
            raise Http404

        # 2. Decode Value Descriptor
        #TODO: not implemented on client

        # 3. Decode Value
        if event_type_original == "temperature" or event_type_original == "temperature_high":
            value_1 = value_encoded[0:8]
            value_original = round(ctypes.c_float.from_buffer(ctypes.c_int(int(value_1, 16))).value, 2)
        elif event_type_original == "explosive_gas":
            value_1 = value_encoded[0:4]
            value_original = int(value_1, 16)
        else:
            value_original = None

        # 4. Decode Priority
        priority_original = int(priority_encoded, 16)

        # 5. Decode Control Bits
        #TODO: not implemented on clinet

    # Generate JSON data
    #XXX: functionalize this
    priority_class = None
    if priority_original >= 0 and priority_original < 4:
        priority_class = "high"
    elif priority_original >=7 and priority_original <= 10:
        priority_class = "low"
    elif priority_original >=4 and priority_original < 7:
        priority_class = "medium"
    data = {'d': {
            'event': event_type_original,
            'value': value_original,
            'prio_value': priority_original,
            'prio_class': priority_class,
            'timestamp': timestamp,
            #'device': {'id': device_id,
            #           'type': 'sigfox',
            #           'version': '0.1'},
            'misc': {'snr': signal}
        }}

    DimeDriver.publish("iot-1/d/sigfox00%s/evt/%s/json" % (device_id, event_type_original), json.dumps(data))

    return HttpResponse(response, content_type="text/plain")

@csrf_exempt
def senseware(request):
    """
    Receives data packets from Senseware modules and republishes them via MQTT.
    They come in as POST objects containing JSON that looks like:
    { "data" : [
        { "pkt" : x,
         "raw": x,
         "ts": x,
         "value": x
         },
        { "pkt" : y,
         "raw": y,
         "ts": y,
         "value": y,
         }
    ],
        "location" : "x",
        "mod" : x,
        "pos" : x,
        "sid" : x,
        "site" : "x",
        "sn" : "x",
        "type" : "x",
        "transform" : "x",
        "ts": x,
        "unit" : "x",
        "subscription_id": "x"
    }
    """

    dict_data = json.loads(request.body)
    nreadings = 0

    # Senseware packet may contain multiple readings (several samples per
    # time period), so run through each of them and publish
    # a SensedEvent to MQTT for each.
    for sensed_data in dict_data['data']:
        # Generate JSON data
        priority = 5 # TODO: configurable?
        device_id = dict_data['sid']
        event_type = dict_data['type']
        #TODO: functionalize this
        data = {'d' :
                {'event' : event_type,
                 'value' : sensed_data['value'],
                 'prio_value' : priority,
                 'timestamp' : sensed_data['ts'],
                 'device' : {'id' : device_id,
                             'type' : 'senseware',
                             'version' : '1.0'},
                 # TODO: misc
                 }
                }

        DimeDriver.publish("iot-1/d/%s/evt/%s/json" % (device_id, event_type),
                           json.dumps(data))

        nreadings += 1

    response = "received %d sensor readings at time %d" % (nreadings, dict_data['ts'])
    return HttpResponse(response, content_type="text/plain")

