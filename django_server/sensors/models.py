from django.db import models
from model_utils.models import TimeStampedModel

class SensorReading(TimeStampedModel):
    class Meta:
        abstract = True

    self.sensor = sensor
    self.msg = msg
    self.priority = priority
