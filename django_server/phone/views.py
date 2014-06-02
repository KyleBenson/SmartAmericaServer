from django.http import HttpResponse
from twilio import twiml
from sensors.models import Alert, Device, SensedEvent, EMERGENCY_EVENT
from phone.models import Contact
from phone.messages import ALERT_CONFIRMED_MESSAGE, ALERT_REJECTED_MESSAGE
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import scale
import os

#TODO: clean up this rather ugly code and move the alerting logic outside the views

DEFAULT_RESPONSE_MESSAGE = "Thank you for contacting the Safe Community Alerting Network.  Everything seems fine."
NOT_REGISTERED_MESSAGE = "You are not currently registered with our database. Text REGISTER to this number to register."
REGISTERED_MESSAGE = "You are now registered in our database and will receive alerts if we detect a potential emergency in your home."
UNREGISTERED_MESSAGE = "Your contact information has been removed from the database.  Thank you for participating in this demo!"
ALREADY_REGISTERED_MESSAGE = "You are already registered in the database!"

def sms_handler(request):
    """Dispatches various other handlers based on some state associated with the
    incoming message's phone number.
    """

    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
    if request.method == 'POST':
        #TODO: get POST working! maybe @csrf_exempt?
        request_data = request.POST
    elif request.method == 'GET':
        request_data = request.GET
    else:
        request_data = {'From' : os.environ.get('PHONE_NUMBER'),
                        'Body' : 'auto-generated message, not POST or GET!'}

    contact_number = request_data['From']
    msg = request_data['Body'].lower()

    # if not None by the end of this handler, will respond with the given message
    response_message = None

    # first, see if this user is even in the database
    contact = None
    try:
        contact = Contact.objects.get(phone_number=contact_number)
    except ObjectDoesNotExist:
        response_message = NOT_REGISTERED_MESSAGE

    if 'subscribe' in msg or 'register' in msg:
        # extract contact's name from message
        contact_info = msg.replace('subscribe', '').replace('register','')
        try:
            first_name, last_name = contact_info.split()
        except ValueError:
            first_name = last_name = contact_info

        try:
            contact = Contact.objects.create(phone_number=contact_number, first_name=first_name.capitalize(), last_name=last_name.capitalize())
            # register this contact with the demo device for the sake of our demo
            dev = Device.objects.get(device_id='demo')
            dev.contact.add(contact)
            dev.save()
            response_message = REGISTERED_MESSAGE
        except IntegrityError:
            response_message = ALREADY_REGISTERED_MESSAGE
    # skip all the rest of these cases if the user isn't registered and didn't
    # request to be
    elif not contact:
        pass
    # handle (un)subscribing first
    elif 'demo' in msg:
        event = SensedEvent(event_type='smoke', device_id='demo',
                            data={'d' :
                                  {'event' : 'smoke',
                                   'value' : '0x0123'}
                                 })
        scale.DimeDriver.publish_event(event)
    elif 'unsubscribe' in msg or 'stop' in msg or 'unregister' in msg:
        try:
            contact = Contact.objects.get(phone_number=contact_number)
            contact.delete()
            response_message = UNREGISTERED_MESSAGE
        except ObjectDoesNotExist:
            response_message = NOT_REGISTERED_MESSAGE

    else:
        try:
            # try correlating contact number with an outstanding event
            #TODO: rather than assume an Alert is over when source event is inactive, perhaps we should have an explicit active field on the Alert itself?
            alert = Alert.objects.filter(contact__phone_number=contact_number,
                                         source_event__active=True).order_by('-created')[0]
            #TODO: handle responses after EmergencyEvent has been generated? cancelling, late confirmation, etc.
            if 'emergency' in msg:
                alert.response = 'confirmed' #TODO: functionalize
                alert.save()

                # If we've already created an EmergencyEvent associated with this alert,
                # perhaps from family member confirming the emergency already,
                # don't publish one again.
                if not SensedEvent.objects.filter(event_type=EMERGENCY_EVENT,
                                                  source_event=alert.source_event).exists():
                    scale.DimeDriver.publish_alert(alert)
                else:
                    response_message = "We've already received your response; " + ALERT_CONFIRMED_MESSAGE
            elif 'okay' in msg:
                alert.response = 'rejected' #TODO: same
                alert.save()
                response_message = ALERT_REJECTED_MESSAGE
                #TODO: eventually send WE'RE OKAY notifications?: scale.DimeDriver.publish_alert(alert)
            else:
                # not an alert-related message, throw to default
                raise IndexError
        except IndexError:
            response_message = DEFAULT_RESPONSE_MESSAGE + " Reply with UNREGISTER to remove your contact info."

    # respond with a message if applicable
    response = twiml.Response()
    if response_message is not None:
        response.sms(response_message, to=contact_number, sender=twilio_number)

    return HttpResponse(response)
