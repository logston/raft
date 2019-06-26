from socket import socket, AF_INET, SOCK_STREAM

from kvstore import KVClient
from channel import Channel


address = ('localhost', 27000)

sock = socket(AF_INET, SOCK_STREAM)
sock.connect(address)

ch = Channel(sock)

client = KVClient(ch)

