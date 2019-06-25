import time
import sys
from queue import Queue
from threading import Thread


import keyboard


class Event:
    pass


class ButtonPress(Event):
    pass


class Timeout(Event):
    def __init__(self, tick):
        self.tick = tick


class TrafficLight:
    STATES = ['G', 'Y', 'R']

    def __init__(self):
        self.out1 = 0
        self.out2 = 2

    def change_state(self):
        if self.out1 == 0 and self.out2 == 2:
            self.out1 = 1

        elif self.out1 == 1 and self.out2 == 2:
            self.out1 = 2
            self.out2 = 0

        elif self.out1 == 2 and self.out2 == 0:
            self.out1 = 2
            self.out2 = 1

        elif self.out1 == 2 and self.out2 == 1:
            self.out1 = 0
            self.out2 = 2

    def __repr__(self):
        return ' '.join((self.STATES[self.out1], self.STATES[self.out2]))


def run_queue(queue, light):

    event = None
    ticks = 0
    while True:

        if event is None:
            event = queue.get_nowait()

        print(ticks, ': ', light)
        ticks += 1
        time.sleep(1)

        if isinstance(event, ButtonPress):
            if light.out1 == 1:
                light.change_state()
                queue.queue.clear()
                queue.put(Timeout(ticks + 5))
                event = None

        elif isinstance(event, Timeout) and event.tick <= ticks:
            if light.out1 in (0, 2):
                light.change_state()
                queue.put(Timeout(ticks + 5))
                event = None

            elif light.out1 == 1:
                light.change_state()
                queue.put(Timeout(ticks + 30))
                event = None


def event_listener(queue):
    while True:
        sys.stdin.readline()
        print('here')
        queue.put(ButtonPress())


def main():
    light = TrafficLight()
    queue = Queue()

    queue.put(Timeout(5))
    thread = Thread(target=run_queue, args=(queue, light), daemon=True)
    thread.start()
    thread = Thread(target=event_listener, args=(queue,), daemon=True)
    thread.start()

    while True:
        time.sleep(0.1)


if __name__ == '__main__':
    main()

