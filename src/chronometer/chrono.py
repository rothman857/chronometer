#!/usr/bin/python3

from datetime import datetime, timedelta
from .tools import console, ntp, timeutil, clock, cal
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
    MONTH = auto()
    YEAR = auto()
    CENTURY = auto()


class Color:
    class BG:
        BLACK = "\x1b[40m"
        BRIGHT_BLUE = "\x1b[104m"
        RED = "\x1b[41m"

    class FG:
        WHITE = "\x1b[97m"
        BRIGHT_BLUE = "\x1b[94m"
        DARK_GRAY = "\x1b[90m"


class Theme:
    text = Color.BG.BLACK + Color.FG.WHITE
    header = Color.BG.BRIGHT_BLUE + Color.FG.WHITE
    border = Color.BG.BLACK + Color.FG.BRIGHT_BLUE
    bar_empty = Color.BG.BLACK + Color.FG.DARK_GRAY
    bar_full = Color.BG.BLACK + Color.FG.WHITE
    highlight = Color.BG.BRIGHT_BLUE + Color.FG.WHITE
    header_alert = Color.BG.RED + Color.FG.WHITE
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
            "Please update \'chrono_config.ini\' with coordinates and desired timezones.  "
            "before running chrono.py again."
        )
        chrono_exit()

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
    def __init__(self, * , width: int = 0) -> None:
        config = load_config()
        time_zone_data_temp = config.time_zones
        time_zone_data_temp.sort(key=lambda tz: tz[1].utcoffset(datetime.now()))
        self.lat = config.latitude
        self.lon = config.longitude
        self.refresh = config.refresh
        self.loop_time = timedelta()
        self.cal_str = ["", "", "", ""]
        self.v_bar = Theme.border + '\N{BOX DRAWINGS DOUBLE VERTICAL}'
        self.b_var_single = Theme.border + '\N{BOX DRAWINGS LIGHT VERTICAL}'
        self.h_bar = Theme.border + '\N{BOX DRAWINGS DOUBLE HORIZONTAL}'
        self.h_bar_up_connect = Theme.border + '\N{BOX DRAWINGS DOUBLE UP AND HORIZONTAL}'
        self.h_bar_down_connect = Theme.border + '\N{BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL}'
        self.corner_ll = Theme.border + '\N{BOX DRAWINGS DOUBLE UP AND RIGHT}'
        self.corner_lr = Theme.border + '\N{BOX DRAWINGS DOUBLE UP AND LEFT}'
        self.corner_ul = Theme.border + '\N{BOX DRAWINGS DOUBLE DOWN AND RIGHT}'
        self.corner_ur = Theme.border + '\N{BOX DRAWINGS DOUBLE DOWN AND LEFT}'
        self.center_l = Theme.border + '\N{BOX DRAWINGS DOUBLE VERTICAL AND RIGHT}'
        self.center_r = Theme.border + '\N{BOX DRAWINGS DOUBLE VERTICAL AND LEFT}'
        self.binary = ("-", '\N{BLACK MEDIUM SQUARE}')
        self.highlight = (Theme.text, Theme.highlight)
        self.rows = os.get_terminal_size().lines
        self.columns = os.get_terminal_size().columns if width < 60 else width
        self.sun = timeutil.Sun(date=None, lon=self.lon, lat=self.lat)
        self.time_zone_data = [time_zone_data_temp[i] for i in flatten((_, _+5) for _ in range(5))]
        self.time_table = {b: ProgressBar(min=0, max=1, width=self.columns - 19, value=0) for b in Bar}


    def render(self):
        ntp_id_str = ntp.peer.server_id
        start_time = datetime.now().astimezone()
        now = start_time + self.loop_time
        u_second = now.microsecond / 1000000
        is_daylight_savings = time.localtime().tm_isdst
        current_tz = time.tzname[is_daylight_savings]
        screen = ""
        console.reset_cursor()
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
                ''.join(row).replace("0", self.binary[0]).replace("1", self.binary[1])
            )

        days_this_month = (
            now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)
        ).day
        days_this_year = 365 + timeutil.is_leap_year(now)
        self.time_table[Bar.SECOND].value = now.second + u_second + random.randint(0, 9999) / 10**10
        self.time_table[Bar.MINUTE].value = (
            now.minute + self.time_table[Bar.SECOND].value / 60 + random.randint(0, 99) / 10**9
        )
        self.time_table[Bar.HOUR].value = now.hour + self.time_table[Bar.MINUTE].value / 60
        self.time_table[Bar.DAY].value = now.day + self.time_table[Bar.HOUR].value / 24
        self.time_table[Bar.MONTH].value = now.month + \
            (self.time_table[Bar.DAY].value - 1) / days_this_month
        self.time_table[Bar.YEAR].value = (
            now.year + (
                timeutil.day_of_year(now) +
                self.time_table[Bar.DAY].value -
                int(self.time_table[Bar.DAY].value)
            ) / days_this_year
        )
        self.time_table[Bar.CENTURY].value = (self.time_table[Bar.YEAR].value - 1) / 100 + 1
        screen += Theme.header
        screen += f"{f'{now: %I:%M:%S %p {current_tz} - %A %B %d, %Y}': ^{self.columns}}\n".upper()
        screen += f'{self.corner_ul}{self.h_bar * (self.columns - 2)}{self.corner_ur}\n'
        for i, bar in enumerate(Bar):
            percent = self.time_table[bar].value - int(self.time_table[bar].value)
            self.time_table[bar].value = percent
            screen += (
                f'{self.v_bar} {Theme.text}{bar.name[0].upper()} '
                f'{self.time_table[bar]}'
                f'{Theme.text} {100 * (percent):011.8f}% {self.v_bar}\n'
            )

        screen += (
            f'{self.center_l}'
            f'{self.h_bar * (self.columns - 23)}'
            f'{self.h_bar_down_connect}'
            f'{self.h_bar * 20}'
            f'{self.center_r}\n'
        )

        self.cal_str[0] = f'{Theme.text}IFC {cal.int_fix_date(now)}'
        self.cal_str[1] = f'{Theme.text}TWC {cal.twc_date(now)}'
        self.cal_str[2] = f'{Theme.text}AND {cal.and_date(now)}'
        self.cal_str[3] = (
            f'{Theme.text}'
            f'JUL {float_width(cal.julian_date(date=now, reduced=False), 11, False)}'
        )

        self.sun.date = now
        self.sun.refresh()
        sol_str = f'{Theme.text}SOL {self.sun.solar_noon:%H:%M:%S}'
        lst_str = f'{Theme.text}LST {clock.sidereal_time(now, self.lon)}'
        met_str = f'{Theme.text}MET {clock.metric_time(now)}'
        hex_str = f'{Theme.text}HEX {clock.hex_time(now)}'
        net_str = f'{Theme.text}NET {clock.new_earth_time(now)}'
        sit_str = f'{Theme.text}SIT {clock.sit_time(now)}'
        utc_str = f'{Theme.text}UTC {clock.utc_time(now)}'
        unx_str = f'{Theme.text}UNX {clock.unix_time(now)}'

        sunrise = self.sun.sunrise_timer
        sunset = self.sun.sunset_timer
        self.sun.refresh(fixed=True)
        daytime = self.sun.daylight
        nighttime = self.sun.nighttime

        if sunset > 0 and sunrise > 0:
            self.sun.refresh(offset=1)
            sunrise = self.sun.sunrise_timer
        elif sunset < 0 and sunrise < 0:
            self.sun.refresh(offset=-1)
            sunset = self.sun.sunset_timer

        leap_drift = timeutil.leap_drift(now)

        time_list = [''] * 5
        for i, s in enumerate([leap_drift, sunrise, sunset, daytime, nighttime]):
            hours, remainder = divmod(abs(s), 3600)
            minutes, seconds = divmod(remainder, 60)
            subs = 1000000 * (seconds - int(seconds))
            time_list[i] = (
                f'{"-" if s < 0 else " "}'
                f'{int(hours):02}:'
                f'{int(minutes):02}:'
                f'{int(seconds):02}.'
                f'{int(subs):06}'
            )

        leap_stats = [
            f'LD{time_list[0]}',
            f'SR{time_list[1]}',
            f'SS{time_list[2]}',
            f'DD{time_list[3]}',
            f'ND{time_list[4]}'
        ]

        for i in range(0, len(self.time_zone_data), 2):
            time0 = now.astimezone(self.time_zone_data[i][1])
            time1 = now.astimezone(self.time_zone_data[i + 1][1])

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
            padding = (self.columns - 60) * ' '
            screen += (
                f'{self.v_bar}'
                f'{self.highlight[flash0]} '
                f'{self.time_zone_data[i][0]:<10}'
                f'{time_str0:6} '
                f'{self.highlight[0]}'
                f'{self.b_var_single}'
            )
            screen += (
                f'{self.highlight[flash1]} '
                f'{self.time_zone_data[i + 1][0]:<10}'
                f'{time_str1:6} '
                f'{self.highlight[0]}'
                f'{padding}'
                f'{self.v_bar} '
                f'{Theme.text}{leap_stats[i//2]} '
                f'{self.v_bar}'
            )
            screen += "\n"

        screen += (
            f'{self.center_l}'
            f'{self.h_bar * (self.columns - 29)}'
            f'{self.h_bar_down_connect}'
            f'{self.h_bar * 5}'
            f'{self.h_bar_up_connect}'
            f'{self.h_bar * 2}'
            f'{self.h_bar_down_connect}'
            f'{self.h_bar * 17}'
            f'{self.center_r}\n'
        )

        screen += (
            f'{self.v_bar} '
            f'{utc_str} '
            f'{self.b_var_single} '
            f'{unx_str}'
            f'{" " * (self.columns - len(met_str + unx_str + b_clockdisp[0]) + 3)}'
            f'{self.v_bar} '
            f'{b_clockdisp[0]} '
            f'{self.v_bar} '
            f'{self.cal_str[0]} '
            f'{self.v_bar}\n'
        )

        screen += (
            f'{self.v_bar} '
            f'{met_str} '
            f'{self.b_var_single} '
            f'{sit_str}'
            f'{" " * (self.columns - len(met_str + sit_str + b_clockdisp[1]) + 3)}'
            f'{self.v_bar} '
            f'{b_clockdisp[1]} '
            f'{self.v_bar} '
            f'{self.cal_str[1]} '
            f'{self.v_bar}\n'
        )

        screen += (
            f'{self.v_bar} '
            f'{sol_str} '
            f'{self.b_var_single} '
            f'{hex_str}'
            f'{" " * (self.columns - len(sol_str + net_str + b_clockdisp[2]) + 3)}'
            f'{self.v_bar} '
            f'{b_clockdisp[2]} '
            f'{self.v_bar} '
            f'{self.cal_str[2]} '
            f'{self.v_bar}\n'
        )

        screen += (
            f'{self.v_bar} '
            f'{lst_str} '
            f'{self.b_var_single} '
            f'{net_str}'
            f'{" " * (self.columns - len(lst_str + hex_str + b_clockdisp[3]) + 3)}'
            f'{self.v_bar} '

            f'{b_clockdisp[3]} '
            f'{self.v_bar} '
            f'{self.cal_str[3]} '
            f'{self.v_bar}\n'
        )

        screen += (
            f'{self.corner_ll}'
            f'{self.h_bar * (self.columns - 29)}'
            f'{self.h_bar_up_connect}'
            f'{self.h_bar * 8}'
            f'{self.h_bar_up_connect}'
            f'{self.h_bar * 17}'
            f'{self.corner_lr}\n'
        )

        ntpid_temp = ntp_id_str

        ntp_str_right = (
            f'ST {ntp.peer.stratum} '
            f'DLY {float_width(float(ntp.peer.delay), 6, False)} '
            f'OFF{float_width(float(ntp.peer.offset), 7, True)}'
        )

        if ntp.peer.source:
            ntp_str_right = f'REF {ntp.peer.source} {ntp_str_right}'

        ntpid_max_width = self.columns - len(ntp_str_right) - 3

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
            f'{" " * (self.columns - len(ntp_str_left + ntp_str_right)-2)}'
            f'{ntp_str_right} '
        )
        screen += Theme.text

        self.loop_time = datetime.now(pytz.utc) - start_time
        return screen

def chrono_exit():
    console.clear_screen()
    console.show_cursor()

def run():
    console.clear_screen()
    console.show_cursor(False)
    c = Chronometer()
    while True:
        try:
            print(c.render(), end='')
            time.sleep(c.refresh)
        except KeyboardInterrupt:
            print(Theme.default, end="")
            chrono_exit()
            break

    



if __name__ == "__main__":
    run()