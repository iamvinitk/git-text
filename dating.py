from datetime import datetime, timedelta, timezone

DAYS_IN_WEEK = 7
WEEKS_IN_YEARS = 52

today = datetime.date(datetime.now(timezone.utc))

sunday_this_week = today + timedelta(days=(6 - today.weekday()))

sunday_at_end = sunday_this_week - timedelta(days=DAYS_IN_WEEK)
sunday_at_start = sunday_this_week - timedelta(weeks=WEEKS_IN_YEARS)
