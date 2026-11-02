"""Prints the time the test servers and pages run on (SWEEP_GAME_NOW): always a session in progress, 15:00 New York time.
A weekday (Monday to Friday before the 17:00 close): that day at 15:00. The market's weekend (Friday 17:00 → Sunday 24:00):
that Friday at 15:00. (2 Nov.: on real time, the suite failed before 10:45 ET — a trade typed « now » came before the
test's own trades of the morning — and on Sunday evening, the new month's session already open.)
   python3 -I tools/game-now.py"""
import datetime
from zoneinfo import ZoneInfo
now = datetime.datetime.now(ZoneInfo('America/New_York'))
wd, h = now.isoweekday(), now.hour   # 5 = Friday, 6 = Saturday, 7 = Sunday
day = (now - datetime.timedelta(days=wd - 5)).date() if (wd == 5 and h >= 17) or wd >= 6 else now.date()
print(f'{day.isoformat()} 15:00')
