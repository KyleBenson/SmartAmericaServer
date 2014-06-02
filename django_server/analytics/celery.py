from __future__ import absolute_import
import os
from datetime import timedelta

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scale.settings')
from django.conf import settings
from celery import Celery

celery_engine = Celery('analytics', broker=settings.BROKER_URL)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
celery_engine.config_from_object('django.conf:settings')
celery_engine.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

