#!/usr/bin/python3

from datetime import datetime, timedelta, date
import time
import json
import os
import random
import pytz
import q
import trig
import abbr
import utils
import network_threads as network
from enum import Enum, auto


here = os.path.dirname(os.path.realpath(__file__))

default_config = {
    'coordinates': {
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
        'trig.Singapore': 'trig.Singapore',
    }
}

if os.path.isfile(os.path.join(here, '.config')):
    with open(os.path.join(here, '.config')) as f:
        running_config = json.load(f)

else:
    with open(os.path.join(here, '.config'), 'w+') as f:
        json.dump(default_config, f, indent=2, sort_keys=True)
        running_config = default_config
        print("Initial .config file generated.  Please update it with coordinates and desired timezones before running chronometer.py again.")
        exit()


random.seed()

def my_tz_sort(tz_entry):
    return tz_entry[1].utcoffset(datetime.now())


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

    for i in range(0, len(time_zone_list), 2):
        _time_zone_list[i] = time_zone_list[i//2][:10]
        _time_zone_list[i+1] = time_zone_list[i//2+5][:10]

    time_zone_list = _time_zone_list


except KeyError as e:
    print(f"Error reading .config ({e}).  Please correct or reset utrig.sing --reset.")
    exit()

class ProgressBar(Enum):
    SECOND = 0
    MINUTE = auto()
    HOUR = auto()
    DAY = auto()
    MONTH = auto()
    YEAR = auto()
    CENTURY = auto()


# Terminal coloring
BLACK_BG = "\x1b[40m"
WHITE_FG = "\x1b[97m"
L_BLUE_FG = "\x1b[94m"
L_BLUE_BG = "\x1b[104m"
D_GRAY_FG = "\x1b[90m"
RST_COLORS = "\x1b[0m"

themes = [
    BLACK_BG,  # background
    WHITE_FG,  # text
    L_BLUE_FG,  # table borders
    L_BLUE_BG,  # text highlight
    D_GRAY_FG  # progress bar dim
]



# Label, value, precision
time_table = [
    ["S", 0],
    ["M", 0],
    ["H", 0],
    ["D", 0],
    ["M", 0],
    ["Y", 0],
    ["C", 0]
]



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


def sidereal_time(dt, lon, fmt):
    offset = dt.utcoffset().total_seconds()/3600
    j = julian_date(dt) - 2451545.0 + .5  - timedelta(hours=offset).total_seconds()/86400
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
    jd = (
        jdn +
        (date.hour - 12) / 24 +
        date.minute / 1440 +
        date.second / 86400 +
        date.microsecond / 86400000000
    )
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
    return abbr.weekday[w] + ' ' + abbr.intfix_month[m-1] + " " + "{:02}".format(d)


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

class SunEvent(Enum):
    SUNRISE = auto()
    SUNSET = auto()
    NOON = auto()
    DAYLIGHT = auto()
    NIGHTTIME = auto()


def sunriseset(dt, offset=0, fixed=False, event=None):  
    # https://en.wikipedia.org/wiki/Sunrise_equation
    dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
    n = julian_date(dt) - 2451545.0 + .5 + .0008  # current julian day trig.since 1/1/2000 12:00
    n = n if fixed else int(n)
    n += offset
    J_star = n + (-lon/360)  # Mean Solar Noon
    M = (357.5291 + 0.98560028 * J_star) % 360  # Solar mean anomaly
    C = 1.9148 * trig.sin(M) + 0.0200*trig.sin(2*M) + 0.0003 * trig.sin(3*M)  # Equation of the center
    λ = (M + C + 180 + 102.9372) % 360  # Ecliptic Longitude
    J_transit = 2451545.0 + J_star + 0.0053 * trig.sin(M) - 0.0069*trig.sin(2*λ)  # Solar Transit
    δ = trig.asin(trig.sin(λ) * trig.sin(23.44))  # Declination of Sun
    temp = (trig.cos(90.83333) - trig.sin(lat) * trig.sin(δ))/(trig.cos(lat) * trig.cos(δ))
    ω0 = trig.acos(temp)  # Hour angle
    J_rise = J_transit - (ω0/360)
    J_set = J_transit + (ω0/360)
    daylight = 2 * ω0 / 15 * 3600
    nighttime = 2 * (180-ω0) / 15 * 3600
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
    return abbr.weekday[weekday] + ' ' + abbr.month[month-1] + " " + "{:02}".format(day)


def and_date(dt):
    day = day_of_year(dt) + 1
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
    return abbr.annus_day[weekday] + ' ' + abbr.annus_month[month-1] + " " + "{:02}".format(day)





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


def main():
    loop_time = timedelta(0)
    dst_str = ["", "", "", ""]
    v_bar = themes[2] + chr(0x2551) + themes[1]
    b_var_single = themes[2] + chr(0x2502) + themes[1]
    h_bar = themes[2] + chr(0x2550) + themes[1]
    h_bar_single = themes[2] + chr(0x2500) + themes[1]
    h_bar_up_connect = themes[2] + chr(0x2569) + themes[1]
    h_bar_down_connect = themes[2] + chr(0x2566) + themes[1]
    corner_ll = themes[2] + chr(0x255A) + themes[1]
    corner_lr = themes[2] + chr(0x255D) + themes[1]
    corner_ul = themes[2] + chr(0x2554) + themes[1]
    corner_ur = themes[2] + chr(0x2557) + themes[1]
    center_l = themes[2] + chr(0x2560) + themes[1]
    center_r = themes[2] + chr(0x2563) + themes[1]
    highlight = [themes[0], themes[3]]
    diamond = chr(0x25fc)
    binary = ("-", diamond)  # "

    

    i = 0
    
    while True:
        ntp_id_str = str(network.ntpid)
        try:
            time.sleep(refresh)
            start_time = datetime.now().astimezone()
            timezone_offset = start_time.utcoffset().total_seconds()
            now = start_time + loop_time
            is_daylight_savings = time.localtime().tm_isdst
            current_tz = time.tzname[is_daylight_savings]
            rows = os.get_terminal_size().lines
            columns = os.get_terminal_size().columns
            half_cols = int(((columns - 1) / 2) // 1)
            screen = ""
            utils.reset_cursor()
            u_second = now.microsecond / 1000000
            print(themes[0], end="")
            hour_binary = divmod(now.astimezone().hour, 10)
            minute_binary = divmod(now.astimezone().minute, 10)
            second_binary = divmod(now.astimezone().second, 10)
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
            for i, row in enumerate(b_clock_mat_t):
                b_clockdisp[i] = (
                    ''.join(row).replace("0", binary[0]).replace("1", binary[1])
                )
            if (now.month == 12):
                days_this_month = 31
            else:
                days_this_month = (
                    datetime(now.year, now.month + 1, 1) -
                    datetime(now.year, now.month, 1)
                ).days
            days_this_year = 366 if is_leap_year(now) else 365
            time_table[ProgressBar.SECOND.value][1] = (
                now.second +
                u_second +
                random.randint(0, 9999)/10000000000
            )
            time_table[ProgressBar.MINUTE.value][1] = (
                now.minute +
                time_table[ProgressBar.SECOND.value][1] / 60 +
                random.randint(0, 99)/10000000000
            )
            time_table[ProgressBar.HOUR.value][1] = (
                now.hour +
                time_table[ProgressBar.MINUTE.value][1] / 60
            )
            time_table[ProgressBar.DAY.value][1] = (
                now.day +
                time_table[ProgressBar.HOUR.value][1] / 24
            )
            time_table[ProgressBar.MONTH.value][1] = (
                now.month +
                (time_table[ProgressBar.DAY.value][1] - 1)/days_this_month
            )
            time_table[ProgressBar.YEAR.value][1] = (
                now.year + (
                    day_of_year(now) +
                    time_table[ProgressBar.DAY.value][1] -
                    int(time_table[ProgressBar.DAY.value][1])
                ) / days_this_year
            )
            time_table[ProgressBar.CENTURY.value][1] = (
                time_table[ProgressBar.YEAR.value][1] - 1
            ) / 100 + 1
            screen += themes[3]
            # screen += (
            #     "{: ^" + str(columns) + "}\n").format(
            #         now.strftime(
            #             "%I:%M:%S %p " + current_tz + " - %A %B %d, %Y"
            #         )
            # ).upper() + themes[0]
            screen += f"{f'{now: %I:%M:%S %p {current_tz} - %A %B %d, %Y}': ^{columns}}".upper() + themes[0]
            screen += f'{corner_ul}{h_bar * (columns - 2)}{corner_ur}\n'

            for i in range(7):
                percent = time_table[i][1] - int(time_table[i][1])
                # screen += v_bar + (
                #     " {0:} " + "{2:}" + themes[1] + " {3:011.8f}% " + v_bar + "\n").format(
                #         time_table[i][0],
                #         0,
                #         draw_progress_bar(width=(columns - 19), max=1, value=percent),
                #         100 * (percent)
                # )
                screen += (
                    f'''{v_bar} {time_table[i][0]} {draw_progress_bar(width=(columns - 19), max=1, value=percent)}{themes[1]} {100 * (percent):011.8f}% {v_bar}\n'''
                )
            screen += center_l + h_bar * (columns - 23) + \
                h_bar_down_connect + h_bar * 20 + center_r + "\n"

            dst_str[0] = "INTL " + int_fix_date(now)
            dst_str[1] = "WRLD " + twc_date(now)
            dst_str[2] = "ANNO " + and_date(now)
            dst_str[3] = "JULN " + float_fixed(julian_date(date=now, reduced=False), 10, False)

            unix_int = int(now.timestamp())
            unix_exact = unix_int + u_second
            unix_str = (f"UNX {unix_int}")

            day_percent_complete = time_table[ProgressBar.DAY.value][1] - int(time_table[ProgressBar.DAY.value][1])
            utc_now = now.astimezone(pytz.utc)
            day_percent_complete_utc = (
                utc_now.hour * 3600 + utc_now.minute * 60 + utc_now.second + utc_now.microsecond / 1000000
            ) / 86400
            sit_now = now.astimezone(pytz.utc) + timedelta(hours=1)
            day_percent_complete_cet = q|(
                sit_now.hour * 3600 + sit_now.minute * 60 + sit_now.second + sit_now.microsecond / 1000000
            ) / 86400

            sunrise, sunset, sol_noon = sunriseset(now)
            solar_str = "SOL " + (now.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(seconds=sol_noon)).strftime(
                '%H:%M:%S'
            )
            lst_str = sidereal_time(now, lon, "LST {hour:02}:{minute:02}:{second:02}")
            metric_str = metric_strf(
                day_percent_complete,
                "MET {hours:02}:{minutes:02}:{seconds:02}"
            )
            hex_str = hex_strf(
                day_percent_complete,
                "HEX {hours:1X}_{minutes:02X}_{seconds:1X}.{sub:03X}"
            )
            net_str = net_time_strf(
                day_percent_complete_utc,
                "NET {degrees:03.0f}°{minutes:02.0f}'{seconds:02.0f}\""
            )
            sit_str = "SIT @{:09.5f}".format(round(day_percent_complete_cet*1000, 5))
            utc_str = "UTC " + now.astimezone(pytz.utc).strftime("%H:%M:%S")

            diff = sunriseset(now, event=SunEvent.DAYLIGHT, fixed=True)
            nighttime = sunriseset(now, event=SunEvent.NIGHTTIME, fixed=True)

            if sunset > 0 and sunrise > 0:
                sunrise = sunriseset(now, event=SunEvent.SUNRISE, offset=1)
            elif sunset < 0 and sunrise < 0:
                sunset = sunriseset(now, event=SunEvent.SUNSET, offset=-1)

            time_List = [None, None, None, None, None]
            for i, s in enumerate([leap_shift(now), sunrise, sunset, diff, nighttime]):
                hours, remainder = divmod(abs(s), 3600)
                minutes, seconds = divmod(remainder, 60)
                subs = 1000000 * (seconds - int(seconds))
                sign = '-' if s < 0 else ' '
                time_List[i] = '{}{:02}:{:02}:{:02}.{:06}'.format(
                    sign, int(hours), int(minutes), int(seconds), int(subs))

            leap_stats = [
                "LD" + time_List[0],
                "SR" + time_List[1],
                "SS" + time_List[2],
                "DD" + time_List[3],
                "ND" + time_List[4]
            ]

            for i in range(0, len(time_zone_list), 2):
                time0 = now.astimezone(time_zone_list[i][1])
                time1 = now.astimezone(time_zone_list[i+1][1])

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

                if time0.date() > now.date():
                    sign0 = "+"
                elif time0.date() < now.date():
                    sign0 = "-"
                else:
                    sign0 = " "

                if time1.date() > now.date():
                    sign1 = "+"
                elif time1.date() < now.date():
                    sign1 = "-"
                else:
                    sign1 = " "

                time_str0 = sign0 + time0.strftime("%H:%M").upper()
                time_str1 = sign1 + time1.strftime("%H:%M").upper()

                padding = (columns - 60) * ' '

                screen += v_bar + ' ' + highlight[flash0] + ("{0:<10}{1:6}").format(
                    time_zone_list[i][0], time_str0) + highlight[0] + ' ' + b_var_single
                screen += ' ' + highlight[flash1] + ("{0:<10}{1:6}").format(
                    time_zone_list[i + 1][0], time_str1) + highlight[0] + ' ' + padding + v_bar + ' ' + leap_stats[i//2] + ' ' + v_bar
                # Each Timezone column is 29 chars, and the bar is 1 = 59

                screen += "\n"

            screen += center_l + h_bar * (columns - 29) + h_bar_down_connect + h_bar * 5 + \
                h_bar_up_connect + h_bar * 2 + h_bar_down_connect + 17 * h_bar + center_r + "\n"

            screen += v_bar + " " + utc_str + " " + b_var_single + " " + unix_str + " " * \
                (columns - len(metric_str + unix_str + b_clockdisp[0]) - 27) + v_bar + \
                ' ' + b_clockdisp[0] + " " + v_bar + " " + dst_str[0] + " " + v_bar + "\n"
            screen += v_bar + " " + metric_str + " " + b_var_single + " " + sit_str + " " * \
                (columns - len(metric_str + sit_str + b_clockdisp[1]) - 27) + v_bar + \
                ' ' + b_clockdisp[1] + " " + v_bar + " " + dst_str[1] + " " + v_bar + "\n"
            screen += v_bar + " " + solar_str + " " + b_var_single + " " + hex_str + " " * \
                (columns - len(solar_str + net_str + b_clockdisp[2]) - 27) + v_bar + \
                ' ' + b_clockdisp[2] + " " + v_bar + " " + dst_str[2] + " " + v_bar + "\n"
            screen += v_bar + " " + lst_str + " " + b_var_single + " " + net_str + " " * \
                (columns - len(lst_str + hex_str + b_clockdisp[3]) - 27) + v_bar + ' ' + \
                b_clockdisp[3] + " " + v_bar + " " + dst_str[3] + " " + v_bar + "\n"
            screen += corner_ll + h_bar * (columns - 29) + h_bar_up_connect + \
                h_bar * 8 + h_bar_up_connect + h_bar * 17 + corner_lr + "\n"
            ntpid_max_width = half_cols - 4
            ntpid_temp = ntp_id_str

            # Calculate NTP server ID scrolling if string is too large
            if(len(ntp_id_str) > ntpid_max_width):

                stages = 16 + len(ntp_id_str) - ntpid_max_width
                current_stage = int(unix_exact/.25) % stages

                if(current_stage < 8):
                    ntpid_temp = ntp_id_str[0:ntpid_max_width]
                elif(current_stage >= (stages - 8)):
                    ntpid_temp = ntp_id_str[(len(ntp_id_str)-ntpid_max_width):]
                else:
                    ntpid_temp = ntp_id_str[(current_stage - 8)
                                             :(current_stage - 8 + ntpid_max_width)]

            ntp_str_left = "NTP:" + ntpid_temp
            ntp_str_right = ("STR:{str} DLY:{dly} OFF:{off}").format(
                str=network.ntpstr,
                dly=float_fixed(float(network.ntpdly), 6, False),
                off=float_fixed(float(network.ntpoff), 7, True)
            )

            screen += themes[3] + " " + ntp_str_left + \
                ((columns - len(ntp_str_left + ntp_str_right)-2) * " ") + ntp_str_right + " "
            screen += themes[1]

            # Switch to the header color theme
            screen += themes[0]

            # Append blank lines to fill out the bottom of the screen
            for i in range(22, rows):
                screen += " " * columns

            loop_time = datetime.now(pytz.utc) - start_time
            print(screen, end="")

        except KeyboardInterrupt:
            utils.show_cursor()
            return

if __name__ == "__main__":
    utils.clear_screen()
    utils.show_cursor(False)
    main()
    utils.clear_screen()
    utils.show_cursor()
    print(RST_COLORS, end="")
