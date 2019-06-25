import logging
import multiprocessing as mp
from socket import socket, AF_INET, SOCK_STREAM
import time

import pytest

from kvstore import KVClient
from message import Channel
from server import run_server


def create_client(address=('localhost', 27000)):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)
    ch = Channel(sock)
    client = KVClient(ch)
    return client


def client_1_test(q):
    try:
        client = create_client()
        client.set('k1', 'v1')
        assert client.get('k1') == 'v2'

    except Exception as e:
        q.put(str(e))
        raise

    time.sleep(0.25)


def client_2_test(q):
    try:
        client = create_client()
        assert client.get('k1') == 'v2'

    except Exception as e:
        q.put(str(e))
        raise

    time.sleep(0.25)


def test_server_smoke():
    server = mp.Process(target=run_server, daemon=True)
    server.start()

    queue = mp.SimpleQueue()

    client_1 = mp.Process(target=client_1_test, args=(queue,), daemon=True)
    client_1.start()

    client_2 = mp.Process(target=client_2_test, args=(queue,), daemon=True)
    client_2.start()

    assert queue.empty()

