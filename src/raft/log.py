
class LogEntry:
    def __init__(self, term, data):
        self.term = term
        self.data = data

    def __repr__(self):
        return f"LogEntry({self.term}, '{self.data}')"

    def __eq__(self, other):
        return self.term == other.term and self.data == other.data

