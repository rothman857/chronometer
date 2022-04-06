from datetime import datetime, timedelta
from . import timeutil, abbr


def julian_date(date: datetime, reduced: bool = False) -> float:
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jdn = date.day + (153 * m + 2) // 5 + y * 365 + y // 4 - y // 100 + y // 400 - 32045
    jd = (
        jdn +
        (date.hour - 12) / 24 +
        date.minute / 1440 +
        date.second / 86400 +
        date.microsecond / 86400000000
    )
    return jd - 2400000 if reduced else jd


def int_fix_date(date: datetime) -> str:
    ordinal = timeutil.day_of_year(date) + 1
    if timeutil.is_leap_year(date):
        if ordinal > 169:
            ordinal -= 1
        elif ordinal == 169:
            return "*LEAP DAY*"
    if ordinal == 365:
        return "*YEAR DAY*"
    month, day = divmod(ordinal - 1, 28)
    month += 1
    day += 1
    week = ordinal % 7
    return f'{abbr.weekday[week]} {abbr.intfix_month[month - 1]} {day:02}'


def twc_date(date: datetime) -> str:
    day = timeutil.day_of_year(date) + 1

    if timeutil.is_leap_year(date):
        if day == 366:
            return "*YEAR DAY*"
        elif day == 183:
            return "*LEAP DAY*"
        elif day > 183:
            day -= 1

    if day == 365:
        return "*YEAR DAY*"
    weekday = day % 7
    month = 1
    for _ in range(0, 4):
        for j in [31, 30, 30]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                break
    return f'{abbr.weekday[weekday]} {abbr.month[month - 1]} {day:02}'


def and_date(date: datetime) -> str:
    day = timeutil.day_of_year(date) + 1
    month = 1
    weekday = (day - 1) % 5
    if day == 366:
        return "*LEAP DAY*"

    exit_loop = False
    for _ in range(0, 5):
        if exit_loop:
            break
        for j in [36, 37]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                exit_loop = True
                break
    return f'{abbr.annus_day[weekday]} {abbr.annus_month[month - 1]} {day:02}'


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
            year=year,
            day=day,
            month=month
        ) + timedelta(seconds=86400 * (J - _J))
    )


if __name__ == '__main__':
    pass
