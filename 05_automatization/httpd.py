from server import HTTPServer
import logging
import sys
import argparse
import config

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', dest='host', default=config.HOST)
    parser.add_argument('--port', dest='port', default=config.PORT)
    parser.add_argument('-w', dest='workers', default=config.WORKERS)
    parser.add_argument('-c', dest='max_connections', default=config.MAX_CONNECTIONS)
    parser.add_argument('-d', dest='document_root', default=config.DOCUMENT_ROOT)
    parser.add_argument('--log', dest='log', default=config.LOG)
    return parser.parse_args()


def create_logger(logpath):
    fmt, dfmt = '[%(asctime)s] %(levelname).1s %(message)s', '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(filename=logpath, format=fmt, datefmt=dfmt, level=logging.INFO)


if __name__ == '__main__':
    args = parse_args()
    create_logger(args.log)
    try:
        server = HTTPServer(args.host, args.port, args.document_root, args.workers, args.max_connections)
        server.start()
    except Exception as e:
        logging.error(f'Unable to launch the server: {e}')
        sys.exit()

    try:
        server.run_workers()
    except KeyboardInterrupt:
        server.terminate_workers()
    except Exception as e:
        server.terminate_workers()
        logging.error(f'Unknown error: {e}')
    finally:
        server.shutdown()
