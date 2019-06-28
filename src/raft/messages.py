import json
import logging


class Message:
    def __init__(self, term, src, dst):
        self.term = term
        self.src = src
        self.dst = dst

    def __str__(self):
        return self.serialize()

    def serialize(self):
        name = self.__class__.__name__
        args = {
            attr_name: getattr(self, attr_name)
            for attr_name in dir(self)
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name))
        }
        logging.debug(f'Serializing: {name}, {args}')
        return json.dumps({
            'name': name,
            'args': args,
        })


class ElectionTimeoutMessage(Message):
    """
    When received, server should start election
    """
    def __init__(self, time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = time


class LeaderTimeoutMessage(Message):
    """
    When received, leader should send new heartbeat.
    """
    def __init__(self, time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = time


class AppendEntriesMessage(Message):
    def __init__(self, leader_id, prev_log_index, prev_log_term,
                 entries, leader_commit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.leader_commit = leader_commit


class AppendEntriesResponseMessage(Message):
    def __init__(self, success, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success = success


class RequestVoteMessage(Message):
    def __init__(self, candidate_id, last_log_index, last_log_term, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate_id = candidate_id
        self.last_log_index = last_log_index
        self.last_log_term = last_log_term


class RequestVoteResponseMessage(Message):
    def __init__(self, vote_granted=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vote_granted = vote_granted

