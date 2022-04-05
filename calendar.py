from datetime import datetime, timedelta
import timeutil
import abbr


def julian_date(date, reduced=False):
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


def int_fix_date(dt):
    ordinal = timeutil.day_of_year(dt) + 1
    if timeutil.is_leap_year(dt):
        if ordinal > 169:
            ordinal -= 1
        elif ordinal == 169:
            return "*LEAP DAY*"
    if ordinal == 365:
        return "*YEAR DAY*"
    m, d = divmod(ordinal - 1, 28)
    m += 1
    d += 1
    w = ordinal % 7
    return abbr.weekday[w] + ' ' + abbr.intfix_month[m - 1] + " " + "{:02}".format(d)


def twc_date(dt):
    _day = timeutil.day_of_year(dt) + 1
    day = _day

    if timeutil.is_leap_year(dt):
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
    return abbr.weekday[weekday] + ' ' + abbr.month[month - 1] + " " + "{:02}".format(day)


def and_date(dt):
    day = timeutil.day_of_year(dt) + 1
    month = 1
    weekday = (day - 1) % 5

    if day == 366:
        return "*LEAP DAY*"

    exit_loop = False
    for i in range(0, 5):
        if exit_loop:
            break
        for j in [36, 37]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                exit_loop = True
                break
    return abbr.annus_day[weekday] + ' ' + abbr.annus_month[month - 1] + " " + "{:02}".format(day)


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
