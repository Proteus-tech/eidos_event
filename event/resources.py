# -*- coding: utf-8 -*-
from serene.resources import ModelResource

from event.models import Event

class EventResource(ModelResource):
    model = Event