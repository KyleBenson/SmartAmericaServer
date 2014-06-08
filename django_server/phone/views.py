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

DEFAULT_GREETING = "Thank you for contacting the Safe Community Alerting Network."
DEFAULT_RESPONSE_MESSAGE = DEFAULT_GREETING + "  Everything seems fine."
NOT_REGISTERED_MESSAGE = "You are not currently registered with our database. Text REGISTER to this number to register."
REGISTERED_MESSAGE = "You are now registered in our database and will receive alerts if we detect a potential emergency in your home."
UNREGISTERED_MESSAGE = "Your contact information has been removed from the database.  Thank you for participating in this demo!"
ALREADY_REGISTERED_MESSAGE = "You are already registered in the database!"


def unregister(contact_number):
    """Unregister the contact with the given number by removing the entry from database"""

    try:
        contact = Contact.objects.get(phone_number=contact_number)
        contact.delete()
        return UNREGISTERED_MESSAGE
    except ObjectDoesNotExist:
        return NOT_REGISTERED_MESSAGE


def contact_preference_options_handler(request):
    """Handles gathered key from user calling to update contact method preference."""

    key_entered = request.GET['Digits']
    response = twiml.Response()

    try:
        contact = Contact.objects.get(phone_number = request.GET['From'])
    except ObjectDoesNotExist:
        response.say(NOT_REGISTERED_MESSAGE)
        return HttpResponse(response)

    response_message = "Your preferences have been updated"

    if key_entered == '1':
        contact.contact_preference = 'sms'
    elif key_entered == '2':
        contact.contact_preference = 'phone'
    else:
        response_message = "You've pressed an incorrect key"

    contact.save()

    response.say(response_message)

    return HttpResponse(response)


def main_menu_options_handler(request):
    key_entered = request.GET['Digits']
    response = twiml.Response()

    if key_entered == '1':
        response.dial(os.environ.get('EMERGENCY_CONTACT_NUMBER'))
    elif key_entered == '2':
        response.say(unregister(request.GET['From']))
    elif key_entered == '3':
        response.say("Press 1 to receive SMS text messages. Press 2 to receive phone calls.")
        response.gather(action='/phone/contact_preference_options',
                        method='GET',
                        numDigits=1,
                        timeout=15,
                        )
    else:
        response_message = "You've pressed an incorrect key"

    return HttpResponse(response)


def phone_call_handler(request):
    """Gives user menu choices for how to direct the call."""

    response = twiml.Response()

    MENU_OPTIONS = "Press 1 to speak with the SCALE coordinator about any questions or issues with SCALE devices. \
        Press 2 to unregister this number from the SCALE database. \
        Press 3 to set your contact method preferences."
    response.say(DEFAULT_GREETING + MENU_OPTIONS)
    response.gather(action='/phone/main_menu_options',
                    method='GET',
                    numDigits=1,
                    timeout=15,
                    )

    return HttpResponse(response)


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
        response_message = unregister(contact_number)

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
