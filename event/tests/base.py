# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from mock import patch, Mock
from django.test import TestCase

class EventTestBase(TestCase):
    def setUp(self):
        # self.patch_redis = patch('redis.Redis')
        # self.mock_redis = self.patch_redis.start()

        self.patch_get_current_request = patch('django_request_local.middleware.RequestLocal.get_current_request')
        self.mock_get_current_request = self.patch_get_current_request.start()
        remote_user = 'http://authhost/user/testuser'
        self.mock_request = Mock()
        self.mock_request.COOKIES = {
            'remote_user': remote_user
        }
        self.mock_request.user = User.objects.create_user('event_user', '', 'event_user')
        self.mock_get_current_request.return_value = self.mock_request

        self.patch_send_task = patch('celery.execute.send_task')
        self.mock_send_task = self.patch_send_task.start()

    def tearDown(self):
        # self.patch_redis.stop()
        self.patch_get_current_request.stop()
        self.patch_send_task.stop()