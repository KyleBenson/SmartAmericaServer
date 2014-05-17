from django.http import HttpResponse
from dime_driver import DimeDriver
import os, json

def sigfox(request):
    device_id = request.GET.get("id")
    timestamp = request.GET.get("time")
    data = request.GET.get("key1")
    signal = request.GET.get("key2")
    response = "your data from device %s at time %s is %s with strength %s" % (device_id, timestamp, data, signal)

    driver = DimeDriver()
    sensor_type = 'smoke'
    print data
    driver.publish("iot-1/d/%s/evt/%s/json" % (device_id, sensor_type), str(data))

    return HttpResponse(response, content_type="text/plain")
