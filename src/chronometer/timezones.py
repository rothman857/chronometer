import pytz
from datetime import datetime
from argparse import ArgumentParser


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('term', nargs='?', default='', type=str)
    args = parser.parse_args()

    timezones = [tz for tz in pytz.all_timezones if args.term.lower() in tz.lower()]
    for tz in timezones:
        print(f'{tz}: {datetime.now(pytz.timezone(zone=tz)):%z}')
