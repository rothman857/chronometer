from datetime import datetime
from chronometer.tools import timeutil, abbr
from itertools import accumulate


def julian_date(date: datetime, reduced: bool = False) -> float:
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jdn = date.day + (153 * m + 2) // 5 + y * 365 + y // 4 - y // 100 + y // 400 - 32045
    jd = (
        jdn
        + (date.hour - 12) / 24
        + date.minute / 1440
        + date.second / 86400
        + date.microsecond / 86400000000
    )
    return jd - 2400000 if reduced else jd


def int_fix_date(date: datetime) -> str:
    ordinal = timeutil.day_of_year(date)
    if timeutil.is_leap_year(date):
        if ordinal > 169:
            ordinal -= 1
        elif ordinal == 169:
            return "*LEAP DAY*"
    if ordinal == 365:
        return "*YEAR DAY*"
    month, day = divmod(ordinal - 1, 28)
    day += 1
    week = (ordinal - 1) % 7
    return f"{abbr.weekday[week]} {abbr.Month.ifc[month]} {day:02}"


def twc_date(date: datetime) -> str:
    day = timeutil.day_of_year(date)

    if timeutil.is_leap_year(date):
        if day == 366:
            return "*YEAR DAY*"
        elif day == 183:
            return "*LEAP DAY*"
        elif day > 183:
            day -= 1

    if day == 365:
        return "*YEAR DAY*"
    weekday = (day - 1) % 7
    month = 0
    for _ in range(0, 4):
        for j in [31, 30, 30]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                break
    return f"{abbr.weekday[weekday]} {abbr.Month.twc[month]} {day:02}"


def is_pax_leap_year(year: int):
    return (year % 100 % 6 == 0 or year % 100 == 99) and year % 400 != 0


pax_days = list(
    accumulate(
        [
            364 + 7 if i % 400 != 0 and any((i % 100 == 99, i % 100 % 6 == 0)) else 364
            for i in range(1928, 1928 + 400)
        ],
        initial=0,
    )
)


def pax_date(date: datetime) -> str:
    cycle, position = divmod(
        (date.replace(tzinfo=None) - datetime(month=1, day=1, year=1928)).days, 146_097
    )
    day = 0
    pax_year = 0
    pax_day_of_year = 0
    for i in range(len(pax_days)):
        pax_year = i + 1928 + 400 * cycle
        if pax_days[i] <= position < pax_days[i + 1]:
            pax_day_of_year = position - pax_days[i]
            break

    month, day = divmod(pax_day_of_year, 28)

    if is_pax_leap_year(pax_year):
        if 335 < pax_day_of_year < 343:
            month = 12
            day = pax_day_of_year - 336
        elif pax_day_of_year >= 343:
            month = 13
            day = pax_day_of_year - 343
    else:
        if month == 12:
            month = 13

    sign = "+" if pax_year > date.year else " "
    return f"{sign}{abbr.weekday[day % 7]} {abbr.Month.pax[month]} {day + 1:02}"


if __name__ == "__main__":
    pass
