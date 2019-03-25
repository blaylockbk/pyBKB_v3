## Brian Blaylock
## March 21, 2019

'''
Workflow for putting GLM on HRRR grid and evaluating the contingency table.

    1) Get HRRR Lightning (LTNG) data and lat/lon grid
    2) Get GLM Events for the previous hour.
    3) Filter Events to HRRR Path
        A rough filter for events not in the HRRR domain
        A fine filter to account for the curvature of the map projection
    4) Map the GLM events onto the HRRR grid.
    5) Apply a spatial filter to bloat (upscale) the number of HRRR grid points that witness each GLM event.
    6) Compute the contingency table.

'''
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as ndimage

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')

from BB_HRRR.HRRR_Pando import get_hrrr_latlon,\
                               get_hrrr_variable
from BB_GOES.get_GLM import get_GLM_file_nearesttime,\
                            accumulate_GLM_FAST,\
                            bin_GLM_on_HRRR_grid
from BB_maps.my_basemap import draw_HRRR_map,\
                               draw_centermap
from BB_HRRR.HRRR_paths import get_paths


def radial_footprint(radius):
    """Specify a radial footprint"""
    y, x = np.ogrid[-radius: radius+1, -radius: radius+1]
    footprint = x**2 + y**2 <= radius**2
    footprint = 1*footprint.astype(float)
    return footprint

def neighborhood_max(values):
    return np.max(values)


## Create HRRR map object with Basemap
m = draw_HRRR_map()
Hlat, Hlon = get_hrrr_latlon(DICT=False)

## Specify the valid Datetime of interest
#DATE = datetime(2018, 5, 14, 22) # Mallard Fire
#DATE = datetime(2018, 7, 5, 23) # Lake Christine
DATE = datetime(2018, 7, 17, 6) # July Storm
#DATE = datetime(2018, 7, 27, 0) # Missing GLM data

validDATE = DATE
fxx = 1
runDATE = validDATE - timedelta(hours=fxx)

##=============================================================================
## 1) Get HRRR Lightning data and lat/lon grid.
Hlat, Hlon = get_hrrr_latlon(DICT=False)
H = get_hrrr_variable(runDATE, 'LTNG:entire', fxx=fxx, verbose=False)

##=============================================================================
## 2) Get GLM Events for the previous hour.
files = get_GLM_file_nearesttime(validDATE-timedelta(minutes=30), window=30, verbose=False)
E = accumulate_GLM_FAST(files, data_type='event', verbose=False)

print('\nGot %s of %s expected files.' % (files['Number'], files['Number Expected']))
print('Total Events: {:,}'.format(len(E['longitude'])))

##=============================================================================
## 3) Filter Events to HRRR domain and 4) Map GLM points HRRR grid
hist, filtered = bin_GLM_on_HRRR_grid(E, Hlat, Hlon, m)
print('In-HRRR Events: {:,}'.format(np.sum(filtered)))

#=============================================================================
## 5) Apply a spatial filter to bloat (enlarge or upscale) the number of HRRR
#     grid points that witness each GLM event.
# The GLM instrument has a resolution of only ~14 km. That is much more coarse
# than the 3 km HRRR grid we just mapped the GLM data onto. If you plotted the
# results of histogram, you would see the data is polkadoted like a speckled
# sussex chicken. We now apply a spatial filter that will fill in the gaps.

custom = np.array([[0,1,1,1,0],
                   [1,1,1,1,1],
                   [1,1,1,1,1],
                   [1,1,1,1,1],
                   [0,1,1,1,0]])
bloat_glm = ndimage.generic_filter(hist, np.max, footprint=custom)

##=============================================================================
## 6) Compute the contingency table

# HRRR binary field (yes/no lightning). Based on a threshold of 0.04, which 
# means the maximum flashes is 0.05 flashes/km2/5min. Since each grid box is
# 9 km2, this value equates to 0.45 flashes/gridbox/5min (because 0.05 * 9).
# If the maximum lightning was sustained for the entire hour, we would expect 6
# flashes in that grid box.
# This threshold was used because it got rid of the popcorn thunderstorms with
# very low values without shrinking the area of forecasted lightning too much.
 
Forecasted_binary = H['value'].data >= 0.04 # flashes/km2/5min
Observed_binary = bloat_glm > 1             # Only use when more than 1 event

def contingency_table(Forecasted_binary, Observed_binary, print_table=True):
    '''
    Return the contingency table values of a, b, c, and d for two binary fields.

    Input: 
        Forecasted_binary - array of True/False if the event was forecasted
        Observed_binary   - array of True/False if the event was observed
    '''
    # a) Hits:                  Where forecasted and observed
    a = np.sum(np.logical_and(Forecasted_binary, Observed_binary))

    # b) False Alarm:           Where forecasted, but not observed
    b = np.sum(Forecasted_binary) - a

    # c) Misses                 Where observed, but not forecasted
    c = np.sum(Observed_binary) - a

    # d) Correct Rejection:     Where not forecasted and not observed
    d = np.sum(np.logical_and(Forecasted_binary==False, Observed_binary==False))

    # Run some checks:
    # n) Total Number
    n = a+b+c+d

    # a+b) Total Forecasted
    total_forecasted = np.sum(Forecasted_binary)

    # a+c) Total Observed
    total_observed = np.sum(Observed_binary)

    # Checks 
    total_grid_points = np.size(Forecasted_binary)

    assert total_grid_points == n, ("WARNING! Total Number of Grid points does not equal n")
    assert total_forecasted == a+b, ("WARNING! Total forecasted points does not equal a+b")
    assert total_observed == a+c, ("WARNING! Total observed points does not equal a+c")

    if print_table:
        print('          {:^20}'.format('Observed'))
        print('         |{:^10}{:^10}| {:}'.format('Yes', 'No', 'Total'))
        print('--------------------------------------------')
        print(' Fxx Yes |{:10,}{:10,}| {:10,}'.format(a, b, a+b))
        print(' Fxx No  |{:10,}{:10,}| {:10,}'.format(c, d, c+d))
        print('--------------------------------------------')
        print('Total    |{:10,}{:10,}| {:10,}'.format(a+c, b+d, a+b+c+d))
        print('\n')

        hit_rate = a/(a+c)
        false_alarm_rate = b/(b+d)
        false_alarm_ratio = b/(a+b)
        proportion_correct = (a+d)/n

        print('Hit Rate: {:.2f}%'.format(hit_rate*100))
        print('False Alarm Rate: {:.2f}%'.format(false_alarm_rate*100))
        print('False Alarm Ratio: {:.2f}%'.format(false_alarm_ratio*100))
        print('Proportion Correct: {:.2f}%'.format(proportion_correct*100))
        print('/n')

    return a, b, c, d


a, b, c, d = contingency_table(Forecasted_binary, Observed_binary)





fig, (ax1, ax2) = plt.subplots(1,2, figsize=(15,5))

plt.sca(ax1)
m.pcolormesh(Hlon, Hlat, Observed_binary, latlon=True)
m.drawcoastlines()
m.drawstates()
m.drawcountries()
plt.title('GLM Events (bloated)')

plt.sca(ax2)
m.pcolormesh(Hlon, Hlat, Forecasted_binary, latlon=True)
m.drawcoastlines()
m.drawstates()
m.drawcountries()
plt.title('HRRR LTNG > 0.04')

plt.suptitle(validDATE, fontweight='semibold')
plt.subplots_adjust(wspace=.01, hspace=.01)
