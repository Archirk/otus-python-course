import unittest
from mock import MagicMock, patch
import store

HOST = 'redis-15377.c82.us-east-1-2.ec2.cloud.redislabs.com'
PASSWORD = 'Z0mu2Jk5ngtOpeXdtev9GpIOuF3GJzL1'
PORT = 15377
TIMEOUT = 2
MAX_RETRIES = 3
DB = 0

class TestSuite(unittest.TestCase):

    def setUp(self):
        self.store = store.Store(host=HOST, port=PORT, password=PASSWORD, db=DB, timeout=TIMEOUT, max_retries=MAX_RETRIES)
        self.mock_store = store.MockStore(host=HOST, port=PORT, password=PASSWORD, db=DB, timeout=TIMEOUT, max_retries=MAX_RETRIES)
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
        self.assertEqual(self.mock_store.get('TestKey'), None)
        self.assertEqual(self.mock_store.attempts, MAX_RETRIES)


TEST_CASES = [TestSuite]