from unittest import mock

from raft import constants
from raft import log
from raft import messages
from raft import utils
from raft.machine import Machine


@mock.patch('raft.machine.utils.now')
def test_init(now):
    now.return_value = 123456789

    controller = mock.MagicMock()
    servers = [(), ()]  # Need two items in list for id = 1 to be valid
    id_ = 1

    m = Machine(id_, controller, servers)
    assert m.current_term == 0
    assert m.voted_for == None
    assert m.log == []
    assert m.commit_index == 0
    assert m.last_applied == 0
    assert m.next_index == [0, 0]
    assert m.match_index == [0, 0]

    assert m.id == id_
    assert m._servers == servers
    assert m._state == constants.State.FOLLOWER
    assert m._election_timeout in range(150, 301)
    assert m._controller is controller

    # assert controller called with ElectionTimeoutMessage
    enqueue_calls = m._controller.enqueue.mock_calls
    first_call = enqueue_calls[0]
    name, args, kwargs = first_call
    first_arg = args[0]
    assert isinstance(first_arg, messages.ElectionTimeoutMessage)
    assert first_arg.src == id_
    assert first_arg.dst == id_
    assert first_arg.term == m.current_term
    assert first_arg.time == 123456789 + m._election_timeout


@mock.patch('raft.machine.utils.now')
def test_handle_schedule_time_message(now):
    now.return_value = 123456789

    controller = mock.MagicMock()
    servers = [(), ()]  # Need two items in list for id = 1 to be valid
    id_ = 1

    m = Machine(id_, controller, servers)
    m._controller.reset_mock()

    m.reset_ElectionTimeoutMessage()

    # assert controller called with ElectionTimeoutMessage
    enqueue_calls = m._controller.enqueue.mock_calls
    first_call = enqueue_calls[0]
    name, args, kwargs = first_call
    first_arg = args[0]
    assert isinstance(first_arg, messages.ElectionTimeoutMessage)
    assert first_arg.src == id_
    assert first_arg.dst == id_
    assert first_arg.time == 123456789 + m._election_timeout


def test_handle_append_entries_leader_to_follower():
    controller = mock.MagicMock()
    servers = [(), ()]  # Need two items in list for id = 1 to be valid
    id_ = 1
    m = Machine(id_, controller, servers)
    m.current_term = 5

    m._state = constants.State.LEADER

    msg = messages.AppendEntriesMessage(
        src=2,
        dst=id_,
        term=7,  # More recent term
        leader_id=2,
        prev_log_index=0,
        prev_log_term=0,
        entries=(),
        leader_commit=0,
    )

    m.handle_AppendEntriesMessage(msg)

    assert m._state == constants.State.FOLLOWER
    assert m.voted_for == 2


def test_handle_append_entries_candidate_to_follower():
    controller = mock.MagicMock()
    servers = [(), ()]  # Need two items in list for id = 1 to be valid
    id_ = 1
    m = Machine(id_, controller, servers)
    m.current_term = 5

    m._state = constants.State.CANDIDATE

    msg = messages.AppendEntriesMessage(
        src=2,
        dst=id_,
        term=7,  # More recent term
        leader_id=2,
        prev_log_index=0,
        prev_log_term=0,
        entries=(),
        leader_commit=0,
    )

    m.handle_AppendEntriesMessage(msg)

    assert m._state == constants.State.FOLLOWER
    assert m.voted_for == 2


def test_handle_append_entries_leader_to_leader_msg_term_too_small():
    controller = mock.MagicMock()
    servers = [(), ()]  # Need two items in list for id = 1 to be valid
    id_ = 1
    m = Machine(id_, controller, servers)
    m.current_term = 5

    m._state = constants.State.LEADER

    msg = messages.AppendEntriesMessage(
        src=2,
        dst=id_,
        term=3,  # Old term
        leader_id=2,
        prev_log_index=0,
        prev_log_term=0,
        entries=(),
        leader_commit=0,
    )

    m.handle_AppendEntriesMessage(msg)

    assert m._state == constants.State.LEADER


def test_handle_append_entries_candidate_to_candidate_msg_term_too_small():
    controller = mock.MagicMock()
    servers = [(), ()]  # Need two items in list for id = 1 to be valid
    id_ = 1
    m = Machine(id_, controller, servers)
    m.current_term = 5

    m._state = constants.State.CANDIDATE
    m.voted_for = id_

    msg = messages.AppendEntriesMessage(
        src=2,
        dst=id_,
        term=3,  # Old term
        leader_id=2,
        prev_log_index=0,
        prev_log_term=0,
        entries=(),
        leader_commit=0,
    )

    m.handle_AppendEntriesMessage(msg)

    assert m._state == constants.State.CANDIDATE
    assert m.voted_for == id_


def test_handle_no_comm_election_timeout_follower_to_candidate():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m.get_last_log_data = lambda: (5, 17)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m._state = constants.State.FOLLOWER
    m.voted_for = None
    m.last_applied = 17

    msg = messages.ElectionTimeoutMessage(
        src=2,
        dst=id_,
        term=m.current_term,
        time=utils.now()
    )

    m.handle_ElectionTimeoutMesssage(msg)

    assert m.current_term == 6
    assert m._state == constants.State.CANDIDATE
    assert m.voted_for == id_

    # Assert messages sent to all other servers
    enqueue_calls = m._controller.enqueue.mock_calls
    assert len(enqueue_calls) == len(m._servers) - 1
    dsts = set()
    for mock_call in enqueue_calls:
        name, args, kwargs = mock_call
        msg = args[0]
        assert isinstance(msg, messages.RequestVoteMessage)
        assert msg.src == id_
        dsts.add(msg.dst)
        assert msg.term == 6
        assert msg.candidate_id == id_
        assert msg.last_log_index == 17
        assert msg.last_log_term == 5

    assert set(range(len(m._servers))) - {id_} == dsts


def test_handle_no_comm_election_timeout_candidate_to_candidate():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m.get_last_log_data = lambda: (5, 17)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m._state = constants.State.CANDIDATE
    m.voted_for = None
    m.last_applied = 17

    msg = messages.ElectionTimeoutMessage(
        src=2,
        dst=id_,
        term=m.current_term,
        time=utils.now()
    )

    m.handle_ElectionTimeoutMesssage(msg)

    assert m.current_term == 6
    assert m._state == constants.State.CANDIDATE
    assert m.voted_for == id_

    # Assert messages sent to all other servers
    enqueue_calls = m._controller.enqueue.mock_calls
    assert len(enqueue_calls) == len(m._servers) - 1
    dsts = set()
    for mock_call in enqueue_calls:
        name, args, kwargs = mock_call
        msg = args[0]
        assert isinstance(msg, messages.RequestVoteMessage)
        assert msg.src == id_
        dsts.add(msg.dst)
        assert msg.term == 6
        assert msg.candidate_id == id_
        assert msg.last_log_index == 17
        assert msg.last_log_term == 5

    assert set(range(len(m._servers))) - {id_} == dsts


@mock.patch('raft.machine.utils.now')
def test_handle_no_comm_election_timeout_leader_to_leader(now):
    now.return_value = 123456789

    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m._state = constants.State.LEADER
    m.voted_for = id_
    m.last_applied = 17

    msg = messages.ElectionTimeoutMessage(
        src=2,
        dst=id_,
        term=m.current_term,
        time=utils.now()
    )

    m.handle_ElectionTimeoutMesssage(msg)

    assert m.current_term == 5
    assert m._state == constants.State.LEADER
    assert m.voted_for == id_

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.ElectionTimeoutMessage)
    assert first_arg.src == id_
    assert first_arg.dst == id_
    assert first_arg.term == m.current_term
    assert first_arg.time == 123456789 + m._election_timeout


def test_handle_request_vote_reply_is_leader():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.voted_for = id_
    m._state = constants.State.LEADER

    msg = messages.RequestVoteResponseMessage(
        src=0,
        dst=1,
        term=99,
    )

    m.handle_RequestVoteResponseMessage(msg)

    assert m._state == constants.State.LEADER
    m._controller.enqueue.assert_not_called()


def test_handle_request_vote_reply_is_follower():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.voted_for = id_
    m._state = constants.State.FOLLOWER

    msg = messages.RequestVoteResponseMessage(
        src=0,
        dst=1,
        term=99,
    )

    m.handle_RequestVoteResponseMessage(msg)

    assert m._state == constants.State.FOLLOWER
    m._controller.enqueue.assert_not_called()


def test_handle_request_vote_reply_is_candidate_stale_term():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.voted_for = id_
    m._state = constants.State.CANDIDATE
    m._votes = 2

    msg = messages.RequestVoteResponseMessage(
        src=0,
        dst=1,
        term=99,
    )

    m.handle_RequestVoteResponseMessage(msg)

    assert m._state == constants.State.CANDIDATE
    m._controller.enqueue.assert_not_called()


def test_handle_request_vote_reply_is_candidate_vote_not_granted():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.voted_for = id_
    m._state = constants.State.CANDIDATE
    m._votes = 2

    msg = messages.RequestVoteResponseMessage(
        src=0,
        dst=1,
        term=m.current_term,
        vote_granted=False,
    )

    m.handle_RequestVoteResponseMessage(msg)

    assert m._state == constants.State.CANDIDATE
    m._controller.enqueue.assert_not_called()


def test_handle_request_vote_reply_is_candidate_win_election():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.voted_for = id_
    m._state = constants.State.CANDIDATE
    m._votes = 2
    m.log = [log.LogEntry(m.current_term, '')]

    msg = messages.RequestVoteResponseMessage(
        src=0,
        dst=1,
        term=m.current_term,
    )

    m.handle_RequestVoteResponseMessage(msg)

    assert m._state == constants.State.LEADER

    # Assert messages sent to all other servers
    enqueue_calls = m._controller.enqueue.mock_calls
    assert len(enqueue_calls) == len(m._servers) - 1
    dsts = set()
    for mock_call in enqueue_calls:
        name, args, kwargs = mock_call
        msg = args[0]
        assert isinstance(msg, messages.AppendEntriesMessage)
        assert msg.src == id_
        dsts.add(msg.dst)
        assert msg.term == m.current_term
        assert msg.leader_id == id_
        assert msg.prev_log_term == 5
        assert msg.prev_log_index == 0
        assert msg.entries == ()
        assert msg.leader_commit == 0

    assert set(range(len(m._servers))) - {id_} == dsts


def test_send_heartbeat():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.log = [log.LogEntry(m.current_term, '')]

    m.send_heartbeat(3)

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.AppendEntriesMessage)
    assert first_arg.src == id_
    assert first_arg.dst == 3
    assert first_arg.term == m.current_term


def test_get_last_log_data():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.log = [log.LogEntry(m.current_term, '')]

    last_log_term, last_log_index = m.get_last_log_data()

    assert last_log_term == 0
    assert last_log_index == 0


def test_handle_RequestVoteMessage_candidate_term_to_low():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.log = [log.LogEntry(m.current_term, '')]
    m.voted_for = None

    msg = messages.RequestVoteMessage(
        src=4,
        dst=id_,
        term=3,
        candidate_id=4,
        last_log_index=0,
        last_log_term=0,
    )
    m.handle_RequestVoteMessage(msg)

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.RequestVoteResponseMessage)
    assert first_arg.src == id_
    assert first_arg.dst == 4
    assert first_arg.term == m.current_term
    assert not first_arg.vote_granted

def test_handle_RequestVoteMessage_voted_for_someone_else():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.log = [log.LogEntry(m.current_term, '')]
    m.voted_for = 2

    msg = messages.RequestVoteMessage(
        src=4,
        dst=id_,
        term=6,
        candidate_id=4,
        last_log_index=0,
        last_log_term=0,
    )
    m.handle_RequestVoteMessage(msg)

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.RequestVoteResponseMessage)
    assert first_arg.src == id_
    assert first_arg.dst == 4
    assert first_arg.term == m.current_term
    assert not first_arg.vote_granted


def test_handle_RequestVoteMessage_last_log_term_too_old():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m.log = [log.LogEntry(3, '')]  # self term is greater than msg last log term
    m.voted_for = None

    msg = messages.RequestVoteMessage(
        src=4,
        dst=id_,
        term=5,
        candidate_id=4,
        last_log_index=0,
        last_log_term=0,
    )
    m.handle_RequestVoteMessage(msg)

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.RequestVoteResponseMessage)
    assert first_arg.src == id_
    assert first_arg.dst == 4
    assert first_arg.term == m.current_term
    assert not first_arg.vote_granted


def test_handle_RequestVoteMessage_last_log_term_same_but_index_too_old():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 2
    m.log = [log.LogEntry(2, ''), log.LogEntry(2, '')]
    m.voted_for = None

    msg = messages.RequestVoteMessage(
        src=4,
        dst=id_,
        term=2,
        candidate_id=4,
        last_log_index=0,
        last_log_term=2,
    )
    m.handle_RequestVoteMessage(msg)

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.RequestVoteResponseMessage)
    assert first_arg.src == id_
    assert first_arg.dst == 4
    assert first_arg.term == m.current_term
    assert not first_arg.vote_granted


def test_handle_RequestVoteMessage_vote_for_candidate():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 2
    m.log = [log.LogEntry(2, '')]
    m.voted_for = None

    msg = messages.RequestVoteMessage(
        src=4,
        dst=id_,
        term=2,
        candidate_id=4,
        last_log_index=0,
        last_log_term=2,
    )
    m.handle_RequestVoteMessage(msg)

    enqueue_calls = m._controller.enqueue.mock_calls
    call = enqueue_calls[0]
    name, args, kwargs = call
    first_arg = args[0]
    assert isinstance(first_arg, messages.RequestVoteResponseMessage)
    assert first_arg.src == id_
    assert first_arg.dst == 4
    assert first_arg.term == m.current_term
    assert first_arg.vote_granted

