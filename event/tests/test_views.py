# -*- coding: utf-8 -*-
import simplejson
from mock import patch, Mock
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from event.models import Event
from event.views import socketio_service, EventUpdatesNamespace
from event.tests.base import EventTestBase
from sample_app.event_types import StoryAdded, StoryCompleted, StoryEstimateChanged, StoryStatusChanged

class TestEventListView(EventTestBase):
    def setUp(self):
        super(TestEventListView, self).setUp()
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

class TestEventUpdatesNamespace(TestCase):
    def setUp(self):
        self.patch_redis_pubsub = patch('redis.Redis.pubsub')
        self.mock_redis_pubsub = self.patch_redis_pubsub.start()
        self.mock_redis_pubsub.listen = []

        socket = Mock()
        socket.session = {'rooms': Mock()}
        self.environ = {'socketio': socket}
        self.ns_name = '/event/updates'
        self.request = Mock()

    def test_on_subscribe(self):
        eun = EventUpdatesNamespace(self.environ, self.ns_name, self.request)
        eun.spawn = Mock()
        eun.join = Mock()
        room = 'http://127.0.0.1:8001/project/PAM'
        eun.on_subscribe(room)
        self.assertEqual(eun.room, room)
        self.assertEqual(eun.join.call_args[0][0], room)
        self.assertEqual(eun.spawn.call_args[0][0], eun.listener)
        self.assertEqual(eun.spawn.call_args[0][1], room)

    def tearDown(self):
        self.patch_redis_pubsub.stop()

class TestAfterEventSave(EventTestBase):
    def test_when_event_saved_it_is_published(self):
        self.assertFalse(self.mock_redis_publish.called)
        Event.objects.create(event_type='MyEvent', resource='http://storyhost/PAM-1',
            project='http://projecthost/project/PAM', data='{}')
        self.assertEqual(self.mock_redis_publish.call_args[0][0], 'socketio_http://projecthost/project/PAM')

        publish_msg = self.mock_redis_publish.call_args[0][1]
        self.assertIn('{"args": ["http://projecthost/project/PAM", "", ', publish_msg)
        self.assertIn('"project": "http://projecthost/project/PAM"', publish_msg)
        self.assertIn('"resource": "http://storyhost/PAM-1"', publish_msg)
        self.assertIn('"event_type": "MyEvent"', publish_msg)
        self.assertIn('"data": "{}"', publish_msg)
        self.assertIn('"name": "new_event"', publish_msg)

class TestSocketioService(TestCase):
    """
    Test socketio_service (no need to inherit from EventTestBase because we'll not be calling redis)
    """
    def setUp(self):
        self.factory = RequestFactory()

        self.patch_gevent_joinall = patch('gevent.joinall')
        self.mock_gevent_joinall = self.patch_gevent_joinall.start()

    def test_get_socketio(self):
        request = self.factory.get('/socket.io')
        socket = Mock()
        environ = {'socketio': socket}
        request.environ = environ
        response = socketio_service(request)
        self.assertEqual(socket._set_environ.call_args[0][0], environ)
        self.assertEqual(socket._set_namespaces.call_args[0][0], {'/event/updates': EventUpdatesNamespace})
        self.assertTrue(socket._spawn_receiver_loop.called)
        self.assertTrue(socket._spawn_watcher.called)

    def tearDown(self):
        self.patch_gevent_joinall.stop()

class TestDemoView(EventTestBase):
    """
    This is testing a demo view, so I'm going to test very lightly
    """
    test_uri = '/event/updates/demo?project=http://projecthost/project/PAM'
    def setUp(self):
        super(TestDemoView, self).setUp()
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