import time


def now():
    """
    Return now in milliseconds
    """
    return int(time.time_ns() / 1e6)

