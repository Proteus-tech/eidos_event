# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from mock import patch
from redis.exceptions import ConnectionError
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
        self.assertGreater(self.mock_send_task.call_args[1]['expires'], datetime.now()) # more than now
        self.assertLess(self.mock_send_task.call_args[1]['expires'], datetime.now()+timedelta(seconds=7)) # but 7 seconds is too much

    @patch('logging.Logger.error')
    def test_add_event_task_send_task_connection_error(self, mock_logger_error):
        event = Event(event_type='MyEvent11', resource='http://storyhost/PAM-1',
            project='http://projecthost/project/PAM', data='{}')
        self.mock_send_task.side_effect = ConnectionError
        add_event_task(event)
        self.assertEqual(self.mock_send_task.call_args[0][0], 'tasks.tasks.process_event')
        self.assertEqual(self.mock_send_task.call_args[1]['args'], [event])
        self.assertGreater(self.mock_send_task.call_args[1]['expires'], datetime.now()) # more than now
        self.assertLess(self.mock_send_task.call_args[1]['expires'], datetime.now()+timedelta(seconds=7)) # but 7 seconds is too much
        self.assertEqual(mock_logger_error.call_args[0][0], 'Redis does not seem to be running')

