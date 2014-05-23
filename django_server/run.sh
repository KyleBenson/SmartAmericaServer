#!/bin/bash
python manage.py syncdb --noinput

celery -A analytics worker -l debug --detach --logfile=celery.log

# get web server port from environment if using BlueMix, otherwise specify it directly
if [ -z "$VCAP_APP_PORT" ];
then SRV_PORT=8080;
else SRV_PORT="$VCAP_APP_PORT";
fi
echo port is $SRV_PORT
python manage.py runserver --noreload 0.0.0.0:$SRV_PORT

if [ -f "celeryd.pid" ];
then kill -9 `cat celeryd.pid` && rm celeryd.pid;
fi
