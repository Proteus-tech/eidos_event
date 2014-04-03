# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.contrib.auth.models import User
import simplejson
from event.models import Event
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

    def test_get_event_by_event_type_StoryCompleted(self):
        response = self.client.get('/events', {
            'event_type': 'StoryCompleted'
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['event_type'], 'StoryCompleted')

    def test_get_event_by_event_type_StoryStatusChanged(self):
        response = self.client.get('/events', {
            'event_type': 'StoryStatusChanged'
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[1]['event_type'], 'StoryStatusChanged')

    def test_get_event_by_event_type_StoryEstimateChanged(self):
        response = self.client.get('/events', {
            'event_type': 'StoryEstimateChanged'
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['event_type'], 'StoryEstimateChanged')
        self.assertEqual(content[1]['event_type'], 'StoryEstimateChanged')

    def test_get_event_by_project(self):
        new_project = "http://newproject_yok"

        sa = StoryAdded(resource=self.resource, project=new_project, data={
            'estimate': None,
        })
        sa_event = sa.save_event()
        sa_event.created_on = self.now
        sa_event.save()

        e3 = StoryEstimateChanged(resource=self.resource, project=new_project, data={
            'old_estimate': None,
            'new_estimate': 3,
        })
        e3 = e3.save_event()
        e3.created_on = self.now + timedelta(days=1)
        e3.save()

        sc = StoryStatusChanged(resource=self.resource, project=new_project, data={
            'from_status': 'Development In Progress',
            'to_status': 'Ready for Testing',
        })
        sc_event = sc.save_event()
        sc_event.created_on = self.now + timedelta(days=3)
        sc_event.save()

        sc = StoryCompleted(resource=self.resource, project=new_project)
        sc_event = sc.save_event()
        sc_event.created_on = self.now + timedelta(days=4)
        sc_event.save()

        response = self.client.get('/events', {
            'project': new_project
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 4)
        self.assertEqual(content[0]['event_type'], 'StoryAdded')
        self.assertEqual(content[1]['event_type'], 'StoryEstimateChanged')
        self.assertEqual(content[2]['event_type'], 'StoryStatusChanged')
        self.assertEqual(content[3]['event_type'], 'StoryCompleted')

    def test_get_event_by_project_and_event(self):
        new_project = "http://newproject_yok"

        sa = StoryAdded(resource=self.resource, project=new_project, data={
            'estimate': None,
        })
        sa_event = sa.save_event()
        sa_event.created_on = self.now
        sa_event.save()

        e3 = StoryEstimateChanged(resource=self.resource, project=new_project, data={
            'old_estimate': None,
            'new_estimate': 3,
        })
        e3 = e3.save_event()
        e3.created_on = self.now + timedelta(days=1)
        e3.save()

        sc = StoryStatusChanged(resource=self.resource, project=new_project, data={
            'from_status': 'Development In Progress',
            'to_status': 'Ready for Testing',
        })
        sc_event = sc.save_event()
        sc_event.created_on = self.now + timedelta(days=3)
        sc_event.save()

        sc = StoryCompleted(resource=self.resource, project=new_project)
        sc_event = sc.save_event()
        sc_event.created_on = self.now + timedelta(days=4)
        sc_event.save()

        response = self.client.get('/events', {
            'project': new_project,
            'event_type': 'StoryAdded'
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['event_type'], 'StoryAdded')

        response = self.client.get('/events', {
            'project': new_project,
            'event_type': 'StoryStatusChanged'
        })
        self.assertEqual(response.status_code, 200)
        content = simplejson.loads(response.content)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['event_type'], 'StoryStatusChanged')


class TestCreateEventListView(EventTestBase):
    def setUp(self):
        super(TestCreateEventListView, self).setUp()
        self.resource = "http://storyhost/story/TST-1"
        self.project='http://projecthost/project/TST'
        self.now = datetime.now()


        User.objects.create_user(username='testuser', password='testuser', email='')
        self.client.login(username='testuser', password='testuser')

    def test_post_event_list_with_json(self):
        data = [{
            "resource": "http://127.0.0.1:8002/story/TST-103",
            "event_type": "StoryEstimateChanged",
            "created_on": "2014-03-24T01:02:27.399465",
            "data": {"old_estimate": None, "new_estimate": 5},
            "project": "http://project_uri"
        },
        {
            "resource": "http://127.0.0.1:8002/story/TST-106",
            "event_type": "BacklogStoryAdded",
            "created_on": "1250-11-24T01:02:27.399465",
            "data": {"estimate": 8},
            "project": "http://project_uri"
        }]
        dumpds_data = simplejson.dumps(data)
        Event.objects.all().delete()

        response = self.client.post('/events', data=dumpds_data, content_type='application/json')

        self.assertEqual(response.status_code, 200)

        events = Event.objects.all().order_by('created_on')

        event = events[0]
        self.assertEqual(event.resource, data[1]['resource'])
        self.assertEqual(event.event_type, data[1]['event_type'])
        self.assertEqual(event.data, "{'estimate': 8}")
        self.assertEqual(event.project, data[1]['project'])
        self.assertEqual(str(event.created_on), '1250-11-24 07:02:27.399465+00:00')

        event = events[1]
        self.assertEqual(event.resource, data[0]['resource'])
        self.assertEqual(event.event_type, data[0]['event_type'])
        self.assertEqual(event.data, "{'old_estimate': None, 'new_estimate': 5}")
        self.assertEqual(event.project, data[0]['project'])
        self.assertEqual(str(event.created_on), '2014-03-24 06:02:27.399465+00:00')

    def test_post_event_list_without_json(self):
        data = []
        dumpds_data = simplejson.dumps(data)
        Event.objects.all().delete()

        response = self.client.post('/events', data=dumpds_data, content_type='application/json')

        self.assertEqual(response.status_code, 200)

        event_amount = Event.objects.all().count()
        self.assertEqual(event_amount, 0)

    def test_post_event_list_with_json_but_wrong_format_date(self):
        data = [{
            "resource": "http://127.0.0.1:8002/story/TST-103",
            "event_type": "StoryEstimateChanged",
            "created_on": "10-20-2012T01:02:27.399465",
            "data": {"old_estimate": None, "new_estimate": 5},
            "project": "http://project_uri"
        },
        {
            "resource": "http://127.0.0.1:8002/story/TST-106",
            "event_type": "BacklogStoryAdded",
            "created_on": "1250-11-24T01:02:27.399465",
            "data": {"estimate": 8},
            "project": "http://project_uri"
        }]
        dumpds_data = simplejson.dumps(data)
        Event.objects.all().delete()

        response = self.client.post('/events', data=dumpds_data, content_type='application/json')

        self.assertEqual(response.status_code, 400)

        count = Event.objects.all().count()
        self.assertEqual(count, 0)

    def test_post_event_list_with_json_but_missing_data(self):
        data = [{
            "resource": "http://127.0.0.1:8002/story/TST-103",
            "event_type": "StoryEstimateChanged",
            "created_on": "2014-03-24T01:02:27.399465",
            "project": "http://project_uri"
        },
        {
            "resource": "http://127.0.0.1:8002/story/TST-106",
            "event_type": "BacklogStoryAdded",
            "created_on": "1250-11-24T01:02:27.399465",
            "data": {"estimate": 8},
            "project": "http://project_uri"
        }]
        dumpds_data = simplejson.dumps(data)
        Event.objects.all().delete()

        response = self.client.post('/events', data=dumpds_data, content_type='application/json')

        self.assertEqual(response.status_code, 200)

        events = Event.objects.all().order_by('created_on')

        event = events[0]
        self.assertEqual(event.resource, data[1]['resource'])
        self.assertEqual(event.event_type, data[1]['event_type'])
        self.assertEqual(event.data, "{'estimate': 8}")
        self.assertEqual(event.project, data[1]['project'])
        self.assertEqual(str(event.created_on), '1250-11-24 07:02:27.399465+00:00')

        event = events[1]
        self.assertEqual(event.resource, data[0]['resource'])
        self.assertEqual(event.event_type, data[0]['event_type'])
        self.assertEqual(event.data, "")
        self.assertEqual(event.project, data[0]['project'])
        self.assertEqual(str(event.created_on), '2014-03-24 06:02:27.399465+00:00')