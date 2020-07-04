import argparse
import socket
import config
import logging
import threading
import multiprocessing as mp
from http_parser import HTTP_parser as hp



class HTTPServer(object):
    def __init__(self, host, port, document_root, workers=1, max_connections=1, batch_size=2048):
        self.host = host
        self.port = port
        self.document_root = document_root
        self.workers = workers
        self.max_connections = max_connections
        self.batch_size = batch_size
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.availbale_methods = ['GET', 'HEAD']

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
        print('Handling')
        r = self.receive(client_socket)
        status = r.split('\n')[0]
        logging.info(f'Request from {client_address[0]}:{client_address[1]} - {status}')

        client_socket.sendall(f'Got your: {r}'.encode('utf-8'))
        client_socket.close()

    def receive(self, client_socket):
        print('Receiving')
        data = ''
        i=1
        while True:
            batch = client_socket.recv(self.batch_size)
            print(len(batch))
            print(i, len(batch), print(batch.decode('utf-8')), batch is None)
            i+=1
            if batch is not None:
                break
            #if data[::-1][0] == '\r\n' and data[::-1][1] == '\r\n':
            #    break
        return ''.join(data)

    def listen(self):
        print('Listening')
        while True:
            client_socket, client_address = self.server.accept()
            logging.info(f'Connection established with: {client_address[0]}:{client_address[1]}')
            client_handler = threading.Thread(target=self.handle, args=(client_socket, client_address))
            client_handler.start()

    def create_workers(self):
        workers = []
        for i in range(self.workers):
            worker = mp.Process(target=server.listen)
            workers.append(worker)
            worker.start()

        for w in workers:
            w.join()  # ????

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', dest='host', default=config.HOST)
    parser.add_argument('--port', dest='port', default=config.PORT)
    parser.add_argument('-w', dest='workers', default=config.WORKERS)
    parser.add_argument('-d', dest='document_root', default=config.DOCUMENT_ROOT)
    parser.add_argument('--log', dest='log', default=config.LOG)
    return parser.parse_args()


def create_logger(logpath):
    fmt, dfmt = '[%(asctime)s] %(levelname).1s %(message)s', '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(filename=logpath, format=fmt, datefmt=dfmt, level=logging.INFO)


if __name__ == '__main__':
    args = parse_args()
    create_logger(args.log)
    server = HTTPServer(args.host, args.port, args.document_root)
    server.start()
    server.create_workers()

