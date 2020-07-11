import responses
from datetime import datetime
import mimetypes

class HTTP_Request(object):
    def __init__(self, request, document_root):
        self.request = request
        self.root = document_root
        self.method = None
        self.uri = None
        self.protocol = None
        self.headers = {}
        self.body = None
        self.parse_start_line()
        self.parse_headers()
        self.parse_body()
        print(f'Starting line:\n{self.method} {self.uri} {self.protocol}')
        print(f'Headers:\n{self.headers}')
        print(f'Body:\n{self.body}')

    def parse_start_line(self):
        try:
            starting_line = self.request.split('\r\n')[0]
            self.method, self.uri, self.protocol = starting_line.split(' ')[0:3]
        except Exception as e:
            raise RuntimeError(f'Unable to parse starting line: {e}')


    def parse_headers(self):
        try:
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
        except Exception as e:
            raise RuntimeError(f'Unable to parse headers: {e}')

    def validate_uri(self):
        pass


    def parse_body(self):
        try:
            self.body = ''.join(self.request.split('\r\n')[1:][self.sep_index + 1:])
        except Exception as e:
            raise RuntimeError(f'Unable to parse request body: {e}')


class HTTP_Response(object):
    def __init__(self, request):
        self.request = request
        self.available_methods = {'GET', 'HEAD'}
        self.validate_method()
        self.code = None
        self.headers = None
        self.body = self.generate_body()
        self.response_start_line = f'{self.request.protocol} {self.code}'

    def validate_method(self):
        if self.request.method not in self.available_methods:
            self.code = responses.INVALID_METHOD
        else:
            self.code = responses.OK

    def set_headers(self):
        self.headers = {'Date': datetime.strftime(datetime.today(), '%a, %b %Y %H:%M:%S %Z'),
                        'Server': 'OTUS_ChirkovServer',
                        'Connection': 'keep-alive',
                        'Content-Type': mimetypes.guess_type(self.request.uri)[0],
                        'Content-Length': len(self.body),
                        }

    def generate_body(self):
        if self.code == responses.OK and self.request.method == 'GET':
            with open(self.request.uri, 'rb') as f:
                return f.read()
        else:
            return ''



