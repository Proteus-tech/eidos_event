# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import simplejson
import redis
from redis.exceptions import ConnectionError
from celery import execute

from django.conf import settings

import logging
logger = logging.getLogger(__name__)

def emit_to_channel(channel, event, *data):
    connection_kwargs = getattr(settings, 'WEBSOCKET_REDIS_BROKER', {})
    lower_connection_kwargs = (connection_kwargs and dict((k.lower(), v) for k,v in connection_kwargs.iteritems())) or connection_kwargs
    r = redis.Redis(**lower_connection_kwargs)
    args = [channel] + list(data)
    try:
        r.publish('socketio_%s' % channel, simplejson.dumps({'name': event, 'args': args}))
    except ConnectionError:
        # in case we don't have redis running
        logger.error('Redis does not seem to be running')

def add_event_task(event):
    try:
        execute.send_task('tasks.tasks.process_event', args=[event], expires=datetime.now()+timedelta(seconds=3), retry_policy={
            'max_retries': -1,
            'interval_start': 0,
            'interval_step': 0.01,
            'interval_max': 0.01,
            })
    except ConnectionError:
        # in case we don't have redis running
        logger.error('Redis does not seem to be running')

def after_event_save(sender, instance, created, **kwargs):
    if created:
        emit_to_channel(instance.project, 'new_event', instance.created_by, instance.serialize())
        add_event_task(instance)