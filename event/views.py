import time
from django.db.models import signals
from django.core.cache import cache
from gevent.event import Event as Gevent
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
#            self.emit_to_room(self.room, 'new_event', instance.created_by, instance.serialize())
signals.post_save.connect(after_event_save, sender=Event)

def socketio_service(request):
    retval = socketio_manage(request.environ, namespaces={'/event/updates': EventUpdatesNamespace}, request=request)

    return retval

from redis import Redis
from django.conf import settings
from django.http import HttpResponse
from gevent import Greenlet

def redis_client():
    """Get a redis client."""
    return Redis(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB,
        socket_timeout=0.5)

def room_channel(name='default'):
    """Get redis pubsub channel key for given chat room."""
    return 'chat:rooms:{n}'.format(n=name)

def socketio(request):
    """The socket.io view."""
    io = request.environ['socketio']
    redis_sub = redis_client().pubsub()
    user = request.user.username

    # Subscribe to incoming pubsub messages from redis.
    def subscriber(io):
        redis_sub.subscribe(room_channel())
        redis_client().publish(room_channel(), user + ' connected.')
        while io.connected:
            for message in redis_sub.listen():
                if message['type'] == 'message':
                    io.send(message['data'])
    greenlet = Greenlet.spawn(subscriber, io)

    # Listen to incoming messages from client.
    while io.connected:
        message = io.recv()
        if message:
            redis_client().publish(room_channel(), user + ': ' + message[0])

    # Disconnected. Publish disconnect message and kill subscriber greenlet.
    redis_client().publish(room_channel(), user + ' disconnected')
    greenlet.throw(Greenlet.GreenletExit)

    return HttpResponse()

notifier = Gevent()
class EventUpdatesView(View):
    permissions = (IsAuthenticated,)

    @classmethod
    def after_event_save(cls, sender, instance, created, **kwargs):
        global notifier
        if created:
            logger.info('setting listener because of event: %s' % instance.id)
            cache.set('event_project', instance.project)
            notifier.set()
            notifier.clear()

    def get(self, request, *args, **kwargs):
        global notifier
        project = request.GET.get('project')
        if not project:
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, {'details': 'project is required'})
        client_latest_event_id = request.GET.get('latest_event_id')
        try:
            server_latest_event = Event.objects.latest('id')
            server_latest_event_id = server_latest_event.id
        except Event.DoesNotExist:
            server_latest_event_id = 0
        logger.info('server_latest_event_id=%s' % server_latest_event_id)
        if server_latest_event_id is None or (client_latest_event_id and server_latest_event_id <= int(client_latest_event_id)):
            keep_waiting = True
            start = time.time()
            while keep_waiting:
                logger.info('in keep_waiting')
                notifier.wait(timeout=59)
                if time.time()-start < 59:
                    # there were some notification but is it ours?
                    event_project = cache.get('event_project')
                    if project == event_project:
                        logger.info('it is our project')
                        break
                    logger.info('it is NOT our project. Continue.')
                else:
                    # timeout, just break
                    logger.info('timeout, just break')
                    break

        # if we get to here, that means there was an event triggered
        # return list of events from client_latest_event_id to the latest one
        filter_kwargs = {
            'project': project,
            }
        if client_latest_event_id:
            filter_kwargs['id__gt'] = client_latest_event_id
        logger.info('filter_kwargs=%s' % filter_kwargs)
        events = Event.objects.filter(**filter_kwargs).order_by('-id')[:20]
        logger.info('returning events: %s' % events)
        return [event for event in reversed(events)]

signals.post_save.connect(EventUpdatesView.after_event_save, sender=Event)

class DemoRenderer(TemplateRenderer):
    template = 'event_updates.html'

class DemoView(View):
    renderers = (DemoRenderer,)

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()
        project = get_params.get('project')
        events = Event.objects.filter(project=project)
        return events
