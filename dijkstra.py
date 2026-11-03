"""Shortest paths on a directed graph with nonnegative, finite edge weights."""

import heapq
import math
from itertools import count

def dijkstra(graph, start, destination):
    """Return (total_seconds, stop_path). Graphs maps each stop to {neighbor: travel_time_seconds}. Uknown stops and invalid weights raise
    ValueError."""

    nodes = set(graph)
    for neighbors in graph.values():
        nodes.update(neighbors)
        for weight in neighbors.values():
            if not math.isfinite(weight) or weight < 0:
                raise ValueError('Edge weights must be finite and nonnegative.')
    if start not in nodes or destination not in nodes:
        raise ValueError('Start and destination must be stops in the graph.')

    distances = {start: 0}
    previous = {}

    # A counter breaks ties without comparing stop IDs.
    order = count()
    queue = [(0, next(order), start)]
    while queue:
        distance, _, stop = heapq.heappop(queue)
        if distance != distances[stop]:
            continue
        if stop == destination:
            path = [stop]
            while stop != start:
                stop = previous[stop]
                path.append(stop)

            return distance, path[::-1]

        for neighbor, weight in graph.get(stop, {}).items():
            candidate = distance + weight
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = stop
                heapq.heappush(queue, (candidate, next(order), neighbor))

    return math.inf, []
