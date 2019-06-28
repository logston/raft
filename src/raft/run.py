import multiprocessing as mp
import time

from raft import constants
from raft.controller import Controller

def run_controller(i):
    c = Controller(i)
    c.run()
    raise RuntimeError('Should never hit this')


def main():
    p_list = []
    for i in range(len(constants.SERVERS)):
        p = mp.Process(target=run_controller, args=(i,))
        p.start()
        p_list.append(p)

    for p in p_list:
        p.join()


try:
    main()
except KeyboardInterrupt:
    pass

