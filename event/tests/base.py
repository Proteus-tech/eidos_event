# -*- coding: utf-8 -*-
from mock import patch
from django.test import TestCase

class EventTestBase(TestCase):
    def setUp(self):
        self.patch_redis_publish = patch('redis.Redis.publish')
        self.mock_redis_publish = self.patch_redis_publish.start()

    def tearDown(self):
        self.patch_redis_publish.stop()