from unittest import mock

from raft import constants
from raft import messages
from raft import utils
from raft.machine import Machine


@mock.patch('raft.machine.utils.now')
def test_init(now):
    now.return_value = 123456789

    controller = mock.MagicMock()
    servers = []
    id_ = 1

    m = Machine(id_, controller, servers)
    assert m.current_term == 0
    assert m.voted_for == None
    assert m.log == []
    assert m.commit_index == 0
    assert m.last_applied == 0
    assert m.next_index == 0
    assert m.match_index == 0

    assert m._id == id_
    assert m._servers == servers
    assert m._state == constants.State.FOLLOWER
    assert m._election_timeout in range(150, 300)
    assert m._controller is controller

    # assert controller called with TimeMessage
    first_call_args = m._controller.enqueue.call_args[0]
    first_arg = first_call_args[0]
    assert isinstance(first_arg, messages.TimeMessage)
    assert first_arg.src == id_
    assert first_arg.dst == id_
    assert first_arg.time == 123456789 + m._election_timeout


def test_handle_append_entries_leader_to_follower():
    controller = mock.MagicMock()
    servers = []
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


def test_handle_append_entries_candidate_to_follower():
    controller = mock.MagicMock()
    servers = []
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

