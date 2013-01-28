# -*- coding: utf-8 -*-
from event.do_signal import add_event_task
from event.models import Event
from event.tests.base import EventTestBase

class TestAddEventTask(EventTestBase):

    def test_add_event_task_send_task_correctly(self):
        event = Event(event_type='MyEvent11', resource='http://storyhost/PAM-1',
            project='http://projecthost/project/PAM', data='{}')
        add_event_task(event)
        self.assertEqual(self.mock_send_task.call_args[0][0], 'tasks.tasks.process_event')
        self.assertEqual(self.mock_send_task.call_args[1]['args'], [event])