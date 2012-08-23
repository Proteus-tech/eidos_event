# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, url
from sample_app.views import DemoView

urlpatterns = patterns('',
    # for demo
    url(r'^/updates/demo$', DemoView.as_view()),
)