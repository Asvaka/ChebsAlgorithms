
# 1st Validate GTFS feed zip file for Salem, Oregon with Canonical GTFS Validator [https://gtfs-validator.mobilitydata.org/] 

import gtfs_kit as gk
import geopandas as gpd
import pandas as pd
import requests, zipfile, os

SALEM_CHERRIOTS_URL = "https://cherriots.rideralerts.com/InfoPoint/gtfs-zip.ashx"
SALEM_CHERRIOTS_ZIP = "salem_cherriots_GTFS.zip"

def get_GTFS_Feed(url, output_path) -> gk.Feed:
    path = os.path.dirname(__file__)
    filename = os.path.join(path, output_path)

    req = requests.get(url)
    with open(filename, "wb") as f:
        f.write(req.content)

    feed = gk.read_feed(filename)
    feed.describe()
    return feed



get_GTFS_Feed(SALEM_CHERRIOTS_URL, SALEM_CHERRIOTS_ZIP)

