import unittest
import hashlib
import datetime
from store import Store
import api
from tests.cases import cases

class TestInvalidRequests(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self):
        """ Test empty request """
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([{'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score', 'token': '', 'arguments': {}},
            {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score', 'token': 'sdd', 'arguments': {}},
            {'account': 'horns&hoofs', 'login': 'admin', 'method': 'online_score', 'token': '', 'arguments': {}}])
    def test_bad_auth(self, request):
        """ Test bad auth """
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([{'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score'},
            {'account': 'horns&hoofs', 'login': 'h&f', 'arguments': {}},
            {'account': 'horns&hoofs', 'method': 'online_score', 'arguments': {}}])
    def test_invalid_method_request(self, request):
        """
        Test invalid method request
        Request is valid if all fields are valid.
        """
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([{},
            {'phone': '79161234567'},
            {'email': 'chirkov@ya.ru'},
            {'first_name': 'Artem'},
            {'last_name': 'Chirkov'},
            {'gender': 0},
            {'birthday': '15.05.1993'},
            {'phone': '79161234567', 'first_name': 'Artem'},
            {'phone': '79161234567', 'last_name': 'Chirkov'},
            {'phone': '79161234567', 'gender': 0},
            {'phone': '79161234567', 'birthday': '15.05.1993'},
            {'email': 'chirkov@ya.ru', 'first_name': 'Artem'},
            {'email': 'chirkov@ya.ru', 'last_name': 'Chirkov'},
            {'email': 'chirkov@ya.ru', 'gender': 0},
            {'email': 'chirkov@ya.ru', 'birthday': '15.05.1993'},
            {'first_name': 'Artem', 'gender': 0},
            {'first_name': 'Artem', 'birthday': '15.05.1993'},
            {'last_name': 'Chirkov', 'gender': 0},
            {'last_name': 'Chirkov', 'birthday': '15.05.1993'}])
    def test_invalid_score_request_no_required_pairs(self, arguments):
        """ Test absent paired arguments  """
        request = {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score', 'arguments': arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([{'phone': '79161234567', 'email': 'chirkov.ru'},
            {'phone': '9161234567', 'email': 'chirkov@ya.ru'},
            {'gender': 4, 'birthday': '15.05.1993'},
            {'gender': 0, 'birthday': '32.05.1993'},
            {'first_name': 0, 'last_name': 'Chirkov'},
            {'gender': 'Artem', 'last_name': 0}])
    def test_invalid_score_request_required_invalid_pairs(self, arguments):
        """ Test valid pairs with invalid values  """
        request = {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score', 'arguments': arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([{},
            {'date': '20.07.2017'},
            {'client_ids': [], 'date': '20.07.2017'},
            {'client_ids': [1, 2], 'date': '20.20.2020'}])
    def test_invalid_interests_request(self, arguments):
        """ Test valid interests request with invalid values"""
        request = {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'clients_interests', 'arguments': arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))


class TestValidRequests(unittest.TestCase):
    def setUp(self):
        HOST = 'redis-15377.c82.us-east-1-2.ec2.cloud.redislabs.com'
        PASSWORD = 'Z0mu2Jk5ngtOpeXdtev9GpIOuF3GJzL1'
        PORT = 15377
        TIMEOUT = 2
        DB = 0
        MAX_RETRIES = 3
        self.context = {}
        self.headers = {}
        self.store = Store(host=HOST, port=PORT, password=PASSWORD, db=DB, timeout=TIMEOUT, max_retries=MAX_RETRIES)
        self.c_int = {0: ['interest_c0'], 1: ['interest_c1'], 2: ['interest_c2'], 3: ['interest_c3'], }
        self.store.cache_set('i:0', '[\"interest_c0\"]', 20)
        self.store.cache_set('i:1', '[\"interest_c1\"]', 20)
        self.store.cache_set('i:2', '[\"interest_c2\"]', 20)
        self.store.cache_set('i:3', '[\"interest_c3\"]', 20)

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg).hexdigest()

    @cases([{"phone": "79175002040", "email": "stupnikov@otus.ru"},
            {"phone": 79175002040, "email": "stupnikov@otus.ru"},
            {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
            {"gender": 0, "birthday": "01.01.2000"},
            {"gender": 2, "birthday": "01.01.2000"},
            {"first_name": "a", "last_name": "b"},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
             "first_name": "a", "last_name": "b"}])
    def test_ok_score_request(self, arguments):
        """ Test valid online_score requests """
        request = {'account': 'horns&hoofs', 'login': 'h&f', 'method': 'online_score', 'arguments': arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        """ Test valid admin online_score requests """
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])

    def test_ok_interests_request(self, arguments):
        """ Test valid interests requests """
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        for k, v in response.items():
            self.assertTrue(v == self.c_int[k])
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


TEST_CASES = [TestInvalidRequests, TestValidRequests]
