import logging
from socket import socket, AF_INET, SOCK_STREAM
import threading

from kvstore import KVServer
from message import Channel


def handle_client(channel):
    logging.info('Running channel')
    KVServer(channel).run()


def server(address=('', 27000)):
    logging.info('Starting server socket')
    sock = socket(AF_INET, SOCK_STREAM)

    sock.bind(address)
    sock.listen(True)

    try:
        while True:
            logging.info('Waiting for client')

            client, addr = sock.accept()
            logging.info(f'Connected to client at {addr}')
            ch = Channel(client)

            thread = threading.Thread(target=handle_client, args=(ch,))
            thread.start()
    except KeyboardInterrupt:
        logging.info('Shutdown server')


if __name__ == '__main__':
    server()

