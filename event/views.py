from django.db.models import signals
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

project_event_listeners = {}

def after_event_save(sender, instance, created, **kwargs):
    if created:
        listener = project_event_listeners.get(instance.project)
        if listener is None:
            logger.info('creating new listener for %s' % instance.project)
            listener = Gevent()
            project_event_listeners[instance.project] = listener
        logger.info('setting listener because of event: %s' % instance.id)
        listener.set()
        listener.clear()

signals.post_save.connect(after_event_save, sender=Event)

class EventUpdatesView(View):
    permissions = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
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
            logger.info('we are going to wait')
            listener = project_event_listeners.get(project)
            if listener is None:
                listener = Gevent()
                project_event_listeners[project] = listener
            listener.wait(timeout=59)

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

class DemoRenderer(TemplateRenderer):
    template = 'event_updates.html'

class DemoView(View):
    renderers = (DemoRenderer,)

    def get(self, request, *args, **kwargs):
        get_params = request.GET.copy()
        project = get_params.get('project')
        events = Event.objects.filter(project=project)
        return events
