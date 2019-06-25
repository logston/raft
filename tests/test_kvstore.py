from multiprocessing import Process
from socket import socketpair

from kvstore import KVServer, KVClient
from message import Channel


def test_kvstore_smoke():
    s1, s2 = socketpair()

    server = Process(target=lambda sock: KVServer(Channel(sock)).run(), args=(s1,))
    server.start()

    client = KVClient(Channel(s2))
    client.set('k1', 'v1')
    assert client.get('k1') == 'v1'

    server.terminate()

