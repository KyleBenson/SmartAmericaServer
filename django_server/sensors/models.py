from django.db import models
from phone.models import Contact
from model_utils.models import TimeStampedModel
from json_field import JSONField

class Device(models.Model):
    device_id = models.CharField(max_length=100)
    owner = models.ForeignKey(Contact)

class SensedEvent(TimeStampedModel):
    #TODO:
    #class Meta:
        #abstract = True

    device = models.ForeignKey(Device)
    event_type = models.CharField(max_length=100)
    #TODO: self.priority = priority
    data = JSONField()
