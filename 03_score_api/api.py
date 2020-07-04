#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from validation_error import ValidationError
import scoring

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field(object):
    def __init__(self, required, nullable=False, value=None, name=None):
        self.required = required
        self.nullable = nullable
        self.value = value
        self.name = name

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

    def check_requirements(self):
        if self.required and self.value is None:
            msg = 'Value for field \'%s\' is required, received \'%s\' instead ' % (self.name, self.value)
            raise ValidationError(msg)
        elif not self.nullable and not isinstance(self.value, int) and self.value is not None and len(self.value) == 0:
            msg = 'Value for field \'%s\' can not be empty, received \'%s\' instead ' % (self.name, self.value)
            raise ValidationError(msg)

    @abc.abstractmethod
    def check_type(self):
        raise NotImplementedError('check_type function is not defined for %s' % self.__class__.__name__)

    def validate(self):
        self.check_requirements()
        self.check_type()

    @property
    def is_empty(self):
        return not isinstance(self.value, int) and (self.value is None or len(self.value) == 0)


class CharField(Field):
    def check_type(self):
        accepted = (str, int)
        if self.name in ('first_name', 'last_name'):
            accepted = (str,)
        if not isinstance(self.value, accepted) and self.value is not None:
            msg = 'Value for field \'%s\' has wrong type' % self.name
            raise ValidationError(msg)


class ArgumentsField(Field):
    def check_type(self):
        accepted = (dict, list, tuple)
        if not isinstance(self.value, accepted) and self.value is not None:
            msg = 'Value for field \'%s\' can must be dict or array-like, received \'%s\' instead ' % (self.name,
                                                                                                       self.value)
            raise ValidationError(msg)


class EmailField(CharField):
    def validate(self):
        if not self.is_empty:
            if '@' not in str(self.value):
                msg = 'Value for field \'%s\' must be an email string, received \'%s\' instead' % (
                    self.name, self.value)
                raise ValidationError(msg)


class PhoneField(CharField):
    def validate(self):
        l, c = 11, '7'
        if not self.is_empty:
            if len(str(self.value)) != l or str(self.value)[0] != c:
                msg = '''Value for field \'%s\' must be an %s symbols long starting with %s, received \'%s\' instead''' \
                      % (self.name, l, c, self.value)
                raise ValidationError(msg)


class DateField(CharField):
    def validate(self):
        if not self.is_empty:
            try:
                datetime.datetime.strptime(self.value, '%d.%m.%Y')
            except:
                msg = 'Value for field \'%s\' must be in format dd.mm.yyyy, received \'%s\' instead' % (
                    self.name, self.value)
                raise ValidationError(msg)


class BirthDayField(DateField):
    def validate(self):
        age_limit = 70
        if not self.is_empty:
            super(BirthDayField, self).validate()  # Check if date in expected format
            birth_date, today_date = self.value, datetime.datetime.today().strftime('%d.%m.%Y')
            bday, bmonth, byear = map(int, birth_date.split('.'))
            day, month, year = map(int, today_date.split('.'))
            msg = 'Your age must be equal or below %s' % age_limit
            if year - byear > age_limit:
                raise ValidationError(msg)
            elif year - byear == 70:
                if bmonth > month:
                    raise ValidationError(msg)
                elif bmonth == month:
                    if bday > day:
                        raise ValidationError(msg)


class GenderField(CharField):
    def validate(self):
        accepted = (0, 1, 2, '', None)
        if self.value not in accepted:
            msg = '''Value for field \'%s\' must be one of (%s), received %s instead''' \
                  % (self.name, ', '.join([str(i) for i in accepted]), self.value)
            raise ValidationError(msg)


class ClientIDsField(ArgumentsField):
    def validate(self):
        if self.is_empty:
            raise ValidationError('Value for field \'%s\'can not be empty.' % self.name)
        elif not isinstance(self.value, list):
            raise ValidationError('Value for field \'%s\' must be an array' % self.name)
        for i in self.value:
            if not isinstance(i, int):
                raise ValidationError('Array for field \'%s\'can must contain only integers' % self.name)


class Request(object):
    def __init__(self, request):
        self.available_fields = {'first_name', 'last_name', 'phone', 'email', 'birthday', 'gender', 'account',
                                 'token', 'arguments', 'method', 'client_ids', 'date', 'login'}
        self.request = request
        self.errors = []
        self.fields = self.get_class_fields()

    def read_arguments(self, arguments):
        for k, v in self.fields.items():
            try:
                self.fields[k].value = arguments[k]
                setattr(self, k, arguments[k])
            except KeyError:
                self.fields[k].value = None
                setattr(self, k, None)
            try:
                self.fields[k].validate()
            except ValidationError as e:
                self.errors.append(e.message)


    def get_class_fields(self):
        fields = {}
        for i in dir(self):
            if i in self.available_fields:
                attr = getattr(self, i)
                if isinstance(attr, Field):
                    fields[i] = attr
        return fields

    def is_valid(self):
        return len(self.errors) == 0

    @property
    def is_empty(self):
        return not self.request


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True, name='client_ids')
    date = DateField(required=False, nullable=True, name='date')

    def get_interests(self, store):
        return {c: scoring.get_interests(store, c) for c in self.client_ids}

    @property
    def nclients(self):
        return {'nclients': len(self.request['client_ids'])}


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True, name='first_name')
    last_name = CharField(required=False, nullable=True, name='last_name')
    email = EmailField(required=False, nullable=True, name='email')
    phone = PhoneField(required=False, nullable=True, name='phone')
    birthday = BirthDayField(required=False, nullable=True, name='birthday')
    gender = GenderField(required=False, nullable=True, name='gender')

    def score(self, store):
        dic = {'first_name': self.first_name,
               'last_name': self.last_name,
               'birthday': self.birthday,
               'gender': self.gender}
        return scoring.get_score(store, self.phone, self.email, **dic)

    @staticmethod
    def is_valid_pair(pair):
        if pair[0] not in (None, '') and pair[1] not in (None, ''):
            return True
        return False

    def is_valid(self):
        pairs = [(self.first_name, self.last_name),
                 (self.phone, self.email),
                 (self.birthday, self.gender)]
        if len(self.errors) == 0:
            for p in pairs:
                if self.is_valid_pair(p):
                    return True
        self.errors.append('Arguments must have at least one valid pair f-l, p-e, g-b')
        return False

    @property
    def has(self):
        return {'has': [k for k, v in self.request.items() if v != '']}


class MethodRequest(Request):
    account = CharField(required=False, nullable=True, name='account')
    login = CharField(required=True, nullable=True, name='login')
    token = CharField(required=True, nullable=True, name='token')
    arguments = ArgumentsField(required=True, nullable=True, name='arguments')
    method = CharField(required=True, nullable=False, name='method')

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    @property
    def is_token_valid(self):
        if not check_auth(self):
            self.errors.append('Token is invalid')
            return False
        return True


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def scoring_handler(request, ctx, store):
    method, arguments = request.request['method'], request.request['arguments']
    actions = {'online_score': OnlineScoreRequest,
               'clients_interests': ClientsInterestsRequest}
    sr = actions[method](arguments)
    sr.read_arguments(arguments)
    if sr.is_valid() and not sr.is_empty:
        if method == 'online_score':
            ctx.update(sr.has)
            if request.is_admin:
                return {'score': 42}, OK
            return {'score': sr.score(store)}, OK

        elif method == 'clients_interests':
            ctx.update(sr.nclients)
            return sr.get_interests(store), OK
    logging.error('%s - %s' % (INVALID_REQUEST, sr.errors))
    return sr.errors, INVALID_REQUEST


def method_handler(request, ctx, store):
    response, code = None, None
    arguments = request['body']
    mr = MethodRequest(arguments)
    mr.read_arguments(arguments)
    if mr.is_empty:
        response, code = mr.errors, INVALID_REQUEST
        logging.error('%s - %s' % (code, response))
    elif not mr.is_valid():
        response, code = mr.errors, INVALID_REQUEST
        logging.error('%s - %s' % (code, response))
    elif not mr.is_token_valid:
        response, code = mr.errors, FORBIDDEN
        logging.error('%s - %s' % (code, response))
    else:
        response, code = scoring_handler(mr, ctx, store)
        logging.info('%s - %s' % (code, response))
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
