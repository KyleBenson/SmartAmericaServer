from django.http import HttpResponse
from twilio import twiml
import os

def sms_handler(request):
    """Dispatches various other handlers based on some state associated with the
    incoming message's phone number.
    """

    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
    if request.method == 'POST':
        dest = request.POST['From']
    elif request.method == 'GET':
        dest = request.GET['From']
    else:
        dest = sender

    response = twiml.Response()
    response.sms("Thank you for contacting SmartAmerica via Twilio!", to=dest, sender=twilio_number)
    return HttpResponse(response)
