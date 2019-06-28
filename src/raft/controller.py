import queue
import threading
import socket
import logging
import random
import sys
import time

from . import channel
from . import constants
from . import utils
from .machine import Machine


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Controller:
    def __init__(self, id_, servers=constants.SERVERS):
        self.id = id_
        self.servers = servers

        self.inbox = queue.PriorityQueue()
        self.outbox = queue.PriorityQueue()

        self.machine = Machine(self.id, self, self.servers)

        self.channel = None
        self.channels = [None] * len(self.servers)

    def run(self):
        self.create_listen_socket()

        threading.Thread(
            target=self.start_talking,
            daemon=True,
        ).start()

        threading.Thread(
            target=self.handle_outbox,
            daemon=True,
        ).start()

        self.handle_incomming_connections()

    def create_listen_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        address = self.servers[self.id]
        sock.bind(address)
        sock.listen(True)
        # logging.info(f'LISTENING: {self.id} on {address}')

        self.channel = channel.Channel(sock)

    def start_talking(self):
        for i in range(len(self.servers)):
            if i != self.id:
                self.channels[i] = self.create_speak_socket(i)

    def create_speak_socket(self, i):
        address = self.servers[i]
        while True:
            try:
                logging.info(f'CONNECTING: {self.id} -> {i} @ {address}')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(address)
                break
            except ConnectionRefusedError:
                # logging.info(f'CONNECTING FAILED: ConnectionRefusedError {self.id} -> {i}. Trying again.')
                time.sleep(random.random())
            except OSError as e:
                # logging.info(f'CONNECTING FAILED: OSError {self.id} -> {i}. Trying again.')
                time.sleep(random.random())

                print(e)
                print(address)

        # logging.info(f'CONNECTED: {self.id} -> {i}')
        return sock

    def enqueue(self, msg):
        # If it is a timeout message, send to other servers after delay
        delivery_time = getattr(msg, 'time', None)
        if delivery_time is None:
            # messages with no delivery time should have a high priority (ie. 0)
            delivery_time = 0

        item  = (delivery_time, msg.dst, msg.serialize())

        if msg.dst == self.id:  # No point in sockets if its going to the same controller
            self.inbox.put(item)
        else:
            self.outbox.put(item)

    def handle_incomming_connections(self):
        while True:
            client, client_address = self.channel.sock.accept()
            # logging.info(f'LISTENING: {self.id} <- {client_address}')
            ch = channel.Channel(client)
            threading.Thread(
                target=self.handle_inbox,
                args=(ch,),
            ).start()

    def handle_inbox(self, ch):
        while True:
            logging.info(f'INBOX: {self.id} waiting for item')
            item = self.inbox.get()
            logging.info(f'INBOX: {self.id} fetched: {item}')

    def handle_outbox(self):
        while True:
            logging.info(f'OUTBOX: {self.id} waiting for item')
            delivery_time, dst, data = item = self.outbox.get()
            logging.info(f'OUTBOX: {self.id} -> {dst} sending item: {item}')

            if delivery_time and utils.now() > delivery_time:
                # not ready, put this back on the queue
                self.outbox.put(item)

            # get socket for dst

            # send message down pipe

