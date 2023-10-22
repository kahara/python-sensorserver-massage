"""Test massaging"""
import datetime
from pathlib import Path

import dateutil.tz
import pytest  # pylint: disable=W0611

from sensorserver_massage.massager import Massager


def test_massager_return_value() -> None:
    """Test massaging"""
    massager = Massager(
        Path("testdata/2023-09-14T09:06:11,142685673+00:00.jsonl"),
        Path("/dev/null"),
        datetime.datetime(2023, 9, 14, 9, 6, 11, 142685, dateutil.tz.UTC),
    )

    assert massager.run() == 0
