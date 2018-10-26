# Brian Blaylock
# September 14, 2018

import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from mpl_toolkits.basemap import Basemap

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')

from BB_HRRR.HRRR_Pando import get_hrrr_latlon
from BB_GOES.get_GLM import get_GLM_files_for_range, accumulate_GLM_FAST
from BB_maps.my_basemap import draw_HRRR_map, draw_centermap, draw_GLM_map

m = draw_HRRR_map()
mU = draw_centermap(lat=40, lon=-115, size=(10,10))
B = draw_GLM_map()

import matplotlib as mpl
mpl.rcParams['figure.figsize'] = [15,15]
mpl.rcParams['figure.titlesize'] = 15
mpl.rcParams['figure.subplot.wspace'] = 0.05
mpl.rcParams['figure.subplot.hspace'] = 0.05
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['lines.linewidth'] = 1.8
mpl.rcParams['savefig.bbox'] = 'tight'
mpl.rcParams['savefig.dpi'] = 100

LL = get_hrrr_latlon()
lat = LL['lat']
lon = LL['lon']


sDATE = datetime(2018, 5, 1)
eDATE = datetime(2018, 9, 1)

for HOUR in range(21, 24):
    HOURS = [HOUR]
    FILES = get_GLM_files_for_range(sDATE, eDATE, HOURS=HOURS)

    GLM = accumulate_GLM_FAST(FILES)


    H, y, x = np.histogram2d(GLM['longitude'], GLM['latitude'], bins=(800, 895))
    Y, X = np.meshgrid(y, x)
    H = np.transpose(H)

    ## Full Range of view
    ## ----------------------------------------------------------------------------
    B.pcolormesh(Y, X, H, latlon=True, cmap='magma', vmin=0, vmax=np.percentile(H, 99.5))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.6)
    cb.set_label(r'GLM Accumulated Flash Count (~14 km$\mathregular{^2}}$ bins)')

    B.drawcoastlines(color='grey', linewidth=.15)
    B.drawcountries(color='grey', linewidth=.15)

    plt.title('GOES-16 Flashes', loc='left', fontweight='semibold')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y'), eDATE.strftime('%d %b %Y')), loc='right')
    plt.title('Hours: %s' % HOURS)

    plt.savefig('figs/full-field_%s' % '-'.join('%02d' % x for x in HOURS))

    plt.cla()
    plt.clf()

    ## CONUS
    ## ----------------------------------------------------------------------------
    m.pcolormesh(Y, X, H, latlon=True, cmap='magma', vmin=0, vmax=np.percentile(H, 99.5))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.6)
    cb.set_label(r'GLM Accumulated Flash Count (~14 km$\mathregular{^2}}$ bins)')

    m.drawcoastlines(color='grey', linewidth=.15)
    m.drawcountries(color='grey', linewidth=.15)
    m.drawstates(color='grey', linewidth=.15)

    plt.title('GOES-16 Flashes', loc='left', fontweight='semibold')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y'), eDATE.strftime('%d %b %Y')), loc='right')
    plt.title('Hours: %s' % HOURS)

    plt.savefig('figs/CONUS_%s' % '-'.join('%02d' % x for x in HOURS))

    plt.cla()
    plt.clf()

    ## Western USA
    ## ----------------------------------------------------------------------------
    mU.pcolormesh(Y, X, H, latlon=True, cmap='magma', vmin=0, vmax=np.percentile(H, 99.5))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.6)
    cb.set_label(r'GLM Accumulated Flash Count (~14 km$\mathregular{^2}}$ bins)')

    mU.drawcoastlines(color='grey', linewidth=.15)
    mU.drawcountries(color='grey', linewidth=.15)
    mU.drawstates(color='grey', linewidth=.15)

    plt.title('GOES-16 Flashes', loc='left', fontweight='semibold')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y'), eDATE.strftime('%d %b %Y')), loc='right')
    plt.title('Hours: %s' % HOURS)

    plt.savefig('figs/West_%s' % '-'.join('%02d' % x for x in HOURS))

    plt.cla()
    plt.clf()