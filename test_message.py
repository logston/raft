import socket
from unittest import mock

from message import Channel


def test_channel_send():
    m = mock.MagicMock(socket.socket)
    c = Channel(m)
    c.send(b'hello')
    m.sendall.assert_has_calls((
        mock.call(b'           5'),
        mock.call(b'hello'),
    ))


def test_channel_recv():
    m = mock.MagicMock(socket.socket)
    m.recv.side_effect = [
        b'           2',
        b'hi',
    ]
    c = Channel(m)
    msg = c.recv()
    assert msg == b'hi'

