from __future__ import absolute_import
from sensors.models import SensedEvent, Device, Alert
from .celery import celery_engine
import scale, os
from datetime import datetime, timedelta

# time to wait before checking if an event was confirmed before escalating
# TODO: put in some config file
EVENT_CHECK_DELAY = 15

# messages to send in response to alerts
#TODO: move elsewhere
ALERT_REJECTED_MESSAGE = "Glad to hear you are okay.  This alert has been canceled; have a nice day!"
ALERT_CONFIRMED_MESSAGE = "Emergency personnel are being dispatched to your house!"
EVENT_ACTIVE_TIME = timedelta(seconds=60)

@celery_engine.task()
def deactivate_events():
    cutoff_time = datetime.now() - EVENT_ACTIVE_TIME
    SensedEvent.objects.filter(active=True, modified__lte=cutoff_time).update(active=False)

@celery_engine.task()
def smoke_analysis(event):
    event_type = event.event_type
    print(event.data)
    data = event.data['d']['value']
    # ignore regular intervals for now

    # check the voltage reading to determine if the alarm is going off
    # TODO: low battery warnings!
    FIRE_ALARM_VOLTAGE_THRESHOLD = 0x0200
    voltage_level = int(data, 0) #0 says guess base of int
    if voltage_level < FIRE_ALARM_VOLTAGE_THRESHOLD:
        event.event_type = 'fire'
        scale.DimeDriver.publish_event(event)

@celery_engine.task()
def check_alert_status(event):
    #TODO: take alerts as args instead of event?
    alerts = Alert.objects.filter(source_event__id=event.id)
    is_rejected, is_confirmed = False, False
    for alert in alerts:
        if alert.response == 'confirmed':
            is_confirmed = True
        elif alert.response == 'rejected':
            is_rejected = True

    # escalate event if no one responded, already been escalated if it's confirmed
    if not is_confirmed and not is_rejected:
        #TODO: set details related to dispatch
        scale.DimeDriver.publish_alert(alerts[0])

@celery_engine.task()
def alert_analysis(event):
    """
    Sends messages to all Contacts associated with this alert event.
    """
    #TODO: handle ESCALATED
    if event.data['d']['response'] == 'confirmed':
        msg = ALERT_CONFIRMED_MESSAGE
    elif event.data['d']['response'] == 'unconfirmed':
        msg = ALERT_CONFIRMED_MESSAGE
    elif event.data['d']['response'] == 'rejected':
        msg = ALERT_REJECTED_MESSAGE

    # find all other alerts that stemmed from the source of this alert and notify contacts
    alerts = Alert.objects.filter(source_event__id=event.data['d']['source_event'])
    for alert in alerts:
        alert.send(msg)

@celery_engine.task()
def fire_analysis(event):
    """
    Send Alert messages to all Contacts associated with this event.
    """
    print("FIRE!!!")
    for contact in event.device.contact.all():
        alert = Alert.objects.create(source_event=event, contact=contact)
        #TODO: perhaps publish alert events and then contact via phone in response to that event?
        alert.send("Possible fire detected in your home!  Respond with EMERGENCY for immediate assistance or OKAY to cancel this alert.")

    # if no one confirms or rejects fire event after some time, escalate and send emergency crew
    check_alert_status.apply_async((event,), countdown=EVENT_CHECK_DELAY)

def analyze(event):
    """
    Routes event analysis to their respective task queues for further processing.
    """
    #TODO: move to new celery task of its own
    #TODO: check for duplicates
    if 'alert' in event.event_type:
        #TODO: alert is overloaded, change to emergency?
        alert_analysis.delay(event)
    elif 'smoke' in event.event_type:
        smoke_analysis.delay(event)
    elif 'fire' in event.event_type:
        fire_analysis.delay(event)

