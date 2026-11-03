# Cherriots Bus-Route Trip Planner

## Setup

Install Python 3.10 or newer. This is a Python project. The planner and tests use only the Python standard library.

Keep these files in the same directory:

- 'transit_dijkstra.py' (graph construction and command-line planner)
- 'dijkstra.py' (shortest-path search)
- 'test_transit_dijkstra.py' (automated tests)
- 'salem_cherriots_GTFS.zip' (bundled schedule data)

## Running the Planner

'''
python3 transit_dijkstra.py 230 1932 --date 20261111 --departure 05:55:00
'''

With the bundled dataset entered into the termal, the expected first output line is:

'''
Earliest arrival: 06:14:00
'''

The remaining lines show vehicle arrivals and departures with stop IDs and trip
IDs. This example starts at stop 230 and ends at stop 1932. Change the stop IDs,
date, and departure time to try other journeys. Stop IDs can be found in
`stops.txt` inside the ZIP. Times such as `25:00:00` mean after midnight on the
selected service day.

## Run the Tests

Run the test file directly in the terminal:

'''
python3 test_transit_dijkstra.py
'''

Expected Result: Five tests pass, with an "OK." These use a small artificial
schedule to check waiting and missed connections, departures after the last bus,
dates without service, times after midnight, and prohibited boarding. The real
feed query above is a separate integration check.

## Preliminary Plot

//

## Implementation

'dijkstra.py' is the general binary-heap shortest-path search, returning total
weight and the reconstructed node path.

'salem_transit_data.py' owns feed loading and schedule preparation. 'read_feed()'
reads the bundled ZIP; 'prep_GTFS(feed, date)' selects active trips using calendar
rules and date exceptions, sorts their stops, and preserves scheduled times,
trip IDs, terminal stops, and boarding/alighting restrictions. It returns a
mapping of trip IDs to stop records with 'arrival_sec' and 'departure_sec'.
'get_GTFS_Feed()' is an optional explicit download helper.

'transit_dijkstra.py' calls those data functions and passes the prepared schedule
to 'build_graph(schedule)', which builds a directed time-expanded graph. Vehicle arrival and departure nodes preserve trip identity;
platform nodes connect boarding, alighting, and chronological waiting events.
A query source connects to the first platform event at or after departure, and
destination platform events connect to a query target. All weights are elapsed
seconds, so the shortest path gives the earliest arrival.
