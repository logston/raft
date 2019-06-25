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
        try:
            while True:
                logging.info('Waiting for data')

                name, args = self.recv()
                logging.info(f'Got data {name} {args}')

                if name == 'get':
                    result = get_value(args)
                elif name == 'set':
                    result = set_value(**args)

                self.ch.send(result.encode())

        except IOError:
            pass


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

