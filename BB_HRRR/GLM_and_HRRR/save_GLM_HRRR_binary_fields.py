## Brian Blaylock
## May 7, 2019

"""
Generate HRRR-GLM binary Lightning tables and store data in a dictionary.
Save the dictionary for later use. Store on Horel-Group8 (approx. 150 GB).
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import multiprocessing
import os

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon
from BB_GOES.get_GOES import get_GOES_nearesttime
from BB_GOES.get_GLM import get_GLM_file_nearesttime, accumulate_GLM_FAST, filter_by_HRRR
from BB_datetimes.range import range_dates

from BB_HRRR.GLM_and_HRRR.GLM_events_HRRR import get_GLM_HRRR_contingency_stats, domains

def get_and_save(DATE):
    print(DATE)
    BASE = '/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/GLM-HRRR_LTNG_binary/'
    FILE = BASE+'/HRRR-GLM-Binary_%s' % DATE.strftime('%Y-%m-%d_%H%M')
    if not os.path.exists(FILE):
        # This function will write the file if it isn't available
        a = get_GLM_HRRR_contingency_stats(DATE)


#sDATE = datetime(2018, 5, 1)
#eDATE = datetime(2018, 8, 1)

sDATE = datetime(2018, 8, 1)
eDATE = datetime(2018, 10, 1)

DATES = range_dates(sDATE, eDATE, HOURS=1)


list(map(get_and_save, DATES))


# NOTE: Can't use multiprocessing because the get_GLM_HRRR_contingency_stats
#       uses it instead.