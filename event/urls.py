# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from serene.views import InstanceModelView
from .resources import EventResource
from .views import EventListView

urlpatterns = patterns('',
                       url(r'^events$', EventListView.as_view(), name='events'),
                       url(r'^event/(?P<id>\d+)$', InstanceModelView.as_view(resource=EventResource), name='event'),
                       )
