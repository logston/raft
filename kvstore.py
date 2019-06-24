import json
import logging


DATA = {}


def get_value(key):
    return DATA[key]


def set_value(**kwargs):
    DATA.update(kwargs)
    return 'OK'


class KVServer:
    def __init__(self, ch):
        self.ch = ch

    def recv(self):
        msg = self.ch.recv()
        data = json.loads(msg)
        return data['name'], data['args']

    def run(self):
        while True:
            logging.info('Waiting for data')

            name, args = self.recv()
            logging.info('Got data', name, args)

            if name == 'get':
                result = get_value(args)
            elif name == 'set':
                result = set_value(**args)

            self.ch.send(result.encode())


class KVClient:
    def __init__(self, ch):
        self.ch = ch

    def get(self, key):
        data = {
            'name': 'get',
            'args': key,
        }
        msg = json.dumps(data).encode()
        self.ch.send(msg)
        resp = self.ch.recv()
        return resp.decode()

    def set(self, key, value):
        data = {
            'name': 'set',
            'args': {key: value},
        }
        msg = json.dumps(data).encode()
        self.ch.send(msg)
        resp = self.ch.recv()
        return resp.decode()


if __name__ == '__main__':
    from socket import socket, AF_INET, SOCK_STREAM
    from message import Channel

    sock = socket(AF_INET, SOCK_STREAM)
    address = ('', 27000)
    sock.bind(address)
    sock.listen(True)
    client, addr = sock.accept()
    ch = Channel(client)
    logging.info('Created socket')
    KVServer(ch).run()

