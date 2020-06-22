#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import scoring
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from dateutil.relativedelta import relativedelta

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


class CharField(object):
    def __init__(self, required, nullable, value=None):
        self.value = value
        self.required = required
        self.nullable = nullable

    def __str__(self):
        return self.value


    @property
    def is_valid(self):
        if self.required and self.value is None:
            return False
        elif not self.nullable and self.value == '':
            return False
        elif self.value is None or isinstance(self.value, str):
            return True
        else:
            return False



class ArgumentsField(object):
    def __init__(self, required, nullable, value=None):
        self.value = value
        self.required = required
        self.nullable = nullable

    @property
    def is_valid(self):
        if self.nullable and self.value == {} or not self.required and self.value is None:
            return True
        elif isinstance(self.value, dict):
            return True
        else:
            return False



class EmailField(CharField):
    @property
    def is_valid(self):
        if super(EmailField, self).is_valid:
            if self.nullable and self.value == '' or not self.required and self.value is None:
                return True
            else:
                return '@' in self.value
        else:
            return False


class PhoneField(object):
    def __init__(self, required, nullable, value=None):
        self.value = value
        self.required = required
        self.nullable = nullable
    @property
    def is_valid(self):
        if self.nullable and self.value == '' or not self.required and self.value is None:
            return True
        else:
            return len(str(self.value)) == 11 and str(self.value)[0] == '7'



class DateField(CharField):
    @property
    def is_valid(self):
        if super(DateField, self).is_valid:
            if self.nullable and self.value == '' or not self.required and self.value is None:
                return True
            else:
                try:
                    datetime.datetime.strptime(self.value, '%d.%m.%Y')
                    return True
                except:
                    return False
        else:
            return False


class BirthDayField(DateField):
    @property
    def is_valid(self):
        if super(BirthDayField, self).is_valid:
            if self.nullable and self.value == '' or not self.required and self.value is None:
                return True
            else:
                birth_date = datetime.datetime.strptime(self.value, '%d.%m.%Y')
                today_date = datetime.datetime.today()
                return relativedelta(today_date, birth_date).years <= 70
        else:
            return False



class GenderField(CharField):
    @property
    def is_valid(self):
        if self.nullable and self.value == '' or not self.required and self.value is None:
            return True
        else:
            return self.value in [0, 1, 2]


class ClientIDsField(object):
    def __init__(self, required, nullable, value=None):
        self.value = value
        self.required = required
        self.nullable = nullable

    @property
    def is_valid(self):
        if isinstance(self.value, list) and len(self.value) > 0:
            for i in self.value:
                if not isinstance(i, int):
                    return False
            return True
        else:
            return False



class MethodRequest(object):
    def __init__(self, data):
        self.account = CharField(required=False, nullable=True)
        self.login = CharField(required=True, nullable=True)
        self.token = CharField(required=True, nullable=True)
        self.arguments = ArgumentsField(required=True, nullable=True)
        self.method = CharField(required=True, nullable=False)
        for k in data:
            self.__dict__[k].value = data[k]


    @property
    def is_admin(self):
        return self.login.value == ADMIN_LOGIN

    @property
    def is_valid(self):
        for k in self.__dict__:
            if not self.__dict__[k].is_valid:
                return False
        return True

    @property
    def is_empty(self):
        for k in self.__dict__:
            if self.__dict__[k].value is not None:
                return False
        return True

    @property
    def is_token_valid(self):
        return check_auth(self)

    @property
    def has(self):
        return {'has': [k for k, v in self.arguments.value.items() if v != '']}

    @property
    def nclients(self):
        return {'nclients': len(self.arguments.value['client_ids'])}

class OnlineScoreRequest(MethodRequest):
    def __init__(self, data):
        self.first_name = CharField(required=False, nullable=True)
        self.last_name = CharField(required=False, nullable=True)
        self.email = EmailField(required=False, nullable=True)
        self.phone = PhoneField(required=False, nullable=True)
        self.birthday = BirthDayField(required=False, nullable=True)
        self.gender = GenderField(required=False, nullable=True)
        if data is not None:
            for k in data:
                self.__dict__[k].value = data[k]

    def calculate(self):
        return scoring.get_score(**self.__dict__)

    def is_valid_pair(self, pair):
        if pair[0] not in (None, '') and pair[1] not in (None, ''):
            return True
        else:
            return False

    @property
    def is_valid(self):
        pairs = [(self.first_name.value, self.last_name.value),
                 (self.phone.value, self.email.value),
                 (self.birthday.value, self.gender.value)]
        if super(OnlineScoreRequest, self).is_valid:
            for p in pairs:
                if self.is_valid_pair(p):
                    return True
            return False
        else:
            return False


class ClientsInterestsRequest(MethodRequest):
    def __init__(self, data):
        self.client_ids = ClientIDsField(required=True, nullable=False)
        self.date = DateField(required=False, nullable=True)
        if data is not None:
            for k in data:
                self.__dict__[k].value = data[k]
    @property
    def is_valid(self):
        return super(ClientsInterestsRequest, self).is_valid

def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account.value + request.login.value + SALT).hexdigest()
    if digest == request.token.value:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    mr = MethodRequest(request['body'])
    if mr.is_empty:
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    elif not mr.is_valid:
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST
    elif not mr.is_token_valid:
        return ERRORS[FORBIDDEN], FORBIDDEN


    if mr.method.value == 'online_score':
        osr = OnlineScoreRequest(mr.arguments.value)
        if osr.is_valid and not osr.is_empty:
            ctx.update(mr.has)
            if mr.is_admin:
                score, code = 42, OK
            else:
                score = osr.calculate()
            response, code = {'score': score}, OK
        else:
            code = INVALID_REQUEST
            response = ERRORS[code]

    elif mr.method.value == 'clients_interests':
        cir = ClientsInterestsRequest(mr.arguments.value)
        if cir.is_valid and not cir.is_empty:
            ctx.update(mr.nclients)
            response = {c: scoring.get_interests(c) for c in cir.client_ids.value}
            code = OK
        else:
            code = INVALID_REQUEST
            response = ERRORS[code]
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
