
class Message:
    def __init__(self, term, src, dst):
        self.term = term
        self.src = src
        self.dst = dst


class ElectionTimeoutMessage(Message):
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

