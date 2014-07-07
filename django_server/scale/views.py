from django.http import HttpResponse
import pprint
import os, yaml
from dime_driver import DimeDriver
from sensors.models import SensedEvent
import time
import subprocess

def print_environment(request):
    response = "Your environment contains:\n"
    env = os.environ
    # the VCAP_APPLICATION variable is a serialized string, so parse with YAML
    # rather than JSON, which will produce unicode strings with ugly u's'
    env = {k:(v if k not in ['VCAP_APPLICATION', 'VCAP_SERVICES'] else yaml.load(v)) for k,v in env.items()}
    # use width=1 to put each variable on a different line
    response += pprint.pformat(env, width=1)
    return HttpResponse(response, content_type="text/plain")

def run_demo(request):
    try:
        event_type = request.GET['event']
    except KeyError:
        event_type = 'smoke'
    try:
        data = request.GET['data']
    except KeyError:
        data = {'d' :
                {'value' : '0x0123',
                 'event' : event_type,
                 'timestamp': time.time(),
                }
               }

    event = SensedEvent(event_type=event_type, device_id='demo', data=data)
    DimeDriver.publish_event(event)
    return HttpResponse('demo for event %s started' % event_type, content_type="text/plain")

def run_dashboard_demo(request):
    subprocess.call('python scale/dashboard_demo.py', shell=True)
    return HttpResponse('dashboard demo started. Go to http://smartamerica.biobright.org/alerts to view it', content_type="text/plain")
