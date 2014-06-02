#!/bin/sh
/home/webapp/.env/eventEnv/bin/python /home/webapp/src/event/manage.py syncdb --migrate --noinput --settings=local_settings.testserver
