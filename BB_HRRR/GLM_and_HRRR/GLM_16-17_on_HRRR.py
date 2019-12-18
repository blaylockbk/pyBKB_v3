## Brian Blaylock
## May 8, 2019                   # Going to Mesa Verde tomorrow! Moab Saturday!

"""
GLM binary array on HRRR grid
"""

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as ndimage
import os
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')

from BB_HRRR.HRRR_Pando import get_hrrr_all_valid, \
                               get_hrrr_latlon,\
                               get_hrrr_variable
from BB_GOES.get_GOES import get_GOES_nearesttime
from BB_GOES.get_GLM import  accumulate_GLM_FAST,\
                             bin_GLM_on_HRRR_grid
from BB_maps.my_basemap import draw_HRRR_map,\
                               draw_centermap

# Get HRRR lat/lon grid and map object
Hlat, Hlon = get_hrrr_latlon(DICT=False)
m = draw_HRRR_map()

## Date of interest (we want the previous hour from this time)
DATE = datetime(2019, 5, 8, 4)

## Load GOES GLM-17 data
# GLM files for hour period
G17_files = get_GOES_nearesttime(DATE-timedelta(minutes=30), 'GLM', 17, window=30)
G16_files = get_GOES_nearesttime(DATE-timedelta(minutes=30), 'GLM', 16, window=30)

# GLM event data from those files
G17 = accumulate_GLM_FAST(G17_files, data_type='event')
G16 = accumulate_GLM_FAST(G16_files, data_type='event')

# Bin GLM on HRRR grid (hist17), and filter in-HRRR events
hist17, filtered17 = bin_GLM_on_HRRR_grid(G17, Hlat, Hlon, m)
hist16, filtered16 = bin_GLM_on_HRRR_grid(G16, Hlat, Hlon, m)

# Dilate the GLM events
custom_filter = np.array([[0,1,1,1,0],
                          [1,1,1,1,1],
                          [1,1,1,1,1],
                          [1,1,1,1,1],
                          [0,1,1,1,0]])
bloat_glm17 = ndimage.generic_filter(hist17, np.max, footprint=custom_filter)
bloat_glm16 = ndimage.generic_filter(hist16, np.max, footprint=custom_filter)

# Only use if number of events > 1...More than 1 GLM event in a grid box.
binary17 = bloat_glm17 > 1
binary16 = bloat_glm16 > 1

# Draw on Map
mask17 = np.ma.array(binary17, mask=binary17==0)
mask16 = np.ma.array(binary16, mask=binary16==0)

m.pcolormesh(Hlon, Hlat, mask17, latlon=True, cmap='YlOrBr', vmax=2, vmin=0, alpha=.5)
m.contour(Hlon, Hlat, mask17.data, latlon=True, levels=[0,1], colors='tab:orange')
m.drawcoastlines(); m.drawstates()

m.pcolormesh(Hlon, Hlat, mask16, latlon=True, cmap='BuPu', vmax=2, vmin=0, alpha=.5)
m.contour(Hlon, Hlat, mask16.data, latlon=True, levels=[0,1], colors='tab:blue')
m.drawcoastlines(); m.drawstates()

plt.show()