# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url  # we are still using defaults for django 1.3.1
from serene.views import InstanceModelView
from .resources import EventResource
from .views import EventListView

urlpatterns = patterns('',
                       url(r'^events$', EventListView.as_view(), name='events'),
                       url(r'^event/(?P<id>\d+)$', InstanceModelView.as_view(resource=EventResource), name='event'),
                       )
