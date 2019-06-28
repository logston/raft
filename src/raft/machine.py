import logging
import random

from . import constants
from . import messages
from . import utils


class Machine:
    def __init__(self, id_, controller, servers=constants.SERVERS):
        ### Implementation details
        self.id = id_
        server_ids = list(range(len(servers)))
        assert id_ in server_ids, f'{self.id} not in {server_ids}'
        self._servers = servers
        self._state = constants.State.FOLLOWER
        self._election_timeout = random.randint(2000, 3000) + 200 * self.id
        self._leader_timeout = 1000
        self._controller = controller
        self._votes = 0

        ### Raft details
        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log = []

        # Volatile state
        self.commit_index = 0
        self.last_applied = 0

        # Volatile state on leaders
        self.next_index = [0] * len(self._servers)
        self.match_index = [0] * len(self._servers)

        # Schedule first timeout
        self._election_timeout_ts = 0
        self.reset_ElectionTimeoutMessage()

    def handle_AppendEntriesMessage(self, msg: messages.AppendEntriesMessage):
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
                self.voted_for = None

        # If any message is received from leader,
        # tell controller to clear its queue of time messages from this
        # machine and to enqueue a new time message from this machine.
        if self._state in (constants.State.CANDIDATE, constants.State.FOLLOWER):
            self.reset_ElectionTimeoutMessage()

        # Reply false if term < current term
        if msg.term < self.current_term:
            success = False

        # Reply false if log doesn't contain an entry at prev log index
        # whose term matches prev log term
        try:
            prev_log_entry = self.log[msg.prev_log_index]
        except IndexError:
            success = False
            m = messages.AppendEntriesResponseMessage(
                src=self.id,
                dst=msg.src,
                term=self.current_term,
                success=success,
            )
            self._controller.enqueue(m)
            return

        if prev_log_entry.term != msg.prev_log_term:
            success = False
            m = messages.AppendEntriesResponseMessage(
                src=self.id,
                dst=msg.src,
                term=self.current_term,
                success=success,
            )
            self._controller.enqueue(m)
            return

        # Reply to heartbeats
        if msg.entries:
            # truncate log with new logs
            self.log[msg.prev_log_index + 1:] = []

        # append new logs
        self.log += msg.entries

        if msg.leader_commit > self.commit_index:
            self.commit_index = min(msg.leader_commit, len(self.log) - 1)

        m = messages.AppendEntriesResponseMessage(
            src=self.id,
            dst=msg.src,
            term=self.current_term,
            success=True,
        )
        self._controller.enqueue(m)

    def handle_AppendEntriesResponseMessage(self, msg):
        if self._state != constants.State.LEADER:
            return

        if msg.success:
            # Update match index
            self.next_index[msg.src] += 1
            self.match_index[msg.src] = self.next_index[msg.src] - 1

        else:
            # Update next index
            self.next_index[msg.src] -= 1

    def get_last_log_data(self):
        index = len(self.log) - 1
        term = 0
        if self.log:
            term = self.log[index].term
        return (term, index)

    def handle_ElectionTimeoutMessage(self, msg):
        """
        If a follower receives no communication over a period of time,
        called the election timeout, then it assumes there is no viable
        leader and begins an election to choose a new leader.

        Follower -> Candidate
        """
        # Don't run for stale timeout messages
        if msg.time < self._election_timeout_ts:
            return

        # If machine is leader and it gets a timeout message,
        # no worries, its the leader no other leader timed out.
        # Just place another timeout message on the controller queue
        # and carry on.
        if self._state == constants.State.LEADER:
            self.reset_ElectionTimeoutMessage()
            return

        self.current_term += 1
        self._state = constants.State.CANDIDATE
        self.voted_for = self.id
        self._votes = 1

        # Get last log index and term from logs
        last_log_term, last_log_index  = self.get_last_log_data()

        # Request votes from all other servers
        for i in range(len(self._servers)):
            if i == self.id:
                continue
            msg = messages.RequestVoteMessage(
                src=self.id,
                dst=i,
                term=self.current_term,
                candidate_id=self.id,
                last_log_index=last_log_index,
                last_log_term=last_log_term,
            )
            self._controller.enqueue(msg)

        # Restart the countdown
        self.reset_ElectionTimeoutMessage()

    def reset_ElectionTimeoutMessage(self):
        self._election_timeout_ts = time = utils.now() + self._election_timeout
        # Tell controller to clear its queue of time messages from this
        # machine and to enqueue a new time message from this machine.
        m = messages.ElectionTimeoutMessage(
            src=self.id,
            dst=self.id,
            term=self.current_term,
            time=self._election_timeout_ts,
        )
        self._controller.enqueue(m)

    def handle_RequestVoteMessage(self, msg: messages.RequestVoteMessage):
        """
        Some other server has asked this server for its vote for leader.

        Follower -> Follower
        """
        if msg.term >= self.current_term:
            self.current_term = msg.term
            # If votedFor is null or equal to candidateId, and candidate's log is
            # at least as up-to-date as receiver's log, grant vote.
            if (self.voted_for is None or self.voted_for == msg.candidate_id):
                # Raft determines which of two logs is more up-to-date by comparing
                # the index and term of the last entries in the logs.
                # If the logs have last entries with different terms, then the log
                # with the later term is more up-to-date. If the logs end with the same
                # term, then whichever log is longer is more up-to-date.
                self_last_log_term_and_index = self.get_last_log_data()
                cand_last_log_term_and_index = msg.last_log_term, msg.last_log_index

                if self_last_log_term_and_index <= cand_last_log_term_and_index:
                    self.voted_for = msg.candidate_id

                    msg = messages.RequestVoteResponseMessage(
                        src=self.id,
                        dst=msg.src,
                        term=msg.term,
                        vote_granted=True,
                    )
                    self._controller.enqueue(msg)
                    return
                else:
                    logging.info(f'{self.id} - RequestVoteMessage, index issues, reject')
            else:
                logging.info(f'{self.id} - RequestVoteMessage, voted for {self.voted_for}, reject')
        else:
            logging.info(f'{self.id} - RequestVoteMessage, term too low, reject')

        msg = messages.RequestVoteResponseMessage(
            src=self.id,
            dst=msg.src,
            term=self.current_term,
            vote_granted=False,
        )
        self._controller.enqueue(msg)

    def handle_RequestVoteResponseMessage(self, msg):
        """
        Received vote from other server.

        Candidate -> Leader
        """
        # If not in candidate state, ignore
        if self._state != constants.State.CANDIDATE:
            return

        if msg.term != self.current_term:
            logging.warning(
                f'{self.id} - Rejecting vote from {msg.src} because term is out of date'
                f'\n{msg.term} != {self.current_term}'
            )
            return

        if not msg.vote_granted:
            logging.warning(f'{self.id} - vote not granted')
            return

        self._votes += 1

        logging.warning(f'{self.id} - GOT A VOTE FROM {msg.src}')

        if self._votes > (len(self._servers) / 2):
            logging.warning(f'{self.id} - !!!!!! BECAME LEADER !!!!!')
            # If received a majority of votes, promote to leader
            self._state = constants.State.LEADER

            # Reinitialize next and match indexes
            _, last_log_index  = self.get_last_log_data()
            self.next_index = [last_log_index + 1] * len(self._servers)
            self.match_index = [0] * len(self._servers)

            # Tell other servers about new reign
            # Send heartbeats to establish control
            for i in range(len(self._servers)):
                if i == self.id:
                    continue

                self.send_heartbeat(i)

            msg = messages.LeaderTimeoutMessage(
                src=self.id,
                dst=self.id,
                term=self.current_term,
                time=utils.now() + self._leader_timeout,
            )
            self._controller.enqueue(msg)

    def handle_LeaderTimeoutMessage(self, msg):
        # Tell other servers about new reign
        # Send heartbeats to establish control
        for i in range(len(self._servers)):
            if i == self.id:
                continue

            self.send_heartbeat(i)

        msg = messages.LeaderTimeoutMessage(
            src=self.id,
            dst=self.id,
            term=self.current_term,
            time=utils.now() + self._leader_timeout,
        )
        self._controller.enqueue(msg)

    def send_heartbeat(self, dst):
        last_log_term, last_log_index  = self.get_last_log_data()

        msg = messages.AppendEntriesMessage(
            src=self.id,
            dst=dst,
            term=self.current_term,
            leader_id=self.id,
            prev_log_index=last_log_index,
            prev_log_term=last_log_term,
            entries=(),
            leader_commit=self.commit_index,
        )
        self._controller.enqueue(msg)


