import time
import sys

INITIAL = {
    'out1': 'G',
    'out2': 'R',
    'clock': 0,
    'walk': False,
}

G1 = lambda s: (s['out1'] == 'G' and
                s['out2'] == 'R' and
                ((s['clock'] < 30 and dict(s, clock=s['clock'] + 1)) or
                 (s['clock'] == 30 and dict(s, clock=0, out1='Y'))))

Y1 = lambda s: (s['out1'] == 'Y' and
                s['out2'] == 'R' and
                ((s['clock'] < 5 and dict(s, clock=s['clock'] + 1)) or
                 (s['clock'] == 5 and dict(s, clock=0, out1='R', out2='G'))))

G2 = lambda s: (s['out1'] == 'R' and
                s['out2'] == 'G' and
                ((s['clock'] < 60 and dict(s, clock=s['clock'] + 1)) or
                 (s['clock'] == 60 and dict(s, clock=0, out2='Y'))))

Y2 = lambda s: (s['out1'] == 'R' and
                s['out2'] == 'Y' and
                ((s['clock'] < 5 and dict(s, clock=s['clock'] + 1)) or
                 (s['clock'] == 5 and dict(s, clock=0, out1='G', out2='R'))))

TICK = lambda evt, s: evt == 'tick' and (G1(s) or Y1(s) or G2(s) or Y2(s))
BUTTON = lambda evt, s: evt == 'button' and dict(s, walk=True)

NEXT = lambda evt, s: TICK(evt, s) or BUTTON(evt, s)


def run():
    import queue
    import threading

    event_queue = queue.Queue()

    def run_timer():
        while True:
            time.sleep(1)
            event_queue.put('tick')

    def run_button():
        while True:
            sys.stdin.readline()
            event_queue.put('button')

    threading.Thread(target=run_timer, daemon=True).start()
    threading.Thread(target=run_button, daemon=True).start()

    state = INITIAL
    while state:
        print(state)
        evt = event_queue.get()
        state = NEXT(evt, state)

try:
    run()
except KeyboardInterrupt:
    pass
