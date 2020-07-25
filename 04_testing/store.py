import redis
import time

HOST = 'redis-15377.c82.us-east-1-2.ec2.cloud.redislabs.com'
PASSWORD = 'Z0mu2Jk5ngtOpeXdtev9GpIOuF3GJzL1'
PORT = 15377
TIMEOUT = 2
DB = 0

class Store(object):
    def __init__(self, host, port, password, db, timeout):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.timeout = timeout
        self.r = None

    def maintain(f):
        def wrapper(self,*args):
            response = None
            start_time = time.time()
            while response is None:
                try:
                    response = f(self, *args)
                except Exception as e:
                    logging.info('Unable to user Redis: %s' % e)
                    pass
                if time.time() - start_time > self.timeout:
                    break
                time.sleep(0.2)
            return response
        return wrapper

    @maintain
    def connect(self):
        self.r = redis.Redis(host=self.host, port=self.port, password=self.password, db=self.db)
        return self.r

    @maintain
    def get(self, key):
        return self.r.get(key)

    @maintain
    def cache_set(self, key, value, ttl=None):
        self.r.set(key, value)
        if ttl:
            self.r.expire(key, ttl)
        return (key ,value, ttl)

    def cache_get(self, key):
        return self.r.get(key)

if __name__ == '__main__':
    s = Store(host=HOST, port=PORT, password=PASSWORD, db=DB, timeout=TIMEOUT)
    s.connect()
    r = s.get('foo')
    print r
