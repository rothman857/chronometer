#!/usr/bin/python3

from datetime import datetime, timedelta, date, tzinfo
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
from typing import Dict, List
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

default_config = {
    'coordinates': {
        '# Note': 'Decimal notation only.  West longitude is negative.',
        'latitude': 40.7128,
        'longitude': -74.0060},
    'refresh': 0.001,
    'timezones': {
        '# Note': (
            'Format = label: time_zone. '
            '(time_zone must be a valid pytz time zone name.  '
            '10 times zones are required.)'
        ),
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
        print(
            "Initial .config file generated.  "
            "Please update it with coordinates and desired timezones "
            "before running chronometer.py again."
        )
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


class timezone_entry:
    def __init__(self, name: str, time_zone: tzinfo):
        self.name = name
        self.time_zone = time_zone


def my_tz_sort(tz_entry: timezone_entry) -> timedelta:
    result = tz_entry.time_zone.utcoffset(now)
    if result:
        return result
    else:
        return timedelta()


try:
    lat = float(running_config['coordinates']['latitude'])
    lon = float(running_config['coordinates']['longitude'])
    refresh = float(running_config['refresh'])
    time_zone_list: List[timezone_entry] = []
    for tz in running_config['timezones']:
        if tz[0] == '#':
            continue
        time_zone_list.append(
            timezone_entry(
                name=tz.upper(),
                time_zone=pytz.timezone(running_config['timezones'][tz])
            )
        )

    time_zone_list.sort(key=my_tz_sort)

    for tz in time_zone_list:
        tz.name = tz.name[:10]

except KeyError as e:
    print(f'Error reading .config ({e}).  Please correct or reset using --reset.')
    exit()


ntpoff = 0
ntpdly = 0
ntpstr = '-'
ntpid = '---'
ntpout = ''


class Color:
    black_bg = "\x1b[40m"
    white_fg = "\x1b[97m"
    l_blue_fg = "\x1b[94m"
    l_blue_bg = "\x1b[104m"
    d_gray_fg = "\x1b[90m"
    reset = "\x1b[0m"


class Theme:
    background = Color.black_bg
    text = Color.white_fg
    table = Color.l_blue_fg
    highlight = Color.l_blue_bg
    dim_bar = Color.d_gray_fg


class Symbol:
    v_bar = f'{Theme.table}║{Theme.text}'
    b_var_single = f'{Theme.table}│{Theme.text}'
    h_bar = f'{Theme.table}─{Theme.text}'
    h_bar_up_connect = f'{Theme.table}╩{Theme.text}'
    h_bar_down_connect = f'{Theme.table}╦{Theme.text}'
    corner_ll = f'{Theme.table}╚{Theme.text}'
    corner_lr = f'{Theme.table}╝{Theme.text}'
    corner_ul = f'{Theme.table}╔{Theme.text}'
    corner_ur = f'{Theme.table}╗{Theme.text}'
    center_l = f'{Theme.table}╠{Theme.text}'
    center_r = f'{Theme.table}╣{Theme.text}'
    highlight = (Theme.background, Theme.highlight)
    box = '◼'
    binary = ("-", box)


weekday_abbr = (
    "SAT",
    "SUN",
    "MON",
    "TUE",
    "WED",
    "THU",
    "FRI"
)

annus_day_abbr = (
    "PRI",
    "SEC",
    "TER",
    "QUA",
    "QUI"
)

annus_month_abbr = (
    "PRI",
    "SEC",
    "TER",
    "QUA",
    "QUI",
    "SEX",
    "SEP",
    "OCT",
    "NON",
    "DEC"
)

intfix_month_abbr = (
    "JAN",
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
    "DEC"
)

month_abbr = (
    "JAN",
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
    "DEC"
)


class time_table:
    second: float
    minute: float
    hour: float
    day: float
    month: float
    year: float
    century: float


ntpq_pattern = re.compile(
    r"([\*\#\+\-\~ ])"      # 0 - Peer Status
    r"([\w+\-\.(): ]+)\s+"  # 1 - Server ID
    r"([\w\.]+)\s+"         # 2 - Reference ID
    r"(\d+)\s+"             # 3 - Stratum
    r"(\w+)\s+"             # 4 - Type
    r"(\d+)\s+"             # 5 - When
    r"(\d+)\s+"             # 6 - Poll
    r"(\d+)\s+"             # 7 - Reach
    r"([\d\.]+)\s+"         # 8 - Delay
    r"([-\d\.]+)\s+"        # 9 - Offset
    r"([\d\.]+)"            # 10- Jitter
)


def reset_cursor():
    print("\033[0;0H", end="")


def draw_progress_bar(*, min: int = 0, width: int, max: int, value: float) -> str:
    level = int((width + 1) * (value - min)/(max - min))
    return f'{chr(0x2550) * level}{Color.d_gray_fg}{(chr(0x2500) * (width - level))}'


def get_local_date_format() -> str:
    today = date.today()
    today_str = today.strftime('%x').split('/')
    if int(today_str[0]) == today.month and int(today_str[1]) == today.day:
        return "{month:02}/{day:02}"
    else:
        return "{day:02}/{month:02}"


def day_of_year(dt: datetime) -> int:
    dt = dt.replace(tzinfo=None)
    return (dt - datetime(dt.year, 1, 1)).days


def is_leap_year(dt: datetime) -> bool:
    year = dt.year
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    else:
        return False


def net_time_strf(day_percent: float) -> str:
    degrees, remainder = divmod(int(1296000*day_percent), 3600)
    degrees, remainder = int(degrees), int(remainder)
    minutes, seconds = divmod(remainder, 60)
    return f'NET {degrees:03.0f}°{minutes:02.0f}\'{seconds:02.0f}\"'


def hex_strf(day_percent: float) -> str:
    hours, remainder = divmod(int(day_percent * 268435456), 16777216)
    minutes, seconds = divmod(remainder, 65536)
    seconds, sub = divmod(seconds, 4096)
    return f'HEX {hours:1X}_{minutes:02X}_{seconds:1X}.{sub:03X}'


def metric_strf(day_percent: float) -> str:
    hours, remainder = divmod(int(day_percent * 100000), 10000)
    minutes, seconds = divmod(remainder, 100)
    return f'MET {hours:02}:{minutes:02}:{seconds:02}'


def float_fixed(flt: float, wd: int, sign: bool = False) -> str:
    int_len = len(str(int(flt)))
    round_amt = wd - int_len - 1
    if sign:
        round_amt -= 1
    return f'{"+" if sign and flt > 0 else ""}{round(flt, round_amt):.02f}'


def sidereal_time(dt: datetime, lon: float, off: float) -> str:
    dt = dt.replace(tzinfo=None)
    j = ((dt - datetime(year=2000, month=1, day=1)) - timedelta(hours=off)).total_seconds()/86400
    l0 = 99.967794687
    l1 = 360.98564736628603
    l2 = 2.907879 * (10 ** -13)
    l3 = -5.302 * (10 ** -22)
    theta = (l0 + (l1 * j) + (l2 * (j ** 2)) + (l3 * (j ** 3)) + lon) % 360
    result = int(timedelta(hours=theta/15).total_seconds())
    hour, remainder = divmod(result, 3600)
    minute, second = divmod(remainder, 60)
    return f'LST {hour:02}:{minute:02}:{second:02}'


def julian_date(date: datetime) -> float:
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jdn = date.day + (153*m+2)//5 + y*365 + y//4 - y//100 + y//400 - 32045
    jd = (
        jdn +
        (date.hour - 12) / 24 +
        date.minute / 1440 +
        date.second / 86400 +
        date.microsecond / 86400000000
    )
    return jd


def int_fix_date(dt: datetime) -> str:
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
    return f'{weekday_abbr[w]} {intfix_month_abbr[m-1]} {d:02}'


def leap_shift(dt: datetime) -> float:
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


def leapage(dt: datetime) -> float:
    years = (dt.year-1) % 400
    count = years // 4
    count -= years // 100
    count += years // 400

    if is_leap_year(dt):
        if dt.month == 2 and dt.day == 29:
            percent_complete = (
                dt - datetime(month=2, day=29, year=dt.year)
            ).total_seconds()/86400
            count += percent_complete
        elif dt >= datetime(month=3, day=1, year=dt.year):
            count += 1
            pass

    if count == 97:
        count = 0
    return count


def sunriseset(dt: datetime, offset: int = 0, fixed: bool = False) -> Dict[str, float]:
    # https://en.wikipedia.org/wiki/Sunrise_equation
    if fixed:
        n = julian_date(dt) - 2451545.0 + .0008  # current julian day since 1/1/2000 12:00
    else:
        n = (
            dt - datetime(month=1, day=1, year=2000, hour=12).replace(tzinfo=utc)
        ).total_seconds()//86400

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
    nighttime = 2 * (180-w_0) / 15 * 3600
    t_rise = (dt - jul_to_greg(J_rise)).total_seconds()
    t_set = (dt - jul_to_greg(J_set)).total_seconds()
    t_noon = (dt - jul_to_greg(J_transit)).total_seconds()
    return {
        'sunrise': t_rise,
        'sunset': t_set,
        'noon': t_noon,
        'daylight': daylight,
        'nighttime': nighttime
    }


def twc_date(dt: datetime) -> str:
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
    for _ in range(0, 4):
        for j in [31, 30, 30]:
            if day - j > 0:
                day -= j
                month += 1
            else:
                break
    return f'{weekday_abbr[weekday]} {month_abbr[month-1]} {day:02}'


def and_date(dt: datetime) -> str:
    day = day_of_year(dt) + 1
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
    return f'{annus_day_abbr[weekday]} {annus_month_abbr[month-1]} {day:02}'


def acos(x: float) -> float:
    return degrees(math.acos(x))


def asin(x: float) -> float:
    return degrees(math.asin(x))


def atan(x: float) -> float:
    return degrees(math.atan(x))


def sin(deg: float) -> float:
    return math.sin(radians(deg))


def cos(deg: float) -> float:
    return math.cos(radians(deg))


def tan(deg: float) -> float:
    return math.tan(radians(deg))


def radians(deg: float) -> float:
    return deg * math.pi / 180


def degrees(rad: float) -> float:
    return rad * 180 / math.pi


def jul_to_greg(J: float) -> datetime:
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
        ).replace(
            tzinfo=utc
        ).astimezone() + timedelta(seconds=86400 * (J - _J)))


os.system("clear")
os.system("setterm -cursor off")

internet_connected = False


def main():
    loop_time = timedelta(0)
    ntp_thread = threading.Thread(target=ntp_daemon)
    ntp_thread.setDaemon(True)
    ping_thread = threading.Thread(target=ping_daemon)
    ntp_thread.setDaemon(True)
    _ = 0
    ntp_thread.start()
    ping_thread.start()
    ntp_started = False
    counter = 0
    while ntpid == "---":
        counter += 1
        time.sleep(1)
        reset_cursor()
        columns = os.get_terminal_size().columns
        rows = os.get_terminal_size().lines
        print('Starting Internet Chronometer...')
        print('Waiting for internet connection...')

        if not internet_connected:
            continue

        print('Starting time synchronization...')
        if not ntp_started:
            subprocess.run(['sudo', 'systemctl', 'start', 'ntp'], stdout=subprocess.PIPE)
            ntp_started = True

        ntpq_info = ntpq_pattern.findall(ntpout)

        ntpq_table_headers = [
            'remote',
            'refid',
            'st',
            'delay',
            'offset'
        ]

        ntpq_table_data = [
            {
                ntpq_table_headers[0]: n[0] + n[1],
                ntpq_table_headers[1]: n[2],
                ntpq_table_headers[2]: n[3],
                ntpq_table_headers[3]: n[8],
                ntpq_table_headers[4]: n[9],
            } for n in ntpq_info
        ]
        ntpq_table_data = sorted(ntpq_table_data, key=lambda i: (i['st'], float(i['delay'])))
        ntpq_table_column_widths = [16, 15, 2, 6, 6]
        ntpq_table = [
            [h.upper() for h in ntpq_table_headers],
            ['-' * w for w in ntpq_table_column_widths],
        ]
        ntpq_table += [
            [r[header] for header in ntpq_table_headers] for r in ntpq_table_data
        ]
        if ntpq_table_data:
            print('Polling NTP servers...')
            print('NTP Peers:')
            print('_' * columns)
            for row in ntpq_table[:(rows-7)]:
                row_array: List[str] = []
                for _, item in enumerate(row):
                    row_array.append(
                        f'{item[:ntpq_table_column_widths[_]]:>{ntpq_table_column_widths[_]}}'
                    )
                print(f'{"|".join(row_array):{columns}}')

    while True:
        ntp_id_str = str(ntpid)
        try:
            time.sleep(refresh)
            start_time = datetime.now(pytz.utc)
            offset = -(
                time.timezone if
                (time.localtime().tm_isdst == 0) else
                time.altzone
            )/(3600)
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
            print(Theme.background, end="")
            hour_binary = divmod(_now.astimezone().hour, 10)
            minute_binary = divmod(_now.astimezone().minute, 10)
            second_binary = divmod(_now.astimezone().second, 10)
            b_clock_mat = [
                bin(hour_binary[0])[2:].zfill(4),
                bin(hour_binary[1])[2:].zfill(4),
                bin(minute_binary[0])[2:].zfill(4),
                bin(minute_binary[1])[2:].zfill(4),
                bin(second_binary[0])[2:].zfill(4),
                bin(second_binary[1])[2:].zfill(4),
            ]

            b_clock_mat_t = [*zip(*b_clock_mat)]
            b_clockdisp = ['', '', '', '']
            for _, row in enumerate(b_clock_mat_t):
                b_clockdisp[_] = (
                    ''.join(row).replace("0", Symbol.binary[0]).replace("1", Symbol.binary[1])
                )
            if (_now_loc.month == 12):
                days_this_month = 31
            else:
                days_this_month = (
                    datetime(_now_loc.year, _now_loc.month + 1, 1) -
                    datetime(_now_loc.year, _now_loc.month, 1)
                ).days
            days_this_year = 366 if is_leap_year(_now_loc) else 365
            time_table.second = (
                _now_loc.second +
                u_second +
                random.randint(0, 9999)/10000000000
            )
            time_table.minute = (
                _now_loc.minute +
                time_table.second / 60 +
                random.randint(0, 99)/10000000000
            )
            time_table.hour = (
                _now_loc.hour +
                time_table.minute / 60
            )
            time_table.day = (
                _now_loc.day +
                time_table.hour / 24
            )
            time_table.month = (
                _now_loc.month +
                (time_table.day - 1)/days_this_month
            )
            time_table.year = (
                _now_loc.year + (
                    day_of_year(_now_loc) +
                    time_table.day -
                    int(time_table.day)
                ) / days_this_year
            )
            time_table.century = (
                time_table.year - 1
            ) / 100 + 1
            screen += Theme.highlight
            screen += (
                f'''{
                        f"""{_now_loc:%I:%M:%S %p {current_tz} - %A %B %d, %Y}"""
                :^{columns}}'''
            ).upper() + Theme.background
            screen += (
                f'{Symbol.corner_ul}'
                f'{Symbol.h_bar * (columns - 2)}'
                f'{Symbol.corner_ur}\n'
            )

            for _ in time_table.__dict__['__annotations__']:
                value = time_table.__dict__[_]
                percent = value - int(value)
                screen += (
                    f'{Symbol.v_bar} '
                    f'{_[0].upper()} '
                    f'{draw_progress_bar(width=(columns - 19), max=1, value=percent) }'
                    f'{Theme.text}'
                    f' {100 * percent:011.8f}% '
                    f'{Symbol.v_bar}\n'

                )

            screen += (
                f'{Symbol.center_l}'
                f'{Symbol.h_bar * (columns - 23)}'
                f'{Symbol.h_bar_down_connect}'
                f'{Symbol.h_bar * 20}'
                f'{Symbol.center_r}\n'
            )

            dst_str = [
                f'INTL {int_fix_date(_now_loc)}',
                f'WRLD {twc_date(_now_loc)}',
                f'ANNO {and_date(_now_loc)}',
                f'JULN {float_fixed(julian_date(date=utcnow), 10, False)}'
            ]

            unix_int = int(utcnow.timestamp())
            unix_exact = unix_int + u_second
            unix_str = f'UNX {unix_int}'

            day_percent_complete = time_table.day - int(time_table.day)
            day_percent_complete_utc = (
                utcnow.hour * 3600 +
                utcnow.minute * 60 +
                utcnow.second +
                utcnow.microsecond / 1000000
            ) / 86400
            day_percent_complete_cet = (
                cetnow.hour * 3600 +
                cetnow.minute * 60 +
                cetnow.second +
                cetnow.microsecond / 1000000
            ) / 86400

            # sunrise, sunset, sol_noon = *sunriseset(_now_loc)
            sun_stats = sunriseset(_now_loc)
            sunrise = sun_stats['sunrise']
            sunset = sun_stats['sunset']
            sol_noon = sun_stats['noon']
            solar_str = (
                f'''SOL {
                    _now_loc.replace(hour=12, minute=0, second=0, microsecond=0) +
                     timedelta(seconds=sol_noon):%H:%M:%S}'''
            )

            lst_str = sidereal_time(_now_loc, lon, offset)
            metric_str = metric_strf(day_percent_complete)
            hex_str = hex_strf(day_percent_complete)
            net_str = net_time_strf(day_percent_complete_utc)
            sit_str = f'SIT @{round(day_percent_complete_cet*1000, 5):09.5f}'
            utc_str = f'UTC {utcnow:%H:%M:%S}'

            diff = sunriseset(_now_loc, fixed=True)['daylight']
            nighttime = sunriseset(_now_loc, fixed=True)['nighttime']

            if sunset > 0 and sunrise > 0:
                sunrise = sunriseset(_now_loc, offset=1)['sunrise']
            elif sunset < 0 and sunrise < 0:
                sunset = sunriseset(_now_loc, offset=-1)['sunset']

            time_List = [str()] * 6
            for _, s in enumerate([leap_shift(_now_loc), sunrise, sunset, diff, nighttime]):
                hours, remainder = divmod(abs(s), 3600)
                minutes, seconds = divmod(remainder, 60)
                subs = 1000000 * (seconds - int(seconds))
                sign = '-' if s < 0 else ' '
                time_List[_] = f'{sign}{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}.{subs:06.0f}'

            leap_stats: List[str] = [
                f'LD{time_List[0]}',
                f'SR{time_List[1]}',
                f'SS{time_List[2]}',
                f'DD{time_List[3]}',
                f'ND{time_List[4]}'
            ]

            for _ in range(0, len(time_zone_list), 2):
                time0 = now.astimezone(time_zone_list[_].time_zone)
                time1 = now.astimezone(time_zone_list[_+1].time_zone)

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

                if time0.date() > _now_loc.date():
                    sign0 = "+"
                elif time0.date() < _now_loc.date():
                    sign0 = "-"
                else:
                    sign0 = " "

                if time1.date() > _now_loc.date():
                    sign1 = "+"
                elif time1.date() < _now_loc.date():
                    sign1 = "-"
                else:
                    sign1 = " "

                time_str0 = f'{sign0}{time0:%H:%M}'
                time_str1 = f'{sign1}{time1:%H:%M}'

                padding = (columns - 60) * ' '

                screen += (
                    f'{Symbol.v_bar} '
                    f'{Symbol.highlight[flash0]}'
                    f'{time_zone_list[_].name:<10}{time_str0:6}'
                    f'{Symbol.highlight[0]} '
                    f'{Symbol.b_var_single}'
                )

                screen += (
                    f' {Symbol.highlight[flash1]}'
                    f'{time_zone_list[_ + 1].name:<10}{time_str1:6}'
                    f'{Symbol.highlight[0]} '
                    f'{padding}'
                    f'{Symbol.v_bar} '
                    f'{leap_stats[_//2]} '
                    f'{Symbol.v_bar}\n'
                )
                # Each Timezone column is 29 chars, and the bar is 1 = 59

            screen += (
                f'{Symbol.center_l}'
                f'{Symbol.h_bar * (columns - 29)}'
                f'{Symbol.h_bar_down_connect}'
                f'{Symbol.h_bar * 5}'
                f'{Symbol.h_bar_up_connect}'
                f'{Symbol.h_bar * 2}'
                f'{Symbol.h_bar_down_connect}'
                f'{Symbol.h_bar * 17}'
                f'{Symbol.center_r}\n'
            )

            for _, clock in enumerate(
                (
                    (utc_str, unix_str),
                    (metric_str, sit_str),
                    (solar_str, net_str),
                    (lst_str, hex_str),
                )
            ):
                screen += (
                    f'{Symbol.v_bar} '
                    f'{clock[0]} '
                    f'{Symbol.b_var_single} '
                    f'{clock[1]}'
                    f'{" " * (columns - len(clock[0] + clock[1] + b_clockdisp[_]) - 27)}'
                    f'{Symbol.v_bar} '
                    f'{b_clockdisp[_]} '
                    f'{Symbol.v_bar} '
                    f'{dst_str[_]} '
                    f'{Symbol.v_bar}\n'
                )

            screen += (
                f'{Symbol.corner_ll}'
                f'{Symbol.h_bar * (columns - 29)}'
                f'{Symbol.h_bar_up_connect}'
                f'{Symbol.h_bar * 8}'
                f'{Symbol.h_bar_up_connect}'
                f'{Symbol.h_bar * 17}'
                f'{Symbol.corner_lr}\n'
            )

            ntpid_max_width = half_cols - 4
            ntpid_temp = ntp_id_str

            screen += Theme.text if is_connected else Theme.dim_bar

            # Calculate NTP server ID scrolling if string is too large
            if(len(ntp_id_str) > ntpid_max_width):

                stages = 16 + len(ntp_id_str) - ntpid_max_width
                current_stage = int(unix_exact/.25) % stages

                if(current_stage < 8):
                    ntpid_temp = ntp_id_str[0:ntpid_max_width]
                elif(current_stage >= (stages - 8)):
                    ntpid_temp = ntp_id_str[(len(ntp_id_str)-ntpid_max_width):]
                else:
                    ntpid_temp = (
                        ntp_id_str[(current_stage - 8):(current_stage - 8 + ntpid_max_width)]
                    )

            ntp_str_left = f'NTP: + {ntpid_temp}'
            ntp_str_right = (
                f'STR:{ntpstr} '
                f'DLY:{float_fixed(float(ntpdly), 6, False)} '
                f'OFF:{float_fixed(float(ntpoff), 7, True)}'
            )

            screen += (
                f'{Theme.highlight} '
                f'{ntp_str_left}'
                f'{((columns - len(ntp_str_left + ntp_str_right)-2) * " ")}'
                f'{ntp_str_right} '
                f'{Theme.text}'
                f'{Theme.background}'
            )

            # Append blank lines to fill out the bottom of the screen
            for _ in range(22, rows):
                screen += " " * columns

            loop_time = datetime.now(pytz.utc) - start_time
            print(screen, end="")

        except KeyboardInterrupt:
            os.system("setterm -cursor on")
            return


def socket_attempt(address: str, port: int) -> bool:
    is_successful = False
    for _ in range(0, 3):
        try:
            socket.create_connection((address, port), 2)
            is_successful = is_successful or True
        except:
            pass

    return is_successful


def ntp_daemon():
    global ntpdly
    global ntpoff
    global ntpstr
    global ntpid
    global ntpout
    global is_connected

    while(True):
        try:
            is_connected = socket_attempt("8.8.8.8", 53)
            ntpq = subprocess.run(['ntpq', '-pw'], stdout=subprocess.PIPE)
            ntpq_sh = subprocess.run(['ntpq', '-p'], stdout=subprocess.PIPE)
            ntpq = ntpq.stdout.decode('utf-8')
            ntpout = ntpq_sh.stdout.decode('utf-8')
            current_server = [n for n in ntpq_pattern.findall(ntpq) if n[0] == '*']

            if(current_server):
                current_server = current_server[0]
                ntpid = current_server[1]
                ntpstr = current_server[3]
                ntpdly = current_server[8]
                ntpoff = current_server[9]

        except Exception as e:
            is_connected = False
            ntpid = e

        time.sleep(3)


def ping_daemon():
    global internet_connected
    while not internet_connected:
        internet_connected = socket_attempt("8.8.8.8", 53)
        time.sleep(3)


if __name__ == "__main__":
    main()
    os.system("clear")
    os.system("setterm -cursor on")
    print(Color.reset, end="")
