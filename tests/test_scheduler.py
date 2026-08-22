from datetime import datetime
from zoneinfo import ZoneInfo

from app.scheduler import next_run


def test_next_run_uses_london_time_and_rolls_to_tomorrow():
    now = datetime(2026, 8, 22, 8, 30, tzinfo=ZoneInfo("Europe/London"))
    result = next_run(now, "07:00", "Europe/London")
    assert result.isoformat() == "2026-08-23T07:00:00+01:00"
