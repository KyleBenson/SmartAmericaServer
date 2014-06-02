#!/bin/bash
python manage.py syncdb --noinput

# start celery worker node and beat for periodic tasks
#TODO: move celery startup to do this in python so it isn't so ugly
#here we have to pull the broker URL out of Django's settings with some ugly scripting
AMQP_BROKER=`echo "from django.conf import settings
print settings.BROKER_URL" | ./manage.py shell | awk '{print $3}'`

rm celery.log 2> /dev/null
#celery -A analytics worker -l debug --detach --logfile=celery.log --pidfile=celery_worker.pid -b "$AMQP_BROKER"
#celery -A analytics beat --logfile=celery_beat.log --pidfile=celery_beat.pid --detach -b "$AMQP_BROKER"

# get web server port from environment if using BlueMix, otherwise specify it directly
if [ -z "$VCAP_APP_PORT" ];
then SRV_PORT=8080;
else SRV_PORT="$VCAP_APP_PORT";
fi
echo port is $SRV_PORT
python manage.py runserver --noreload 0.0.0.0:$SRV_PORT

if [ -f "celery_worker.pid" ];
then kill -9 `cat celery_worker.pid` && rm celery_worker.pid;
fi

if [ -f "celery_beat.pid" ];
then kill -9 `cat celery_beat.pid` && rm celery_beat.pid;
fi
