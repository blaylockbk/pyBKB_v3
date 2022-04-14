# Brian Blaylock
# July 3, 2018

"""
Download TDWR files from UCAR THREDDS server and save to the current directory
by date and scan type.

Terminal Doppler Weather Radar - SLC
 lat:  40.97
 lon:-111.93

Downloaded from UCAR Thredds server
http://thredds.ucar.edu/thredds/catalog/terminal/level3/catalog.html

Example, this is the HTTP server URL you can download from
http://thredds.ucar.edu/thredds/fileServer/terminal/level3/TV0/SLC/20160123/Level3_SLC_TV0_20160123_2359.nids

Catalog: browse the availalbe data here
http://thredds.ucar.edu/thredds/catalog/terminal/level3/TV0/SLC/catalog.html


TV0/Base Velocity Tilt 1 (knots)
TV1/Base Velocity Tilt 2 (knots)
TV2/Base Velocity Tilt 3 (knots)
TR0/Base Reflectivity Tilt 1 (dbz)
TR1/Base Reflectivity Tilt 2 (dbz)
TR2/Base Reflectivity Tilt 3 (dbz)
NCR/Composite Reflectivity
"""

from urllib.request import urlretrieve
import os
from datetime import datetime, timedelta


# ---- Start Date Options -----------------------------------------------------
year = "2018"
month = "7"
day = "2"

num_days = 2  # The number of consecutive days you wish to download, including
# the initial date.
# NOTE: The THREDDS server only keeps the last 20 days of data


# ---- Create a list of dates -------------------------------------------------
# We need to check if a radar file exists for every minute
base = datetime.strptime(year + month + day, "%Y%m%d")
num_minutes = num_days * 24 * 60
date_list = [base + timedelta(minutes=x) for x in range(0, num_minutes)]


# ---- Specify which scan you want to download --------------------------------
scan = ["TV0"]  ## Just download one scan type
# scan = ['TV0','TV1','TV2']                         ## TV0, TV1, and TV2 are radial velocity
scan = [
    "TV0",
    "TV1",
    "TV2",
    "NCR",
    "TR0",
    "TR1",
    "TR2",
]  ## velocity, reflectivity, and composite, just grabbing all

# ---- Location ---------------------------------------------------------------
tdwr = "SLC"  # SLC is the Salt Lake City TDWR

print("Ok, I'll work on these...")
print("Dates", date_list[0], "through", date_list[-1])
print("Scans", scan)

for DATE in date_list:
    for j in scan:
        # Make a directory for this day
        new_dir = (
            str(DATE.year).zfill(4) + str(DATE.month).zfill(2) + str(DATE.day).zfill(2)
        )

        # Make a directory for each YYYYMMDD and sub directory for the scan type
        if os.path.exists(new_dir + "/" + j) == False:
            os.makedirs(new_dir + "/" + j)
            print("created subdirectory", new_dir + "/" + j)

        # look for a file for every possible hour and minute
        # Download if the data exists
        hrmin = str(DATE.hour).zfill(2) + str(DATE.minute).zfill(2)
        url = (
            "http://thredds.ucar.edu/thredds/fileServer/terminal/level3/"
            + j
            + "/"
            + tdwr
            + "/"
            + new_dir
            + "/Level3_"
            + tdwr
            + "_"
            + j
            + "_"
            + new_dir
            + "_"
            + hrmin
            + ".nids"
        )
        filename = (
            new_dir
            + "/"
            + j
            + "/"
            + "Level3_"
            + tdwr
            + "_"
            + j
            + "_"
            + new_dir
            + "_"
            + hrmin
            + ".nids"
        )
        try:
            urlretrieve(url, filename)
        except:
            pass
        # else, keep the file
        else:
            print("Saved", filename, os.path.getsize(filename) / 1000.0, "KB")
