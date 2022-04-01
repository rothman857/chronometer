from chrono import *
from datetime import datetime

test_date = datetime(day=1, month=4, year=2022)
longitude = 84.36611111

class TestChrono:
    def test_julian_date(self):
        assert julian_date(date=test_date) == 2459670.5

    def test_julian_to_greg(self):
        assert jul_to_greg(julian_date(test_date)) == test_date