#!/bin/bash
python manage.py syncdb --noinput

# start celery worker node and beat for periodic tasks
rm celery.log 2> /dev/null
celery -A analytics worker -l debug --detach --logfile=celery.log --pidfile=celery_worker.pid
celery -A analytics beat --logfile=celery_beat.log --pidfile=celery_beat.pid --detach

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
