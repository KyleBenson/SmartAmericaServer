from django_twilio.client import twilio_client
from sensors.models import SensedEvent
import scale, os

def analyze(event):
    #TODO: route to other handlers
    #TODO: remove all possible/confirmed instances, that should be a field
    event_type = event.type
    data = event.data
    if 'smoke' in event_type:
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
    elif 'possible_fire' in event_type:
        #TODO: allow use of phrase help
        message = twilio_client.messages.create(to=os.environ.get("PHONE_NUMBER"), body="Possible fire detected in your home!  Respond with EMERGENCY for immediate assistance or OKAY to cancel this alert.", _from=os.environ.get("TWILIO_PHONE_NUMBER"))
        event.type = 'confirmed_fire'
        scale.dime_driver.DimeDriver.publish_event(event)
        #TODO: confirm alert or escalate asynchronously
        #threading.Timer(interval, function, args=[], kwargs={})
