from django.http import HttpResponse
from dime_driver import DimeDriver
import os, json, ctypes
from django.http import Http404

def sigfox(request):
    device_id = request.GET.get("id")
    timestamp = request.GET.get("time")
    data = request.GET.get("key1")
    signal = request.GET.get("key2")
    response = "your data from device %s at time %s is %s with strength %s" % (device_id, timestamp, data, signal)

    # the hacked smoke sensor only ever sends 4 hex digits
    # TODO: make that arduino program conform to our binary representation
    if len(data) < 7:
        sensor_type = 'smoke'
        # need to get in hex form first...
        # TODO: make smoke sensing system work with decimal values
        if not data.startswith('0x'):
            data = '0x' + str(data)

        event_type_original = 'smoke'
        value_original = data
        priority_original = 10

    else:
        #Divided Sigfox Message data into Segments
        event_type_encoded = data[0:2]
        vd_encoded = data[2:6]
        value_encoded = data[6:22]
        priority_encoded = data[22]
        cb_encoded = data[23]

        # 1. Decode Type
        dirname, filename = os.path.split(os.path.abspath(__file__))
        type_file = open(dirname+"/"+"event_type_server.json", "rt")
        type_stream = type_file.read()
        type_info = json.loads(type_stream)

        try:
            event_type_original = type_info[event_type_encoded]
        except KeyError:
            print "Unknown Event Code: " + event_type_encoded
            # TODO: return 404 error
            raise Http404

        # 2. Decode Value Descriptor

        # 3. Decode Value
        value_1 = value_encoded[0:8]
        value_original = str(ctypes.c_float.from_buffer(ctypes.c_int(int(value_1,16))).value)

        # 4. Decode Priority
        priority_original = str(int(priority_encoded, 16))

        # 5. Decode Control Bits
        #TODO:

    # Generate JSON data
    #TODO: functionalize this
    data = {'d' :
            {'event' : event_type_original,
             'value' : value_original,
             'prio_value' : priority_original,
             'timestamp' : timestamp,
             'device' : {'id' : device_id,
                         'type' : 'sigfox',
                         'version' : '0.1'},
             'misc' : {'signal' : signal}
             }
            }

    DimeDriver.publish("iot-1/d/%s/evt/%s/json" % (device_id, event_type_original), json.dumps(data))

    return HttpResponse(response, content_type="text/plain")
