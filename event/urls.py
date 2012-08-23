# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from serene.views import InstanceModelView

from event.resources import EventResource
from event.views import EventListView, EventUpdatesView

urlpatterns = patterns('',
    url(r'^s$', EventListView.as_view(), name='events'),
    url(r'^/(?P<id>\d+)$', InstanceModelView.as_view(resource=EventResource), name='event'),
    url(r'^/updates$', EventUpdatesView.as_view(), name='event_updates'),
)