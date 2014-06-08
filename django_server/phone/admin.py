from django.contrib import admin
from phone import models

class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'contact_preference')

admin.site.register(models.Contact, ContactAdmin)
