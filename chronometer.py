#!/usr/bin/python3

from datetime import datetime, timedelta, date
import time
import json
import os
import threading
import subprocess
import socket
import re
import math
import random
import argparse
import pytz

ap = argparse.ArgumentParser()
ap.add_argument('-d', action='store_true', help='Debug mode')
ap.add_argument('--date', action='store', default=None)
ap.add_argument('-r', '--reset', action='store_true', help='Reset .config file')
args = ap.parse_args()

utc = pytz.utc

if args.date:
    args.d = True

here = os.path.dirname(os.path.realpath(__file__))

default_config = {'coordinates': {
    '# Note': 'Decimal notation only.  West longitude is negative.',
    'latitude': 40.7128,
    'longitude': -74.0060},
    'refresh': 0.001,
    'timezones': {
    '# Note': 'Format = label: time_zone. (time_zone must be a valid pytz time zone name.  10 times zones are required.)',
    'Pacific': 'US/Pacific',
    'Eastern': 'US/Eastern',
    'Israel': 'Israel',
    'London': 'Europe/London',
    'Sydney': 'Australia/Sydney',
    'Germany': 'Europe/Berlin',
    'Hong Kong': 'Asia/Hong_Kong',
    'India': 'Asia/Kolkata',
    'Japan': 'Asia/Tokyo',
    'Singapore': 'Singapore',
}
}

if os.path.isfile(os.path.join(here, '.config')) and not args.reset:
    with open(os.path.join(here, '.config')) as f:
        running_config = json.load(f)

else:
    with open(os.path.join(here, '.config'), 'w+') as f:
        json.dump(default_config, f, indent=2, sort_keys=True)
        running_config = default_config
        print("Initial .config file generated.  Please update it with coordinates and desired timezones before running chronometer.py again.")
        exit()

if args.reset:
    print(".config reset to defaults.")
    exit()

if args.d:
    dbg_start = datetime.now()
    dbg_override = datetime.strptime(args.date, '%b %d %Y %I:%M:%S %p')

random.seed()
is_connected = False

now = datetime.now()
def my_tz_sort(tz_entry):
    return tz_entry[1].utcoffset(now)

try:
    lat = float(running_config['coordinates']['latitude'])
    lon = float(running_config['coordinates']['longitude'])
    refresh = float(running_config['refresh'])
    time_zone_list = []
    for tz in running_config['timezones']:
        if tz[0] == '#':
            continue
        time_zone_list.append([tz.upper(), pytz.timezone(running_config['timezones'][tz])])

    time_zone_list.sort(key=my_tz_sort)
    _time_zone_list = [None] * len(time_zone_list)

    for i in range(0,len(time_zone_list), 2):
        _time_zone_list[i] = time_zone_list[i//2]
        _time_zone_list[i+1] = time_zone_list[i//2+5]

    time_zone_list = _time_zone_list


except KeyError as e:
    print("Error reading .config ({}).  Please correct or reset using --reset.".format(e))
    exit()

SECOND = 0
MINUTE = 1
HOUR = 2
DAY = 3
MONTH = 4
YEAR = 5
CENTURY = 6

LABEL = 0
VALUE = 1

ntpoff = 0
ntpdly = 0
ntpstr = "-"
ntpid = "---"

# Terminal coloring
BLACK_BG = "\x1b[40m"
WHITE_FG = "\x1b[97m"
L_BLUE_FG = "\x1b[94m"
L_BLUE_BG = "\x1b[104m"
D_GRAY_FG = "\x1b[90m"
RST_COLORS = "\x1b[0m"

themes = [BLACK_BG,      # background
          WHITE_FG,      # text
          L_BLUE_FG,    # table borders
          L_BLUE_BG,    # text highlight
          D_GRAY_FG]   # progress bar dim

weekday_abbr = ["SAT",
                "SUN",
                "MON",
                "TUE",
                "WED",
                "THU",
                "FRI"]

annus_day_abbr = ["PRI",
                  "SEC",
                  "TER",
                  "QUA",
                  "QUI"]

annus_month_abbr = ["PRI",
                    "SEC",
                    "TER",
                    "QUA",
                    "QUI",
                    "SEX",
                    "SEP",
                    "NON",
                    "DEC"]

intfix_month_abbr = ["JAN",
                     "FEB",
                     "MAR",
                     "APR",
                     "MAY",
                     "JUN",
                     "SOL",
                     "JUL",
                     "AUG",
                     "SEP",
                     "OCT",
                     "NOV",
                     "DEC"]

month_abbr = ["JAN",
              "FEB",
              "MAR",
              "APR",
              "MAY",
              "JUN",
              "JUL",
              "AUG",
              "SEP",
              "OCT",
              "NOV",
              "DEC"]

#               Label       value precision
time_table = [["S",    0,    10],
              ["M",    0,    10],
              ["H",      0,    10],
              ["D",       0,    10],
              ["M",     0,    10],
              ["Y",      0,    10],
              ["C",   0,    10]]


def reset_cursor():
    print("\033[0;0H", end="")


def draw_progress_bar(*, min=0, width, max, value):
    level = int((width + 1) * (value - min)/(max - min))
    return (chr(0x2550) * level + D_GRAY_FG + (chr(0x2500) * (width - level)))


def get_local_date_format():
    today = date.today()
    today_str = today.strftime('%x').split('/')
    if int(today_str[0]) == today.month and int(today_str[1]) == today.day:
        return "{month:02}/{day:02}"
    else:
        return "{day:02}/{month:02}"


def day_of_year(dt):
    dt = dt.replace(tzinfo=None)
    return (dt - datetime(dt.year, 1, 1)).days


def is_leap_year(dt):
    year = dt.year
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True


def net_time_strf(day_percent, fmt):
    _ = dict()
    _["degrees"], remainder = divmod(int(1296000*day_percent), 3600)
    _["degrees"], remainder = int(_["degrees"]), int(remainder)
    _["minutes"], _["seconds"] = divmod(remainder, 60)
    return fmt.format(**_)


def hex_strf(day_percent, fmt):
    _ = dict()
    _["hours"], remainder = divmod(int(day_percent * 268435456), 16777216)
    _["minutes"], _["seconds"] = divmod(remainder, 65536)
    _["seconds"], _["sub"] = divmod(_["seconds"], 4096)
    return fmt.format(**_)


def metric_strf(day_percent, fmt):
    _ = dict()
    _["hours"], remainder = divmod(int(day_percent * 100000), 10000)
    _["minutes"], _["seconds"] = divmod(remainder, 100)
    return fmt.format(**_)


def float_fixed(flt, wd, sign=False):
    wd = str(wd)
    sign = "+" if sign else ""
    return ('{:.' + wd + 's}').format(('{:' + sign + '.' + wd + 'f}').format(flt))

def _float_fixed(flt, wd, sign=False):
    sign = "+" if sign else ""
    return sign + str(flt)[:wd-(len(sign))]


def sidereal_time(dt, lon, off, fmt):
    dt = dt.replace(tzinfo=None)
    j = ((dt - datetime(year=2000, month=1, day=1)) - timedelta(hours=off)).total_seconds()/86400
    l0 = 99.967794687
    l1 = 360.98564736628603
    l2 = 2.907879 * (10 ** -13)
    l3 = -5.302 * (10 ** -22)
    theta = (l0 + (l1 * j) + (l2 * (j ** 2)) + (l3 * (j ** 3)) + lon) % 360
    result = int(timedelta(hours=theta/15).total_seconds())
    _ = dict()
    _["hour"], remainder = divmod(result, 3600)
    _["minute"], _["second"] = divmod(remainder, 60)
    return fmt.format(**_)


def julian_date(date, reduced=False):
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3

    jdn = date.day + (153*m+2)//5 + y*365 + y//4 - y//100 + y//400 - 32045
    jd = jdn + (date.hour - 12) / 24 + date.minute / 1440 + date.second / 86400 + date.microsecond / 86400000000

    return jd - 2400000 if reduced else jd


def int_fix_date(dt):
    ordinal = day_of_year(dt) + 1
    if is_leap_year(dt):
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

    #return weekday_abbr[w] + ' ' + get_local_date_format().format(month=m, day=d)
    return weekday_abbr[w] + ' ' + intfix_month_abbr[m-1] + " " + "{:02}".format(d)


def leap_shift(dt):
    dt = dt.replace(tzinfo=None)
    ratio = 365/365.2425
    start_year = dt.year - (dt.year % 400)
    if dt.year == start_year:
        if dt < datetime(month=3, day=1, year=dt.year):
            start_date = datetime(month=3, day=1, year=dt.year-400)
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
    years = (dt.year-1) % 400
    count = years // 4
    count -= years // 100
    count += years // 400

    if is_leap_year(dt):
        if dt.month == 2 and dt.day == 29:
            percent_complete = (dt - datetime(month=2, day=29, year=dt.year)).total_seconds()/86400
            count += percent_complete
        elif dt >= datetime(month=3, day=1, year=dt.year):
            count += 1
            pass

    if count == 97:
        count = 0
    return count


def sunriseset(dt, offset=0, fixed=False, event=''):  # https://en.wikipedia.org/wiki/Sunrise_equation
    n = julian_date(dt) - 2451545.0 + .0008  # current julian day since 1/1/2000 12:00
    _n = (dt - datetime(month=1, day=1, year=2000, hour=12).replace(tzinfo=utc)).total_seconds()//86400

    n = n if fixed else _n
    n += offset
    J_star = n + (-lon/360)  # Mean Solar Noon
    M = (357.5291 + 0.98560028 * J_star) % 360  # Solar mean anomaly
    C = 1.9148 * sin(M) + 0.0200*sin(2*M) + 0.0003 * sin(3*M)  # Equation of the center
    _lambda = (M + C + 180 + 102.9372) % 360  # Ecliptic Longitude
    J_transit = 2451545.0 + J_star + 0.0053 * sin(M) - 0.0069*sin(2*_lambda)  # Solar Transit
    delta = asin(sin(_lambda) * sin(23.44))  # Declination of Sun
    temp = (cos(90.83333) - sin(lat) * sin(delta))/(cos(lat) * cos(delta))
    w_0 = acos(temp)  # Hour angle
    J_rise = J_transit - (w_0/360)
    J_set = J_transit + (w_0/360)
    daylight = 2 * w_0 / 15 * 3600
    t_rise = (dt - jul_to_greg(J_rise)).total_seconds()
    t_set = (dt - jul_to_greg(J_set)).total_seconds()
    t_noon = (dt - jul_to_greg(J_transit)).total_seconds()
 
    if event == '':
        return t_rise, t_set, t_noon
    elif event == 'sunrise':
        return t_rise
    elif event == 'sunset':
        return t_set
    elif event == 'noon':
        return t_noon
    elif event == 'daylight':
        return daylight


def twc_date(dt):
    _day = day_of_year(dt) + 1
    day = _day

    if is_leap_year(dt):
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
    for i in range(0, 4):
        for j in [31, 30, 30]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                break
    return weekday_abbr[weekday] + ' ' + month_abbr[month-1] + " " + "{:02}".format(day)


def and_date(dt):
    day = day_of_year(dt) + 1
    month = 1
    weekday = (day - 1) % 5

    if day == 366:
        return "*LEAP DAY*"

    for i in range(0, 5):
        for j in [36, 37]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                break
    return annus_day_abbr[weekday] + ' ' + annus_month_abbr[month-1] + " " + "{:02}".format(day)


def acos(x):
    return degrees(math.acos(x))


def asin(x):
    return degrees(math.asin(x))


def atan(x):
    return degrees(math.atan(x))


def sin(deg):
    return math.sin(radians(deg))


def cos(deg):
    return math.cos(radians(deg))


def tan(deg):
    return math.tan(radians(deg))


def radians(deg):
    return deg * math.pi / 180


def degrees(rad):
    return rad * 180 / math.pi


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
    return (datetime(year=Y, day=D, month=M).replace(tzinfo=utc).astimezone() + timedelta(seconds=86400 * (J - _J)))


os.system("clear")
os.system("setterm -cursor off")


def main():
    loop_time = timedelta(0)
    dst_str = ["", "", "", ""]
    v_bar = themes[2] + chr(0x2551) + themes[1]
    b_var_single = themes[2] + chr(0x2502) + themes[1]
    h_bar = themes[2] + chr(0x2550) + themes[1]
    h_bar_single = themes[2] + chr(0x2500) + themes[1]
    h_bar_up_connect = themes[2] + chr(0x2569) + themes[1]
    h_bar_down_connect = themes[2] + chr(0x2566) + themes[1]
#   h_bar_up_connect_single = themes[2] + chr(0x2567) + themes[1]
    corner_ll = themes[2] + chr(0x255A) + themes[1]
    corner_lr = themes[2] + chr(0x255D) + themes[1]
    corner_ul = themes[2] + chr(0x2554) + themes[1]
    corner_ur = themes[2] + chr(0x2557) + themes[1]
    center_l = themes[2] + chr(0x2560) + themes[1]
    center_r = themes[2] + chr(0x2563) + themes[1]
    highlight = [themes[0], themes[3]]
    binary = "-#"

    while True:
        ntp_id_str = str(ntpid)
        try:
            time.sleep(refresh)
            start_time = datetime.utcnow()
            offset = -(time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)/(3600)
            now = start_time + loop_time
            if args.d:
                now = dbg_override + (start_time - dbg_start)

            _now = now.replace(tzinfo=utc)
            _now_loc = _now.astimezone()

            utcnow = now
            cetnow = utcnow + timedelta(hours=1)

            is_daylight_savings = time.localtime().tm_isdst

            current_tz = time.tzname[is_daylight_savings]

            rows = os.get_terminal_size().lines
            columns = os.get_terminal_size().columns
            half_cols = int(((columns - 1) / 2) // 1)
            screen = ""
            reset_cursor()
            u_second = now.microsecond / 1000000
            print(themes[0], end="")
            hour_binary = divmod(_now.astimezone().hour, 10)
            minute_binary = divmod(_now.astimezone().minute, 10)
            second_binary = divmod(_now.astimezone().second, 10)

            b_clock_mat = [bin(hour_binary[0])[2:].zfill(4),
                           bin(hour_binary[1])[2:].zfill(4),
                           bin(minute_binary[0])[2:].zfill(4),
                           bin(minute_binary[1])[2:].zfill(4),
                           bin(second_binary[0])[2:].zfill(4),
                           bin(second_binary[1])[2:].zfill(4),
                           ]

            b_clock_mat_t = [*zip(*b_clock_mat)]
            b_clockdisp = ['', '', '', '']

            for i, row in enumerate(b_clock_mat_t):
                b_clockdisp[i] = ''.join(row).replace("0", binary[0]).replace("1", binary[1])

            if (_now_loc.month == 12):
                days_this_month = 31
            else:
                days_this_month = (datetime(_now_loc.year, _now_loc.month + 1, 1) - datetime(_now_loc.year, _now_loc.month, 1)).days

            days_this_year = 366 if is_leap_year(_now_loc) else 365

            time_table[SECOND][VALUE] = _now_loc.second + u_second + random.randint(0, 9999)/10000000000
            time_table[MINUTE][VALUE] = _now_loc.minute + time_table[SECOND][VALUE] / 60 + random.randint(0, 99)/10000000000
            time_table[HOUR][VALUE] = _now_loc.hour + time_table[MINUTE][VALUE] / 60
            time_table[DAY][VALUE] = _now_loc.day + time_table[HOUR][VALUE] / 24
            time_table[MONTH][VALUE] = _now_loc.month + (time_table[DAY][VALUE] - 1)/days_this_month
            time_table[YEAR][VALUE] = _now_loc.year + (day_of_year(_now_loc) + time_table[DAY][VALUE] - int(time_table[DAY][VALUE])) / days_this_year
            time_table[CENTURY][VALUE] = (time_table[YEAR][VALUE] - 1) / 100 + 1

            screen += themes[3]
            screen += ("{: ^" + str(columns) + "}\n").format(_now_loc.strftime("%I:%M:%S %p " + current_tz + " - %A %B %d, %Y")).upper() + themes[0]
            screen += corner_ul + h_bar * (columns - 2) + corner_ur + "\n"

            for i in range(7):
                percent = time_table[i][VALUE] - int(time_table[i][VALUE])
                screen += v_bar + (" {0:} " + "{2:}" + themes[1] + " {3:011.8f}% " + v_bar + "\n").format(
                    time_table[i][LABEL],
                    time_table[i][VALUE],
                    draw_progress_bar(width=(columns - 19), max=1, value=percent),
                    100 * (percent))

            screen += center_l + h_bar * (columns - 25) + h_bar_down_connect + h_bar * 22 + center_r + "\n"

            dst_str[0] = "INTL " + int_fix_date(_now_loc)
            dst_str[1] = "WRLD " + twc_date(_now_loc)
            dst_str[2] = "ANNO " + and_date(_now_loc)
            dst_str[3] = "RJUL " + float_fixed(julian_date(date=utcnow, reduced=True), 10, False)

            unix_int = int(utcnow.timestamp())
            unix_exact = unix_int + u_second
            unix_str = ("UNX {0}").format(unix_int)

            day_percent_complete = time_table[DAY][VALUE] - int(time_table[DAY][VALUE])
            day_percent_complete_utc = (utcnow.hour * 3600 + utcnow.minute * 60 + utcnow.second + utcnow.microsecond / 1000000) / 86400
            day_percent_complete_cet = (cetnow.hour * 3600 + cetnow.minute * 60 + cetnow.second + cetnow.microsecond / 1000000) / 86400

            sunrise, sunset, sol_noon = sunriseset(_now_loc)
            solar_str = "SOL " + (_now_loc.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(seconds=sol_noon)).strftime(
                '%H:%M:%S'
            )
            lst_str = sidereal_time(_now_loc, lon, offset, "LST {hour:02}:{minute:02}:{second:02}")
            metric_str = metric_strf(day_percent_complete, "MET {hours:02}:{minutes:02}:{seconds:02}")
            hex_str = hex_strf(day_percent_complete, "HEX {hours:1X}_{minutes:02X}_{seconds:1X}.{sub:03X}")
            net_str = net_time_strf(day_percent_complete_utc, "NET {degrees:03.0f}°{minutes:02.0f}'{seconds:02.0f}\"")
            sit_str = "SIT @{:09.5f}".format(round(day_percent_complete_cet*1000, 5))
            utc_str = "UTC " + utcnow.strftime("%H:%M:%S")

            diff = sunriseset(_now_loc, event='daylight', fixed=True)

            if sunset > 0 and sunrise > 0:
                sunrise = sunriseset(_now_loc, event='sunrise', offset=1)
            elif sunset < 0 and sunrise < 0:
                sunset = sunriseset(_now_loc, event='sunset', offset=-1)

            time_List = [None, None, None, None]
            for i, s in enumerate([leap_shift(_now_loc), sunrise, sunset, diff]):
                hours, remainder = divmod(abs(s), 3600)
                minutes, seconds = divmod(remainder, 60)
                subs = 100000 * (seconds - int(seconds))
                sign = '-' if s < 0 else ' '
                time_List[i] = '{}{:02}:{:02}:{:02}.{:05}'.format(sign, int(hours), int(minutes), int(seconds), int(subs))

            leap_stats = ["LSHFT" + time_List[0],
                          h_bar_single * 20,
                          "SUNRI" + time_List[1],
                          "SUNST" + time_List[2],
                          "DAYLN" + time_List[3]
                          ]

            for i in range(0, len(time_zone_list), 2):
                time0 = _now.astimezone(time_zone_list[i][1])
                time1 = _now.astimezone(time_zone_list[i+1][1])

                flash0 = False
                flash1 = False
                flash_dur = .1

                if (time0.weekday() < 5):
                    if (time0.hour > 8 and time0.hour < 17):
                        flash0 = True
                    elif (time0.hour == 8):
                        flash0 = (u_second < flash_dur)
                    elif (time0.hour == 17):
                        flash0 = not (u_second < flash_dur)

                if (time1.weekday() < 5):
                    if (time1.hour > 8 and time1.hour < 17):
                        flash1 = True
                    elif (time1.hour == 8):
                        flash1 = (u_second < flash_dur)
                    elif (time1.hour == 17):
                        flash1 = not (u_second < flash_dur)

                if time0.day > _now_loc.day:
                    sign0 = "+"
                elif time0.day < _now_loc.day:
                    sign0 = "-"
                else:
                    sign0 = ' '

                if time1.day > _now_loc.day:
                    sign1 = "+"
                elif time1.day < _now_loc.day:
                    sign1 = "-"
                else:
                    sign1 = ' '

                time_str0 = sign0 + time0.strftime("%H:%M").upper()
                time_str1 = sign1 + time1.strftime("%H:%M").upper()

                padding = (columns - 60) * ' '

                screen += v_bar + ' ' + highlight[flash0] + ("{0:>9}{1:6}").format(time_zone_list[i][0], time_str0) + highlight[0] + ' ' + b_var_single
                screen += ' ' + highlight[flash1] + ("{0:>9}{1:6}").format(time_zone_list[i + 1][0], time_str1) + highlight[0] + ' ' + padding + v_bar + ' ' + leap_stats[i//2] + ' ' + v_bar
                # Each Timezone column is 29 chars, and the bar is 1 = 59

                screen += "\n"

            screen += center_l + h_bar * (columns - 29) + h_bar_down_connect + h_bar * 3 + h_bar_up_connect + h_bar * 4 + h_bar_down_connect + 17 * h_bar + center_r + "\n"

            screen += v_bar + " " + utc_str + " " + b_var_single + " " + unix_str + " " * \
                (columns - len(metric_str + unix_str + b_clockdisp[0]) - 27) + v_bar + ' ' + b_clockdisp[0] + " " + v_bar + " " + dst_str[0] + " " + v_bar + "\n"
            screen += v_bar + " " + metric_str + " " + b_var_single + " " + sit_str + " " * \
                (columns - len(metric_str + sit_str + b_clockdisp[1]) - 27) + v_bar + ' ' + b_clockdisp[1] + " " + v_bar + " " + dst_str[1] + " " + v_bar + "\n"
            screen += v_bar + " " + solar_str + " " + b_var_single + " " + hex_str + " " * \
                (columns - len(solar_str + net_str + b_clockdisp[2]) - 27) + v_bar + ' ' + b_clockdisp[2] + " " + v_bar + " " + dst_str[2] + " " + v_bar + "\n"
            screen += v_bar + " " + lst_str + " " + b_var_single + " " + net_str + " " * \
                (columns - len(lst_str + hex_str + b_clockdisp[3]) - 27) + v_bar + ' ' + b_clockdisp[3] + " " + v_bar + " " + dst_str[3] + " " + v_bar + "\n"
            screen += corner_ll + h_bar * (columns - 29) + h_bar_up_connect + h_bar * 8 + h_bar_up_connect + h_bar * 17 + corner_lr + "\n"
            ntpid_max_width = half_cols - 4
            ntpid_temp = ntp_id_str

            if(is_connected):
                screen += themes[1]
            else:
                screen += themes[4]

            # Calculate NTP server ID scrolling if string is too large
            if(len(ntp_id_str) > ntpid_max_width):

                stages = 16 + len(ntp_id_str) - ntpid_max_width
                current_stage = int(unix_exact/.25) % stages

                if(current_stage < 8):
                    ntpid_temp = ntp_id_str[0:ntpid_max_width]
                elif(current_stage >= (stages - 8)):
                    ntpid_temp = ntp_id_str[(len(ntp_id_str)-ntpid_max_width):]
                else:
                    ntpid_temp = ntp_id_str[(current_stage - 8):(current_stage - 8 + ntpid_max_width)]

            ntp_str_left = "NTP:" + ntpid_temp
            ntp_str_right = ("STR:{str}/DLY:{dly}/OFF:{off}").format(
                str=ntpstr,
                dly=float_fixed(ntpdly, 6, False),
                off=float_fixed(ntpoff, 7, True)
            )

            screen += themes[3] + " " + ntp_str_left + ((columns - len(ntp_str_left + ntp_str_right)-2) * " ") + ntp_str_right + " "
            screen += themes[1]

            # Switch to the header color theme
            screen += themes[0]

            # Append blank lines to fill out the bottom of the screen
            for i in range(22, rows):
                screen += " " * columns

            loop_time = datetime.utcnow() - start_time
            print(screen, end="")

        except KeyboardInterrupt:
            return


def ntp_daemon():
    global ntpdly
    global ntpoff
    global ntpstr
    global ntpid
    global is_connected

    def socket_attempt(address, port):
        is_successful = False
        for _ in range(0, 3):
            try:
                socket.create_connection((address, port), 2)
                is_successful = is_successful or True
            except:
                pass

        return is_successful

    pattern = re.compile(
        r"\*([\w+\-\.(): ]+)\s+" +  # 1 - Server ID
        r"([\w\.]+)\s+" +           # 2 - Reference ID
        r"(\d+)\s+" +               # 3 - Stratum
        r"(\w+)\s+" +               # 4 - Type
        r"(\d+)\s+" +               # 5 - When
        r"(\d+)\s+" +               # 6 - Poll
        r"(\d+)\s+" +               # 7 - Reach
        r"([\d\.]+)\s+" +           # 8 - Delay
        r"([-\d\.]+)\s+" +          # 9 - Offset
        r"([\d\.]+)"                # 10- Jitter
    )

    while(True):
        try:
            is_connected = socket_attempt("8.8.8.8", 53)

            ntpq = subprocess.run(['ntpq', '-pw'], stdout=subprocess.PIPE)
            ntpq = ntpq.stdout.decode('utf-8')
            current_server = re.search(r"\*.+", ntpq)
            current_server = pattern.search(ntpq)

            if(current_server):
                ntpoff = float(current_server.group(9))
                ntpdly = float(current_server.group(8))
                ntpstr = current_server.group(3)
                ntpid = current_server.group(1)

        except Exception as e:
            is_connected = False
            ntpid = e

        time.sleep(15)


if __name__ == "__main__":
    thread = threading.Thread(target=ntp_daemon)
    thread.setDaemon(True)
    thread.start()
    main()
    os.system("clear")
    os.system("setterm -cursor on")
    print(RST_COLORS, end="")
