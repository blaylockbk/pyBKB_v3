## Brian Blaylock
## May 8, 2019

"""
I foolishly quit and restarted FSS calculations of different radii in the
middle of loops, and this resulted in skipped/missed lines in the files.
I need a method to identify which data is missing, compute the data, and insert
the data it in the correct location (correct line) in the CSV files.
    1. For a date, is it missing in any of the files?
        a. Where should the missing data be inserted? (What line?)
    2. Get grid for that data.
    3. Compute FSS rXX for that date
    4. For the domains that need the date, insert the line.
"""


import os
from datetime import datetime, timedelta
import numpy as np

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')


from BB_HRRR.GLM_and_HRRR.GLM_events_HRRR import get_GLM_HRRR_contingency_stats,\
                                                 m, Hlat, Hlon, domains
from BB_HRRR.GLM_and_HRRR.fractions_skill_score_SPECIAL import fractions_skill_score_SPECIAL


def refill_dates(DOM, month, hour, radius):
    ## 1. For a date, is it missing in the files?
    ## ============================================================================
    ## List the expected DATES
    sDATE = datetime(2018, month, 1, hour)
    if month != 12:
        eDATE = datetime(2018, month+1, 1, hour)
    else:
        eDATE = datetime(2018+1, 1, 1, hour)
    expected_DATES = np.array([sDATE+timedelta(days=d) for d in range((eDATE-sDATE).days)])

    for expected_DATE  in expected_DATES:
        # Keep track of which domain needs the data inserted.
        # `needed` will be populated with True/False. It has the same size and
        # order as `DOM`.
        # Location is the index the data needs to be inserted at
        needed = [] 
        location = []
        for domain in DOM:
            # Get the file we are interested in:
            DIR = './HRRR_GLM_Fractions_Skill_Score_r%02d/%s/' % (radius, domain)
            FILE = '%s_2018_m%02d_h%02d.csv' % (domain, month, hour)
            #
            # Does the file exist?
            if os.path.exists(DIR+FILE):
            #    print('The File Exists %s' % (DIR+FILE))
                # Load the dates
                list_DATES = np.genfromtxt(DIR+FILE, delimiter=',', names=True, encoding='UTF-8', dtype=None)['DATE']
                if np.shape(list_DATES) == ():
                    print('no shape!!!')
                else:
                    DATES = np.array([])
                    for D in list_DATES:
                        try:
                            DATE_fmt = '%Y-%m-%d %H:%M:%S'
                            DATES = np.append(DATES, datetime.strptime(D, DATE_fmt))
                        except:        
                            DATE_fmt = '%m/%d/%Y %H:%M'
                            DATES = np.append(DATES, datetime.strptime(D, DATE_fmt))
                #
                # Is the expected date in the current file?
                in_file = expected_DATE in DATES
                needed.append(not in_file)
                if not in_file:
                    # What is index of previous date? We want to insert after that...
                    loc = np.argwhere(expected_DATE-timedelta(days=1) == DATES)
                    if np.size(loc)==0:
                        location.append(len(DATES))
                    else:
                        location.append(loc[0][0])
                else:
                    location.append(np.nan)
        #print(needed)
        #print(location)
        #
        if any(needed):
            #
            ## 2. Get grid for data
            ## ========================================================================
            # Get the binary tables
            stats = get_GLM_HRRR_contingency_stats(expected_DATE)
            obs_binary = stats.get("Observed Binary")
            fxx_binary = stats.get("Forecast Binary")
            #
            ## 3. Compute FSS rXX for that date
            ## ========================================================================
            # Compute FSS
            FSS = fractions_skill_score_SPECIAL(obs_binary, fxx_binary, domains, radius=radius)
            #
            ## 4. Insert the line =========================================================
            ## ============================================================================
            for need, loc, domain in zip(needed, location, DOM):
                if need:
                    print('Refill', expected_DATE, loc, domain)
                    # Open the file for the domain and read all the lines
                    DIR = './HRRR_GLM_Fractions_Skill_Score_r%02d/%s/' % (radius, domain)
                    FILE = '%s_2018_m%02d_h%02d.csv' % (domain, month, hour)
                    f = open(DIR+FILE, "r")
                    contents = f.readlines()
                    f.close()
                    # Format the FSS data into a line to insert into the file...
                    filler = ','.join(np.array(np.round(FSS[domain], 4), dtype=str))
                    line = expected_DATE.strftime(DATE_fmt)+","+filler
                    #
                    # Insert the line. Loc position is +2 to account for header row
                    #                  and insert *after* last line
                    contents.insert(loc+2, '%s\n' % line)
                    #
                    # Write the new file with the inserted line.
                    f = open(DIR+FILE, "w")
                    contents = "".join(contents)
                    f.write(contents)
                    f.close()

if __name__=='__main__':
    DOM = ['HRRR', 'West', 'Central', 'East', 'Utah', 'Colorado', 'Texas', 'Florida']

    #for radius in [5, 10, 20, 40, 60]:
    for radius in [60,80]:
        for month in range(5,11):
            for hour in range(0,24):
                print(DOM, month, hour, radius)
                refill_dates(DOM, month, hour, radius)





