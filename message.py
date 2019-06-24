from socket import socket, AF_INET, SOCK_STREAM


class Channel:
    def __init__(self, sock):
        self.sock = sock
        self.header_len = 12

    def send(self, msg: bytes):
        # Send len(msg)
        # Send msg
        assert len(msg) < 10 ** 12
        header = b'%12d' % len(msg)
        self.sock.sendall(header)
        self.sock.sendall(msg)

    def recv_exact(self, size):
        msg = b''
        while len(msg) < size:
            fragment = self.sock.recv(size - len(msg))
            if not fragment:
                raise IOError('Incomplete message')
            msg += fragment
        return msg

    def recv(self):
        # Received the size of the message
        # Received the payload (exactly the size in bytes)
        # Return the message
        header = self.sock.recv(12)
        assert len(header) == self.header_len

        msg = self.sock.recv(int(header))

        return msg

def accept_connection(address=('', 27000)):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(address)
    sock.listen(True)
    client, addr = sock.accept()
    ch = Channel(client)
    return ch

def make_connection(address=('localhost', 27000)):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(address)
    return Channel(sock)


if __name__ == '__main__':
    from socket import socketpair

    s1, s2 = socketpair()
    ch1 = Channel(s1)
    ch2 = Channel(s2)
    ch1.send(b'hi!')
    ch2.recv() == b'hi!'

