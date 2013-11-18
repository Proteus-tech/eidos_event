# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from serene.views import InstanceModelView

from realtime.resources import EventResource
from realtime.views import EventListView, DemoView

urlpatterns = patterns('',
    url(r'^events$', EventListView.as_view(), name='events'),
    url(r'^event/(?P<id>\d+)$', InstanceModelView.as_view(resource=EventResource), name='event'),
    url(r'^event/updates/demo$', DemoView.as_view()),
    url(r'^socket\.io', 'realtime.views.socketio_service', name='socketio_service'),
)