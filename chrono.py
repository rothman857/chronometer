#!/usr/bin/python3

from datetime import datetime, timedelta
import time
import json
import os
import random
from typing import List, Tuple, NoReturn
import pytz
import console
import ntp
from enum import Enum, auto
import timeutil
import clock
import cal

random.seed()


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


here = os.path.dirname(os.path.realpath(__file__))
if os.path.isfile(os.path.join(here, '.config')):
    with open(os.path.join(here, '.config')) as f:
        running_config = json.load(f)

else:
    with open(os.path.join(here, '.config'), 'w+') as f:
        json.dump(default_config, f, indent=2, sort_keys=True)
        running_config = default_config
        print(
            """Initial .config file generated.  
            Please update it with coordinates and desired timezones 
            before running chronometer.py again.""")
        exit()


try:
    lat = float(running_config['coordinates']['latitude'])
    lon = float(running_config['coordinates']['longitude'])
    refresh = float(running_config['refresh'])
    time_zone_list: List[Tuple[str, pytz.tzinfo.DstTzInfo]] = []
    for tz in running_config['timezones']:
        if tz[0] == '#':
            continue
        time_zone_list.append((tz.upper(), pytz.timezone(running_config['timezones'][tz])))

    time_zone_list.sort(key=lambda tz: tz[1].utcoffset(datetime.now()))
    _time_zone_list = [None] * len(time_zone_list)

    for i in range(0, len(time_zone_list), 2):
        _time_zone_list[i] = time_zone_list[i // 2][:10]
        _time_zone_list[i + 1] = time_zone_list[i // 2 + 5][:10]

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
class Color:
    BLACK_BG = "\x1b[40m"
    RED_BG = "\x1b[41m"
    WHITE_FG = "\x1b[97m"
    L_BLUE_FG = "\x1b[94m"
    L_BLUE_BG = "\x1b[104m"
    D_GRAY_FG = "\x1b[90m"


class Theme:
    text = Color.BLACK_BG + Color.WHITE_FG
    header = Color.L_BLUE_BG + Color.WHITE_FG
    border = Color.BLACK_BG + Color.L_BLUE_FG
    bar_empty = Color.BLACK_BG + Color.D_GRAY_FG
    bar_full = Color.BLACK_BG + Color.WHITE_FG
    highlight = Color.L_BLUE_BG + Color.WHITE_FG
    header_alert = Color.RED_BG + Color.WHITE_FG
    default = text


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


def draw_progress_bar(*, min: int = 0, width: int, max: int, value: float) -> str:
    level = int((width + 1) * (value - min) / (max - min))
    return (Theme.bar_full + chr(0x2550) * level + Theme.bar_empty + (chr(0x2500) * (width - level)))


def float_fixed(flt, wd, sign=False):
    wd = str(wd)
    sign = "+" if sign else ""
    return ('{:.' + wd + 's}').format(('{:' + sign + '.' + wd + 'f}').format(flt))


def main() -> NoReturn:
    ntp.thread.start()
    loop_time = timedelta(0)
    dst_str = ["", "", "", ""]
    v_bar = Theme.border + chr(0x2551)
    b_var_single = Theme.border + chr(0x2502)
    h_bar = Theme.border + chr(0x2550)
    h_bar_single = Theme.border + chr(0x2500)
    h_bar_up_connect = Theme.border + chr(0x2569)
    h_bar_down_connect = Theme.border + chr(0x2566)
    corner_ll = Theme.border + chr(0x255A)
    corner_lr = Theme.border + chr(0x255D)
    corner_ul = Theme.border + chr(0x2554)
    corner_ur = Theme.border + chr(0x2557)
    center_l = Theme.border + chr(0x2560)
    center_r = Theme.border + chr(0x2563)
    highlight = [Theme.text, Theme.highlight]
    diamond = chr(0x25fc)
    binary = ("-", diamond)
    rows = os.get_terminal_size().lines
    columns = os.get_terminal_size().columns
    half_cols = int(((columns - 1) / 2) // 1)

    while True:
        ntp_id_str = ntp.ntp_peer.server_id
        try:
            time.sleep(refresh)
            start_time = datetime.now().astimezone()
            now = start_time + loop_time
            u_second = now.microsecond / 1000000
            is_daylight_savings = time.localtime().tm_isdst
            current_tz = time.tzname[is_daylight_savings]
            screen = ""
            console.reset_cursor()
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
                b_clockdisp[i] = Theme.text + (
                    ''.join(row).replace("0", binary[0]).replace("1", binary[1])
                )
            if (now.month == 12):
                days_this_month = 31
            else:
                days_this_month = (
                    datetime(now.year, now.month + 1, 1) -
                    datetime(now.year, now.month, 1)
                ).days
            days_this_year = 366 if timeutil.is_leap_year(now) else 365
            time_table[ProgressBar.SECOND.value][1] = (
                now.second +
                u_second +
                random.randint(0, 9999) / 10000000000
            )
            time_table[ProgressBar.MINUTE.value][1] = (
                now.minute +
                time_table[ProgressBar.SECOND.value][1] / 60 +
                random.randint(0, 99) / 10000000000
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
                (time_table[ProgressBar.DAY.value][1] - 1) / days_this_month
            )
            time_table[ProgressBar.YEAR.value][1] = (
                now.year + (
                    timeutil.day_of_year(now) +
                    time_table[ProgressBar.DAY.value][1] -
                    int(time_table[ProgressBar.DAY.value][1])
                ) / days_this_year
            )
            time_table[ProgressBar.CENTURY.value][1] = (
                time_table[ProgressBar.YEAR.value][1] - 1
            ) / 100 + 1
            screen += Theme.header
            screen += f"{f'{now: %I:%M:%S %p {current_tz} - %A %B %d, %Y}': ^{columns}}".upper()
            screen += f'{corner_ul}{h_bar * (columns - 2)}{corner_ur}\n'

            for i in range(7):
                percent = time_table[i][1] - int(time_table[i][1])
                screen += (
                    f'{v_bar} {Theme.text}{time_table[i][0]} '
                    f'{draw_progress_bar(width=(columns - 19), max=1, value=percent)}'
                    f'{Theme.text} {100 * (percent):011.8f}% {v_bar}\n'
                )
            screen += (
                f'{center_l}'
                f'{h_bar * (columns - 23)}'
                f'{h_bar_down_connect}'
                f'{h_bar * 20}'
                f'{center_r}\n'
            )

            dst_str[0] = f'{Theme.text}INTL {cal.int_fix_date(now)}'
            dst_str[1] = f'{Theme.text}WRLD {cal.twc_date(now)}'
            dst_str[2] = f'{Theme.text}ANNO {cal.and_date(now)}'
            dst_str[3] = f'{Theme.text}JULN {float_fixed(cal.julian_date(date=now, reduced=False), 10, False)}'

            unix_int = int(now.timestamp())
            unix_exact = unix_int + u_second
            unix_str = (f"{Theme.text}UNX {unix_int}")

            day_percent_complete = (
                time_table[ProgressBar.DAY.value][1] - int(time_table[ProgressBar.DAY.value][1])
            )
            utc_now = now.astimezone(pytz.utc)
            day_percent_complete_utc = (
                utc_now.hour * 3600 +
                utc_now.minute * 60 +
                utc_now.second +
                utc_now.microsecond / 1000000
            ) / 86400
            sit_now = now.astimezone(pytz.utc) + timedelta(hours=1)
            day_percent_complete_cet = (
                sit_now.hour * 3600 +
                sit_now.minute * 60 +
                sit_now.second +
                sit_now.microsecond / 1000000
            ) / 86400

            sunrise, sunset, sol_noon = timeutil.sunriseset(now, lon, lat)
            solar_time = (
                now.replace(hour=12, minute=0, second=0, microsecond=0) +
                timedelta(seconds=sol_noon)
            )
            sol_str = (
                f'{Theme.text}SOL {solar_time:%H:%M:%S}'
            )
            lst_str = f'{Theme.text}LST {clock.sidereal_time(now, lon)}'
            met_str = f'{Theme.text}MET {clock.metric_time(day_percent_complete)}'
            hex_str = f'{Theme.text}HEX {clock.hex_time(day_percent_complete)}'
            net_str = f'{Theme.text}NET {clock.new_earth_time(day_percent_complete_utc)}'
            sit_str = f'{Theme.text}SIT {clock.sit_time(day_percent_complete_cet)}'
            utc_str = f'{Theme.text}UTC {now.astimezone(pytz.utc):%H:%M:%S}'

            diff = timeutil.sunriseset(now, lon, lat, event=timeutil.SunEvent.DAYLIGHT, fixed=True)
            nighttime = timeutil.sunriseset(
                now, lon, lat, event=timeutil.SunEvent.NIGHTTIME, fixed=True)

            if sunset > 0 and sunrise > 0:
                sunrise = timeutil.sunriseset(
                    now, lon, lat, event=timeutil.SunEvent.SUNRISE, offset=1)
            elif sunset < 0 and sunrise < 0:
                sunset = timeutil.sunriseset(
                    now, lon, lat, event=timeutil.SunEvent.SUNSET, offset=-1)

            time_List = [None, None, None, None, None]
            for i, s in enumerate([timeutil.leap_shift(now), sunrise, sunset, diff, nighttime]):
                hours, remainder = divmod(abs(s), 3600)
                minutes, seconds = divmod(remainder, 60)
                subs = 1000000 * (seconds - int(seconds))
                time_List[i] = (
                    f'{"-" if s < 0 else " "}'
                    f'{int(hours):02}:'
                    f'{int(minutes):02}:'
                    f'{int(seconds):02}.'
                    f'{int(subs):06}'
                )

            leap_stats = [
                f'LD{time_List[0]}',
                f'SR{time_List[1]}',
                f'SS{time_List[2]}',
                f'DD{time_List[3]}',
                f'ND{time_List[4]}'
            ]

            for i in range(0, len(time_zone_list), 2):
                time0 = now.astimezone(time_zone_list[i][1])
                time1 = now.astimezone(time_zone_list[i + 1][1])

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

                time_str0 = f'{sign0}{time0:%H:%M}'
                time_str1 = f'{sign1}{time1:%H:%M}'
                padding = (columns - 60) * ' '
                screen += (
                    f'{v_bar} '
                    f'{highlight[flash0]}'
                    f'{time_zone_list[i][0]:<10}'
                    f'{time_str0:6}'
                    f'{highlight[0]} '
                    f'{b_var_single}'
                )
                screen += (
                    f' {highlight[flash1]}'
                    f'{time_zone_list[i + 1][0]:<10}'
                    f'{time_str1:6}'
                    f'{highlight[0]} '
                    f'{padding}'
                    f'{v_bar} '
                    f'{Theme.text}{leap_stats[i//2]} '
                    f'{v_bar}'
                )
                screen += "\n"

            screen += (
                f'{center_l}'
                f'{h_bar * (columns - 29)}'
                f'{h_bar_down_connect}'
                f'{h_bar * 5}'
                f'{h_bar_up_connect}'
                f'{h_bar * 2}'
                f'{h_bar_down_connect}'
                f'{h_bar * 17}'
                f'{center_r}\n'
            )

            screen += (
                f'{v_bar} '
                f'{utc_str} '
                f'{b_var_single} '
                f'{unix_str}'
                f'{" " * (columns - len(met_str + unix_str + b_clockdisp[0]) + 3)}'
                f'{v_bar} '
                f'{b_clockdisp[0]} '
                f'{v_bar} '
                f'{dst_str[0]} '
                f'{v_bar}\n'
            )

            screen += (
                f'{v_bar} '
                f'{met_str} '
                f'{b_var_single} '
                f'{sit_str}'
                f'{" " * (columns - len(met_str + sit_str + b_clockdisp[1]) + 3)}'
                f'{v_bar} '
                f'{b_clockdisp[1]} '
                f'{v_bar} '
                f'{dst_str[1]} '
                f'{v_bar}\n'
            )

            screen += (
                f'{v_bar} '
                f'{sol_str} '
                f'{b_var_single} '
                f'{hex_str}'
                f'{" " * (columns - len(sol_str + net_str + b_clockdisp[2]) + 3)}'
                f'{v_bar} '
                f'{b_clockdisp[2]} '
                f'{v_bar} '
                f'{dst_str[2]} '
                f'{v_bar}\n'
            )

            screen += (
                f'{v_bar} '
                f'{lst_str} '
                f'{b_var_single} '
                f'{net_str}'
                f'{" " * (columns - len(lst_str + hex_str + b_clockdisp[3]) + 3)}'
                f'{v_bar} '

                f'{b_clockdisp[3]} '
                f'{v_bar} '
                f'{dst_str[3]} '
                f'{v_bar}\n'
            )

            screen += (
                f'{corner_ll}'
                f'{h_bar * (columns - 29)}'
                f'{h_bar_up_connect}'
                f'{h_bar * 8}'
                f'{h_bar_up_connect}'
                f'{h_bar * 17}'
                f'{corner_lr}\n'
            )

            ntpid_max_width = half_cols - 4
            ntpid_temp = ntp_id_str

            # Calculate NTP server ID scrolling if string is too large
            if(len(ntp_id_str) > ntpid_max_width):

                stages = 16 + len(ntp_id_str) - ntpid_max_width
                current_stage = int(unix_exact / .25) % stages

                if(current_stage < 8):
                    ntpid_temp = ntp_id_str[0:ntpid_max_width]
                elif(current_stage >= (stages - 8)):
                    ntpid_temp = ntp_id_str[(len(ntp_id_str) - ntpid_max_width):]
                else:
                    ntpid_temp = (
                        ntp_id_str[(current_stage - 8):(current_stage - 8 + ntpid_max_width)]
                    )

            ntp_str_left = f'NTP {ntpid_temp}'
            ntp_str_right = (
                f'ST {ntp.ntp_peer.stratum} '
                f'DLY {float_fixed(float(ntp.ntp_peer.delay), 6, False)} '
                f'OFF{float_fixed(float(ntp.ntp_peer.offset), 7, True)}'
            )

            screen += Theme.header if ntp.ntp_peer.server_id else Theme.header_alert
            screen += (
                f' {ntp_str_left}'
                f'{" " * (columns - len(ntp_str_left + ntp_str_right)-2)}'
                f'{ntp_str_right} '
            )
            screen += Theme.text

            # Append blank lines to fill out the bottom of the screen
            for i in range(22, rows):
                screen += " " * columns

            loop_time = datetime.now(pytz.utc) - start_time
            print(screen, end="")
            time.sleep(1)

        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    console.clear_screen()
    console.show_cursor(False)
    main()
    console.clear_screen()
    console.show_cursor()
    print(Theme.default, end="")
