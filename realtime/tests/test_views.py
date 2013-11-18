# -*- coding: utf-8 -*-
from mock import patch, Mock
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from event.models import Event
from realtime.views import socketio_service, EventUpdatesNamespace
from event.tests.base import EventTestBase


class TestEventUpdatesNamespace(TestCase):
    def setUp(self):
        self.patch_redis_pubsub = patch('redis.Redis.pubsub')
        self.mock_redis_pubsub = self.patch_redis_pubsub.start()
        self.redis = Mock(spec=['listen', 'subscribe'])
        self.redis.listen.return_value = [{'type':'message', 'data':'"abcd"'}]
        self.mock_redis_pubsub.return_value = self.redis

        socket = Mock()
        socket.session = {'rooms': Mock()}
        self.environ = {'socketio': socket}
        self.ns_name = '/event/updates'
        self.request = Mock()

    def test_listener(self):
        eun = EventUpdatesNamespace(self.environ, self.ns_name, self.request)
        eun.process_event = Mock()
        room = 'http://127.0.0.1:8001/project/PAM'
        eun.listener(room)
        self.redis.subscribe.assert_called_once_with('socketio_%s' % room)
        self.assertEqual(eun.process_event.call_args[0][0], 'abcd')

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

    def test_on_new_event(self):
        eun = EventUpdatesNamespace(self.environ, self.ns_name, self.request)
        eun.emit = Mock()
        eun.on_new_event('abc', 'def')
        self.assertEqual(eun.emit.call_args[0][0], 'new_event')
        self.assertEqual(eun.emit.call_args[0][1], 'abc')
        self.assertEqual(eun.emit.call_args[0][2], 'def')

    def tearDown(self):
        self.patch_redis_pubsub.stop()


class TestAfterEventSave(EventTestBase):
    def setUp(self):
        super(TestAfterEventSave, self).setUp()
        self.patch_redis = patch('redis.Redis')
        self.mock_redis = self.patch_redis.start()
        self.mock_redis_object = Mock()
        self.mock_redis.return_value = self.mock_redis_object

    def tearDown(self):
        self.patch_redis.stop()
        super(TestAfterEventSave, self).tearDown()

    def test_when_event_saved_it_is_published(self):
        self.assertFalse(self.mock_redis_object.publish.called)
        Event.objects.create(event_type='MyEvent', resource='http://storyhost/PAM-1',
            project='http://projecthost/project/PAM', data='{}')
        self.assertEqual(self.mock_redis.call_args[1]['host'], 'localhost')
        self.assertEqual(self.mock_redis.call_args[1]['port'], 6379)
        self.assertEqual(self.mock_redis.call_args[1]['db'], 0)
        self.assertEqual(self.mock_redis_object.publish.call_args[0][0], 'socketio_http://projecthost/project/PAM')

        publish_msg = self.mock_redis_object.publish.call_args[0][1]
        self.assertIn('{"args": ["http://projecthost/project/PAM", "http://authhost/user/testuser", ', publish_msg)
        self.assertIn('"project": "http://projecthost/project/PAM"', publish_msg)
        self.assertIn('"resource": "http://storyhost/PAM-1"', publish_msg)
        self.assertIn('"event_type": "MyEvent"', publish_msg)
        self.assertIn('"data": "{}"', publish_msg)
        self.assertIn('"name": "new_event"', publish_msg)

    def test_when_event_saved_task_is_sent(self):
        event = Event.objects.create(event_type='MyEvent11', resource='http://storyhost/PAM-1',
            project='http://projecthost/project/PAM', data='{}')
        self.assertEqual(self.mock_send_task.call_args[0][0], 'tasks.tasks.process_event')
        self.assertEqual(self.mock_send_task.call_args[1]['args'], [event])


class TestSocketioService(TestCase):
    """i
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
        self.assertTrue(isinstance(response, HttpResponse))
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