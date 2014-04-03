# -*- coding: utf-8 -*-
from datetime import datetime
from djangorestframework import status
from djangorestframework.permissions import IsAuthenticated
from djangorestframework.response import ErrorResponse
from djangorestframework.views import ListOrCreateModelView
import simplejson
from event.models import Event
from event.resources import EventResource


class EventListView(ListOrCreateModelView):
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

    def post(self, request, *args, **kwargs):
        data = self.DATA
        wait_for_save = []
        result = []
        for event in data:
            try:
                event['created_on'] = datetime.strptime(event['created_on'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                raise ErrorResponse(status.HTTP_400_BAD_REQUEST, "event error:: %s" % event['resource'])
            wait_for_save.append(Event(**event))

        for event in wait_for_save:
            event.save()
            result.append(event)
        return result