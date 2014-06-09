from __future__ import absolute_import
from sensors.models import SensedEvent, Alert, EMERGENCY_EVENT
from phone.messages import ALERT_CONFIRMED_MESSAGE
from .celery import celery_engine
import scale
from datetime import datetime, timedelta
import numpy

# TODO: put these in some config file
# time to wait before checking if an event was confirmed before escalating
EVENT_CHECK_DELAY = 30
EVENT_ACTIVE_TIME = timedelta(seconds=30)
EVENT_DUPLICATE_TIME = timedelta(seconds=5)

# Celery wasn't running on BlueMix so we can deactivate it there
USING_CELERY = False

@celery_engine.task()
def deactivate_events():
    cutoff_time = datetime.now() - EVENT_ACTIVE_TIME
    SensedEvent.objects.filter(active=True,
                               modified__lte=cutoff_time).update(active=False)


def get_recent_events(event):
    return SensedEvent.objects.filter(
        device=event.device,
        event_type=event.event_type,
        active=True).exclude(pk=event.pk).order_by('-created')


def is_possible_fire(event):
    """
    check the voltage reading to determine if the alarm is going off
    """
    data = event.data['d']['value']
    # TODO: low battery warnings!
    FIRE_ALARM_VOLTAGE_THRESHOLD = 0x0200
    voltage_level = int(data, 0) # 0 says guess base of int

    # just use thresholding for demo device until we make some way of adding
    # fake data to make the stdev check work properly
    if event.device.device_id == 'demo':
        return voltage_level < FIRE_ALARM_VOLTAGE_THRESHOLD

    else:
        # if voltage is > 10 standard deviations from the norm, we assume the alarm
        # is going off
        recent_events = get_recent_events(event)[:10]
        data = numpy.array([int(ev.data['d']['value'], 0) for ev in recent_events])
        stdevs = abs(data.mean() - voltage_level) / data.std()
        return stdevs > 10


@celery_engine.task()
def smoke_analysis(event):

    if is_possible_fire(event):
        # Possible emergency, but check if this is a duplicate first, which is
        # defined as active and occurring within EVENT_DUPLICATE_TIME of another event
        # that would be considered an anomaly.  Note that this could theoretically extend
        # a cluster of events considered duplicates indefinitely, so we must choose this
        # constant carefully, especially for emergencies like FIRE that may be controlled,
        # dismissed, and then start up again within a short amount of time.

        # TODO: should we only look at events within EVENT_DUPLICATE_TIME of now?
        # Perhaps such a long-lived event should send another Alert if it's still active?

        recent_events = get_recent_events(event)

        # if we make it through without breaking, we found a huge cluster of one event
        # if the queryset was empty, this is clearly an original event!
        is_original = False if recent_events else True
        last_anomaly_time = event.created

        for revent in recent_events:
            if (last_anomaly_time - revent.created < EVENT_DUPLICATE_TIME) and is_possible_fire(revent):
                # not orignal event
                print("Not original event")
                break
            if last_anomaly_time - revent.created > EVENT_DUPLICATE_TIME:
                # stop looking as we've reached the end of the
                # possible anomaly cluster without finding other significant events
                is_original = True
                break
            if is_possible_fire(revent):
                # move the boundary of the cluster
                last_anomaly_time = revent.created

        if is_original:
            # this is the first event in recent history, publish the possible emergency
            event.event_type = 'fire'
            scale.DimeDriver.publish_event(event)

@celery_engine.task()
def check_alert_status(event):
    # TODO: take alerts as args instead of event?
    alerts = Alert.objects.filter(source_event__pk=event.pk)
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
    #TODO: functionalize these / make a new event type for "alert"?
    if event.data['d']['response'] == 'confirmed':
        msg = ALERT_CONFIRMED_MESSAGE
    elif event.data['d']['response'] == 'unconfirmed':
        #TODO: what's going on here?
        msg = ALERT_CONFIRMED_MESSAGE
    elif event.data['d']['response'] == 'rejected':
        return
        #msg = ALERT_REJECTED_MESSAGE

    # find all other alerts that stemmed from the source of this alert and notify contacts
    alerts = Alert.objects.filter(source_event__id=event.data['d']['source_event'])
    for alert in alerts:
        alert.send(msg)

@celery_engine.task()
def fire_analysis(event):
    """
    Send Alert messages to all Contacts associated with this event.
    """
    for contact in event.device.contact.all():
        alert = Alert.objects.create(source_event=event, contact=contact)
        #TODO: perhaps publish alert events and then contact via phone in response to that event?
        print("sending alert to %s" % contact.phone_number)
        alert.send("Possible fire detected in your home!")

    # if no one confirms or rejects fire event after some time, escalate and send emergency crew
    if USING_CELERY:
        check_alert_status.apply_async((event,), countdown=EVENT_CHECK_DELAY)
    else:
        import threading
        t = threading.Timer(EVENT_CHECK_DELAY, check_alert_status, args=[event])
        t.start()

def analyze(event):
    """
    Routes event analysis to their respective task queues for further processing.
    """
    #TODO: move to new celery task of its own
    #TODO: check for duplicates
    if EMERGENCY_EVENT in event.event_type:
        alert_analysis.delay(event) if USING_CELERY else alert_analysis(event)
    elif 'smoke' in event.event_type:
        smoke_analysis.delay(event) if USING_CELERY else smoke_analysis(event)
    elif 'fire' in event.event_type:
        fire_analysis.delay(event) if USING_CELERY else fire_analysis(event)

