
# 1st Validate GTFS feed zip file for Salem, Oregon with Canonical GTFS Validator [https://gtfs-validator.mobilitydata.org/] 

import gtfs_kit as gk
import geopandas as gpd
import pandas as pd
import requests, os

SALEM_CHERRIOTS_URL = "https://cherriots.rideralerts.com/InfoPoint/gtfs-zip.ashx"
SALEM_CHERRIOTS_ZIP = "salem_cherriots_GTFS.zip"
TRIP_DATE = "20261111" 

def get_GTFS_Feed(url, output_path) -> gk.Feed:
    path = os.path.dirname(__file__)
    filename = os.path.join(path, output_path)

    req = requests.get(url)
    with open(filename, "wb") as f:
        f.write(req.content)

    feed = gk.read_feed(filename, dist_units = "m")
    return feed

#NEED TO GET STOP-STOP TRAVEL TIME AND DIST
def get_GTFS_ADJ_list(feed:gk.Feed) -> pd.DataFrame:

    # Limit to a single date
    active_trips = feed.get_trips(date=TRIP_DATE)["trip_id"]

    #Filter stop times to only include active trips
    stop_times = feed.stop_times[feed.stop_times["trip_id"].isin(active_trips)]
    stop_times = stop_times[["trip_id", "stop_sequence", "stop_id", "arrival_time", "departure_time"]]

    #Sort stop times bt trip_id and sequence
    stop_times = stop_times.sort_values(by=["trip_id", "stop_sequence"])

    #convert to seconds
    stop_times["arrival_sec"] = list(map(gk.helpers.timestr_to_seconds, stop_times['arrival_time']))
    stop_times["departure_sec"] = list(map(gk.helpers.timestr_to_seconds, stop_times['departure_time']))
    print(stop_times.head(10))



def adj_list(s):
    pass



feed = get_GTFS_Feed(SALEM_CHERRIOTS_URL, SALEM_CHERRIOTS_ZIP)
get_GTFS_ADJ_list(feed)
