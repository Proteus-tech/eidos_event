import logging

from django.http import HttpResponse
from djangorestframework.views import View
from djangorestframework.renderers import TemplateRenderer
import simplejson

from event.models import Event

logger = logging.getLogger(__name__)


from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin
from socketio import socketio_manage
from event.utils import redis_connection

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
