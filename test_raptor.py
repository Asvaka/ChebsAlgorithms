import unittest
from raptor import build_routes, build_stop_routes, raptor
from salem_transit_data import prep_GTFS, seconds

class ScheduleTests(unittest.TestCase):
    def feed_small(self):
        def stop(trip, seq, name, time):
                    return dict(trip_id=trip, stop_sequence=str(seq), stop_id=name, arrival_time=time, departure_time=time)
        
        return dict(calendar=[], calendar_dates=[dict(service_id='S', date='20261111', exception_type='1')],
                    trips=[dict(trip_id='abc', service_id='S'), dict(trip_id='bd', service_id='S')],
                    transfers=[], frequencies=[], stop_times=[
                        stop('abc', 0, 'A', '08:00:00'), stop('abc', 1, 'B', '08:10:00'),
                        stop('abc', 2, 'C', '08:20:00'), stop('bd', 0, 'B', '08:25:00'),
                        stop('bd', 1, 'D', '08:35:00')
                    ])
    
    def test_small_route_building(self):
        """
        Checks if the route and stops for the small feed are built correctly for RAPTOR
        """
        print("Running test_small_route_building...")
        routes = build_routes(prep_GTFS(self.feed_small(), '20261111'))
        stop_routes = build_stop_routes(routes)

        #B should have two routes that stops at it, ABC and BD
        #Also tracks that the position of B in these routes is consistent
        for (route_id, position) in stop_routes['B']:  
            self.assertEqual(len(routes[route_id]), 2)
            self.assertIn('B', routes[route_id]['stops'])
            self.assertEqual(position, routes[route_id]['stops'].index('B'))


if __name__ == '__main__':
    unittest.main()


