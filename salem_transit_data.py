
# 1st Validate GTFS feed zip file for Salem, Oregon with Canonical GTFS Validator [https://gtfs-validator.mobilitydata.org/]
"""Load Cherriots GTFS data and prepare schedules for routing algorithms. Feed tables are lists of dictionaries where preparation preserves
the schedule instead of collapsing it into static stop-to-stop travel durations. Uses only PSL."""

import csv
import io
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

SALEM_CHERRIOTS_URL = "https://cherriots.rideralerts.com/InfoPoint/gtfs-zip.ashx"
SALEM_CHERRIOTS_ZIP = "salem_cherriots_GTFS.zip"
TRIP_DATE = "20261111" 

def get_GTFS_Feed(url=SALEM_CHERRIOTS_URL, output_path=SALEM_CHERRIOTS_ZIP):
    """Explicitly downloads a feed, saves it, and reads its tables."""

    filename = Path(output_path)

    if not filename.is_absolute():
        filename = Path(__file__).parent / filename

    with urlopen(url, timeout = 60) as response:
        payload = response.read()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise ValueError('Downloaded GTFS ZIP failed validation.')

    filename.write_bytes(payload)
    return read_feed(filename)

def seconds(value):

    hour, minute, second = map(int, value.split(':'))
    if hour < 0 or not 0 <= minute < 60 or not 0 <= second < 60:
        raise ValueError(f'Invalid GTFS time: {value}')

    return hour * 3600 + minute * 60 + second

def read_feed(path):
    with zipfile.ZipFile(path) as archive:
        def table(name):
            if name not in archive.namelist():
                return []
            return list(csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig'))))
        return {name: table(name + '.txt') for name in
                ('calendar', 'calendar_dates', 'trips', 'stop_times', 'stops', 'transfers', 'frequencies')}

def active_services(feed, date):

    day = datetime.strptime(date, '%Y%m%d')
    weekday = ('monday', 'tuesday', 'wednesday', 'thursday','friday', 'saturday', 'sunday')[day.weekday()]

    active = {row['service_id'] for row in feed['calendar']
              if row['start_date'] <= date <= row['end_date'] and row[weekday] == '1'}

    for row in feed['calendar_dates']:
        if row['date'] == date:
            if row['exception_type'] == '1':
                active.add(row['service_id'])
            elif row['exception_type'] == '2':
                active.discard(row['service_id'])

    return active

def prep_GTFS(feed, date=TRIP_DATE):
    """Select active trips and preserve all scheduled stops including terminals. Returns {trip_id: [stop records]} which is sorted by stop_sequence.
    Each record keeps its original GTFS fields as well as arrival_sec and departure_sec. Shared schedule rep. could be used for RAPTOR implementation."""

    if feed['transfers'] or feed['frequencies']:
        raise ValueError('The current state only supports scheduled trips and same-stop transfers for now.')

    services = active_services(feed, date)
    trips = {row['trip_id'] for row in feed['trips'] if row['service_id'] in services}
    prepared = defaultdict(list)

    for row in feed['stop_times']:
        if row['trip_id'] not in trips:
            continue

        record = dict(row)
        record['arrival_sec'] = seconds(row['arrival_time'])
        record['departure_sec'] = seconds(row['departure_time'])
        prepared[row['trip_id']].append(record)

    for rows in prepared.values():
        rows.sort(key=lambda row: int(row['stop_sequence']))
        previous_departure = None

        for row in rows:
            arrival, departure = row['arrival_sec'], row['departure_sec']
            if departure < arrival or (previous_departure is not None and arrival < previous_departure):
                raise ValueError('GTFS events are not in chronological order.')
            previous_departure = departure

    return dict(prepared)
