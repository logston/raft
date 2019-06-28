import logging
import sys


LOADED = False


def load_forest():

    global LOADED
    if LOADED:
        return

    level = 'debug'
    for i, item in enumerate(sys.argv):
        if item.lower() == '--log-level':
            level = sys.argv[i + 1]
            break

    level = getattr(logging, level.upper())

    stream = sys.stdout

    logging.basicConfig(
        stream=stream,
        level=level,
    )

    LOADED = True


load_forest()

