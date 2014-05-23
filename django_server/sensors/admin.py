from django.contrib import admin
from sensors import models

admin.site.register(models.SensedEvent)
admin.site.register(models.Device)
admin.site.register(models.Alert)
