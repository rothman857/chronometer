from datetime import datetime, timedelta
import cal


def new_earth_time(day_percent: float) -> str:
    degrees, remainder = divmod(int(1296000 * day_percent), 3600)
    degrees, remainder = int(degrees), int(remainder)
    minutes, seconds = divmod(remainder, 60)
    return f'{degrees:03.0f}°{minutes:02.0f}\'{seconds:02.0f}\"'


def sit_time(day_percent: float) -> str:
    return f"@{round(day_percent*1000, 5):09.5f}"


def hex_time(day_percent: float) -> str:
    hours, remainder = divmod(int(day_percent * 2**28), 2**24)
    minutes, seconds = divmod(remainder, 2 ** 16)
    seconds, subseconds = divmod(seconds, 2 ** 12)
    return f'{hours:1X}_{minutes:02X}_{seconds:1X}.{subseconds:03X}'


def metric_time(day_percent: float) -> str:
    hours, remainder = divmod(int(day_percent * 100_000), 10_000)
    minutes, seconds = divmod(remainder, 100)
    return f'{hours:02}:{minutes:02}:{seconds:02}'


def sidereal_time(dt: datetime, lon: float) -> str:
    offset = dt.utcoffset().total_seconds() / 3600
    j = cal.julian_date(dt) - 2451545.0 + .5 - timedelta(hours=offset).total_seconds() / 86400
    l0 = 99.967794687
    l1 = 360.98564736628603
    l2 = 2.907879 * (10 ** -13)
    l3 = -5.302 * (10 ** -22)
    theta = (l0 + (l1 * j) + (l2 * (j ** 2)) + (l3 * (j ** 3)) + lon) % 360
    result = int(timedelta(hours=theta / 15).total_seconds())
    _ = dict()
    hour, remainder = divmod(result, 3600)
    minute, second = divmod(remainder, 60)
    return f'{hour:02}:{minute:02}:{second:02}'
