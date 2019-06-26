import time
from unittest import mock

from raft import utils


@mock.patch('raft.utils.time.time_ns')
def test_now(time_ns):
    time_ns.return_value = 1561567442123456789
    assert utils.now() == 1561567442123

