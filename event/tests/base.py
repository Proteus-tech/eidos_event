# -*- coding: utf-8 -*-
from mock import patch, Mock
from django.test import TestCase

class EventTestBase(TestCase):
    def setUp(self):
        self.patch_redis = patch('redis.Redis')
        self.mock_redis = self.patch_redis.start()
        self.mock_redis_class = Mock()
        self.mock_redis.return_value = self.mock_redis_class
        self.mock_redis_publish = self.mock_redis_class.publish

    def tearDown(self):
        self.patch_redis.stop()