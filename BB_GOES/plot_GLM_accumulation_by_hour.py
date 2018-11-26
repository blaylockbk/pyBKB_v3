# Brian Blaylock
# September 14, 2018

import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from mpl_toolkits.basemap import Basemap

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')
from BB_GOES.get_GLM import get_GLM_files_for_range, accumulate_GLM_FAST
from BB_maps.my_basemap import draw_HRRR_map, draw_centermap, draw_GLM_map


B = draw_GLM_map()                              # GLM Field of View
m = draw_HRRR_map()                             # CONUS
mW = draw_centermap(40, -115, (10,10))          # West
mU = draw_centermap(39.5, -111.6, (3.2,3.2))    # Utah


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


def make_plots(MAP, lon, lat, data, sDATE, eDATE, hour, save=True):
    if MAP == m:
        plt.figure(figsize=(15,15))
        domain = 'CONUS'
    elif MAP == mW:
        plt.figure(figsize=(9, 9))
        domain = 'WEST'
    elif MAP == mU:
        plt.figure(figsize=(9, 9))
        domain = 'UTAH'
    elif MAP == B:
        plt.figure(figsize=(9, 9))
        domain = 'GLM'

    plt.cla()
    plt.clf()
    MAP.pcolormesh(lon, lat, data, latlon=True, cmap='magma', vmin=0, vmax=np.percentile(data, 99.5))
    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.8, extend='max')
    cb.set_label(r'GLM Accumulated Flash Count (~14 km$\mathregular{^2}}$ bins)')

    plt.title('GOES-16 Flashes', loc='left', fontweight='semibold')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y'),
                                       eDATE.strftime('%d %b %Y')), loc='right', fontsize=10)
    plt.title('%02d:00 UTC' % (hour))

    plt.savefig('figs/full-field_%s' % '-'.join('%02d' % x for x in HOURS))
    MAP.drawcoastlines(linewidth=.3, color='w')
    MAP.drawcountries(linewidth=.3, color='w')
    MAP.drawstates(linewidth=.3, color='w')        
    if MAP == mU:
        MAP.drawcounties(linewidth=.2, color='lightgrey')
    
    SAVEDIR = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/GOES16_GLM/Hourly_%s-%s/%s/' % (sDATE.strftime('%b%Y'), eDATE.strftime('%b%Y'), domain)

    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
        # then link the photo viewer
        photo_viewer = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/Brian_Blaylock/photo_viewer/photo_viewer.php'
        os.link(photo_viewer, SAVEDIR+'photo_viewer.php')
    plt.savefig(SAVEDIR+'%s_h%02d' % ('GLM', hour))


sDATE = datetime(2018, 5, 1)
eDATE = datetime(2018, 5, 5)

for hour in range(24):
    HOURS = [hour]
    FILES = get_GLM_files_for_range(sDATE, eDATE, HOURS=HOURS)
    GLM = accumulate_GLM_FAST(FILES)
    H, y, x = np.histogram2d(GLM['longitude'], GLM['latitude'], bins=(800, 895))
    Y, X = np.meshgrid(y, x)
    H = np.transpose(H)

    make_plots(m, Y, X, H, sDATE, eDATE, hour, save=True)
    make_plots(mW, Y, X, H, sDATE, eDATE, hour, save=True)
    make_plots(mU, Y, X, H, sDATE, eDATE, hour, save=True)
    make_plots(B, Y, X, H, sDATE, eDATE, hour, save=True)
'''
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
'''