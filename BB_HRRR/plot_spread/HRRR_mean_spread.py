# Brian Blaylock
# November 19, 2018

"""
Loop: Plot mean HRRR model spread for every hour of the day between a range of
dates.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime, timedelta

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon
from BB_HRRR.HRRR_Spread import mean_spread
from BB_datetimes.range import range_dates
from BB_HRRR.HRRR_Pando import get_hrrr_latlon
from BB_maps.my_basemap import draw_HRRR_map, draw_centermap

import matplotlib as mpl
mpl.rcParams['figure.figsize'] = [15,15]
mpl.rcParams['figure.titlesize'] = 15
mpl.rcParams['figure.titleweight'] = 'bold'
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['axes.labelsize'] = 12
mpl.rcParams['axes.titlesize'] = 15
mpl.rcParams['lines.linewidth'] = 1.8
mpl.rcParams['grid.linewidth'] = .25
mpl.rcParams['figure.subplot.wspace'] = 0.05
mpl.rcParams['figure.subplot.hspace'] = 0.05
mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['legend.framealpha'] = .75
mpl.rcParams['legend.loc'] = 'best'
mpl.rcParams['savefig.bbox'] = 'tight'
mpl.rcParams['savefig.dpi'] = 100

# Build map objects and get HRRR latitude and longitude grids.
latlon = get_hrrr_latlon()
lat = latlon['lat']
lon = latlon['lon']
m = draw_HRRR_map()                             # CONUS
mW = draw_centermap(40, -115, (10,10))          # West
mU = draw_centermap(39.5, -111.6, (3.2,3.2))    # Utah

# Variable constants
VARS = {'TMP:2 m':{'cmap':'magma',
                    'vmax':4,
                    'vmin':0,
                    'label':'2 m Temperature',
                    'units':'C'},
        'DPT:2 m':{'cmap':'magma',
                    'vmax':4,
                    'vmin':0,
                    'label':'2 m Dew Point',
                    'units':'C'},
        'UVGRD:10 m':{'cmap':'magma',
                       'vmax':5,
                       'vmin':0,
                       'label':'10 m Wind Speed',
                       'units':r'm s$\mathregular{^{-1}}$'},
        'UGRD:10 m':{'cmap':'magma',
                      'vmax':5,
                      'vmin':0,
                      'label':'10 m U Wind Component',
                      'units':r'm s$\mathregular{^{-1}}$'},
        'VGRD:10 m':{'cmap':'magma',
                      'vmax':5,
                      'vmin':0,
                      'label':'10 m V Wind Component',
                      'units':r'm s$\mathregular{^{-1}}$'},                       
        'REFC:entire':{'cmap':'magma',
                       'vmax':25,
                       'vmin':0,
                       'label':'Simulated Composite Reflectivity',
                       'units':'dBZ'},
        'LTNG:entire':{'cmap':'magma',
                       'vmax':1,
                       'vmin':0,
                       'label':'Hourly Max Lightning Threat',
                       'units':r'Flashes km$\mathregular{^{-2}}$ 5min$\mathregular{^{-1}}$'},
        'HGT:500 mb':{'cmap':'magma',
                      'vmax':8,
                      'vmin':0,
                      'label':'500 hPa Geopotential Height',
                      'units':'m'},
        'CAPE:surface':{'cmap':'magma',
                        'vmax':1500,
                        'vmin':0,
                        'label':'Convective Available Potential Energy',
                        'units':'J kg'}                                             
                    }

def make_plots(MAP, data, variable, sDATE, eDATE, hour, fxx, save=True):
    if MAP == m:
        plt.figure(figsize=(15,15))
        domain = 'CONUS'
    elif MAP == mW:
        plt.figure(figsize=(9, 9))
        domain = 'WEST'
    elif MAP == mU:
        plt.figure(figsize=(9, 9))
        domain = 'UTAH'

    plt.cla()
    plt.clf()
    MAP.pcolormesh(lon, lat, data,
                   cmap=VARS[variable]['cmap'],
                   vmin=0,
                   latlon=True)
    MAP.drawcoastlines(linewidth=.3, color='w')
    MAP.drawcountries(linewidth=.3, color='w')
    MAP.drawstates(linewidth=.3, color='w')

    plt.title('HRRR %s' % variable, fontweight='bold', loc='left')
    plt.title('Start: %s\n End: %s' % (sDATE.strftime('%d %b %Y %H:%M UTC'),
                                       eDATE.strftime('%d %b %Y %H:%M UTC')), loc='right', fontsize=10)
    if MAP == m:
        plt.title('Hour: %s\nFXX: %s' % (hour, fxx))
    else:
        plt.ylabel('Hour: %s\nFXX: %s' % (hour, fxx))
        
    if MAP == mU:
        MAP.drawcounties(linewidth=.2, color='lightgrey')

    cb = plt.colorbar(orientation='horizontal', pad=.01, shrink=.8)
    cb.set_label('Mean Model Spread\n%s (%s)' % (VARS[variable]['label'], VARS[variable]['units']))
    
    SAVEDIR = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_Spread/Hourly_%s-%s/%s/%s/' % (sDATE.strftime('%b%Y'), eDATE.strftime('%b%Y'), variable.split(':')[0], domain)

    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
        # then link the photo viewer
        photo_viewer = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/Brian_Blaylock/photo_viewer/photo_viewer.php'
        os.link(photo_viewer, SAVEDIR+'photo_viewer.php')
    plt.savefig(SAVEDIR+'%s_h%02d' % (variable.replace(':', '-').replace(' ', '-'), hour))



variable = 'TMP:2 m'
V = VARS[variable]

# Mean Spread for hour 1200 UTC for the range of dates
for hour in range(24):
    sDATE = datetime(2018, 5, 1, hour)
    eDATE = datetime(2018, 10, 1, hour)
    DATES = range_dates(sDATE, eDATE, DAYS=1)
    fxx = range(0,19)
    variable = 'TMP:2 m'

    # Get mean spread for hour
    AVG_SPREAD = mean_spread(DATES, variable=variable, fxx=fxx)

    # Generate Figures
    make_plots(m, AVG_SPREAD, variable, sDATE, eDATE, hour, fxx, save=True)
    make_plots(mW, AVG_SPREAD, variable, sDATE, eDATE, hour, fxx, save=True)
    make_plots(mU, AVG_SPREAD, variable, sDATE, eDATE, hour, fxx, save=True)
