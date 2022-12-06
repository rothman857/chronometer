#!/usr/bin/python3

from datetime import datetime, timedelta
from chronometer.tools import console, ntp, timeutil, clock, cal
import time
import os
import random
from typing import Any, Iterable, List, Tuple
import pytz
from enum import Enum, auto
import shutil
import configparser

random.seed()


class Bar(Enum):
    SECOND = auto()
    MINUTE = auto()
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    YEAR = auto()
    CENTURY = auto()


class Theme:
    text = console.Color.BG.BLACK + console.Color.FG.WHITE
    header = console.Color.BG.BRIGHT_BLUE + console.Color.FG.WHITE
    border = console.Color.BG.BLACK + console.Color.FG.BRIGHT_BLUE
    bar_empty = console.Color.BG.BLACK + console.Color.FG.DARK_GRAY
    bar_full = console.Color.BG.BLACK + console.Color.FG.WHITE
    highlight = console.Color.BG.BRIGHT_BLUE + console.Color.FG.WHITE
    header_alert = console.Color.BG.RED + console.Color.FG.WHITE
    default = text


class ProgressBar:

    bar_full_char = "\N{BOX DRAWINGS HEAVY HORIZONTAL}"
    bar_empty_char = "\N{BOX DRAWINGS LIGHT HORIZONTAL}"

    def __init__(self, min: int, max: int, width: int, value: float) -> None:
        self.min = min
        self.max = max
        self.width = width
        self.value = value

    def __str__(self) -> str:
        level = int((self.width + 1) * (self.value - self.min) / (self.max - self.min))
        return (
            f'{Theme.bar_full}'
            f'{self.bar_full_char * level}'
            f'{Theme.bar_empty}'
            f'{self.bar_empty_char * (self.width - level)}'
        )


class ChronoConfig:
    latitude: float = 0
    longitude: float = 0
    refresh: float = 0
    time_zones: List[Tuple[str, Any]] = []


def load_config(filename: str = '.chrono_config') -> ChronoConfig:
    config = ChronoConfig()
    here = os.path.dirname(os.path.realpath(__file__))
    config_file_path = os.path.join(os.path.expanduser('~'), filename)

    if not os.path.isfile(config_file_path):
        shutil.copyfile(os.path.join(here, 'files', 'default_config.ini'), config_file_path)
        print(
            "Initial config file generated.  "
            "Please update \'~/.chrono_config\' with coordinates and desired timezones.  "
            "before running chrono.py again."
        )
        console.show_cursor()
        exit()

    try:
        parser = configparser.ConfigParser()
        parser.read(config_file_path)
        time_zone_data = [
            (
                tz.upper().replace('_', ' ')[:10],
                pytz.timezone(parser['timezones'][tz])
            ) for tz in parser['timezones']
        ]
    except configparser.ParsingError as e:
        print(f"Error reading chrono_config ({e}).")
        exit()

    config.latitude = float(parser['settings']['latitude'])
    config.longitude = float(parser['settings']['longitude'])
    config.refresh = float(parser['settings']['refresh'])
    config.time_zones = time_zone_data
    return config


def float_width(value: float, width: int, signed: bool = False) -> str:
    sign = "+" if signed else ""
    return f'{f"{value:{sign}.{width}f}":.{width}s}'


def flatten(l: Iterable):
    return (item for sublist in l for item in sublist)


class Chronometer:
    config = load_config()
    lon = config.longitude
    lat = config.latitude
    time_zone_data_temp = config.time_zones
    time_zone_data_temp.sort(key=lambda tz: tz[1].utcoffset(datetime.now()))
    loop_time = timedelta()
    cal_str = ["", "", "", ""]
    v_bar = Theme.border + '\N{BOX DRAWINGS DOUBLE VERTICAL}'
    b_var_single = Theme.border + '\N{BOX DRAWINGS LIGHT VERTICAL}'
    h_bar = Theme.border + '\N{BOX DRAWINGS DOUBLE HORIZONTAL}'
    h_bar_up_connect = Theme.border + '\N{BOX DRAWINGS DOUBLE UP AND HORIZONTAL}'
    h_bar_down_connect = Theme.border + '\N{BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL}'
    corner_ll = Theme.border + '\N{BOX DRAWINGS DOUBLE UP AND RIGHT}'
    corner_lr = Theme.border + '\N{BOX DRAWINGS DOUBLE UP AND LEFT}'
    corner_ul = Theme.border + '\N{BOX DRAWINGS DOUBLE DOWN AND RIGHT}'
    corner_ur = Theme.border + '\N{BOX DRAWINGS DOUBLE DOWN AND LEFT}'
    center_l = Theme.border + '\N{BOX DRAWINGS DOUBLE VERTICAL AND RIGHT}'
    center_r = Theme.border + '\N{BOX DRAWINGS DOUBLE VERTICAL AND LEFT}'
    binary = ("-", '\N{BLACK MEDIUM SQUARE}')
    highlight = (Theme.text, Theme.highlight)
    rows = os.get_terminal_size().lines
    columns = os.get_terminal_size().columns  # if width < 60 else width
    sun = timeutil.Sun(date=None, lon=lon, lat=lat)

    time_zone_data = []
    for i in flatten((_, _ + 4) for _ in range(4)):
        time_zone_data.append(time_zone_data_temp[i])

    time_table = {}
    for b in Bar:
        time_table.update({b: ProgressBar(min=0, max=1, width=columns - 19, value=0)})

    @classmethod
    def render(cls):
        start_time = datetime.now().astimezone()
        now = start_time + cls.loop_time
        u_second = now.microsecond / 1000000
        is_daylight_savings = time.localtime().tm_isdst
        current_tz = time.tzname[is_daylight_savings]
        screen = ""
        hour_binary = divmod(now.hour, 10)
        minute_binary = divmod(now.minute, 10)
        second_binary = divmod(now.second, 10)
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
                ''.join(row).replace("0", cls.binary[0]).replace("1", cls.binary[1])
            )

        days_this_month = (
            now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)
        ).day
        days_this_year = 365 + timeutil.is_leap_year(now)
        cls.time_table[Bar.SECOND].value = now.second + u_second + random.randint(0, 9999) / 10**10
        cls.time_table[Bar.MINUTE].value = (
            now.minute + cls.time_table[Bar.SECOND].value / 60 + random.randint(0, 99) / 10**9
        )
        cls.time_table[Bar.HOUR].value = now.hour + cls.time_table[Bar.MINUTE].value / 60
        cls.time_table[Bar.DAY].value = now.day + cls.time_table[Bar.HOUR].value / 24
        cls.time_table[Bar.WEEK].value = (
            (now.weekday()+1)%7 + cls.time_table[Bar.DAY].value % 1
            )/7
        cls.time_table[Bar.MONTH].value = now.month + \
            (cls.time_table[Bar.DAY].value - 1) / days_this_month
        cls.time_table[Bar.YEAR].value = (
            now.year + (
                timeutil.day_of_year(now) - 1 +
                cls.time_table[Bar.DAY].value -
                int(cls.time_table[Bar.DAY].value)
            ) / days_this_year
        )
        cls.time_table[Bar.CENTURY].value = (cls.time_table[Bar.YEAR].value - 1) / 100 + 1
        screen += Theme.header
        screen += f"{f'{now: %I:%M:%S %p {current_tz} - %A %B %d, %Y}': ^{cls.columns}}\n".upper()
        screen += f'{cls.corner_ul}{cls.h_bar * (cls.columns - 2)}{cls.corner_ur}\n'
        for i, bar in enumerate(Bar):
            percent = cls.time_table[bar].value - int(cls.time_table[bar].value)
            cls.time_table[bar].value = percent
            screen += (
                f'{cls.v_bar} {Theme.text}{bar.name[0].upper()} '
                f'{cls.time_table[bar]}'
                f'{Theme.text} {100 * (percent):011.8f}% {cls.v_bar}\n'
            )

        screen += (
            f'{cls.center_l}'
            f'{cls.h_bar * (cls.columns - 23)}'
            f'{cls.h_bar_down_connect}'
            f'{cls.h_bar * 20}'
            f'{cls.center_r}\n'
        )

        cls.cal_str[0] = f'{Theme.text}IFC  {cal.int_fix_date(now)}'
        cls.cal_str[1] = f'{Theme.text}TWC  {cal.twc_date(now)}'
        cls.cal_str[2] = f'{Theme.text}PAX {cal.pax_date(now)}'
        cls.cal_str[3] = (
            f'{Theme.text}'
            f'JUL {float_width(cal.julian_date(date=now, reduced=False), 11, False)}'
        )

        cls.sun.date = now
        cls.sun.refresh()
        sol_str = f'{Theme.text}SOL {cls.sun.solar_noon:%H:%M:%S}'
        lst_str = f'{Theme.text}LST {clock.sidereal_time(now, cls.lon)}'
        met_str = f'{Theme.text}DEC {clock.metric_time(now)}'
        hex_str = f'{Theme.text}HEX {clock.hex_time(now)}'
        net_str = f'{Theme.text}NET {clock.new_earth_time(now)}'
        sit_str = f'{Theme.text}SIT {clock.sit_time(now)}'
        utc_str = f'{Theme.text}UTC {clock.utc_time(now)}'
        unx_str = f'{Theme.text}UNX {clock.unix_time(now)}'

        sunrise = cls.sun.sunrise_timer
        sunset = cls.sun.sunset_timer
        cls.sun.refresh(fixed=True)
        daytime = cls.sun.daylight
        nighttime = cls.sun.nighttime

        if sunset > 0 and sunrise > 0:
            cls.sun.refresh(offset=1)
            sunrise = cls.sun.sunrise_timer
        elif sunset < 0 and sunrise < 0:
            cls.sun.refresh(offset=-1)
            sunset = cls.sun.sunset_timer

        leap_drift = timeutil.leap_drift(now)
        hours, remainder = divmod(abs(leap_drift), 3600)
        minutes, seconds = divmod(remainder, 60)
        subs = seconds - int(seconds)
        leap_drift_str = (
            f'{"-" if leap_drift < 0 else "+"}'
            f'{int(hours):02}:'
            f'{int(minutes):02}:'
            f'{int(seconds):02}.'
            f'{int(10000 * subs):04}'
        )
        next_leap = timeutil.next_leap(now) - now
        days, remainder = divmod(next_leap.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        per_progress = (
            (now - timeutil.prev_leap(now))/(timeutil.next_leap(now) - timeutil.prev_leap(now))
        )
        cyc_progress = (now - timeutil.prev_cycle(now)).total_seconds() / ((365 * 400 + 97) * 86400)

        leap_stats = [
            f"DFT {leap_drift_str}",
            f"NXT -{int(days):04}:{int(hours):02}:{int(minutes):02}:{int(seconds):02}",
            f'PER {100*per_progress:013.10f}%',
            f"CYC {100*cyc_progress:013.10f}%",
        ]

        for i in range(0, len(cls.time_zone_data), 2):
            time0 = now.astimezone(cls.time_zone_data[i][1])
            time1 = now.astimezone(cls.time_zone_data[i + 1][1])

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
            padding = (cls.columns - 60) * ' '
            screen += (
                f'{cls.v_bar}'
                f'{cls.highlight[flash0]} '
                f'{cls.time_zone_data[i][0]:<10}'
                f'{time_str0:6} '
                f'{cls.highlight[0]}'
                f'{cls.b_var_single}'
            )
            screen += (
                f'{cls.highlight[flash1]} '
                f'{cls.time_zone_data[i + 1][0]:<10}'
                f'{time_str1:6} '
                f'{cls.highlight[0]}'
                f'{padding}'
                f'{cls.v_bar} '
                f'{Theme.text}{leap_stats[i//2]} '
                f'{cls.v_bar}'
            )
            screen += "\n"

        screen += (
            f'{cls.center_l}'
            f'{cls.h_bar * (cls.columns - 29)}'
            f'{cls.h_bar_down_connect}'
            f'{cls.h_bar * 5}'
            f'{cls.h_bar_up_connect}'
            f'{cls.h_bar * 2}'
            f'{cls.h_bar_down_connect}'
            f'{cls.h_bar * 17}'
            f'{cls.center_r}\n'
        )

        screen += (
            f'{cls.v_bar} '
            f'{utc_str} '
            f'{cls.b_var_single} '
            f'{unx_str}'
            f'{" " * (cls.columns - len(met_str + unx_str + b_clockdisp[0]) + 3)}'
            f'{cls.v_bar} '
            f'{b_clockdisp[0]} '
            f'{cls.v_bar} '
            f'{cls.cal_str[0]} '
            f'{cls.v_bar}\n'
        )

        screen += (
            f'{cls.v_bar} '
            f'{met_str} '
            f'{cls.b_var_single} '
            f'{sit_str}'
            f'{" " * (cls.columns - len(met_str + sit_str + b_clockdisp[1]) + 3)}'
            f'{cls.v_bar} '
            f'{b_clockdisp[1]} '
            f'{cls.v_bar} '
            f'{cls.cal_str[1]} '
            f'{cls.v_bar}\n'
        )

        screen += (
            f'{cls.v_bar} '
            f'{sol_str} '
            f'{cls.b_var_single} '
            f'{hex_str}'
            f'{" " * (cls.columns - len(sol_str + net_str + b_clockdisp[2]) + 3)}'
            f'{cls.v_bar} '
            f'{b_clockdisp[2]} '
            f'{cls.v_bar} '
            f'{cls.cal_str[2]} '
            f'{cls.v_bar}\n'
        )

        screen += (
            f'{cls.v_bar} '
            f'{lst_str} '
            f'{cls.b_var_single} '
            f'{net_str}'
            f'{" " * (cls.columns - len(lst_str + hex_str + b_clockdisp[3]) + 3)}'
            f'{cls.v_bar} '

            f'{b_clockdisp[3]} '
            f'{cls.v_bar} '
            f'{cls.cal_str[3]} '
            f'{cls.v_bar}\n'
        )

        screen += (
            f'{cls.corner_ll}'
            f'{cls.h_bar * (cls.columns - 29)}'
            f'{cls.h_bar_up_connect}'
            f'{cls.h_bar * 8}'
            f'{cls.h_bar_up_connect}'
            f'{cls.h_bar * 17}'
            f'{cls.corner_lr}\n'
        )

        if ntp.service_status == ntp.ServiceStatus.ACTIVE:
            ntp_id_str = ntp.peer.server_id
            ntpid_temp = ntp_id_str

            ntp_str_right = (
                f'ST {ntp.peer.stratum} '
                f'DLY {float_width(float(ntp.peer.delay), 6, False)} '
                f'OFF{float_width(float(ntp.peer.offset), 7, True)}'
            )

            if ntp.peer.source:
                ntp_str_right = f'REF {ntp.peer.source} {ntp_str_right}'

            ntpid_max_width = cls.columns - len(ntp_str_right) - 3

            # Calculate NTP server ID scrolling if string is too large
            if(len(ntp_id_str) > ntpid_max_width):

                stages = 16 + len(ntp_id_str) - ntpid_max_width
                current_stage = int(now.timestamp() / .25) % stages

                if(current_stage < 8):
                    ntpid_temp = ntp_id_str[0:ntpid_max_width]
                elif(current_stage >= (stages - 8)):
                    ntpid_temp = ntp_id_str[(len(ntp_id_str) - ntpid_max_width):]
                else:
                    ntpid_temp = (
                        ntp_id_str[(current_stage - 8):(current_stage - 8 + ntpid_max_width)]
                    )
            ntp_str_left = f'{ntpid_temp}'

            screen += (Theme.header if ntp.peer.state == ntp.State.PEER else Theme.header_alert)

            screen += (
                f' {ntp_str_left}'
                f'{" " * (cls.columns - len(ntp_str_left + ntp_str_right)-2)}'
                f'{ntp_str_right} '
            )
        screen += Theme.text

        cls.loop_time = datetime.now(pytz.utc) - start_time
        return screen


def run():
    console.clear_screen()
    console.show_cursor(False)

    while True:
        try:
            print(Chronometer.render(), end='\n' * (Chronometer.rows - 22))
            console.reset_cursor()
            time.sleep(Chronometer.config.refresh)
        except KeyboardInterrupt:
            print(Theme.default, end="")
            console.clear_screen()
            console.show_cursor()
            break


if __name__ == "__main__":
    pass
