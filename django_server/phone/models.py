from django.db import models

class Contact(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50, unique=True)

    contact_preference = models.CharField(max_length=10, default='sms')

    def __str__(self):
        return self.phone_number
    #TODO: address for first responder
