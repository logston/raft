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

    def recv(self):
        # Received the size of the message
        # Received the payload (exactly the size in bytes)
        # Return the message
        header = self.sock.recv(12)

        if header == b'':
            # Client has closed connection
            raise IOError('Client closed connection')

        assert len(header) == self.header_len, header

        msg = self.sock.recv(int(header))

        return msg

