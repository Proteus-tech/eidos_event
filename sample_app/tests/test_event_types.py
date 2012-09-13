# -*- coding: utf-8 -*-
import simplejson
from datetime import datetime

from event.tests.base import EventTestBase
from sample_app.event_types import StoryAdded, StoryEstimateChanged, StoryCompleted, StoryStatusChanged

class TestStoryAdded(EventTestBase):
    def setUp(self):
        super(TestStoryAdded, self).setUp()
        self.data = {
            'estimate': 2,
        }

    def test_create_story_added_event(self):
        story_added_event = StoryAdded(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        self.assertEqual(story_added_event.estimate, self.data['estimate'])

    def test_create_event_invalid_attribute(self):
        with self.assertRaisesRegexp(AttributeError, 'StoryAdded does not have attribute another_field'):
            data = self.data.copy()
            data.update({'another_field': 'abc'})
            event_type = StoryAdded(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)

    def test_save_event(self):
        event_type = StoryAdded(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'StoryAdded')
        self.assertEqual(event_instance.data, simplejson.dumps(self.data))

class TestStoryEstimated(EventTestBase):
    def setUp(self):
        super(TestStoryEstimated, self).setUp()
        self.data = {
            'old_estimate': 1,
            'new_estimate': 2,
        }

    def test_create_story_added_event(self):
        story_added_event = StoryEstimateChanged(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        self.assertEqual(story_added_event.old_estimate, self.data['old_estimate'])
        self.assertEqual(story_added_event.new_estimate, self.data['new_estimate'])

    def test_create_event_invalid_attribute(self):
        with self.assertRaisesRegexp(AttributeError, 'StoryEstimateChanged does not have attribute another_field'):
            data = self.data.copy()
            data.update({'another_field': 'abc'})
            event_type = StoryEstimateChanged(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)

    def test_save_event(self):
        event_type = StoryEstimateChanged(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'StoryEstimateChanged')
        self.assertEqual(event_instance.data, simplejson.dumps(self.data))

class TestStoryCompleted(EventTestBase):
    def setUp(self):
        super(TestStoryCompleted, self).setUp()
        now = datetime.now()
        self.data = {
            'estimate': 2,
        }

    def test_create_story_added_event(self):
        story_added_event = StoryCompleted(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        self.assertEqual(story_added_event.resource, 'http://storyhost/story/TST-1')

    def test_create_event_invalid_attribute(self):
        with self.assertRaisesRegexp(AttributeError, 'StoryCompleted does not have attribute another_field'):
            data = self.data.copy()
            data.update({'another_field': 'abc'})
            event_type = StoryCompleted(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)

    def test_save_event(self):
        event_type = StoryCompleted(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'StoryCompleted')
        self.assertEqual(event_instance.data, simplejson.dumps(self.data))

class TestStoryStatusChanged(EventTestBase):
    def setUp(self):
        super(TestStoryStatusChanged, self).setUp()
        self.data = {
            'from_status': 'Development In Progress',
            'to_status': 'Ready For Testing',
        }

    def test_create_story_added_event(self):
        story_added_event = StoryStatusChanged(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        self.assertEqual(story_added_event.from_status, self.data['from_status'])
        self.assertEqual(story_added_event.to_status, self.data['to_status'])

    def test_create_event_invalid_attribute(self):
        with self.assertRaisesRegexp(AttributeError, 'StoryStatusChanged does not have attribute another_field'):
            data = self.data.copy()
            data.update({'another_field': 'abc'})
            event_type = StoryStatusChanged(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=data)

    def test_save_event(self):
        event_type = StoryStatusChanged(resource='http://storyhost/story/TST-1', project='http://projecthost/project/TST', data=self.data)
        event_instance = event_type.save_event()
        self.assertTrue(event_instance.id) # make sure it is already saved
        self.assertEqual(event_instance.resource, 'http://storyhost/story/TST-1')
        self.assertEqual(event_instance.event_type, 'StoryStatusChanged')
        self.assertEqual(event_instance.data, simplejson.dumps(self.data))
