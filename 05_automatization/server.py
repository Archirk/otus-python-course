import socket
import logging
import threading
import multiprocessing as mp
from http_parser import HTTP_Request, HTTP_Response



class HTTPServer(object):
    def __init__(self, host, port, document_root, workers, max_connections, batch_size=2048):
        self.host = host
        self.port = int(port)
        self.document_root = document_root
        self.workers = int(workers)
        self.running_workers = []
        self.max_connections = max_connections
        self.batch_size = batch_size
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(self.max_connections)
        logging.info(f'Server is launched at {self.host}:{self.port}')

    def shutdown(self):
        self.server.shutdown(socket.SHUT_RDWR)
        logging.info(f'Server at {self.host}:{self.port} is shutdown')

    def handle(self, client_socket, client_address):
        request = HTTP_Request(self.receive(client_socket), self.document_root)
        request.validate_method()
        request.validate_uri()
        logging.info(f'Request from {client_address[0]}:{client_address[1]} - {request.method}')
        response = HTTP_Response(request)
        response.set_body()
        response.set_headers()
        response.set_status_line()
        if request.method != 'GET':
            response.body = b''
        response = response.generate_response()
        client_socket.sendall(response)
        client_socket.close()

    def receive(self, client_socket):
        data = ''
        while True:
            batch = client_socket.recv(self.batch_size)
            data += batch.decode('utf-8')
            if '\r\n\r\n' in data:
                break
        return data

    def listen(self):
        while True:
            client_socket, client_address = self.server.accept()
            logging.info(f'Connection established with: {client_address[0]}:{client_address[1]}')
            client_handler = threading.Thread(target=self.handle, args=(client_socket, client_address))
            client_handler.start()

    def run_workers(self):
        self.running_workers = []
        for i in range(self.workers):
            worker = mp.Process(target=self.listen, name=f'OTUS_SERVER_WORKER_{i+1}')
            self.running_workers.append(worker)
            worker.start()
            logging.info(f'{worker.name} is created')
        for w in self.running_workers:
            w.join()

    def terminate_workers(self):
        for w in self.running_workers:
            w.terminate()
            logging.info(f'{w.name} is terminated')


