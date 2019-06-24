class Channel:
    def __init__(self, sock):
        self.sock = sock
        self.header_len = 12

    def send(self, msg: bytes):
        # Send len(msg)
        # Send msg
        assert len(msg) < 10 ** 12
        header = b'{:12d}'.format(len(msg))
        self.sock.sendall(header)
        self.sock.sendall(msg)

    def recv(self):
        # Received the size of the message
        # Received the payload (exactly the size in bytes)
        # Return the message
        header = self.sock.recv(12)
        assert len(header) == self.header_len

        msg = self.sock.recv(int(header))

        return msg


if __name__ == '__main__':
    from socket import socket, AF_INET, SOCK_STREAM

    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(('', 27000))
    sock.listen(True)
    client, addr = sock.accept()
    ch = Channel(client)

