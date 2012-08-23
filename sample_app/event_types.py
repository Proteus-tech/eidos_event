# -*- coding: utf-8 -*-
from event.base import EventType

__all__ = [
    'StoryAdded',
    'StoryEstimateChanged',
    'StoryCompleted',
    'StoryStatusChanged',
]

class StoryAdded(EventType):
    event_attributes = ('estimate',)

class StoryEstimateChanged(EventType):
    event_attributes = ('old_estimate', 'new_estimate')

class StoryCompleted(EventType):
    event_attributes = ('estimate',)

class StoryStatusChanged(EventType):
    event_attributes = ('from_status', 'to_status')