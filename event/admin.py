# -*- coding: utf-8 -*-

from django.contrib import admin

from event.models import Event
from event.forms import EventForm

class EventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'resource', 'data', 'created_by', 'created_on')
    list_filter = ('event_type', 'project', 'created_by', 'created_on')

    form = EventForm

admin.site.register(Event, EventAdmin)