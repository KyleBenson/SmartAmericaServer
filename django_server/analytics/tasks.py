from __future__ import absolute_import
from django_twilio.client import twilio_client
from sensors.models import SensedEvent, Device, Alert
from phone.views import ALERT_CONFIRMED_MESSAGE
import scale, os
from .celery import celery_engine

# time to wait before checking if an event was confirmed before escalating
# TODO: put in some config file
EVENT_CHECK_DELAY = 15

@celery_engine.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@celery_engine.task()
def smoke_analysis(event):
    event_type = event.event_type
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

    event.event_type = 'possible_fire'
    scale.DimeDriver.publish_event(event)

@celery_engine.task()
def check_event_status(event):
    alerts = Alert.objects.filter(source_event__id=event.id)
    is_rejected, is_confirmed = False, False
    for alert in alerts:
        if alert.response == 'confirmed':
            is_confirmed = True
        elif alert.response == 'rejected':
            is_rejected = True

    # escalate event if no one responds, already been escalated if it's confirmed
    if not is_confirmed and not is_rejected:
        for alert in alerts:
            message = twilio_client.messages.create(to=alert.contact.phone_number,
                                                    body=ALERT_CONFIRMED_MESSAGE,
                                                    _from=os.environ.get("TWILIO_PHONE_NUMBER"))
            #TODO: emergency_dispatch

def analyze(event):
    """
    Routes event analysis to their respective task queues for further processing.
    """
    #TODO: remove all possible/confirmed instances, that should be a field
    if 'smoke' in event.event_type:
        smoke_analysis(event)
    elif 'possible_fire' in event.event_type:
        #TODO: move to a celery task
        for contact in event.device.contact.all():
            Alert(source_event=event, contact=contact).save()
            message = twilio_client.messages.create(to=contact.phone_number,
                                                    body="Possible fire detected in your home!  Respond with EMERGENCY for immediate assistance or OKAY to cancel this alert.",
                                                    _from=os.environ.get("TWILIO_PHONE_NUMBER"))

        check_event_status.apply_async((event,), countdown=EVENT_CHECK_DELAY)

    elif 'blahblah' in event.event_type:
        event.event_type = 'confirmed_fire'
        scale.DimeDriver.publish_event(event)
        #TODO: confirm alert or escalate asynchronously
        #threading.Timer(interval, function, args=[], kwargs={})
