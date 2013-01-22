# -*- coding: utf-8 -*-
from datetime import datetime, date
import simplejson
from event.models import Event

dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime) or isinstance(obj, date) else None

class EventType(object):
    event_attributes = tuple()

    def __init__(self, resource, project, data={}, created_by=None):
        if self.event_attributes:
            unknown_attributes = list(set(data.keys()) - set(self.event_attributes))
            if unknown_attributes:
                # just report one at a time for now
                raise AttributeError('%s does not have attribute %s' % (self.__class__.__name__, unknown_attributes[0]))
            for attribute in self.event_attributes:
                setattr(self, attribute, data.get(attribute))
        elif data.keys():
            # we have no attribute
            # just report one at a time for now
            raise AttributeError('%s does not have attribute %s' % (self.__class__.__name__, data.keys()[0]))

        self.resource = resource
        self.project = project
        self.created_by = created_by

    def save_event(self):
        to_update_data = {}
        [to_update_data.update({attribute:getattr(self,attribute)}) for attribute in self.event_attributes]
        event_type = self.__class__.__name__
        resource = self.resource
        project = self.project
        data = simplejson.dumps(to_update_data, default=dthandler)
        created_by = self.created_by
        if hasattr(self, 'event_id'):
            try:
                existing_event = Event.objects.get(id=self.event_id)
                existing_event.resource = resource
                existing_event.project = project
                existing_event.data = data
                existing_event.created_by = created_by
                existing_event.save()
                return existing_event
            except Event.DoesNotExist:
                # let it pass down to creating new event
                pass
        new_event = Event.objects.create(
            event_type = event_type,
            resource = resource,
            project = project,
            data = data,
            created_by = created_by
        )
        self.event_id = new_event.id
        return new_event