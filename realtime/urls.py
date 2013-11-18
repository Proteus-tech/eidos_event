# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from realtime.views import DemoView

urlpatterns = patterns('',
    url(r'^event/updates/demo$', DemoView.as_view()),
    url(r'^socket\.io', 'realtime.views.socketio_service', name='socketio_service'),
)