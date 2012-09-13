# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from serene.views import InstanceModelView

from event.resources import EventResource
from event.views import EventListView, DemoView

urlpatterns = patterns('',
    url(r'^events$', EventListView.as_view(), name='events'),
    url(r'^event/(?P<id>\d+)$', InstanceModelView.as_view(resource=EventResource), name='event'),
    url(r'^event/updates/demo$', DemoView.as_view()),
    url(r'^socket\.io', 'event.views.socketio_service', name='socketio_service'),
)