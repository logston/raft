import socket
from unittest import mock

from raft.message import Channel


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


def test_smoke():
    from socket import socketpair

    s1, s2 = socketpair()
    ch1 = Channel(s1)
    ch2 = Channel(s2)
    ch1.send(b'hi!')
    ch2.recv() == b'hi!'

