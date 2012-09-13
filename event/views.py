from django.db.models import signals
from datetime import datetime
from djangorestframework import status
from djangorestframework.views import ListModelView, View
from djangorestframework.response import ErrorResponse
from djangorestframework.renderers import TemplateRenderer
from auth_client.permissions import IsAuthenticated

from event.models import Event as Event
from event.resources import EventResource

import logging
logger = logging.getLogger(__name__)

class EventListView(ListModelView):
    permissions = (IsAuthenticated,)
    resource = EventResource

    def get_filter_kwargs(self, request, **kwargs):
        get_params = request.GET.copy()
        if not get_params:
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, 'You must pass in a filter.')
        filter_kwargs = kwargs.copy()
        for key, value in get_params.items():
            if key.startswith('created_on__'):
                # convert datetime to database format
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
            elif key.startswith('resource__in'):
                filter_kwargs.update({key:request.GET.getlist('resource__in')})
                continue
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

import redis
def emit_to_channel(channel, event, *data):
    r = redis.Redis()
    args = [channel] + list(data)
    r.publish('socketio_%s' % channel, simplejson.dumps({'name': event, 'args': args}))

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

def after_event_save(sender, instance, created, **kwargs):
    emit_to_channel(instance.project, 'new_event', instance.created_by, instance.serialize())

signals.post_save.connect(after_event_save, sender=Event)

def socketio_service(request):
    retval = socketio_manage(request.environ, namespaces={'/event/updates': EventUpdatesNamespace}, request=request)

    return retval

class DemoRenderer(TemplateRenderer):
    template = 'event_updates.html'

class DemoView(View):
    renderers = (DemoRenderer,)

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()
        project = get_params.get('project')
        events = Event.objects.filter(project=project)
        return events
