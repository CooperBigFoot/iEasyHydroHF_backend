from datetime import datetime
from unittest.mock import patch

import pytest
from zoneinfo import ZoneInfo


@pytest.fixture
def datetime_mock():
    with patch("sapphire_backend.telegrams.parser.dt") as mock:
        mock.now.return_value = datetime(2024, 4, 15, tzinfo=ZoneInfo("UTC"))
        mock.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock


@pytest.fixture
def datetime_kyrgyz_mock():
    with patch("sapphire_backend.telegrams.parser.dt") as mock:
        mock.now.return_value = datetime(2020, 4, 15, tzinfo=ZoneInfo("Asia/Bishkek"))
        mock.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock
