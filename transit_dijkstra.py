"""Time-expanded Dijkstra for one GFTS service day (using PSL)."""

import argparse
from collections import defaultdict
from pathlib import Path

from dijkstra import dijkstra
from salem_transit_data import SALEM_CHERRIOTS_ZIP, TRIP_DATE, prep_GTFS, read_feed, seconds

def clock(value):
    value = int(value)
    return f'{value // 3600:02}:{value // 60 % 60:02}:{value % 60:02}'

def build_graph(schedule):
    """Return graph and platform events indexed by stop. Vehicle arrival/departure nodes retain trip identity.
    Input is the sorted schedule returned by salem_transit_data.prep_GTFS()."""

    graph = {}
    events = defaultdict(set)

    def edge(start, end, weight):
        if weight < 0:
            raise ValueError('GTFS events are not in chronological order.')

        graph.setdefault(start, {})[end] = weight
        graph.setdefault(end, {})

    for trip, rows in schedule.items():
        previous = None
        for row in rows:
            arrival, departure = row['arrival_sec'], row['departure_sec']
            stop, sequence = row['stop_id'], row['stop_sequence']
            a = ('arrival', trip, sequence, stop, arrival)
            d = ('departure', trip, sequence, stop, departure)
            edge(a, d, departure - arrival)

            if previous is not None:
                edge(previous, a, arrival - previous[-1])

            previous = d
            for field, event, time, boarding in (
                ('pickup_type', d, departure, True),
                ('drop_off_type', a, arrival, False),
            ):
                kind = row.get(field, '') or '0'
                if kind in ('2', '3'):
                    raise ValueError('On-demand pickup/drop-pff requires additional handling.')
                if kind == '1':
                    continue

                platform = ('platform', stop, time)
                events[stop].add(time)
                edge(platform, event, 0) if boarding else edge(event, platform, 0)

    for stop, times in events.items():
        ordered = sorted(times)
        for earlier, later in zip(ordered, ordered[1:]):
            edge(('platform', stop, earlier), ('platform', stop, later), later - earlier)

    return graph, events

def earliest_arrival(graph, events, start, destination, departure):
    """Return (absolute arrival seconds, event path). Query nodes are added to a shallow copy; the preprocessed
    graph is reusable."""

    if departure < 0:
        raise ValueError('Departure must be nonnegative.')

    if start == destination:
        return departure, []

    query = dict(graph)
    source, target = ('source',), ('target',)
    eligible = [time for time in events.get(start, ()) if time >= departure]
    query[source] = {}
    query[target] = {}

    if eligible:
        first = min(eligible)
        query[source][('platform', start, first)] = first - departure

    for time in events.get(destination, ()):
        node = ('platform', destination, time)
        query[node] = dict(query.get(node, {}))
        query[node][target] = 0

    duration, path = dijkstra(query, source, target)

    return departure + duration, path

def main():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('start', help='Origin stop_id')
    parser.add_argument('destination', help='Destination stop_id')
    parser.add_argument('--date', default=TRIP_DATE, help='GTFS service day YYYYMMDD')
    parser.add_argument('--departure', required=True)
    parser.add_argument('--feed', type=Path, default=Path(__file__).with_name(SALEM_CHERRIOTS_ZIP))
    args = parser.parse_args()

    try:
        feed = read_feed(args.feed)
        stops = {r['stop_id'] for r in feed['stops']}
        if args.start not in stops or args.destination not in stops:
            raise ValueError('Start and destination must be GTFS stop IDs.')

        schedule = prep_GTFS(feed, args.date)
        graph, events = build_graph(schedule)
        arrival, path = earliest_arrival(graph, events, args.start, args.destination, seconds(args.departure))

    except ValueError as error:
        parser.error(str(error))

    if arrival == float('inf'):
        print('There was no journey found for this service day.')
        return
    
    print(f'Earliest arrival: {clock(arrival)}')
    for node in path:
        if node[0] in ('arrival', 'departure'):
            kind, trip, _, stop, time = node
            print(f'{clock(time)} {kind}: stop{stop}, trip{trip}')

if __name__ == "__main__":
    main()
    