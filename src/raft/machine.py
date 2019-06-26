import random

from . import constants
from . import messages
from . import utils


class Machine:
    def __init__(self, id_, controller, servers=constants.SERVERS):
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0
        self.next_index = 0
        self.match_index = 0

        self._id = id_
        self._servers = servers
        self._state = constants.State.FOLLOWER
        self._election_timeout = random.randint(150, 300)
        self._controller = controller

        # Schedule first timeout
        m = messages.TimeMessage(
            src=self.id,
            dst=self.id,
            time=utils.now() + self._election_timeout,
        )
        self._controller.enqueue(m)

    @property
    def id(self):
        return self._id

    def handle_append_entries(self, msg: messages.AppendEntriesMessage):
        """
        Could be heartbeat.
        Leader -> Follower
        Follower -> Follower

        Could be append entires request during vote.
        Candidate -> Follower

        Could just be append entires request.
        Follower -> Follower
        """
        # Need to check if should be demoted
        if self._state in (constants.State.CANDIDATE, constants.State.LEADER):
            if msg.term >= self.current_term:
                self._state = constants.State.FOLLOWER
                self.voted_for = msg.leader_id

    def handle_no_comm_election_timeout(self, msg):
        """
        If a follower receives no communication over a period of time,
        called the election timeout, then it assumes there is no viable
        leader and begins an election to choose a new leader.

        Follower -> Candidate
        """
        # Increment term

        # Change to candidate state

        # Vote for self

        # Issue requests for vote to every other server in cluster

    def handle_request_vote(self, msg):
        """
        Some other server has asked this server for its vote for leader.

        Follower -> Follower
        """

    def handle_request_vote_reply(self, msg):
        """
        Received vote from other server.

        Follower -> Follower
        Candidate -> Leader
        """
        # If not in candidate state, ignore

        # If received a majority of votes, promote to leader

        # Send heartbeats to establish control

