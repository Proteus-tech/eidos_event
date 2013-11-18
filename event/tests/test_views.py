# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.contrib.auth.models import User
import simplejson
from event.tests.base import EventTestBase
from sample_app.event_types import StoryAdded, StoryCompleted, StoryStatusChanged, StoryEstimateChanged


class TestEventListView(EventTestBase):
    def setUp(self):
        super(TestEventListView, self).setUp()
        self.story_list = "[\"http://storyhost/story/TST-1\"]"
        self.resource = "http://storyhost/story/TST-1"
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
        response = self.client.get('/events', HTTP_X_RESOURCE_IN=self.story_list)
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
        response = self.client.get('/events', HTTP_X_RESOURCE_IN=self.story_list)
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

