from enum import Enum


class State(Enum):
    LEADER = 1
    CANDIDATE = 2
    FOLLOWER = 3


SERVERS = (
    ('127.0.0.1', 20146),
    ('127.0.0.1', 20147),
    ('127.0.0.1', 20148),
    ('127.0.0.1', 20149),
    ('127.0.0.1', 20150),
)

