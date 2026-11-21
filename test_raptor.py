import unittest
from raptor import *
from salem_transit_data import *

class ScheduleTests(unittest.TestCase):
    def feed_small(self):
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
    
    def test_small_route_building(self):
        """
        Checks if the route and stops for the small feed are built correctly for RAPTOR
        """
        #print(prep_GTFS(self.feed_small(), '20261111'))
        routes = build_routes(prep_GTFS(self.feed_small(), '20261111'))
        stop_routes = build_stop_routes(routes)

        #B should have two routes that stops at it, ABC and BD
        #Also tracks that the position of B in these routes is consistent
        for (route_id, position) in stop_routes['B']:  
            self.assertEqual(len(routes[route_id]), 2)
            self.assertIn('B', routes[route_id]['stops'])
            self.assertEqual(position, routes[route_id]['stops'].index('B'))

    def test_small_raptor(self):
        """
        Returns the earliest arrival from route A to route D using the small feed.
        """
        routes = build_routes(prep_GTFS(self.feed_small(), '20261111'))
        stop_routes = build_stop_routes(routes)
        earliest_arrival, path = raptor(routes, stop_routes, 'A', 'D', '08:00:00')
        self.assertEqual(earliest_arrival, 30900)
        self.assertEqual(path, {(0, 'A'): None, (1, 'B'): ('R0', 0, 0), (1, 'C'): ('R0', 0, 0), (2, 'D'): ('R1', 0, 0)})

    def feed_missed_connection(self):
        """ 
        Returns a small sample feed creating a missed connection case.
        Contains:
            - One active service date
            - Three trips, three stops
                - Trip first runs A -> B from 08:00 to 08:10; Trip missed runs B -> C from 08:05 to 08:15
                  Trip later runs B -> C from 08:20 to 08:30
        """       
        def stop(trip, seq, name, time):
            return dict(trip_id=trip, stop_sequence=str(seq), stop_id=name, arrival_time=time, departure_time=time)
        return dict(calendar=[], calendar_dates=[dict(service_id='S', date='20261111', exception_type='1')],
                    trips=[dict(trip_id=t, service_id='S') for t in ['first', 'missed', 'later']],
                    transfers=[], frequencies=[], stop_times=[
                        stop('first', 0, 'A', '08:00:00'), stop('first', 1, 'B', '08:10:00'),
                        stop('missed', 0, 'B', '08:05:00'), stop('missed', 1, 'C', '08:15:00'),
                        stop('later', 0, 'B', '08:20:00'), stop('later', 1, 'C', '08:30:00')
                    ])

    def test_missed_connection(self):
            """
            Returns the earliest arrival from route A to route C using the missed connection feed.
            """
            routes = build_routes(prep_GTFS(self.feed_missed_connection(), '20261111'))
            stop_routes = build_stop_routes(routes)
            earliest_arrival, path = raptor(routes, stop_routes, 'A', 'C', '07:55:00')
            self.assertEqual(earliest_arrival, seconds('08:30:00'))

    def feed_complex(self):
         feed = get_GTFS_Feed(url=SALEM_CHERRIOTS_URL, output_path=SALEM_CHERRIOTS_ZIP)
         preped_GTFS = prep_GTFS(feed, "20261112")
         print(preped_GTFS)



if __name__ == '__main__':
    unittest.main(verbosity=2)


