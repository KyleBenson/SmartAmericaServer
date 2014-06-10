import os
from django.db import models
from phone.models import Contact
from model_utils.models import TimeStampedModel
from json_field import JSONField
from django_twilio.client import twilio_client
from urllib import urlencode

#TODO: alert is overloaded, change to emergency?
EMERGENCY_EVENT = 'alert'

class Device(models.Model):
    """
    A device may be a physical sensor device, or it may be a unique
    virtual sensor, likely identified partly by the physical computer
    it lives on.
    """
    device_id = models.CharField(max_length=100, primary_key=True)
    contact = models.ManyToManyField(Contact, null=True)


class SensedEvent(TimeStampedModel):
    """
    A SensedEvent may be a raw sensor reading or it may be a more abstract
    event, e.g. fire, flood, etc.
    """
    #TODO:
    #class Meta:
        #abstract = True

    device = models.ForeignKey(Device)
    source_event = models.ForeignKey('self', null=True) # more abstract events (e.g. fire) derive from other events (e.g. smoke)
    event_type = models.CharField(max_length=100)
    #TODO: self.priority = priority
    data = JSONField()
    active = models.BooleanField(default=True)



class Alert(TimeStampedModel):

    """
    We send an alert message to possible victims due to a SensedEvent being escalated by the analytics engine.
    """

    source_event = models.ForeignKey(SensedEvent)
    contact = models.ForeignKey(Contact)
    response = models.CharField(max_length=20, default="unconfirmed") # unconfirmed, confirmed, rejected
    #TODO: how to handle multiple outstanding alerts?  multiple phone #'s?

    def send(self, msg):

        """
        Sends an alert message, using SMS or a phone call as per the Contact's
        preferenes, via Twilio for confirmation.
        """

        if self.contact.contact_preference == 'sms':
            # prompt for response if this alert is unconfirmed
            if self.response == 'unconfirmed':
                msg = msg + "  Respond with EMERGENCY for immediate assistance or OKAY to cancel this alert.",

            twilio_client.messages.create(to=self.contact.phone_number,
                                          body=msg,
                                          _from=os.environ.get("TWILIO_PHONE_NUMBER"))

        elif self.contact.contact_preference == 'phone':
            # they've already been notified of a confirmation on the phone
            # because that's how they confirmed it! same with rejection
            if self.response == 'confirmed' or self.response == 'rejected':
                return

            # phone starts talking too quickly, so add an additional greeting
            # to make the main message clearer
            msg = "This is an automated message from the Safe Community Alerting Network. " + msg

            twilio_client.calls.create(to=self.contact.phone_number,
                                       from_=os.environ.get("TWILIO_PHONE_NUMBER"),
                                       url=os.environ.get('URL_ROOT') + '/phone/alert?' + urlencode({'msg': msg}),
                                       method='GET',
                                       )
