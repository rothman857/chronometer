from typing import List
import pytz
from datetime import datetime
from argparse import ArgumentParser


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("term", nargs="*", default="", type=str)
    args = parser.parse_args()

    cc_map = {
        cc: country
        for cc, country in pytz.country_names.items()
        if " ".join(args.term).lower() in country.lower()
    }

    for country_code, country in cc_map.items():
        print(f"Country: {country}")
        timezones: List[str] = []
        timezones += (tz for tz in pytz.all_timezones if tz.startswith(country_code))
        for code, ctzs in pytz.country_timezones.items():
            if code == country_code:
                timezones += (tz for tz in ctzs)
        for tz in timezones:
            print(f"    {tz}: {datetime.now(pytz.timezone(zone=tz)):%z}")
        print()
