import multiprocessing as mp
from socket import socketpair

from raft.kvstore import KVServer, KVClient
from raft.channel import Channel


def test_kvstore_smoke(tmp_path):
    s1, s2 = socketpair()

    def mock_handle_client(ch, log_path):
        KVServer(ch, log_path).run()

    log_path = tmp_path / 'kvstore.log'

    ch = Channel(s1)
    server = mp.Process(
        target=mock_handle_client,
        args=(ch, log_path),
        daemon=True
    )
    server.start()

    client = KVClient(Channel(s2))
    client.set('k1', 'v1')
    assert client.get('k1') == 'v1'

    assert log_path.read_text() == '{"k1": "v1"}\n'

