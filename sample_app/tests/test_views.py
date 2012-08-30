# -*- coding: utf-8 -*-
from mock import patch, DEFAULT
import simplejson
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache

from event.models import Event
from sample_app.event_types import StoryAdded, StoryCompleted, StoryEstimateChanged, StoryStatusChanged
from event.views import EventUpdatesView

class TestEventListView(TestCase):
    def setUp(self):
        self.resource = 'http://storyhost/story/TST-1'
        self.project='http://projecthost/project/TST'
        self.now = datetime.now()
        self.added = StoryAdded(resource=self.resource, project=self.project, data={
            'estimate': None,
        })
        self.added_event = self.added.save_event()
        self.added_event.created_on = self.now
        self.added_event.save()

        self.estimated_3 = StoryEstimateChanged(resource=self.resource, project=self.project, data={
            'old_estimate': None,
            'new_estimate': 3,
        })
        self.estimated_3_event = self.estimated_3.save_event()
        self.estimated_3_event.created_on = self.now + timedelta(days=1)
        self.estimated_3_event.save()

        self.to_development = StoryStatusChanged(resource=self.resource, project=self.project, data={
            'from_status': None,
            'to_status': 'Development In Progress',
        }, created_by='http://authhost/user/sinapam')
        self.to_development_event = self.to_development.save_event()
        self.to_development_event.created_on = self.now + timedelta(days=1)
        self.to_development_event.save()

        self.estimated_5 = StoryEstimateChanged(resource=self.resource, project=self.project, data={
            'old_estimate': 3,
            'new_estimate': 5,
        })
        self.estimated_5_event = self.estimated_5.save_event()
        self.estimated_5_event.created_on = self.now + timedelta(days=2)
        self.estimated_5_event.save()

        self.to_ready_for_testing = StoryStatusChanged(resource=self.resource, project=self.project, data={
            'from_status': 'Development In Progress',
            'to_status': 'Ready for Testing',
        })
        self.to_ready_for_testing_event = self.to_ready_for_testing.save_event()
        self.to_ready_for_testing_event.created_on = self.now + timedelta(days=3)
        self.to_ready_for_testing_event.save()

        self.to_complete = StoryCompleted(resource=self.resource, project=self.project)
        self.to_complete_event = self.to_complete.save_event()
        self.to_complete_event.created_on = self.now + timedelta(days=4)
        self.to_complete_event.save()

        self.other_resource_event = StoryAdded(resource='http://storyhost/story/TST-2', project=self.project, data={
            'estimate': 5,
        })
        self.other_resource_event.save_event()

        User.objects.create_user(username='testuser', password='testuser', email='')
        self.client.login(username='testuser', password='testuser')
        self.client.defaults = dict(
            HTTP_ACCEPT='application/json',
            CONTENT_TYPE='application/json'
        )

    def test_get_event_list_filtered_by_resource(self):
        response = self.client.get('/events', {'resource': self.resource})
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 6)
        self.assertEqual(content[0]['event_type'], 'StoryAdded')
        self.assertEqual(content[1]['event_type'], 'StoryEstimateChanged')
        self.assertEqual(content[2]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[3]['event_type'], 'StoryEstimateChanged')
        self.assertEqual(content[4]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[5]['event_type'], 'StoryCompleted')

    def test_get_event_list_filtered_by_event_type(self):
        response = self.client.get('/events', {'event_type': 'StoryStatusChanged'})
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[1]['event_type'], 'StoryStatusChanged')

    def test_get_event_list_filtered_by_data(self):
        data = {
            'old_estimate': 3,
            'new_estimate': 5,
        }
        response = self.client.get('/events', {'data': simplejson.dumps(data)})
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['event_type'], 'StoryEstimateChanged')

    def test_get_event_list_filtered_by_created_by(self):
        response = self.client.get('/events', {'created_by': 'http://authhost/user/sinapam'})
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['event_type'], 'StoryStatusChanged')

    def test_get_event_list_filtered_by_created_on(self):
        response = self.client.get('/events', {
            'created_on__gt': (self.now + timedelta(days=2)).isoformat(),
            'created_on__lte': (self.now + timedelta(days=4)).isoformat()
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[1]['event_type'], 'StoryCompleted')

    def test_get_event_list_no_filter(self):
        response = self.client.get('/events')
        self.assertContains(response, 'You must pass in a filter', status_code=400)

    def test_get_event_list_check_content(self):
        response = self.client.get('/events', {'resource': self.resource})
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 6)
        # check event_type
        self.assertEqual(content[0]['event_type'], 'StoryAdded')
        self.assertEqual(content[1]['event_type'], 'StoryEstimateChanged')
        self.assertEqual(content[2]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[3]['event_type'], 'StoryEstimateChanged')
        self.assertEqual(content[4]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[5]['event_type'], 'StoryCompleted')
        # check resource
        for event in content:
            self.assertEqual(event['resource'], self.resource)
        # check links
        self.assertEqual(content[0]['links']['self']['href'], 'http://testserver/event/%s' % self.added_event.id)
        self.assertEqual(content[1]['links']['self']['href'], 'http://testserver/event/%s' % self.estimated_3_event.id)
        self.assertEqual(content[2]['links']['self']['href'], 'http://testserver/event/%s' % self.to_development_event.id)
        self.assertEqual(content[3]['links']['self']['href'], 'http://testserver/event/%s' % self.estimated_5_event.id)
        self.assertEqual(content[4]['links']['self']['href'], 'http://testserver/event/%s' % self.to_ready_for_testing_event.id)
        self.assertEqual(content[5]['links']['self']['href'], 'http://testserver/event/%s' % self.to_complete_event.id)

class TestEventUpdatesView(TestCase):
    test_uri = '/event/updates'
    def setUp(self):

        User.objects.create_user(username='testuser', password='testuser', email='')
        self.client.login(username='testuser', password='testuser')
        self.client.defaults = dict(
            HTTP_ACCEPT='application/json',
            CONTENT_TYPE='application/json'
        )
        self.test_project = 'http://projecthost/project/TST'

    def tearDown(self):
        # clear cache every time, so that it doesn't affect other tests
        cache.delete('http://projecthost/project/TST')
        cache.delete('http://projecthost/project/PAM')

    def create_events(self):
        self.PAM_events = []
        self.TST_events = []
        for index in xrange(1,3):
            event = Event.objects.create(event_type='MyEvent%s' % index, resource='http://storyhost/PAM-1',
                project='http://projecthost/project/PAM', data='{}')
            self.PAM_events.append(event)
        for index in xrange(1,5):
            event = Event.objects.create(event_type='MyEvent%s' % index, resource='http://storyhost/TST-1',
                project=self.test_project, data='{}')
            self.TST_events.append(event)
        for index in xrange(1,4):
            event = Event.objects.create(event_type='MyEvent%s' % index, resource='http://storyhost/PAM-1',
                project='http://projecthost/project/PAM', data='{}')
            self.PAM_events.append(event)
        for index in xrange(1,2):
            event = Event.objects.create(event_type='MyEvent%s' % index, resource='http://storyhost/TST-1',
                project=self.test_project, data='{}')
            self.TST_events.append(event)

    def test_get_without_project(self):
        self.create_events()
        uri = '%s?latest_event_id=%s' % (self.test_uri, self.TST_events[2].id)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 400)
        response_dict = simplejson.loads(response.content)
        self.assertEqual(response_dict['details'], 'project is required')

    def test_get_project_empty(self):
        self.create_events()
        uri = '%s?project=&latest_event_id=%s' % (self.test_uri, self.TST_events[2].id)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 400)
        response_dict = simplejson.loads(response.content)
        self.assertEqual(response_dict['details'], 'project is required')

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_no_wait_client_latest_less_than_server_latest(self, set, clear, wait):
        self.create_events()
        self.assertEqual(set.call_count, 10)
        self.assertEqual(clear.call_count, 10)
        uri = '%s?project=%s&latest_event_id=%s' % (self.test_uri, self.test_project, self.TST_events[2].id)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        events = simplejson.loads(response.content)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['id'], self.TST_events[3].id)
        self.assertEqual(events[1]['id'], self.TST_events[4].id)

        # no wait
        self.assertFalse(wait.called)

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_no_wait_client_does_not_send_latest_event_id(self, set, clear, wait):
        self.create_events()
        self.assertEqual(set.call_count, 10)
        self.assertEqual(clear.call_count, 10)

        uri = '%s?project=%s' % (self.test_uri, self.test_project)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        events = simplejson.loads(response.content)
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0]['id'], self.TST_events[0].id)
        self.assertEqual(events[1]['id'], self.TST_events[1].id)
        self.assertEqual(events[2]['id'], self.TST_events[2].id)
        self.assertEqual(events[3]['id'], self.TST_events[3].id)
        self.assertEqual(events[4]['id'], self.TST_events[4].id)

        # no wait
        self.assertFalse(wait.called)

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_no_wait_client_sends_empty_latest_event_id(self, set, clear, wait):
        self.create_events()
        self.assertEqual(set.call_count, 10)
        self.assertEqual(clear.call_count, 10)
        uri = '%s?project=%s&latest_event_id=' % (self.test_uri, self.test_project)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        events = simplejson.loads(response.content)
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0]['id'], self.TST_events[0].id)
        self.assertEqual(events[1]['id'], self.TST_events[1].id)
        self.assertEqual(events[2]['id'], self.TST_events[2].id)
        self.assertEqual(events[3]['id'], self.TST_events[3].id)
        self.assertEqual(events[4]['id'], self.TST_events[4].id)

        # no wait
        self.assertFalse(wait.called)

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_wait_client_latest_equal_server_latest(self,set, clear, wait):
        self.create_events()
        self.assertEqual(set.call_count, 10)
        self.assertEqual(clear.call_count, 10)
        uri = '%s?project=%s&latest_event_id=%s' % (self.test_uri, self.test_project, self.TST_events[4].id)
        response = self.client.get(uri)

        self.assertEqual(response.status_code, 200)
        # in real life, there should be no response return,
        # so we are just checking that wait is called
        self.assertTrue(wait.called)
        self.assertTrue(wait.call_args[1]['timeout'], 180)

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_wait_client_latest_more_than_server_latest(self, set, clear, wait):
        self.create_events()
        self.assertEqual(set.call_count, 10)
        self.assertEqual(clear.call_count, 10)
        uri = '%s?project=%s&latest_event_id=%s' % (self.test_uri, self.test_project, self.TST_events[4].id+1)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        # in real life, there should be no response return,
        # so we are just checking that wait is called
        self.assertTrue(wait.called)
        self.assertTrue(wait.call_args[1]['timeout'], 180)

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_wait_server_latest_is_none(self,set, clear, wait):
        uri = '%s?project=%s&latest_event_id=3' % (self.test_uri, self.test_project) # just any number will do here
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        # in real life, there should be no response return,
        # so we are just checking that wait is called
        self.assertTrue(wait.called)
        self.assertTrue(wait.call_args[1]['timeout'], 180)

    @patch.multiple('gevent.event.Event', set=DEFAULT, clear=DEFAULT, wait=DEFAULT)
    def test_get_20_latest_event_at_most(self, set, clear, wait):
        self.create_events()
        self.create_events()
        self.create_events()
        self.create_events()
        self.create_events()
        self.create_events()
        self.assertEqual(set.call_count, 60)
        self.assertEqual(clear.call_count, 60)
        uri = '%s?project=%s&latest_event_id=%s' % (self.test_uri, self.test_project, 0)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        events = simplejson.loads(response.content)
        test_events = Event.objects.filter(project=self.test_project)
        self.assertEqual(len(test_events), 30)
        self.assertEqual(len(events), 20)
        self.assertGreater(events[1]['id'], events[0]['id'])

        # in real life, there should be no response return,
        # so we are just checking that wait is called
        self.assertFalse(wait.called)

class TestDemoView(TestCase):
    """
    This is testing a demo view, so I'm going to test very lightly
    """
    test_uri = '/event/updates/demo?project=http://projecthost/project/PAM'
    def setUp(self):
        for index in xrange(1,6):
            Event.objects.create(event_type='MyEvent%s' % index, resource='http://storyhost/PAM-1',
                project='http://projecthost/project/PAM', data='{}')

    def test_get_view(self):
        response = self.client.get(self.test_uri)
        self.assertEqual(len(response.context['object']), Event.objects.all().count())
        self.assertContains(response, 'MyEvent1: {}')
        self.assertContains(response, 'MyEvent2: {}')
        self.assertContains(response, 'MyEvent3: {}')
        self.assertContains(response, 'MyEvent4: {}')
        self.assertContains(response, 'MyEvent5: {}')