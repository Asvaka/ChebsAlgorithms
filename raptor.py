"""
Round bAsed Public Transit Optimized Router
    - Determines the earliest possible arrival time between an origin and destination,
    given a specified departure time
"""
from salem_transit_data import *
from collections import defaultdict
import math


#Take in a schedule from prep_GTFS, schedule = prep_GTFS(feed, date)
def build_routes(schedule: dict[str, list[dict]]) -> dict[str, dict[str, list]]:
    """Groups trips that go to the same ordered stops into routes, and sorts each trip by departure time."""
    #For every trip, read the stop_ids in order and treat that sequence as the trip’s pattern
    patterns = defaultdict(list)
    for trip_id, rows in schedule.items():
        key = tuple(row['stop_id'] for row in rows)
        patterns[key].append(rows)

    routes = {}
    for number_id, (key, trips) in enumerate(patterns.items()):
        #Sorts routes by their departure time
        trips.sort(key=lambda rows: rows[0]['departure_sec'])
        for earlier, later in zip(trips, trips[1:]):
            #Checks that theres no overlap between departure times
            if any(b['arrival_sec'] < a['arrival_sec'] for a, b in zip(earlier, later)):
                raise ValueError('Trips on the same route overtake each other.')
        routes[f'R{number_id}'] = {'stops': list(key), 'trips': trips}

    return routes

def build_stop_routes(routes: dict[str, dict[str,list]]) -> dict[str, list[tuple[str, int]]]:
    """Builds a map of stop_id to the routes that visit that stop and their stop positions."""
    stop_routes = defaultdict(list)

    for route_id, route in routes.items():
        for index, stop in enumerate(route['stops']):
            stop_routes[stop].append((route_id, index)) 
    return stop_routes
    
#Input: Source and target stops ps, pt and departure time T.  
def raptor(routes, stop_routes, source, target, departure_time):
    """
    Given a source stop ps, a target stop pt, and a departure time T, it asks for a journey that 
    departs ps no earlier than T, and arrives at pt as early as possible. [RAPTOR]
    - Departure time given in format hh:mm:ss
    """
    departure_time = seconds(departure_time)

    #T[k][p]: Earliest arrival time at stop p, using k rounds of trips
    tau = defaultdict(lambda: defaultdict(lambda: math.inf))

    #T*[p]: Overall earliest arrival time at stop p across all rounds
    tau_star = defaultdict(lambda: math.inf)

    #Init round one with the origin stop
    #T[0][origin] = departure_time 
    #T*[origin] = dept_time
    tau[0][source] = departure_time
    tau_star[source] = departure_time



    #(round k, stop):(route_id, trip index, boarding position)
    parent = {}
    parent[(0, source)] = None

    marked_stops = set()
    marked_stops.add(source)

    k = 0
    while marked_stops:
        k+=1
        boarding_pos = 0

        for stop, times in tau[k-1].items():
            tau[k][stop] = times
        Q = {}

        #Accumulate routes serving marked
        for stop in marked_stops:
            for route_id, pos in stop_routes.get(stop, []):
                if route_id not in Q or Q[route_id] > pos:
                    Q[route_id] = pos

        marked_stops = set()
        #Traverse each route
        for route_id, pos in Q.items():
            t = None
            boarding_pos = 0

            for num, stop_pi in enumerate(routes[route_id]['stops'][pos:], pos):
                #Can the label be improved in this round? Includes local nd target pruning
                if t is not None:
                    arr_time_at_pi = routes[route_id]['trips'][t][num]['arrival_sec']
                    min_tau_taustar = min(tau_star[stop_pi],tau_star[target])
                    if arr_time_at_pi < min_tau_taustar:
                        parent[(k,stop_pi)] = (route_id, t, boarding_pos)
                        tau[k][stop_pi] = arr_time_at_pi
                        tau_star[stop_pi] = arr_time_at_pi
                        marked_stops.add(stop_pi)

                # Can we catch an earlier trip at pi?
                if t is None or (t is not None and tau[k-1][stop_pi] <= routes[route_id]['trips'][t][num]['departure_sec']):
                    for trip_index, trip in enumerate(routes[route_id]['trips']):
                        trip_dep = trip[num]['departure_sec']
                        if trip_dep >= tau[k-1][stop_pi]:
                            t = trip_index
                            boarding_pos=num
                            break

    
    #print(f"Earliest arrival from starting stop {source} to departing stop {target} is {hhmmss(tau_star[target])}")
    return tau_star[target], parent


def feed_small():
        """
        Returns a small sample feed. 
        Contains:
            - One active service date
            - Two trips and five stops:
                - Trip abc runs A -> B -> C from 08:00 to 08:20; trip bd runs B -> D from 08:25 to 08:35.
        """
        def stop(trip, seq, name, time):
                    return dict(trip_id=trip, stop_sequence=str(seq), stop_id=name, arrival_time=time, departure_time=time)

        return dict(calendar=[], calendar_dates=[dict(service_id='S', date='20261111', exception_type='1')],
                    trips=[dict(trip_id='abc', service_id='S'), dict(trip_id='bd', service_id='S')],
                    transfers=[], frequencies=[], stop_times=[
                        stop('abc', 0, 'A', '08:00:00'), stop('abc', 1, 'B', '08:10:00'),
                        stop('abc', 2, 'C', '08:20:00'), stop('bd', 0, 'B', '08:25:00'),
                        stop('bd', 1, 'D', '08:35:00')
                    ])

feed = feed_small()

def test_small_raptor():
        """
        Returns the earliest arrival from route A to route D using the small feed.
        """
        routes = build_routes(prep_GTFS(feed_small(), '20261111'))
        stop_routes = build_stop_routes(routes)
        earliest_arrival, path = raptor(routes, stop_routes, 'A', 'D', '08:00:00')
        print(earliest_arrival)

test_small_raptor()

