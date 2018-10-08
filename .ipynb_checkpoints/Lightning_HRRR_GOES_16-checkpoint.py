# Brian Blaylock
# September 27, 2018

"""
Plot image of GOES ABI, GLM overlaid with HRRR RMSDs
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')

from BB_GOES.get_ABI import get_GOES_truecolor, file_nearest
from BB_GOES.get_GLM import get_GLM_files_for_ABI, accumulate_GLM
from BB_HRRR.HRRR_Pando import get_hrrr_variable
from BB_HRRR.HRRR_RMSD import RMSD
from BB_maps.my_basemap import draw_HRRR_map
from BB_cmap.NWS_standard_cmap import cm_wind, cm_temp, cm_dpt
from BB_cmap.reflectivity_cmap import reflect_ncdc

m = draw_HRRR_map()

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

DATE = datetime(2018, 7, 24, 0)

# Get GOES16 ABI
FILE = file_nearest(DATE)
ABI = get_GOES_truecolor(FILE, verbose=False)

# Get GOES16 GLM
GLM_files = get_GLM_files_for_ABI(FILE)
GLM = accumulate_GLM(GLM_files)

# Get HRRR RMSDs
variable = 'TMP:2 m'
rmsd = RMSD(DATE, variable)

if variable in ['LTNG:entire']:
    contours = [0.75, 20]
    units = 'Max Flashes/km2/5min'
    fxx = 1
    cmap = {'cmap':'plasma',
            'vmax':5,
            'vmin': 0}
elif variable in ['REFC:entire']:
    contours = [20, 200]
    units = 'dBZ'
    fxx = 0
    cmap = reflect_ncdc()
elif variable in ['TMP:2 m']:
    contours = [4, 20]
    units = 'C'
    fxx = 0
    cmap = cm_temp()
elif variable in ['UVGRD:10 m']:
    contours = [4, 20]
    units = r'm s$\mathregular{^{-1}}$'
    fxx = 0
    cmap = cm_wind() 

# Get HRRR Analysis
H = get_hrrr_variable(DATE, variable, fxx=fxx)
if variable.split(':')[0] == 'UVGRD':
    masked = H['SPEED']
else:
    masked = H['value']
masked = np.ma.array(masked)
masked[masked <= 0.02] = np.ma.masked

if variable.split(":")[0] in ['TMP', 'DPT']:
    masked -= 273.15
    
# Plot Images
## Figure 1: RMSD over ABI and GLM
# Plot ABI
newmap = m.pcolormesh(ABI['lon'], ABI['lat'], ABI['TrueColor'][:,:,0], color=ABI['rgb_tuple'], linewidth=0, latlon=True)
newmap.set_array(None)

# Plot HRRR RMSD
m.contour(rmsd['lon'], rmsd['lat'], rmsd['RMSD'], levels=contours, colors='magenta', linewidths=0.75, latlon=True)
m.contourf(rmsd['lon'], rmsd['lat'], rmsd['RMSD'], levels=contours, colors='magenta', latlon=True, alpha=.35)
plt.xlabel('RMSD > %s %s' % (contours[0], units), color='magenta')

# Plot GLM
m.scatter(GLM['longitude'], GLM['latitude'], c='yellow', marker='+', latlon=True)

m.drawcoastlines(color='grey')
m.drawcountries(color='grey')
m.drawstates(color='grey')

plt.title('GOES16 ABI+GLM\n%s to %s' % (ABI['sDATE'].strftime('%Y-%m-%d %H:%M'), ABI['eDATE'].strftime('%Y-%m-%d %H:%M')), loc='left')
plt.title('HRRR %s RMSD\nvalid: %s' % (variable,H['valid'].strftime('%Y-%m-%d %H:%M')), loc='right')

plt.savefig('figs/Lightning_GOES_HRRR-%s_%s' % (variable.replace(':', '-').replace(' ', '-'), DATE.strftime('%Y%m%d-%H%M')))

## Figure 2: RMSD over HRRR analysis and GLM
# Plot HRRR value
m.pcolormesh(H['lon'], H['lat'], masked, latlon=True, cmap=cmap['cmap'], vmax=cmap['vmax'], vmin=cmap['vmin'])
plt.colorbar(orientation='horizontal', shrink=.8, pad=.05)

# Plot HRRR RMSD
m.contour(rmsd['lon'], rmsd['lat'], rmsd['RMSD'], levels=contours, colors='magenta', linewidths=0.75, latlon=True)
plt.xlabel('RMSD > %s %s' % (contours[0], units), color='magenta')

# Plot GLM
#m.scatter(GLM['longitude'], GLM['latitude'], c='yellow', marker='+', latlon=True)
m.scatter(GLM['longitude'], GLM['latitude'], edgecolors='k', s=300, marker='o', facecolors='none', latlon=True, zorder=100, linewidth=.2)

m.drawcoastlines(color='grey')
m.drawcountries(color='grey')
m.drawstates(color='grey')

plt.title('GOES16 GLM\n%s to %s' % (ABI['sDATE'].strftime('%Y-%m-%d %H:%M'), ABI['eDATE'].strftime('%Y-%m-%d %H:%M')), loc='left')
plt.title('HRRR %s RMSD and analysis\nvalid: %s' % (variable,H['valid'].strftime('%Y-%m-%d %H:%M')), loc='right')

plt.savefig('figs/Lightning_GLM_HRRR-%s_%s' % (variable.replace(':', '-').replace(' ', '-'), DATE.strftime('%Y%m%d-%H%M')))

print('Finished %s %s' % (variable, DATE))