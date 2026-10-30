
# 1st Validate GTFS feed zip file for Salem, Oregon with Canonical GTFS Validator [https://gtfs-validator.mobilitydata.org/] 

import gtfs_kit as gk
import geopandas as gpd
import pandas as pd
import requests, os


SALEM_CHERRIOTS_URL = "https://cherriots.rideralerts.com/InfoPoint/gtfs-zip.ashx"
SALEM_CHERRIOTS_ZIP = "salem_cherriots_GTFS.zip"

def get_GTFS_Feed(url, output_path) -> gk.Feed:
    path = os.path.dirname(__file__)
    filename = os.path.join(path, output_path)

    req = requests.get(url)
    with open(filename, "wb") as f:
        f.write(req.content)

    feed = gk.read_feed(filename)
    return feed


#NEED TO GET STOP-STOP TRAVEL TIME AND DIST
def final_GTFS_DF(feed:gk.Feed) -> pd.DataFrame:
    stats = gk.trips.compute_trip_stats(feed)
    stats.drop(columns=['route_type','shape_id','stop_pattern_name','block_id','service_id','speed','direction_id'])
    print(stats)
    return stats


        

feed = get_GTFS_Feed(SALEM_CHERRIOTS_URL, SALEM_CHERRIOTS_ZIP)
stop_df = final_GTFS_DF(feed)

