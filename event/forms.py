# -*- coding: utf-8 -*-
import inspect
from django import forms

from event.models import Event
from event import event_types

def get_event_types():
    return [(event_type, event_type) for event_type in event_types.__all__]

class EventForm(forms.ModelForm):
    class Meta:
        model = Event

    event_type = forms.ChoiceField(choices=get_event_types())