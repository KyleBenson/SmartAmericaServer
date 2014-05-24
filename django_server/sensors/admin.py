from django.contrib import admin
from sensors import models

class SensedEventAdmin(admin.ModelAdmin):
    list_display = ('device', 'event_type', 'active')

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id',)

class AlertAdmin(admin.ModelAdmin):
    list_display = ('source_event', 'contact', 'response')

admin.site.register(models.SensedEvent, SensedEventAdmin)
admin.site.register(models.Device, DeviceAdmin)
admin.site.register(models.Alert, AlertAdmin)
