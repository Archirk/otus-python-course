import redis
import logging


class Store(object):
    def __init__(self, host, port, password, db, timeout, max_retries):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.timeout = timeout
        self.max_retries = max_retries
        self.attempts = 0
        self.r = redis.Redis(host=self.host, port=self.port,
                                        password=self.password, db=self.db,
                                        socket_timeout=self.timeout,
                                        socket_connect_timeout=self.timeout)

    def echo(self, val):
        return self.r.echo(val)

    def maintain(f):
        def wrapper(self, *args):
            response = None
            for i in range(self.max_retries):
                try:
                    response = f(self, *args)
                except Exception as e:
                    self.attempts += 1
                    logging.info('Unable to use Redis: %s' % e)
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

