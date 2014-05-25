from django.http import HttpResponse
from dime_driver import DimeDriver
import os, json

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
        if not data.startswith('0x'):
            data = '0x' + data

        #TODO: functionalize this
        data = {'d':
                {'event' : 'smoke',
                 'value' : str(data),
                 'timestamp' : timestamp,
                 'device' : {'id' : device_id,
                             'type' : 'sigfox',
                             'version' : '0.1'},
                 'misc' : {'signal' : signal}
                }
               }
    else:
        raise NotImplementedException("GUOXI will implement this!")
        #TODO: set data, sensor_type, and device_id

    DimeDriver.publish("iot-1/d/%s/evt/%s/json" % (device_id, sensor_type), json.dumps(data))

    return HttpResponse(response, content_type="text/plain")
