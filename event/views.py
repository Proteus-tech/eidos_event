from django.db.models import signals
from datetime import datetime
from django.http import HttpResponse
from django.conf import settings
from django_request_local.middleware import RequestLocal
from djangorestframework import status
from djangorestframework.views import ListModelView, View
from djangorestframework.response import ErrorResponse
from djangorestframework.renderers import TemplateRenderer
from auth_client.permissions import IsAuthenticated

from event.models import Event as Event
from event.resources import EventResource

import simplejson

import logging
logger = logging.getLogger(__name__)

class EventListView(ListModelView):
    permissions = (IsAuthenticated,)
    resource = EventResource

    def get_filter_kwargs(self, request, **kwargs):
        is_get_story_list = True

        try:
            story_list = request.META['HTTP_X_RESOURCE_IN']
        except KeyError :
            is_get_story_list = False

        get_params = request.GET

        if  not len(get_params) and not is_get_story_list:
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'You must pass in a filter.')
        filter_kwargs = kwargs.copy()
        if is_get_story_list:
            story_list = simplejson.loads(story_list)
            filter_kwargs.update({'resource__in':story_list})
        if len(get_params):
            for key, value in get_params.items():
                if key.startswith('created_on__'):
                    # convert datetime to database format
                    value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
                filter_kwargs.update({key:value})
        return filter_kwargs

    def get(self, request, *args, **kwargs):
        filter_kwargs = self.get_filter_kwargs(request, **kwargs)
        return super(EventListView, self).get(request, *args, **filter_kwargs)

from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from socketio import socketio_manage
from event.utils import redis_connection
import simplejson
from redis.exceptions import ConnectionError
from celery import execute

import redis
def emit_to_channel(channel, event, *data):
    connection_kwargs = getattr(settings, 'WEBSOCKET_REDIS_BROKER', {})
    lower_connection_kwargs = (connection_kwargs and dict((k.lower(), v) for k,v in connection_kwargs.iteritems())) or connection_kwargs
    r = redis.Redis(**lower_connection_kwargs)
    args = [channel] + list(data)
    try:
        r.publish('socketio_%s' % channel, simplejson.dumps({'name': event, 'args': args}))
    except ConnectionError:
        # in case we don't have redis running
        logger.warning('Redis does not seem to be running')

def add_event_task(event):
    request = RequestLocal.get_current_request()
    user = request and request.user
    cookies = request and request.COOKIES
    #execute.send_task(taskname, arguments, kwargs={}, countdown, expires,...)
    execute.send_task('tasks.tasks.process_event', args=[event, user, cookies])


class EventUpdatesNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    def listener(self, room):
        # ``redis_connection()`` is an utility function that returns a redis connection from a pool
        r = redis_connection().pubsub()
        r.subscribe('socketio_%s' % room)

        for m in r.listen():
            if m['type'] == 'message':
                data = simplejson.loads(m['data'])
                self.process_event(data)

    def on_subscribe(self, room):
        self.room = room
        self.join(room)
        self.spawn(self.listener, room)
        return True

    def on_new_event(self, *args):
        self.emit('new_event', *args)

    def recv_disconnect(self):
        # since the connection to redis doesn't get closed properly in the disconnect function,
        # we are overriding this function to call it here
        self.kill_local_jobs()
        self.disconnect(silent=True)

def after_event_save(sender, instance, created, **kwargs):
    if created:
        emit_to_channel(instance.project, 'new_event', instance.created_by, instance.serialize())
        add_event_task(instance)

signals.post_save.connect(after_event_save, sender=Event)

def socketio_service(request):
    socketio_manage(request.environ, namespaces={'/event/updates': EventUpdatesNamespace}, request=request)
    # Only returning this so that it doesn't throw exception, but it doesn't really need anything returned
    return HttpResponse('')

class DemoRenderer(TemplateRenderer):
    template = 'event_updates.html'

class DemoView(View):
    renderers = (DemoRenderer,)

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()
        project = get_params.get('project')
        events = Event.objects.filter(project=project)
        return events
