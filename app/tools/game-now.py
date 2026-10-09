"""Prints the time the test servers should use for the game (SWEEP_GAME_NOW), or nothing.
During the market's weekend (Friday 17:00 → Sunday 18:00 New York time) there is no open session, and several tests
need one (routine steps, Execution ring, plan): the server is pinned to that Friday 15:00 ET. Other days: real time.
   python3 -I tools/game-now.py"""
import datetime
from zoneinfo import ZoneInfo
now = datetime.datetime.now(ZoneInfo('America/New_York'))
wd, h = now.isoweekday(), now.hour   # 5 = Friday, 6 = Saturday, 7 = Sunday
if (wd == 5 and h >= 17) or wd == 6 or (wd == 7 and h < 18):
    fri = (now - datetime.timedelta(days=wd - 5)).date()
    print(f'{fri.isoformat()} 15:00')
