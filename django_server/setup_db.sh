#!/bin/bash
python manage.py syncdb --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('vagrant', 'vagrant@example.com', 'vagrant')" | ./manage.py shell