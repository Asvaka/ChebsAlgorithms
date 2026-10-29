# I am reading this https://www.transit-data.com/
# pip install gtfs_functions
from gtfs_functions import *
import geopandas as gpd
import pandas as pd
import requests, zipfile, os

'''
Need from GTFS:
stop_times.txt
stops.txt
routes.txt?
'''


SALEM_GTFS_URL = "https://cherriots.rideralerts.com/InfoPoint/gtfs-zip.ashx"

def download_feed(url):
    gtfs_path = url
    feed = gf.Feed(gtfs_path, time_windows=[0, 6, 10, 12, 16, 19, 24])

    routes = feed.routes
    routes.head(2)

download_feed(SALEM_GTFS_URL)






