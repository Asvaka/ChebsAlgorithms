import unittest
from transit_dijkstra import build_graph, earliest_arrival
from salem_transit_data import prep_GTFS, seconds

class ScheduleTests(unittest.TestCase):
    def feed(self):
        def stop(trip, seq, name, time):
            return dict(trip_id=trip, stop_sequence=str(seq), stop_id=name, arrival_time=time, departure_time=time)
        return dict(calendar=[], calendar_dates=[dict(service_id='S', date='20261111', exception_type='1')],
                    trips=[dict(trip_id=t, service_id='S') for t in ['first', 'missed', 'later']],
                    transfers=[], frequencies=[], stop_times=[
                        stop('first', 0, 'A', '08:00:00'), stop('first', 1, 'B', '08:10:00'),
                        stop('missed', 0, 'B', '08:05:00'), stop('missed', 1, 'C', '08:15:00'),
                        stop('later', 0, 'B', '08:20:00'), stop('later', 1, 'C', '08:30:00')
                    ])

    def test_wait_and_missed_transfer(self):
        graph, events = build_graph(prep_GTFS(self.feed(), '20261111'))
        arrival, path = earliest_arrival(graph, events, 'A', 'C', seconds('07:55:00'))

        self.assertEqual(arrival, seconds('08:30:00'))
        self.assertTrue(any(node[0] == 'departure' and node[1] == 'later' for node in path))
        self.assertFalse(any(node[0] == 'departure' and node[1] == 'missed' for node in path))

    def test_departure_after_last_bus(self):
        graph, events = build_graph(prep_GTFS(self.feed(), '20261111'))
        self.assertEqual(earliest_arrival(graph, events, 'A', 'C', seconds('08:01:00')),
                         (float('inf'), []))

    def test_no_service(self):
        graph, events = build_graph(prep_GTFS(self.feed(), '20261112'))
        self.assertEqual(graph, {})

    def test_after_midnight(self):
        self.assertEqual(seconds('25:10:00'), 90600)

    def test_no_pickup(self):
        feed = self.feed()
        feed['stop_times'][0]['pickup_type'] = '1'

        graph, events = build_graph(prep_GTFS(feed, '20261111'))
        self.assertEqual(earliest_arrival(graph, events, 'A', 'C', 0)[0], float('inf'))

if __name__ == '__main__':
    unittest.main()