from socket import socketpair

from kvstore import KVServer, KVClient


def test_kvstore_smoke():
    s1, s2 = socketpair()



    KVServer(s1).run()

    client = KVClient(s2)
    client.set('k1', 'v1')
    assert client.get('k1') == 'v1'

