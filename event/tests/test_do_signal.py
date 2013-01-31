# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from mock import patch
from redis.exceptions import ConnectionError
from event.do_signal import add_event_task, emit_to_channel
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
        self.assertDictEqual(self.mock_send_task.call_args[1]['retry_policy'], {
            'max_retries': -1,
            'interval_start': 0,
            'interval_step': 0.01,
            'interval_max': 0.01,
        })

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
        self.assertDictEqual(self.mock_send_task.call_args[1]['retry_policy'], {
            'max_retries': -1,
            'interval_start': 0,
            'interval_step': 0.01,
            'interval_max': 0.01,
            })
        self.assertEqual(mock_logger_error.call_args[0][0], 'Redis does not seem to be running')

class TestEmitToChannel(EventTestBase):

    def test_emit_to_channel_event_is_publised_correctly(self):
        self.assertFalse(self.mock_redis_publish.called)
        event = Event(event_type='MyEvent', resource='http://storyhost/PAM-1',
            project='http://projecthost/project/PAM', data='{}',
            created_on=datetime(2013, 1, 31), created_by='http://authhost/user/testuser')
        emit_to_channel('http://projecthost/project/PAM', 'new_event', event.created_by, event.serialize())
        self.assertEqual(self.mock_redis.call_args[1]['host'], 'localhost')
        self.assertEqual(self.mock_redis.call_args[1]['port'], 6379)
        self.assertEqual(self.mock_redis.call_args[1]['db'], 0)
        self.assertEqual(self.mock_redis_publish.call_args[0][0], 'socketio_http://projecthost/project/PAM')

        publish_msg = self.mock_redis_publish.call_args[0][1]
        self.assertIn('{"args": ["http://projecthost/project/PAM", "http://authhost/user/testuser", ', publish_msg)
        self.assertIn('"project": "http://projecthost/project/PAM"', publish_msg)
        self.assertIn('"resource": "http://storyhost/PAM-1"', publish_msg)
        self.assertIn('"event_type": "MyEvent"', publish_msg)
        self.assertIn('"data": "{}"', publish_msg)
        self.assertIn('"name": "new_event"', publish_msg)
