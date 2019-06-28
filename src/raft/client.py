from socket import socket, AF_INET, SOCK_STREAM

from . import channel
from . import messages
from . import constants


def get_ch(i):
    address = constants.SERVERS[i]
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)

    ch = channel.Channel(sock)

    return ch


def send_msg(i):
    src = -1
    dst = i
    entries = ['INSERT A']

    msg = messages.OpMessage(
        src=src,
        dst=dst,
        term=None,
        entries=entries,
    )

    get_ch(dst).send(msg.serialize().encode())

