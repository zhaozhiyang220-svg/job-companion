from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

BJT = ZoneInfo("Asia/Shanghai")


def monday_of(now: datetime | None = None) -> date:
    n = (now or datetime.now(BJT)).astimezone(BJT)
    return (n - timedelta(days=n.weekday())).date()


def week_range(monday: date) -> tuple[datetime, datetime]:
    start = datetime.combine(monday, datetime.min.time(), tzinfo=BJT)
    end = start + timedelta(days=7) - timedelta(microseconds=1)
    return start.astimezone(UTC), end.astimezone(UTC)
