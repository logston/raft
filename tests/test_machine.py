from unittest import mock

from raft import constants
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
    assert m.next_index == 0
    assert m.match_index == 0

    assert m.id == id_
    assert m._servers == servers
    assert m._state == constants.State.FOLLOWER
    assert m._election_timeout in range(150, 300)
    assert m._controller is controller

    # assert controller called with TimeMessage
    enqueue_calls = m._controller.enqueue.mock_calls
    first_call = enqueue_calls[0]
    name, args, kwargs = first_call
    first_arg = args[0]
    assert isinstance(first_arg, messages.TimeMessage)
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
        prev_log_index=None,
        prev_log_term=None,
        entries=(),
        leader_commit=None,
    )

    m.handle_append_entries(msg)

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
        prev_log_index=None,
        prev_log_term=None,
        entries=(),
        leader_commit=None,
    )

    m.handle_append_entries(msg)

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
        prev_log_index=None,
        prev_log_term=None,
        entries=(),
        leader_commit=None,
    )

    m.handle_append_entries(msg)

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
        prev_log_index=None,
        prev_log_term=None,
        entries=(),
        leader_commit=None,
    )

    m.handle_append_entries(msg)

    assert m._state == constants.State.CANDIDATE
    assert m.voted_for == id_


def test_handle_no_comm_election_timeout():
    controller = mock.MagicMock()
    id_ = 1
    m = Machine(id_, controller)
    m._controller.enqueue.reset_mock()
    m.current_term = 5
    m._state = constants.State.FOLLOWER
    m.voted_for = None
    m.last_applied = 17

    msg = messages.TimeMessage(
        src=2,
        dst=id_,
        time=utils.now()
    )

    m.handle_no_comm_election_timeout(msg)

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

