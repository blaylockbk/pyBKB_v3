# Brian Blaylock
# November 16, 2018

"""
Generate datetime lists more efficiently
"""


from datetime import datetime, timedelta
import numpy as np

def range_dates(sDATE, eDATE, HOURS=False, DAYS=False):
    """
    Make a list of dates
    Inputs:
        sDATE - start datetime
        eDATE - end datetime

        HOURS - Incremented Hours. Default is 1.
                If =6, then list of dates every 6 hours.
        DAYS  - Incremented Days. Default is False.
    """
    # NOTE: Either HOURS or DAYS can have a value, but not both.
    if (not HOURS and not DAYS) or (HOURS and DAYS):
        print('HOURS or DAYS needs to have a value, but not both.')
        return

    if HOURS:
        hours = (eDATE-sDATE).days*24
        DATES = np.array([sDATE + timedelta(hours=x) for x in range(0, hours, HOURS)])
        return DATES
    if DAYS: 
        days = (eDATE-sDATE).days
        DATES = np.array([sDATE + timedelta(days=x) for x in range(0, days, DAYS)])
        return DATES


if __name__ == '__main__':

    sDATE = datetime(2018, 1, 1)
    eDATE = datetime(2018, 1, 6)
    
    print(range_dates(sDATE, eDATE, HOURS=1))

    print(ragne_dates(sDATE, eDATE, HOURS=6))

    print(ragne_dates(sDATE, eDATE, DAYS=1))