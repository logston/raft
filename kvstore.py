import json
from socket import socket, AF_INET, SOCK_STREAM

from message import Channel


DATA = {}


def get_value(key):
    return DATA[key]


def set_value(key, value):
    DATA[key] = value
    return 'OK'


class KVServer:
    def __init__(self, sock):
        self.ch = Channel(sock)

    def recv(self):
        msg = self.ch.recv()
        data = json.loads(msg)
        return data['name'], data['args'].split(',')

    def run(self):
        while True:
            print('Waiting for data')

            name, args = self.recv()
            print('Got data', name, args)

            if name == 'get':
                result = get_value(*args)
            elif name == 'set':
                result = set_value(*args)

            self.ch.send(result.encode())


class KVClient:
    def __init__(self, sock):
        self.ch = Channel(sock)

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
            'args': ','.join((key, value)),
        }
        msg = json.dumps(data).encode()
        self.ch.send(msg)
        resp = self.ch.recv()
        return resp.decode()


if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_STREAM)
    address = ('', 27000)
    sock.bind(address)
    sock.listen(True)
    client, addr = sock.accept()
    print('Created socket')
    KVServer(client).run()

