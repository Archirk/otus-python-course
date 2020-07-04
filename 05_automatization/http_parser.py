

class HTTP_parser(object):

    @classmethod
    def parse_start_line(cls, first_batch):
        txt = first_batch.decode('utf-8')
        try:
            method, uri, version = txt.split(' ')[0:3]
            return method, uri, version
        except:
            raise Exception('Unable to parse start_line')


    @classmethod
    def parse_request(cls, request):
        status_line, headers, body = request.split
