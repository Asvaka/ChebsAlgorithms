"""Reproduces a preliminary Dijkstra scaling experiment on the bundled GTFS feed."""

import argparse
import csv
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path

from salem_transit_data import read_feed, prep_GTFS, TRIP_DATE, SALEM_CHERRIOTS_ZIP
from transit_dijkstra import build_graph, earliest_arrival

def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feed', type=Path, default=Path(__file__).with_name(SALEM_CHERRIOTS_ZIP))
    parser.add_argument('--date', default=TRIP_DATE)
    parser.add_argument('--sizes', type=int, nargs='+', default=[10, 25, 50, 100, 200])
    parser.add_argument('--repetitions', type=int, default=10)
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    if args.repetitions < 2 or any (n < 1 for n in args.sizes):
        parser.error('Use at least two repetitions and positive trip counts please.')

    schedule = prep_GTFS(read_feed(args.feed), args.date)

    eligible = [t for t in sorted(schedule) if len(schedule[t]) > 1
                and schedule[t][0]['stop_id'] != schedule[t][-1]['stop_id']
                and (schedule[t][0].get('pickup_type', '') or '0') == '0'
                and (schedule[t][-1].get('drop_off_type', '') or '0') == '0']
    if not eligible:
        parser.error('No suitable reference trip in the selected service day')
    
    reference = eligible[0]

    trip_order = [reference] + [t for t in sorted(schedule) if t != reference]

    sizes = sorted({min(n, len(trip_order)) for n in args.sizes})
    if len(sizes) < 2:
        parser.error('At least two distinct input sizes are needed')

    first, last = schedule[reference][0], schedule[reference][-1]
    start, destination, departure = first['stop_id'], last['stop_id'], first['departure_sec']
    raw, summary = [], []

    for size in sizes:
        subset = {t: schedule[t] for t in trip_order[:size]}
        before = time.perf_counter()
        graph, events = build_graph(subset)
        build_ms = (time.perf_counter() - before) * 1000
        nodes, edges = len(graph), sum(len(n) for n in graph.values())

        earliest_arrival(graph, events, start, destination, departure)

        samples = []
        for repetition in range(1, args.repetitions + 1):
            before = time.perf_counter()
            arrival, path = earliest_arrival(graph, events, start, destination, departure)
            elapsed = (time.perf_counter() - before) * 1000
            if not path or arrival > last['arrival_sec']:
                raise RuntimeError('Reference trip should provide a reachable upper bound')
            samples.append(elapsed)
            raw.append(dict(trips=size, nodes=nodes, edges=edges, repetition=repetition,
                            query_ms=elapsed, arrival_sec=arrival))
            
        summary.append(dict(trips=size, nodes=nodes, edges=edges, build_ms=build_ms,
                            mean_query_ms=statistics.mean(samples),
                            stdev_query_ms=statistics.stdev(samples)))

        print(f'{size} trips, {nodes} nodes: {statistics.mean(samples):.3f} ms')

        args.output.mkdir(parents=True, exist_ok=True)

    for name, rows in [('raw.csv', raw), ('summary.csv', summary)]:
        with (args.output / name).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    metadata = dict(feed_sha256=hashlib.sha256(args.feed.read_bytes()).hexdigest(),
                    date=args.date, python=platform.python_version(), platform=platform.platform(),
                    repetitions=args.repetitions, reference_trip=reference, start=start,
                    destination=destination, departure_sec=departure, trip_order=trip_order[:max(sizes)])
    (args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize = (8, 5), layout = 'constrained')

    ax.errorbar([r['nodes'] for r in summary], [r['mean_query_ms'] for r in summary],
                yerr=[r['stdev_query_ms'] for r in summary], fmt='o-', capsize=4,
                color="#ff9b10", linewidth=2)
    ax.set(xlabel='Input Size (Time-Expanded Graph Nodes)', ylabel='Mean Query Time (ms)',
           title=f'Preliminary Dijkstra Query Performance\n{args.repetitions} Runs per Size; Error Bars: Sample Standard Deviation')
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.25)

    fig.savefig(args.output / 'preliminary_plot.png', dpi=180)
    plt.close(fig)
    print(f'Results saved in {args.output}')

if __name__ == '__main__':
    main()