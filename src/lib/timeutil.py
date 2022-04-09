from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Union
from . import trig, cal
import pytz
from enum import Enum, auto


class SunEvent(Enum):
    SUNRISE = auto()
    SUNSET = auto()
    NOON = auto()
    DAYLIGHT = auto()
    NIGHTTIME = auto()


def is_leap_year(dt: datetime) -> bool:
    year = dt.year
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False


def day_of_year(dt: datetime) -> int:
    dt = dt.replace(tzinfo=None)
    return (dt - datetime(dt.year, 1, 1)).days


def get_local_date_format() -> str:
    today = date.today()
    today_str = today.strftime('%x').split('/')
    if int(today_str[0]) == today.month and int(today_str[1]) == today.day:
        return "{month:02}/{day:02}"
    else:
        return "{day:02}/{month:02}"


def leap_drift(dt: datetime) -> float:
    dt = dt.replace(tzinfo=None)
    ratio = 365 / 365.2425
    start_year = dt.year - (dt.year % 400)
    if dt.year == start_year:
        if dt < datetime(month=3, day=1, year=dt.year):
            start_date = datetime(month=3, day=1, year=dt.year - 400)
        else:
            start_date = datetime(month=3, day=1, year=dt.year)
    else:
        start_date = datetime(month=3, day=1, year=start_year)

    seconds = (dt - start_date).total_seconds()
    actual_seconds = seconds * ratio
    diff = seconds - actual_seconds
    shift = leapage(dt) * 86400 - diff
    return shift


def leapage(dt: datetime) -> float:
    years = (dt.year - 1) % 400
    count = years // 4
    count -= years // 100
    count += years // 400

    if is_leap_year(dt):
        if dt.month == 2 and dt.day == 29:
            percent_complete = (
                dt - datetime(month=2, day=29, year=dt.year)
            ).total_seconds() / 86400
            count += percent_complete
        elif dt >= datetime(month=3, day=1, year=dt.year):
            count += 1
            pass

    if count == 97:
        count = 0
    return count


class Sun:
    def __init__(self, date: datetime, lon: float, lat: float) -> None:
        self.lon = lon
        self.lat = lat
        self._date = date

    def refresh(self, offset: int = 0, fixed: bool = False) -> None:
        n = cal.julian_date(self.date) - 2451545.0 + .5 + .0008
        n = n if fixed else int(n)
        n += offset
        J_star = n + (-self.lon / 360)
        M = (357.5291 + 0.98560028 * J_star) % 360
        C = 1.9148 * trig.sin(M) + 0.0200 * trig.sin(2 * M) + 0.0003 * trig.sin(3 * M)
        λ = (M + C + 180 + 102.9372) % 360
        self.J_transit = 2451545.0 + J_star + 0.0053 * trig.sin(M) - 0.0069 * trig.sin(2 * λ)
        δ = trig.asin(trig.sin(λ) * trig.sin(23.44))
        temp = (
            (trig.cos(90.83333) - trig.sin(self.lat) * trig.sin(δ)) /
            (trig.cos(self.lat) * trig.cos(δ))
        )
        self.ω0 = trig.acos(temp)

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, dt: datetime):
        self._date = dt.astimezone(pytz.utc).replace(tzinfo=None)

    @property
    def daylight(self):
        return 2 * self.ω0 / 15 * 3600

    @property
    def nighttime(self):
        return 2 * (180 - self.ω0) / 15 * 3600

    @property
    def sunrise_timer(self):
        return (self.date - jul_to_greg(self.J_transit - (self.ω0 / 360))).total_seconds()

    @property
    def sunset_timer(self):
        return (self.date - jul_to_greg(self.J_transit + (self.ω0 / 360))).total_seconds()

    @property
    def solar_noon(self):
        offset = (self.date - jul_to_greg(self.J_transit)).total_seconds()
        return self.date.replace(
            hour=12, minute=0, second=0, microsecond=0
        ) + timedelta(seconds=offset)


def jul_to_greg(J: float) -> datetime:
    J += .5
    _J = int(J)
    f = _J + 1401 + (((4 * _J + 274277) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    g = (e % 1461) // 4
    h = 5 * g + 2
    day = (h % 153) // 5 + 1
    month = ((h // 153 + 2) % 12) + 1
    year = (e // 1461) - 4716 + (12 + 2 - month) // 12
    return (
        datetime(
            day=day,
            month=month,
            year=year,
        ) + timedelta(seconds=86400 * (J - _J))
    )


if __name__ == '__main__':
    pass