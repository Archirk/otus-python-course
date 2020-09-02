import unittest
from mock import patch, MagicMock
from mockredis import mock_redis_client
import store

HOST = 'host'
PASSWORD = 'password'
PORT = 15377
TIMEOUT = 2
MAX_RETRIES = 3
DB = 0

class TestSuite(unittest.TestCase):

    @patch('redis.Redis', mock_redis_client)
    def setUp(self):
        self.store = store.Store(host=HOST, port=PORT, password=PASSWORD, db=DB, timeout=TIMEOUT, max_retries=MAX_RETRIES)
        self.redis = self.store.r
        self.redis.set('TestKey', 'TestValue')

    def tearDown(self):
        self.redis.flushdb()

    def test_get(self):
        """ Test get method """
        self.assertEqual(self.store.get('TestKey'), 'TestValue')


    def test_cache_set(self):
        """ Test cache_set method """
        self.store.cache_set('CacheKey', 'CacheTTL=10s', 10)
        self.assertEqual(self.store.get('CacheKey'), 'CacheTTL=10s')
        self.assertGreater(self.redis.pttl('CacheKey'), 0)


    def test_cache_get(self):
        """ Test cache_get method """
        self.store.cache_set('CacheGetKey', 'CacheTTL=10s', 10)
        self.assertEqual(self.store.cache_get('CacheGetKey'), 'CacheTTL=10s')

    def test_connection_error(self):
        """ Test connection error """
        self.store.r.get = MagicMock(side_effect=Exception('ConnectionError'))  # No ConnectionError in 2.7
        self.assertEqual(self.store.get('TestKey'), None)
        self.assertEqual(self.store.attempts, MAX_RETRIES)


TEST_CASES = [TestSuite]