import logging
import multiprocessing as mp
from socket import socket, AF_INET, SOCK_STREAM
import time

import pytest

from raft.kvstore import KVClient
from raft.message import Channel
from raft.server import run_server

from . import utils


def create_client(address=('localhost', 27000)):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)
    ch = Channel(sock)
    client = KVClient(ch)
    return client


@utils.queue_exceptions
def client_1_test():
    client = create_client()
    client.set('k2', 'v1')
    assert client.get('k2') == 'v1'


@utils.queue_exceptions
def client_2_test():
    client = create_client()
    assert client.get('k2') == 'v1'


def test_server_smoke(tmp_path):
    log_path = tmp_path / 'kvstore.log'
    kwargs = {'log_path': log_path}
    server = mp.Process(target=run_server, kwargs=kwargs, daemon=True)
    server.start()

    queue = mp.SimpleQueue()

    client_1 = mp.Process(target=client_1_test, args=(queue,), daemon=True)
    client_1.start()

    client_2 = mp.Process(target=client_2_test, args=(queue,), daemon=True)
    client_2.start()

    time.sleep(0.25)  # gotta wait until other processes do their thing

    assert queue.empty()

    assert log_path.read_text() == '{"k2": "v1"}\n'

