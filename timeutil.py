from datetime import datetime, date, timedelta
import trig
import calendar
import pytz
from enum import Enum, auto


class SunEvent(Enum):
    SUNRISE = auto()
    SUNSET = auto()
    NOON = auto()
    DAYLIGHT = auto()
    NIGHTTIME = auto()


def is_leap_year(dt):
    year = dt.year
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True


def day_of_year(dt):
    dt = dt.replace(tzinfo=None)
    return (dt - datetime(dt.year, 1, 1)).days


def get_local_date_format():
    today = date.today()
    today_str = today.strftime('%x').split('/')
    if int(today_str[0]) == today.month and int(today_str[1]) == today.day:
        return "{month:02}/{day:02}"
    else:
        return "{day:02}/{month:02}"


def leap_shift(dt):
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


def leapage(dt):
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


def sunriseset(dt, lon, lat, offset=0, fixed=False, event=None):
    # https://en.wikipedia.org/wiki/Sunrise_equation
    dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
    # current julian day trig.since 1/1/2000 12:00
    n = calendar.julian_date(dt) - 2451545.0 + .5 + .0008
    n = n if fixed else int(n)
    n += offset
    J_star = n + (-lon / 360)  # Mean Solar Noon
    M = (357.5291 + 0.98560028 * J_star) % 360  # Solar mean anomaly
    C = 1.9148 * trig.sin(M) + 0.0200 * trig.sin(2 * M) + 0.0003 * \
        trig.sin(3 * M)  # Equation of the center
    λ = (M + C + 180 + 102.9372) % 360  # Ecliptic Longitude
    J_transit = 2451545.0 + J_star + 0.0053 * \
        trig.sin(M) - 0.0069 * trig.sin(2 * λ)  # Solar Transit
    δ = trig.asin(trig.sin(λ) * trig.sin(23.44))  # Declination of Sun
    temp = (trig.cos(90.83333) - trig.sin(lat) * trig.sin(δ)) / (trig.cos(lat) * trig.cos(δ))
    ω0 = trig.acos(temp)  # Hour angle
    J_rise = J_transit - (ω0 / 360)
    J_set = J_transit + (ω0 / 360)
    daylight = 2 * ω0 / 15 * 3600
    nighttime = 2 * (180 - ω0) / 15 * 3600
    t_rise = (dt - jul_to_greg(J_rise)).total_seconds()
    t_set = (dt - jul_to_greg(J_set)).total_seconds()
    t_noon = (dt - jul_to_greg(J_transit)).total_seconds()
    if event == SunEvent.SUNRISE:
        return t_rise
    elif event == SunEvent.SUNSET:
        return t_set
    elif event == SunEvent.NOON:
        return t_noon
    elif event == SunEvent.DAYLIGHT:
        return daylight
    elif event == SunEvent.NIGHTTIME:
        return nighttime
    else:
        return t_rise, t_set, t_noon


def jul_to_greg(J):
    J += .5
    _J = int(J)
    f = _J + 1401 + (((4 * _J + 274277) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    g = (e % 1461) // 4
    h = 5 * g + 2
    D = (h % 153) // 5 + 1
    M = ((h // 153 + 2) % 12) + 1
    Y = (e // 1461) - 4716 + (12 + 2 - M) // 12
    return (
        datetime(
            year=Y,
            day=D,
            month=M
        ) + timedelta(seconds=86400 * (J - _J))
    )
