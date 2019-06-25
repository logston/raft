import functools


def clear_kvstore_log(func):
    with open('kvstore.log', 'w') as fp:
        fp.write('START\n')

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    with open('kvstore.log', 'w') as fp:
        fp.write('DONE\n')

    return wrapper


def queue_exceptions(func):
    """
    Decorate subprocesses tests with this to catch their failed assertions
    and places them in the queue passed to the subprocess.
    """
    @functools.wraps(func)
    def wrapper(q):
        try:
            func()
        except Exception as e:
            q.put(str(e))
            raise
    return wrapper

