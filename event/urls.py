# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from serene.views import InstanceModelView

from event.resources import EventResource
from event.views import EventListView, EventUpdatesView, DemoView
import socketio.sdjango

urlpatterns = patterns('',
    url(r'^events$', EventListView.as_view(), name='events'),
    url(r'^event/(?P<id>\d+)$', InstanceModelView.as_view(resource=EventResource), name='event'),
    url(r'^event/updates$', EventUpdatesView.as_view(), name='event_updates'),# for demo
    url(r'^event/updates/demo$', DemoView.as_view()),
    url("^socket\.io", include(socketio.sdjango.urls)),
)