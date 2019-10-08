## Brian Blaylock
## October 8, 2019 

"""
Obtain a sounding from the HRRR archive
"""
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

from HRRR_Pando import get_hrrr_variable, get_hrrr_latlon, pluck_hrrr_point

# We need to get the latitude/longitude grids first
Hlatlon = get_hrrr_latlon()



def get_hrrr_sounding(DATE, variable, fxx=0, field='prs',
                      lat=40.771, lon=-111.965, verbose=True):
    """
    Generate a sounding from HRRR grids.
    Levels at 25 mb intervals from the pressure files only available from
    analyses F00.
    Fewer levels from surface file (sfc) are available for forecast hours.

    ** NOTE: for locations that reside above 1000 mb (like Salt Lake City)
             you will need to trim off the first few values.

    Input:
        DATE     - datetime representing the valid date.
        variable - a string indicating the variable in the .idx file (e.g. 'TMP')
        fxx      - forecast hour. Default is 0 for F00.
        field    - either 'prs' or 'sfc' (see details below, default is 'prs')
        lat      - latitude point (default is KSLC)
        lon      - longitude point (default is KSLC)
    Return:
        levels   - a list of levels in millibars
        sounding - a list of the variable value at the corresponding levels.

    ---------------------------------------------------------------------------

    For pressure field (prs):
        *only fxx=0 is available*
        variables available
            HGT   - Geopotential Height
            TMP   - Temperature
            RH    - Relative Humidity
            DPT   - Dew Point
            SPFH  - Specific Humidity
            VVEL  - Vertical Velocity
            UGRD  - U wind component
            VGRD  - V wind component
            ABSV  - ?
            CLWMR - Cloud water mixing ratio
            CICE  - Cloud ice mixing ratio
            RWMR  - Rain mixing ratio
            SNMR  - Snow mixing ratio
            GRLE  - Graupel mixing ratio

    For surface field (sfc):
        *available for f00-f36*
        variables available:
            HGT  - Geopotential Height (not for 250 mb)
            TMP  - Temperature (not for 250 mb)
            DPT  - Dew Point (not for 250 mb)
            UGRD  - U wind component
            VGRD  - V wind component

    """
    # What are the levels? That depends on the field and variable requested.
    if field == 'prs':
        levels = range(1000, 25, -25)
    elif field == 'sfc':
        if 'GRD' in variable: # if we are requesting a UGRD or VGRD wind
            levels = [1000, 925, 850, 700, 500, 250]
        else:
            levels = [1000, 925, 850, 700, 500]


    # What is the grid point we want to extract?
    x, y = pluck_hrrr_point(Hlatlon, lat, lon, XY_only=True, verbose=verbose)
    
    # We have the valid date, but what is the run date?
    RUN_DATE = DATE - timedelta(hours=fxx)

    # Obtain the value at the point for each level
    sounding = [get_hrrr_variable(RUN_DATE, '%s:%s' % (variable,LEV), field=field, value_only=True, verbose=False)['value'][x, y] for LEV in levels]

    return np.array(levels), np.array(sounding)

if __name__=='__main__':

    DATE = datetime(2019, 1, 10, 12)
    level, tmp = get_hrrr_sounding(DATE, 'TMP')
    level, dpt = get_hrrr_sounding(DATE, 'DPT')
    level, ugrd = get_hrrr_sounding(DATE, 'UGRD')
    level, vgrd = get_hrrr_sounding(DATE, 'VGRD')

    tmp -= 273.15
    dpt -= 273.15

    plt.plot(tmp, level, color='r')
    plt.plot(dpt, level, color='g')
    plt.barbs(np.zeros_like(level), level, ugrd, vgrd,
            barb_increments={'half':2.5, 'full':5,'flag':25,})

    plt.grid(linestyle='--', linewidth=.5)

    plt.gca().set_yscale('log')
    ticks = range(1000, 0, -100)
    plt.gca().invert_yaxis()
    plt.yticks(ticks, ticks)

    plt.title('HRRR prs sounding', loc='left')
    plt.title('valid %s' % DATE.strftime('%H:%M UTC %d %b %Y'), loc='right')
    plt.show()




    
