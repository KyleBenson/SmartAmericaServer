from __future__ import absolute_import
from django_twilio.client import twilio_client
from sensors.models import SensedEvent, Device, Alert
import scale, os
from .celery import celery_engine

@celery_engine.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@celery_engine.task()
def smoke_analysis(event):
    event_type = event.type
    data = event.data
    # ignore regular intervals for now
    # TODO: low battery warnings!
    FIRE_ALARM_VOLTAGE_THRESHOLD = 0x0200
    voltage_level = data
    if not voltage_level.startswith('0x'):
        voltage_level = '0x' + voltage_level
        voltage_level = int(voltage_level, 0) #0 says guess base of int
    if voltage_level > FIRE_ALARM_VOLTAGE_THRESHOLD:
        # not a fire
        return

    event.type = 'possible_fire'
    scale.dime_driver.DimeDriver.publish_event(event)

def analyze(event):
    """
    Routes event analysis to their respective task queues for further processing.
    """
    #TODO: remove all possible/confirmed instances, that should be a field
    if 'smoke' in event.type:
        smoke_analysis(event)
    elif 'possible_fire' in event.type:
        for contact in event.device.owner.all():
            Alert(source_event=event, contact=contact).save()
            message = twilio_client.messages.create(to=contact.phone_number,
                                                    body="Possible fire detected in your home!  Respond with EMERGENCY for immediate assistance or OKAY to cancel this alert.",
                                                    _from=os.environ.get("TWILIO_PHONE_NUMBER"))

    elif 'blahblah' in event.type:
        event.type = 'confirmed_fire'
        scale.dime_driver.DimeDriver.publish_event(event)
        #TODO: confirm alert or escalate asynchronously
        #threading.Timer(interval, function, args=[], kwargs={})
