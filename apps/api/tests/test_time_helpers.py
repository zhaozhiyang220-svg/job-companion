from datetime import datetime
from zoneinfo import ZoneInfo

from src.services.time_helpers import monday_of, week_range

BJT = ZoneInfo("Asia/Shanghai")


def test_monday_of_wednesday() -> None:
    d = datetime(2026, 6, 24, 12, 0, tzinfo=BJT)  # 2026-06-24 是周三
    m = monday_of(d)
    assert m.isoformat() == "2026-06-22"


def test_week_range_spans_seven_days() -> None:
    s, e = week_range(datetime(2026, 6, 22).date())
    assert (e - s).days == 6
