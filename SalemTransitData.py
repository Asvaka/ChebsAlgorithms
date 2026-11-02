
# 1st Validate GTFS feed zip file for Salem, Oregon with Canonical GTFS Validator [https://gtfs-validator.mobilitydata.org/] 

import gtfs_kit as gk
import geopandas as gpd
import pandas as pd
import requests, os

SALEM_CHERRIOTS_URL = "https://cherriots.rideralerts.com/InfoPoint/gtfs-zip.ashx"
SALEM_CHERRIOTS_ZIP = "salem_cherriots_GTFS.zip"
TRIP_DATE = "20261117" 

def get_GTFS_Feed(url, output_path) -> gk.Feed:
    path = os.path.dirname(__file__)
    filename = os.path.join(path, output_path)

    req = requests.get(url)
    with open(filename, "wb") as f:
        f.write(req.content)

    feed = gk.read_feed(filename, dist_units = "m")
    return feed

#NEED TO GET STOP-STOP TRAVEL TIME AND DIST
def prep_GTFS(feed:gk.Feed) -> pd.DataFrame:
    #Limit to a single date because its easier to analyze trips for just one day
    #We could expand later?
    active_trips = feed.get_trips(date=TRIP_DATE)["trip_id"]

    #Filter stop times to only include active trips
    stop_times = feed.stop_times[feed.stop_times["trip_id"].isin(active_trips)]
    stop_times = stop_times[["trip_id", "stop_sequence", "stop_id", "arrival_time", "departure_time"]]

    #Sort stop times bt trip_id and sequence, this makes sure the same trip is
    stop_times = stop_times.sort_values(by=["trip_id", "stop_sequence"])

    #convert to seconds
    stop_times["arrival_sec"] = list(map(gk.helpers.timestr_to_seconds, stop_times['arrival_time']))
    stop_times["departure_sec"] = list(map(gk.helpers.timestr_to_seconds, stop_times['departure_time']))

    #Shift stop times to get the next stop for each trip, 
    #Group by trip id bc it makes sure we only look at the next stop for that trip
    stop_times["next_stop_id"] = stop_times.groupby("trip_id")["stop_id"].shift(-1)
    stop_times["next_arrival_sec"] = stop_times.groupby("trip_id")["arrival_sec"].shift(-1)

    #Calc total travel time between current stop and next stop for each trip
    stop_times["travel_time_sec"] = stop_times["next_arrival_sec"] - stop_times["departure_sec"]

    #Drop last stop for each trip because it has no next stop and gives NAN
    stop_times = stop_times.dropna(subset=["next_stop_id"])

    return stop_times[["trip_id", "stop_id", "next_stop_id", "travel_time_sec"]]


def adj_list(df: pd.DataFrame) -> dict:
    adj = {}
    for _, row in df.iterrows():
        stop_id = row["stop_id"]
        next_stop_id = row["next_stop_id"]
        travel_time_sec = row["travel_time_sec"]
        if stop_id not in adj:
            adj[stop_id] = {}
        adj[stop_id][next_stop_id] = travel_time_sec
    return adj


feed = get_GTFS_Feed(SALEM_CHERRIOTS_URL, SALEM_CHERRIOTS_ZIP)
stop_times_df = prep_GTFS(feed)
adjacency_list = adj_list(stop_times_df)
print(adjacency_list)

