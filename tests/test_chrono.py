from datetime import datetime, timedelta, time
import pytz
from chronometer.tools import cal, abbr, timeutil, clock


def list_pax_dates(start_year: int, duration: int):
    pax_dates = []
    for year in range(start_year, start_year + duration):
        leap_year = cal.is_pax_leap_year(year)
        days_in_year = (28 * 13) + 7 if leap_year else (28 * 13)
        for day in range(days_in_year):
            weekday = day % 7
            month = day // 28
            d = day % 28
            if leap_year:
                if 335 < day < 343:
                    month = 12
                    d = day - 336
                elif day >= 343:
                    month = 13
                    d = day - 343
            else:
                if month == 12:
                    month = 13
            pax_dates.append(
                f"{abbr.weekday[weekday]} {abbr.Month.pax[month]} {d+1:02}"
            )
    return pax_dates


def ifc_dates(start, dur):
    ifc_dates = []
    for year in range(start, start + dur):
        for month in abbr.Month.ifc:
            for day in range(1, 29):
                ifc_dates.append(f"{abbr.weekday[(day - 1) % 7]} {month} {day:02}")
                if day == 28 and month == "JUN" and timeutil.is_leap_year(year):
                    ifc_dates.append("*LEAP DAY*")
        ifc_dates.append("*YEAR DAY*")
    return ifc_dates


def twc_dates(start, dur):
    i = 0
    twc_dates = []
    for year in range(start, start + dur):
        for m, month in enumerate(abbr.Month.twc):
            days_in_month = [31, 30, 30][m % 3]
            for day in range(1, days_in_month + 1):
                twc_dates.append(f"{abbr.weekday[i % 7]} {month} {day:02}")
                if day == 30 and month == "DEC":
                    twc_dates.append("*YEAR DAY*")
                if day == 30 and month == "JUN" and timeutil.is_leap_year(year):
                    twc_dates.append("*LEAP DAY*")
                i += 1
    return twc_dates


class TestCalendars:
    def test_pax(self):
        start_date = datetime(year=1928, month=1, day=1)
        for pax_date_str in list_pax_dates(1928, 500):
            assert pax_date_str == cal.pax_date(start_date)[1:]
            start_date += timedelta(days=1)

    def test_ifc(self):
        start_date = datetime(year=2000, month=1, day=1)
        for ifc_date_str in ifc_dates(2000, 500):
            assert ifc_date_str == cal.int_fix_date(start_date)
            start_date += timedelta(days=1)

    def test_twc(self):
        start_date = datetime(year=2000, month=1, day=1)
        for twc_date_str in twc_dates(2000, 500):
            assert twc_date_str == cal.twc_date(start_date)
            start_date += timedelta(days=1)

    def test_julian_data(self):
        assert 2451544.5 == cal.julian_date(date=datetime(year=2000, month=1, day=1))
        assert 2816787.5 == cal.julian_date(date=datetime(year=3000, month=1, day=1))


class TestClocks:
    def test_metric_time(self):
        assert "00:00:00" == clock.metric_time(time())
        assert "02:50:00" == clock.metric_time(time(hour=6))
        assert "05:00:00" == clock.metric_time(time(hour=12))
        assert "07:50:00" == clock.metric_time(time(hour=18))

    def test_hex_time(self):
        assert "0_00_0.000" == clock.hex_time(time())
        assert "4_00_0.000" == clock.hex_time(time(hour=6))
        assert "8_00_0.000" == clock.hex_time(time(hour=12))
        assert "C_00_0.000" == clock.hex_time(time(hour=18))

    def test_unix_time(self):
        assert "946702800" == clock.unix_time(datetime(year=2000, month=1, day=1))
        assert "1234567890" == clock.unix_time(
            datetime(year=2009, month=2, day=13, hour=18, minute=31, second=30)
        )

    def test_sit_time(self):
        assert "@000.00000" == clock.sit_time(
            datetime(
                year=2000, month=1, day=1, hour=0, tzinfo=pytz.timezone("Etc/GMT-1")
            )
        )


class TestUtils:
    def test_day_of_week(self):
        assert 1 == timeutil.day_of_year(datetime(month=1, day=1, year=2000))
        assert 365 == timeutil.day_of_year(datetime(month=12, day=31, year=1999))
        assert 366 == timeutil.day_of_year(datetime(month=12, day=31, year=2000))
