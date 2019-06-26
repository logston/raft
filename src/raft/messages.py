
class Message:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class TimeMessage(Message):
    def __init__(self, time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time = time


class AppendEntriesMessage(Message):
    def __init__(self, term, leader_id, prev_log_index, prev_log_term,
                 entries, leader_commit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.term = term
        self.leader_id = leader_id
        self.prev_log_index = prev_log_index
        self.prev_log_term = prev_log_term
        self.entries = entries
        self.leader_commit = leader_commit

