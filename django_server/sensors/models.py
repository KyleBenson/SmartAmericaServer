from django.db import models
from phone.models import Contact
from model_utils.models import TimeStampedModel
from json_field import JSONField

class Device(models.Model):
    """
    A device may be a physical sensor device, or it may be a unique
    virtual sensor, likely identified partly by the physical computer
    it lives on.
    """
    device_id = models.CharField(max_length=100, primary_key=True)
    owner = models.ManyToManyField(Contact)

class SensedEvent(TimeStampedModel):
    """
    A SensedEvent may be a raw sensor reading or it may be a more abstract
    event, e.g. fire, flood, etc.
    """
    #TODO:
    #class Meta:
        #abstract = True

    device = models.ForeignKey(Device)
    type = models.CharField(max_length=100)
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
