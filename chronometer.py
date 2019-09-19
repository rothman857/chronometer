#!/usr/bin/python3
from datetime import datetime, timedelta
import time
import os
import threading
import subprocess
import socket
import re
import math
import random
from myColors import colors
from pytz import timezone, utc

dbg_on = False
random.seed()
time_zone_list = []
is_connected = False

config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "chrono-config")
config_file = open(config_file)
for line in config_file:
    setting = re.search(r"^[^#].+", line)
    if setting:
        setting = re.split(r"\s+", setting.string)
        if (setting[0] == "timezone"):
            time_zone_list.append([setting[2].replace("'",""), timezone(setting[1])])
        if (setting[0] == "longitude"):
            lon = float(setting[1])
        if (setting[0] == "refresh"):
            refresh = float(setting[1])
config_file.close()

themes = [colors.bg.black,      # background
          colors.fg.white,      # text
          colors.fg.lightblue,  # table borders
          colors.bg.lightblue,  # text highlight
          colors.fg.darkgray]   # progress bar dim

SECOND = 0
MINUTE = 1
HOUR = 2
DAY = 3
MONTH = 4
YEAR = 5
CENTURY = 6

LABEL = 0
VALUE = 1
PRECISION = 2

ntpoff = 0
ntpdly = 0
ntpstr = "-"
ntpid = "---"

weekday_abbr = ["MO",
                "TU",
                "WE",
                "TH",
                "FR",
                "SA",
                "SU"]

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
    return (chr(0x2550) * level + colors.fg.darkgray + (chr(0x2500) * (width - level)))


def timedelta_strf(t_delta, fmt):
    _ = {"days": t_delta.days}
    _["hours"], remainder = divmod(t_delta.seconds, 3600)
    _["minutes"], _["seconds"] = divmod(remainder, 60)
    return fmt.format(**_)


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


def float_fixed(flt, wd, sign):
    wd = str(wd)
    sign = "+" if sign else ""
    return ('{:.' + wd + 's}').format(('{:' + sign + '.' + wd + 'f}').format(flt))


def get_relative_date(ordinal, weekday, month, year):
    firstday = (datetime(year, month, 1).weekday() + 1) % 7
    first_sunday = (7 - firstday) % 7 + 1
    return datetime(year, month, first_sunday + weekday + 7 * (ordinal - 1))


def solar_time(dt, lon, off, fmt):
    lstm = 15 * off
    d = (dt - dt.replace(day=1, month=1)).total_seconds()/(86400)
    b = (360/365.242) * (d - 81) * math.pi/180
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    tc = 4 * (lon - lstm) + eot
    lst = (dt + timedelta(hours=tc/60))
    _ = {"hour": lst.hour, "minute": lst.minute, "second": lst.second}
    return fmt.format(**_)


def sidereal_time(dt, lon, off, fmt):
    j = ((datetime.now() - datetime(year=2000, month=1, day=1)) - timedelta(hours=off)).total_seconds()/86400
    l0 = 99.967794687
    l1 = 360.98564736628603
    l2 = 2.907879 * (10 ** -13)
    l3 = -5.302 * (10 ** -22)
    theta = (l0 + (l1 * j) + (l2 * (j ** 2)) + (l3 * (j ** 3)) + lon) % 360
    result = int(timedelta(hours = theta/15).total_seconds())
    _ = dict()
    _["hour"], remainder = divmod(result, 3600)
    _["minute"], _["second"] = divmod(remainder, 60)
    return fmt.format(**_)


def is_dst(zonename, utc_time):
    if zonename not in ["STD", "DST"]:
        tz = timezone(zonename)
        now = utc.localize(utc_time)
        return now.astimezone(tz).dst() != timedelta(0)
    else:
        return False


def dbg(a, b):
    if(dbg_on):
        print("<< DEBUG " + a + ">>  (press enter to continue)")
        print(b)
        input()
    return


os.system("clear")
os.system("setterm -cursor off")


def main():
    loop_time = timedelta(0)
    dst_str = ["", "", "", ""]
    v_bar = themes[2] + chr(0x2551) + themes[1]
    b_var_single = themes[2] + chr(0x2502) + themes[1]
    h_bar = themes[2] + chr(0x2550) + themes[1]
    h_bar_up_connect = themes[2] + chr(0x2569) + themes[1]
    h_bar_down_connect = themes[2] + chr(0x2566) + themes[1]
    h_bar_up_connect_single = themes[2] + chr(0x2567) + themes[1]
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
            start_time = datetime.now() + timedelta(hours=5)
            offset = -(time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)/(3600)
            now = start_time + loop_time + timedelta(hours=5)
            utcnow = now.utcnow()
            cetnow = utcnow + timedelta(hours=1)
            DST = [get_relative_date(2, 0, 3, now.year).replace(hour=2),
                   get_relative_date(1, 0, 11, now.year).replace(hour=2)]
            is_daylight_savings = time.localtime().tm_isdst

            if (now < DST[0]):
                next_date = DST[0]
            elif ((now < DST[1]) and is_daylight_savings):
                next_date = DST[1]
            else:
                next_date = get_relative_date(2, 0, 3, now.year + 1).replace(hour=2)

            current_tz = time.tzname[is_daylight_savings]
            time_until_dst = next_date - now + timedelta(seconds=1)

            rows = os.get_terminal_size().lines
            columns = os.get_terminal_size().columns
            half_cols = int(((columns - 1) / 2) // 1)
            screen = ""
            reset_cursor()
            u_second = now.microsecond / 1000000
            print(themes[0], end="")
            hour_binary = divmod(now.hour, 10)
            minute_binary = divmod(now.minute, 10)
            second_binary = divmod(now.second, 10)

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
                b_clockdisp[i] = ''.join(row).replace("0", " " + binary[0]).replace("1", " " + binary[1])

            if (now.month == 12):
                days_this_month = 31
            else:
                days_this_month = (datetime(now.year, now.month + 1, 1) - datetime(now.year, now.month, 1)).days

            day_of_year = (now - datetime(now.year, 1, 1)).days
            days_this_year = (datetime(now.year + 1, 1, 1) - datetime(now.year, 1, 1)).days

            time_table[SECOND][VALUE] = now.second + u_second + random.randint(0,9999)/10000000000
            time_table[MINUTE][VALUE] = now.minute + time_table[SECOND][VALUE] / 60 + random.randint(0,99)/10000000000
            time_table[HOUR][VALUE] = now.hour + time_table[MINUTE][VALUE] / 60
            time_table[DAY][VALUE] = now.day + time_table[HOUR][VALUE] / 24
            time_table[MONTH][VALUE] = now.month + (time_table[DAY][VALUE] - 1)/days_this_month
            time_table[YEAR][VALUE] = now.year + (day_of_year + time_table[DAY][VALUE] - int(time_table[DAY][VALUE])) / days_this_year
            time_table[CENTURY][VALUE] = (time_table[YEAR][VALUE] - 1) / 100 + 1

            screen += themes[3]
            screen += ("{: ^" + str(columns) + "}\n").format(now.strftime("%I:%M:%S %p " + current_tz + " - %A %B %d, %Y")).upper() + themes[0]
            screen += corner_ul + h_bar * (columns - 2) + corner_ur + "\n"

            for i in range(7):
                percent = time_table[i][VALUE] - int(time_table[i][VALUE])
                screen += v_bar + (" {0:} " + "{2:}" + themes[1] + " {3:011.8f}% " + v_bar + "\n").format(
                          time_table[i][LABEL],
                          time_table[i][VALUE],
                          draw_progress_bar(width=(columns - 19), max=1, value=percent),
                          100 * (percent))

            screen += center_l + h_bar * (columns - 2) + center_r + "\n"

            dst_str[0] = "{:^8}".format("DST->STD" if is_daylight_savings else "STD->DST")
            dst_str[1] = weekday_abbr[next_date.weekday()] + " " + next_date.strftime("%m/%d")
            dst_str[2] = timedelta_strf(time_until_dst, "{days:03} DAYS")
            dst_str[3] = timedelta_strf(time_until_dst, "{hours:02}:{minutes:02}:{seconds:02}")

            unix_int = int(utcnow.timestamp())
            unix_exact = unix_int + u_second
            unix_str = ("UNX: {0}").format(unix_int)

            day_percent_complete = time_table[DAY][VALUE] - int(time_table[DAY][VALUE])
            day_percent_complete_utc = (utcnow.hour * 3600 + utcnow.minute * 60 + utcnow.second + utcnow.microsecond / 1000000) / 86400
            day_percent_complete_cet = (cetnow.hour * 3600 + cetnow.minute * 60 + cetnow.second + cetnow.microsecond / 1000000) / 86400

            solar_str = str(solar_time(now, lon, offset, "SOL: {hour:02}:{minute:02}:{second:02}"))
            lst_str = sidereal_time(now, lon, offset, "LST: {hour:02}:{minute:02}:{second:02}")
            metric_str = metric_strf(day_percent_complete, "MET: {hours:02}:{minutes:02}:{seconds:02}")
            hex_str = hex_strf(day_percent_complete, "HEX: {hours:1X}_{minutes:02X}_{seconds:1X}.{sub:03X}")
            net_str = net_time_strf(day_percent_complete_utc, "NET: {degrees:03.0f}°{minutes:02.0f}'{seconds:02.0f}\"")
            sit_str = "SIT: @{:09.5f}".format(round(day_percent_complete_cet*1000, 5))
            utc_str = "UTC: " + utcnow.strftime("%H:%M:%S")
            
            offset_dbg = timedelta(hours=0, minutes=0)

            for i in range(0, len(time_zone_list), 2):
                time0 = datetime.now(time_zone_list[i][1]) + offset_dbg
                time1 = datetime.now(time_zone_list[i + 1][1]) + offset_dbg

                flash0 = False
                flash1 = False
                flash_dur = .15

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
                    elif  (time1.hour == 17):
                        flash1 = not (u_second < flash_dur)

                time_str0 = time0.strftime("%I:%M %p %b %d").upper()
                time_str1 = time1.strftime("%I:%M %p %b %d").upper()
                screen += v_bar + highlight[flash0] + (" {0:>9}: {1:15} ").format(time_zone_list[i][0], time_str0) + highlight[0] + b_var_single * 2
                screen += highlight[flash1] + (" {0:>9}: {1:15} ").format(time_zone_list[i + 1][0], time_str1) + highlight[0]
                # Each Timezone column is 29 chars, and the bar is 1 = 59
                spacer = " " * (columns - 60)
                screen += spacer + v_bar + "\n"

            screen += center_l + h_bar * (columns - 27) + h_bar_down_connect + h_bar * 13 + h_bar_down_connect + 10 * h_bar + center_r + "\n"

            screen += v_bar + " " + utc_str + " " + b_var_single + " " + unix_str + " " * (columns - len(metric_str + unix_str + b_clockdisp[0]) - 19) + v_bar + b_clockdisp[0] + " " + v_bar + " " + dst_str[0] + " " + v_bar + "\n"
            screen += v_bar + " " + metric_str + " " + b_var_single + " " + sit_str + " " * (columns - len(metric_str + sit_str + b_clockdisp[1]) - 19) + v_bar + b_clockdisp[1] + " " + v_bar + " " + dst_str[1] + " " + v_bar + "\n"
            screen += v_bar + " " + solar_str + " " + b_var_single + " " + hex_str + " " * (columns - len(solar_str + net_str + b_clockdisp[2]) - 19) + v_bar + b_clockdisp[2] + " " + v_bar + " " + dst_str[2] + " " + v_bar + "\n"
            screen += v_bar + " " + lst_str + " " + b_var_single + " " + net_str + " " * (columns - len(lst_str + hex_str + b_clockdisp[3]) - 19) + v_bar + b_clockdisp[3] + " " + v_bar + " " + dst_str[3] + " " + v_bar + "\n"
            screen += corner_ll + h_bar * (columns - 27) + h_bar_up_connect + h_bar * 13 + h_bar_up_connect + h_bar * 10 + corner_lr + "\n"
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

            screen += themes[3] + " "+ ntp_str_left + ((columns - len(ntp_str_left + ntp_str_right)-2) * " ") + ntp_str_right + " "
            screen += themes[1]

            # Switch to the header color theme
            screen += themes[0]

            # Append blank lines to fill out the bottom of the screen
            for i in range(22, rows):
                screen += " " * columns

            loop_time = datetime.now() - start_time + timedelta(hours=5)
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
    t = threading.Thread(target=ntp_daemon)
    t.setDaemon(True)
    t.start()
    main()
    os.system("clear")
    os.system("setterm -cursor on")
    print(colors.reset.all, end="")
