# -*- coding: utf-8 -*-
from datetime import datetime, date
import simplejson

from event.base import EventType, dthandler
from event.tests.base import EventTestBase

class SomeEventType(EventType):
    event_attributes = ['data_a', 'data_b', 'data_c']

class TestEventType(EventTestBase):
    def test_create_event(self):
        data = {
            'data_a': 'a',
            'data_b': 'b',
            'data_c': 'c',
        }
        event_type = SomeEventType(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)
        self.assertEqual(event_type.data_a, data['data_a'])
        self.assertEqual(event_type.data_b, data['data_b'])
        self.assertEqual(event_type.data_c, data['data_c'])

    def test_create_event_invalid_attribute(self):
        with self.assertRaisesRegexp(AttributeError, 'SomeEventType does not have attribute data_d'):
            data = {
                'data_a': 'a',
                'data_b': 'b',
                'data_c': 'c',
                'data_d': 'd'
            }
            event_type = SomeEventType(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)

    def test_save_event(self):
        data = {
            'data_a': 'a',
            'data_b': 'b',
            'data_c': 'c',
        }
        event_type = SomeEventType(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'SomeEventType')
        self.assertEqual(event_instance.data, simplejson.dumps(data))

    def test_save_event_multiple_times_go_to_same_instance(self):
        data = {
            'data_a': 'a',
            'data_b': 'b',
            'data_c': 'c',
            }
        event_type = SomeEventType(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'SomeEventType')
        self.assertEqual(event_instance.data, simplejson.dumps(data))

        # save again
        event_instance_second_save = event_type.save_event()
        self.assertEqual(event_instance.id, event_instance_second_save.id)


    def test_save_event_with_date_datetime(self):
        data = {
            'data_a': 'a',
            'data_b': date(2012, 3, 20),
            'data_c': datetime(2013, 12, 30),
            }
        event_type = SomeEventType(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'SomeEventType')
        self.assertEqual(event_instance.data, simplejson.dumps(data, default=dthandler))




