# -*- coding: utf-8 -*-
import datetime

from mock import patch, Mock
from django.core.urlresolvers import reverse

from event.models import Event
from event.tests.base import EventTestBase

class TestEvent(EventTestBase):
    def test_unicode(self):
        # create event
        event = Event.objects.create(
            resource = 'http://storyhost/story/TST-1',
            event_type = 'StoryAdded',
            data = '{"estimate":2}'
        )
        self.assertEqual(unicode(event), u'%s event of %s on %s' % (event.event_type, event.resource, event.created_on))

    def test_get_absolute_url(self):
        event = Event.objects.create(
            resource = 'http://storyhost/story/TST-1',
            event_type = 'StoryAdded',
            data = '{"estimate":2}'
        )
        self.assertEqual(event.get_absolute_url(), reverse('event', kwargs={'id': event.id}))

    def test_save(self):
        patch_request_local = patch('django_request_local.middleware.RequestLocal.get_current_request')
        mock_request_local = patch_request_local.start()
        remote_user = 'http://authhost/user/testuser'
        mock_request = Mock()
        mock_request.COOKIES = {
            'remote_user': remote_user
        }
        mock_request_local.return_value = mock_request

        event = Event.objects.create(
            resource = 'http://storyhost/story/TST-1',
            event_type = 'StoryAdded',
            data = '{"estimate":2}'
        )
        self.assertEqual(event.created_by, remote_user)
        self.assertEqual(event.event_type, 'StoryAdded')
        self.assertEqual(event.data, '{"estimate":2}')
        self.assertTrue(event.created_on)

        patch_request_local.stop()

    def test_save_with_created_by(self):
        patch_request_local = patch('django_request_local.middleware.RequestLocal.get_current_request')
        mock_request_local = patch_request_local.start()
        remote_user = 'http://authhost/user/testuser'
        mock_request = Mock()
        mock_request.COOKIES = {
            'remote_user': remote_user
        }
        mock_request_local.return_value = mock_request

        event = Event.objects.create(
            resource = 'http://storyhost/story/TST-1',
            event_type = 'StoryAdded',
            data = '{"estimate":2}',
            created_by = 'http://authhost/user/sinapam'
        )
        self.assertEqual(event.created_by, 'http://authhost/user/sinapam')

        patch_request_local.stop()

    def test_save_with_created_on(self):
        patch_request_local = patch('django_request_local.middleware.RequestLocal.get_current_request')
        mock_request_local = patch_request_local.start()
        remote_user = 'http://authhost/user/testuser'
        mock_request = Mock()
        mock_request.COOKIES = {
            'remote_user': remote_user
        }
        mock_request_local.return_value = mock_request

        event = Event.objects.create(
            resource='http://storyhost/story/TST-1',
            event_type='Uncompleted',
            data='{"estimate":2}',
            created_on=datetime.date(2007, 12, 5)
        )
        self.assertEqual(event.created_on, datetime.date(2007, 12, 5))

        patch_request_local.stop()
