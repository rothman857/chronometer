from cal import *
from timeutil import *
from datetime import datetime
from chrono import *

test_date = datetime(day=1, month=4, year=2022)
longitude = 84.36611111

class TestChrono:
    def test_julian_date(self):
        assert julian_date(date=test_date) == 2459670.5

    def test_julian_to_greg(self):
        assert jul_to_greg(julian_date(test_date)) == test_date


    def test_float_fixed(self):
        assert float_fixed(12.12345, 5) == "12.12"
        assert float_fixed(12.12345, 4) == "12.1"
        assert float_fixed(12.12345678, 8) == "12.12346"

        assert float_fixed(12.12345, 5, True) == "+12.1"
        assert float_fixed(12.12345678, 8, True) == "+12.1235"
        assert float_fixed(12.1, 8, True) == "+12.1235"


