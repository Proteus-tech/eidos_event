from django.db.models import signals
from gevent.event import Event as Gevent
from datetime import datetime
from django.core.cache import cache
from djangorestframework.views import ListModelView, View
from djangorestframework.response import ErrorResponse
from djangorestframework import status



from event.models import Event as Event
from event.resources import EventResource

class EventListView(ListModelView):
#    permissions = (IsAuthenticated,)
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


class EventUpdatesView(View):
#    permissions = (IsAuthenticated,)
    event_added = Gevent()

    @classmethod
    def after_event_save(cls, sender, instance, created, **kwargs):
        if created:
            cache.set(instance.project, instance.id)
            cls.event_added.set()
            cls.event_added.clear()

    def get(self, request, *args, **kwargs):
        project = request.GET.get('project')
        if not project:
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, {'details': 'project is required'})
        client_latest_event_id = request.GET.get('latest_event_id')
        server_latest_event_id = cache.get(project)
        if server_latest_event_id is None or (client_latest_event_id and server_latest_event_id <= int(client_latest_event_id)):
            self.event_added.wait()
        # if we get to here, that means there is value in cache that is different from the client
        server_latest_event_id = cache.get(project)
        # return list of events from client_latest_event_id to the latest one
        filter_kwargs = {
            'project': project,
            'id__gt': client_latest_event_id or 0
        }
        return Event.objects.filter(**filter_kwargs)

signals.post_save.connect(EventUpdatesView.after_event_save, sender=Event)
