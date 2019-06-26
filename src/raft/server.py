import logging
import socket
import sys
import threading

from .kvstore import KVServer
from .channel import Channel


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def handle_client(channel, log_path):
    logging.info('Running channel')
    KVServer(channel, log_path).run()


def run_server(address=('', 27000), log_path='kvstore.log'):
    logging.info('Starting server socket')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(address)
    sock.listen(True)

    threads = []

    try:
        while True:
            logging.info('Waiting for client')

            client, addr = sock.accept()
            logging.info(f'Connected to client at {addr}')
            ch = Channel(client)

            thread = threading.Thread(target=handle_client, args=(ch, log_path))
            threads.append(thread)
            thread.start()

    except KeyboardInterrupt:
        for thread in threads:
            thread.join()

        sock.close()

        logging.info('Shutdown server')


if __name__ == '__main__':
    run_server()

