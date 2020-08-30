import redis
import time
import logging
from mock import MagicMock


class Store(object):
    def __init__(self, host, port, password, db, timeout, max_retries):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.timeout = timeout
        self.max_retries = max_retries
        self.attempts = 0
        self.r = redis.Redis(host=self.host, port=self.port, password=self.password, db=self.db)

    def echo(self, val):
        return self.r.echo(val)

    def maintain(f):
        def wrapper(self, *args):
            response = None
            start_time = time.time()
            while response is None:
                try:
                    response = f(self, *args)
                except Exception as e:
                    logging.info('Unable to use Redis: %s' % e)
                    self.attempts += 1
                if time.time() - start_time > self.timeout:
                    break
                if self.attempts == self.max_retries:
                    break
            return response
        return wrapper

    @maintain
    def get(self, key):
        return self.r.get(key)

    @maintain
    def cache_set(self, key, value, ttl=None):
        self.r.set(key, value)
        if ttl:
            self.r.expire(key, ttl)
        return key, value, ttl

    @maintain
    def cache_get(self, key):
        return self.r.get(key)

class MockStore(Store):
    @property
    def is_connected(self):
        return False

    def maintain(f):
        def wrapper(self, *args):
            response = None
            start_time = time.time()
            self.attempts = 0
            while response is None:
                try:
                    if not self.is_connected:
                        mock = MagicMock(side_effect=Exception('ConnectionError!'))
                        mock()
                    response = f(self, *args)
                except Exception as e:
                    logging.info('Unable to use Redis: %s' % e)
                    self.attempts += 1
                if time.time() - start_time > self.timeout:
                    break
                if self.attempts == self.max_retries:
                    break
            return response
        return wrapper

    @maintain
    def get(self, key):
        return self.r.get(key)

