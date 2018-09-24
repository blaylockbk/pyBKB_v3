# Brian Blaylock
# September 21, 2018

"""
Time Series of RMSD value for HRRR
"""

import numpy as np 
import matplotlib.pyplot as plt 
from datetime import datetime, timedelta
import multiprocessing
import os

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
sys.path.append('B:\pyBKB_v3')

from BB_HRRR.HRRR_RMSD import RMSD
from BB_maps.my_basemap import draw_HRRR_map

m = draw_HRRR_map()

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

def graph_this(DATE):
    img_name = SAVEDIR + 'HRRR_RMSD-%s_%s' % (variable.replace(':', '-').replace(' ', '-'), DATE.strftime('%Y%m%d-%H%M'))
    if not os.path.exists(img_name):
        if variable in ['LTNG:entire', 'APCP:surface', 'WIND:10 m']:
            # These variables are hourly values and don't have an analysis value
            FORECASTS = range(1,19) 
        else:
            # The other variables have an analysis
            FORECASTS = range(0,19)
        rmsd = RMSD(DATE, variable, FORECASTS=FORECASTS, verbose=False)
        
        m.pcolormesh(rmsd['lon'], rmsd['lat'], rmsd['RMSD'], latlon=True, vmin=0)
        plt.colorbar(orientation='horizontal', shrink=.8, pad=.01)

        m.drawcoastlines(color='w', linewidth=.15)
        m.drawcountries(color='w', linewidth=.15)
        m.drawstates(color='w', linewidth=.15)

        plt.title('HRRR RMSD %s' % variable, loc='left', fontweight='semibold')
        plt.title('Valid: %s' % DATE.strftime('%Y-%m-%d %H:%M UTC'), loc='right')

        plt.savefig(img_name)

        sys.stdout.write('\r %s %s finished' % (variable, DATE))
        sys.stdout.flush()

        plt.close()
    
sDATE = datetime(2018, 6, 1)
eDATE = datetime(2018, 6, 10)
num_hours = (eDATE-sDATE).days*24 + int((eDATE-sDATE).seconds/60/60)
DATES = [sDATE + timedelta(hours=h) for h in range(num_hours)]

for variable in ['TMP:2 m', 'UGRD:10 m', 'VGRD:10 m', 'LTNG:entire', 'REFC:entire', 'WIND:10 m', 'CAPE:surface', 'HGT:500 mb', 'DPT:2 m']:
    SAVEDIR = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_RMSE/TimeSeries/%s/' % variable.split(':')[0]
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)

    cpus = 14
    P = multiprocessing.Pool(cpus)
    P.map(graph_this, DATES) 
    P.close()