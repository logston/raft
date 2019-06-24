
data = {}

def get(key):
    return data[key]

def set(key, value):
    data[key] = value
    return True


class KVServer:
    def __init__(self, address):
        self.ch = Channel(...)

    def run(self):
        while True:
            msg = self.ch.recv()
            name, args = msg
            if name == 'get':
                result = get(args)
            elif name == 'set':
                result = set(args)
            self.ch.send(result)


class KVClient:
    def __init__(self, address):
        self.ch = Channel(...)

    def get(self, key):
        msg = .... create message ...
        ch.send(msg)
        resp = ch.recv()
        return decode(resp)

    def set(self, key, value):
        msg = ... create message...
        ch.send(msg)
        resp = ch.recv()
        return decode(resp)


