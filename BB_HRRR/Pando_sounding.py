## Brian Blaylock
## October 8, 2019 

"""
Obtain a sounding from the HRRR archive
"""
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

from HRRR_Pando import get_hrrr_sounding

if __name__=='__main__':

    DATE = datetime(2019, 1, 10, 12)
    level, [tmp] = get_hrrr_sounding(DATE, 'TMP')
    level, [dpt] = get_hrrr_sounding(DATE, 'DPT')
    level, [ugrd] = get_hrrr_sounding(DATE, 'UGRD')
    level, [vgrd] = get_hrrr_sounding(DATE, 'VGRD')

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




    
