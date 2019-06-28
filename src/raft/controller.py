import queue
import threading
import socket
import json
import logging
import random
import sys
import time

from . import channel
from . import constants
from . import messages
from . import utils
from .machine import Machine


log = logging.getLogger(__name__)


class Controller:
    def __init__(self, id_, servers=constants.SERVERS):
        self.id = id_
        self.servers = servers

        self.inbox = queue.Queue()
        self.outbox = queue.Queue()

        self.machine = Machine(self.id, self, self.servers)

        self.channel = None

    def run(self):
        self.create_listen_socket()

        threading.Thread(
            target=self.handle_outbox,
            daemon=True,
        ).start()

        threading.Thread(
            target=self.handle_inbox,
            daemon=True,
        ).start()

        self.handle_incomming_connections()

    def create_listen_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        address = self.servers[self.id]
        sock.bind(address)
        sock.listen(True)
        log.debug(f'{self.id} - LISTENING: on {address}')

        self.channel = channel.Channel(sock)

    def create_channel(self, i):
        address = self.servers[i]

        log.debug(f'{self.id} - CONNECTING: -> {i} @ {address}')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        log.debug(f'{self.id} - CONNECTED: -> {i}')
        return channel.Channel(sock)

    def enqueue(self, msg):
        # If it is a timeout message, send to other servers after delay
        delivery_time = getattr(msg, 'time', 0)
        if delivery_time > 0:
            log.debug(f'{self.id} - ENQUEUE - {delivery_time - utils.now()}')
        sleep_time = 0
        if delivery_time:
            # put on outbox queue in future
            sleep_time = (delivery_time - utils.now()) / 1000

        log.info(f'{self.id} - OUTBOX: -> {msg.dst} sending item: {msg}')
        threading.Thread(
            target=self.delay_outbox,
            args=(sleep_time, msg),
            daemon=True,
        ).start()

    def delay_outbox(self, sleep_time, item):
        time.sleep(sleep_time)
        self.outbox.put(item)

    def handle_incomming_connections(self):
        while True:
            try:
                client, client_address = self.channel.sock.accept()
            except KeyboardInterrupt:
                sys.exit(0)

            log.debug(f'{self.id} - LISTENING: <- {client_address}')
            ch = channel.Channel(client)
            threading.Thread(
                target=self.handle_channel,
                args=(ch,),
            ).start()

    def handle_channel(self, ch):
        while True:
            log.debug(f'{self.id} - CHANNEL: waiting for data')

            try:
                data = ch.recv().decode()
            except OSError as e:
                log.debug(f'{self.id} - CHANNEL: {e}')
                break

            msg = self.deserialize_msg(data)

            log.debug(f'{self.id} - CHANNEL: Putting on queue: {msg}')

            self.inbox.put(msg)

    def deserialize_msg(self, data):
        serialized_msg = json.loads(data)

        name = serialized_msg.get('name')
        args = serialized_msg.get('args')

        msg = getattr(messages, name)(**args)

        return msg

    def handle_outbox(self):
        while True:
            log.debug(f'{self.id} - OUTBOX: waiting for item')
            msg = self.outbox.get()

            if msg.dst == self.id:  # No point in sockets if its going to the same controller
                self.inbox.put(msg)
            else:
                # send message down pipe
                try:
                    self.create_channel(msg.dst).send(msg.serialize().encode())
                except Exception as e:
                    log.debug(f'{self.id} - OUTBOX: -> {msg.dst} send failed. Trying again')
                    self.outbox.put(msg)

    def handle_inbox(self):
        while True:
            log.debug(f'{self.id} - INBOX: waiting for msg')
            msg = self.inbox.get()
            log.debug(f'{self.id} - INBOX: fetched: {msg.__class__.__name__} from {msg.src}')

            getattr(self.machine, f'handle_{msg.__class__.__name__}')(msg)

