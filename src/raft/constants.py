from enum import Enum


class State(Enum):
    LEADER = 1
    CANDIDATE = 2
    FOLLOWER = 3


SERVERS = (
    ('localhost', '20146'),
    ('localhost', '20147'),
    ('localhost', '20148'),
    ('localhost', '20149'),
    ('localhost', '20150'),
)

