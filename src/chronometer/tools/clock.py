from datetime import datetime, timedelta, time
from typing import Union
from chronometer.tools import cal
import pytz


TimeLike = Union[datetime, time]


def _day_percent(t: TimeLike):
    t = t.time() if isinstance(t, datetime) else t
    return (t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000) / 86400


def sidereal_time(dt: datetime, lon: float) -> str:
    utc_offset = dt.utcoffset()
    offset = utc_offset.total_seconds() / 3600 if utc_offset else 0
    j = cal.julian_date(dt) - 2451545.0 + .5 - timedelta(hours=offset).total_seconds() / 86400
    l0 = 99.967794687
    l1 = 360.98564736628603
    l2 = 2.907879 * (10 ** -13)
    l3 = -5.302 * (10 ** -22)
    θ = (l0 + (l1 * j) + (l2 * (j ** 2)) + (l3 * (j ** 3)) + lon) % 360
    result = int(timedelta(hours=θ / 15).total_seconds())
    hour, remainder = divmod(result, 3600)
    minute, second = divmod(remainder, 60)
    return f'{hour:02}:{minute:02}:{second:02}'


def new_earth_time(dt: datetime) -> str:
    percent_complete = _day_percent(dt.astimezone(pytz.utc))
    degrees, remainder = divmod(int(1296000 * percent_complete), 3600)
    degrees, remainder = int(degrees), int(remainder)
    minutes, seconds = divmod(remainder, 60)
    return f'{degrees:03.0f}°{minutes:02.0f}\'{seconds:02.0f}\"'


def sit_time(dt: datetime) -> str:
    cet_date = dt.astimezone(pytz.timezone('Etc/GMT-1'))
    percent_complete = _day_percent(cet_date)
    return f'@{round(percent_complete*1000, 5):09.5f}'


def hex_time(t: TimeLike) -> str:
    t = t.time() if isinstance(t, datetime) else t
    percent_complete = _day_percent(t)
    hours, remainder = divmod(int(percent_complete * 2**28), 2**24)
    minutes, seconds = divmod(remainder, 2 ** 16)
    seconds, subseconds = divmod(seconds, 2 ** 12)
    return f'{hours:1X}_{minutes:02X}_{seconds:1X}.{subseconds:03X}'


def metric_time(t: TimeLike) -> str:
    t = t.time() if isinstance(t, datetime) else t
    percent_complete = _day_percent(t)
    hours, remainder = divmod(int(percent_complete * 100_000), 10_000)
    minutes, seconds = divmod(remainder, 100)
    return f'{hours:02}:{minutes:02}:{seconds:02}'


def unix_time(dt: datetime) -> str:
    return str(int(dt.timestamp()))


def utc_time(dt: datetime) -> str:
    return f'{dt.astimezone(pytz.utc):%H:%M:%S}'


if __name__ == '__main__':
    pass
