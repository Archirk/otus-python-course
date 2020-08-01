import responses
from datetime import datetime
import mimetypes
import re
from urllib.parse import unquote
from os import path
from pathlib import Path

class HTTP_Request(object):
    def __init__(self, request, document_root):
        self.request = request
        self.root = document_root
        self.available_methods = {'GET', 'HEAD'}
        self.method = None
        self.uri = None
        self.uri_path = None
        self.protocol = None
        self.headers = {}
        self.body = None
        self.response_code = None
        self.parse_request()
        self.normalize_uri()

    def parse_start_line(self):
        starting_line = self.request.split('\r\n')[0]
        self.method, self.uri, self.protocol = starting_line.split(' ')[0:3]

    def parse_headers(self):
        another_lines = self.request.split('\r\n')[1:]
        self.sep_index = 0
        j = 0
        for i in another_lines:
            if i == '':
                self.sep_index = j
                break
            header = i.split(': ')[0]
            value = ''.join(i.split(': ')[1:])
            self.headers[header] = value
            j += 1

    def parse_body(self):
        self.body = ''.join(self.request.split('\r\n')[1:][self.sep_index + 1:])

    def parse_request(self):
        self.parse_start_line()
        self.parse_headers()
        self.parse_body()

    def normalize_uri(self):
        self.uri = self.uri.split('?')[0].split('#')[0]
        pat = r'^\/[\/\.a-zA-Z0-9\-\_\%]+$'
        if re.match(pat, self.uri):
            self.uri_path = path.realpath(self.root + unquote(self.uri))
            if self.uri.endswith('/'):
                self.uri_path += '/index.html'
        else:
            self.response_code = responses.NOT_FOUND

    def validate_method(self):
        if self.method not in self.available_methods:
            self.response_code = responses.METHOD_NOT_ALLOWED
        else:
            self.response_code = responses.OK

    def validate_uri(self):
        root = Path.cwd() if self.root == '.' else Path(self.root)
        uri = Path(self.uri_path)
        if self.uri_path is None:
            self.response_code = responses.NOT_FOUND
        elif not path.isfile(self.uri_path):
            self.response_code = responses.NOT_FOUND
        elif root not in uri.parents:
            self.response_code = responses.FORBIDDEN


class HTTP_Response(object):
    def __init__(self, request):
        self.request = request
        self.protocol = self.request.protocol

        self.code = self.request.response_code
        self.status_line = None
        self.headers = None
        self.body = b''
        self.content_length = 0

    def __str__(self):
        return self.generate_response()

    def set_status_line(self):
        self.status_line = f'{self.protocol} {self.code} {responses.MSG[self.code]}'

    def set_headers(self):
        headers = {'Date': datetime.strftime(datetime.today(), '%a, %b %Y %H:%M:%S %Z'),
                        'Server': 'OTUS_ChirkovServer',
                        'Connection': 'close',
                        }
        if self.code == 200:
            headers['Content-Type'] = mimetypes.guess_type(self.request.uri_path)[0]
            headers['Content-Length'] = self.content_length
        self.headers = '\r\n'.join([f'{k}: {v}' for k, v in headers.items()])

    def generate_body(self):
        if self.code == responses.OK:
            with open(self.request.uri_path, 'rb') as f:
                return f.read()

    def set_content_length(self):
        self.content_length = path.getsize(self.request.uri_path)

    def set_body(self):
        self.body = b''
        if self.code == responses.OK:
            with open(self.request.uri_path, 'rb') as f:
                self.body = f.read()
                self.content_length = len(self.body)

    def generate_response(self):
        r = f'{self.status_line}\r\n{self.headers}\r\n\r\n'.encode(encoding='utf-8')
        return r + self.body
