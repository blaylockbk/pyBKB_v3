# Brian Blaylock
# July 27, 2018

"""
HRRR Time Lagged Ensemble:
https://rapidrefresh.noaa.gov/internal/pdfs/alcott_HRRRTLE_8jun2016-adj.pdf
"""

import numpy as np
from datetime import datetime, timedelta
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\\pyBKB_v2')
from BB_HRRR.HRRR_Pando import get_hrrr_variable
from BB_maps.my_basemap import draw_HRRR_map
from BB_cmap.NCAR_ensemble_cmap import cm_prob

def radial_footprint(radius):
    y,x = np.ogrid[-radius: radius+1, -radius: radius+1]
    footprint = x**2+y**2 <= radius**2
    footprint = 1*footprint.astype(float)
    return footprint

def first_filter(values):
    '''
    If the pixel is over the threshold, then set all surrounding pixels as 
    above the threshold. This ensures that this pixel will receive 100%
    probability that it will be over the threshold. We do this with a filter.
    If any pixel within the radius exceeds the threshold, then that point is
    set to exceed the threshold.
    '''
    return np.max(values) >= threshold

def second_filter(values):
    '''
    The second filter sums up the amount of points in the radius
    '''
    return np.sum(values)


validDATE = datetime(2018, 7, 17, 6)
threshold = 35
radius = 9
fxx = range(0,5)
members = []

for f in fxx:
    runDATE = validDATE - timedelta(hours=f)
    H = get_hrrr_variable(runDATE, 'REFC:entire', fxx=f)
    first = ndimage.generic_filter(H['value'], first_filter, footprint=radial_footprint(radius))
    second = ndimage.generic_filter(first, second_filter, footprint=radial_footprint(radius))
    members.append(second)

max_points = np.sum(radial_footprint(radius))


member_mean = np.mean(members/max_points, axis=0)

masked = member_mean
masked = np.ma.array(masked)
masked[masked <= 0] = np.ma.masked

m = draw_HRRR_map()

plt.figure(figsize=[10,5])
cm = cm_prob()
m.pcolormesh(H['lon'], H['lat'], masked,
             cmap=cm['cmap'],
             vmax=cm['vmax'],
             vmin=cm['vmin'],
             latlon=True)
plt.colorbar()

m.drawcoastlines()
m.drawcountries()
m.drawstates()

plt.title('HRRR Probability Reflectivity > %s dBZ' % threshold, loc='left')
plt.title('\nValid: %s' % validDATE.strftime('%Y %b %d %H:%M UTC'), loc='right')
plt.xlabel('FXX: %s\nRadius: %s km' % (fxx, radius*3))



# Percentiles
pValues = {}
for p in [0,1,2,3,4,5,10,25,33,50,66,75,90,95,96,97,98,99,100]:
    print('working on p%02d' % p)
    asdfpValues['p%02d' % p] = ndimage.percentile_filter(H['value'], p, footprint=radial_footprint(9), mode='reflect')