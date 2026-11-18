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
    - Departure time given in formatio hh:mm:ss
    """
    departure_time = seconds(departure_time)

    #T[k][p]: Earliest arrival time at stop p, using at most k trips
    tau = defaultdict(lambda: defaultdict(lambda: math.inf))

    #T*[p]: Overall earliest arrival time at stop p across all rounds
    tau_star = defaultdict(lambda: math.inf)

    #Init round one with the orgin stop
    #T[0][origin] = departure_time 
    #T*[origin] = dept_time
    tau[0][source] = departure_time
    tau_star[source] = departure_time

    marked_stops = {source}

    k = 0
    while marked_stops:
        k+=1
        improved = False

        for stop, times in tau[k-1].items():
            tau[k][stop] = times

        Q = {}

        for stop in marked_stops:
            print(f"stop: {stop}")
            for route_id in stop_routes.get(stop, []):
                print(f"stop_route: {stop_routes}")
                stop_idx = routes[route_id].index(stop)
                print(stop_idx)
        marked_stops = False




# 6 foreach k ← 1, 2, . . . do
# // Accumulate routes serving marked
# stops from previous round
# 7 Clear Q
# 8 foreach marked stop p do
# 9 foreach route r serving p do
# 10 if (r, p′) ∈ Q for some stop p′ then
# 11 Substitute (r, p′) by (r, p) in Q if p
# comes before p′ in r
# 12 else
# 13 Add (r, p) to Q
# 14 unmark p
# // Traverse each route
# 15 foreach route (r, p) ∈ Q do
# 16 t ← ⊥ // the current trip
# 17 foreach stop pi of r beginning with p do
# // Can the label be improved in
# this round? Includes local
# and target pruning
# 18 if t 6 = ⊥ and
# arr(t, pi) < min{τ ∗(pi), τ ∗(pt)} then
# 19 τk(pi) ← τarr(t, pi)
# 20 τ ∗(pi) ← τarr(t, pi)
# 21 mark pi
# // Can we catch an earlier trip
# at pi?
# 22 if τk−1(pi) ≤ τdep(t, pi) then
# 23 t ← et(r, pi)
# // Look at foot-paths
# 24 foreach marked stop p do
# 25 foreach foot-path (p, p′) ∈ F do
# 26 τk(p′) ← min{τk(p′), τk(p) + `(p, p′)}
# 27 mark p′
# // Stopping criterion
# 28 if no stops are marked then
# 29 stop