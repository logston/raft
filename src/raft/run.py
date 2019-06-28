import logging
import multiprocessing as mp
import time

from . import constants
from .controller import Controller
from . import forest


log = logging.getLogger(__name__)


def run_controller(i):
    c = Controller(i)
    c.run()
    raise RuntimeError('Should never hit this')



def main():
    p_list = []
    for i in range(len(constants.SERVERS)):
        p = mp.Process(target=run_controller, args=(i,))
        p.start()
        log.warning(f'{i} is PID {p.pid}')
        p_list.append(p)

    for p in p_list:
        p.join()


try:
    main()
except KeyboardInterrupt:
    pass

