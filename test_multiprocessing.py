import multiprocessing as mp
import time

import pytest


def mock_server():
    while True:
        time.sleep(0.1)


def client_success(q):
    assert True


def client_failure(q):
    try:
        assert 1 == 2, 'Just checking'
    except Exception as e:
        # Really just need to send back anything to signal
        # failure. But why not something more...
        q.put(str(e))
        raise  # re-raise for full traceback in stdout


def test_multiprocessing():
    server = mp.Process(target=mock_server, daemon=True)
    server.start()

    queue = mp.SimpleQueue()

    client_1 = mp.Process(target=client_success, args=(queue,), daemon=True)
    client_1.start()

    client_2 = mp.Process(target=client_failure, args=(queue,), daemon=True)
    client_2.start()

    time.sleep(1)  # Let child processes do their thing

    with pytest.raises(AssertionError):
        assert queue.empty()

