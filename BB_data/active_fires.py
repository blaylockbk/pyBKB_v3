# Brian Blaylock
# Version 3.0 update
# July 3, 2018

"""
Functions for downloading data related to active wildland fires

    get_fires                         - Return dictionary of fires from Active
                                        Fire Mapping Program.
    get_incidents                     - Return dictionary of fires from
                                        InciWeb.
    download_latest_fire_shapefile    - Download point data for fire and smoke.
    download_fire_perimeter_shapefile - Downloads the current fire perimeters. 
"""

import numpy as np 
from datetime import datetime, timedelta
import requests
from xml.etree import ElementTree
from urllib.request import urlretrieve
import os
import zipfile


def get_fires(DATE=datetime.utcnow(),
              min_size=1000, max_size=3000000,
              west_of=-100,
              AK=False, HI=False,
              verbose=True):
    """
    Returns a dictionary of fire information from the Active Fire Mapping Program
        i.e. https://fsapps.nwcg.gov/afm/data/lg_fire/lg_fire_info_2016-06-01.txt
    
    column names:
      0  INAME      - Incident Name
      1  INUM       - Incident Number
      2  CAUSE      - Cause of Fire
      3  REP_DATE   - Reported date
      4  START_DATE - Start date
      5  IMT_TYPE   - Incident Management Team Type. 5:local, 4:city, 3:state, 2:National+State, 1:National+State
      6  STATE      - State
      7  AREA       - Fire area in acres
      8  P_CNT      - Percent Contained
      9  EXP_CTN    - Expected Containment
      10 LAT        - Latitude of fire start location
      11 LON        - Longitude of fire start location
      12 COUNTY

    Input:
        DATE     - Datetime object. Defaults to the current utc datetime.
        min_size - The minimum fire size in acres.
        max_size - The maximum fire size in acres (hurricanes are sometimes
                   shown in the list).
        west_of  - The western boundary of fires. Default -100 ignores fires on
                   the East coast.
        AK       - False: do not include fires from Alaska (default)
                   True:  include fires from Alaska
        HI       - False: do not include fires from Hawaii (default)
                   True:  include fires from Hawaii
        verbose  - True: print some stuff to the screen (default)
                   False: do not print some stuff
    """
    # Build URL and make request
    URL = 'https://fsapps.nwcg.gov/afm/data/lg_fire/lg_fire_info_%s.txt' % DATE.strftime('%Y-%m-%d')
    r = requests.get(URL)

    # If it doesn't exist, try yesterday, else return an error
    if not r.ok:
        DATE = DATE - timedelta(days=1)
        URL = 'https://fsapps.nwcg.gov/afm/data/lg_fire/lg_fire_info_%s.txt' % DATE.strftime('%Y-%m-%d')
        r = requests.get(URL)
        if verbose:
            print("The date you requested wasn't available, so I got you %s instead." % DATE)

    if r.ok:
        # Initialize the return dictionary
        return_this = {'DATE':DATE,
                       'URL':URL,
                       'FIRES':{}}

        # Fill the FIRES key with a dictionary of each fire information
        for i, line in enumerate(r.text.split('\r\n')):
            F = line.split('\t')
            if line=='' or i==0 or int(F[7]) < min_size or int(F[7]) > max_size:
                continue # Skip header, small fires, and large fires
            if AK is False and F[6] == 'Alaska':
                continue # Skip Alaska
            if HI is False and F[6] == 'Hawaii':
                continue # Skip Hawaii
            if float(F[11]) > west_of:
                continue # Skip fires east of the west longitude

            return_this['FIRES'][F[0]] = {'incident number': F[1],
                                          'cause': F[2],
                                          'report date': datetime.strptime(F[3], '%d-%b-%y') if F[3] != 'Not Reported' else 'Not Reported',
                                          'start date': datetime.strptime(F[4], '%d-%b-%y') if F[4] != 'Not Reported' else 'Not Reported',
                                          'IMT Type': F[5],
                                          'state': F[6],
                                          'area': int(F[7]),
                                          'percent contained': F[8],
                                          'expected containment': datetime.strptime(F[9], '%d-%b-%y')  if F[9] != 'Not Reported' else 'Not Reported',
                                          'LAT': float(F[10]),
                                          'LON': float(F[11]),
                                          'is MesoWest': False} # MesoWest station ID if you want to include the observed data in plot
        if verbose:
            print('Got fire data from Active Fire Mapping Program: %s' % URL)

        return return_this

    else:
        if verbose:
            print('  !! URL NOT AVAILABLE: %s' % URL)
        return 'URL NOT AVAILABLE'


def get_incidents(inctype="Wildfire",
                  recent_days=2,
                  limit_num=10,
                  west_of=-100,
                  verbose=True):
    '''
    Return a dictionary of incidents from InciWeb XML RSS in the same format
    as get_fires().
        https://inciweb.nwcg.gov/feeds/rss/incidents/
    
    Note: InciWeb only includes lat/lon of each incident and does not include
          size of incident or location by state (thus you can't filter by fire
          size or remove Alaska and Hawaii incidents). If there are two
          fires with the same name, one incident will be overwitten.
    
    Input:
        inctype     - The type of incident.
                        'Wildfire' (default)
                        'Prescribed Fire'
                        'Flood'
                        'Burned Area Emergency Response'
        recent_days - Limit incidents to those published within the recent days.
                      Default is set to 2 that that only incidents updated in
                      the last two days are returned.
        limit_num   - Limit the number of incidents to return.
        west_of     - The western boundary of fires. Default -100 ignores fires
                      on East coast.
        verbose     - True: print some stuff to the screen (default)
    '''
    # Built URL and make request
    URL = 'https://inciweb.nwcg.gov/feeds/rss/incidents/'
    xml = requests.get(URL)
    
    # Parse the xml data
    tree = ElementTree.fromstring(xml.content)

    # Refer to the 'channel' branch and get all items
    items = [i for i in tree.find('channel') if i.tag == 'item']

    # Initialize the 
    return_this = {'DATE':datetime.now(),
                   'URL':URL,
                   'FIRES':{}}

    for i in items:
        if len(return_this.keys()) >= limit_num:
            continue
        try:
            # Only grab fires updated in within recent_dates
            published = i.find('published').text
            DATE = datetime.strptime(published[5:22], "%d %b %Y %H:%M")
            if DATE > datetime.utcnow()-timedelta(days=recent_days):
                # Only grab requested incident type
                title = i.find('title').text
                if title.split(' ')[-1] == '(%s)' % inctype:
                    # Remove unnecessary names from title
                    title = title.replace(' Fire (%s)' % inctype, '')
                    title = title.replace(' Fire  (%s)' % inctype, '')
                    title = title.replace(' (%s)' % inctype, '')
                    title = title.replace('  (%s)' % inctype, '')
                    title = title.upper()
                    lat, lon = i.find('{http://www.georss.org/georss}point').text.split(' ')
                    if float(lon) <= west_of:
                        return_this['FIRES'][title] = {'incident number': np.nan,
                                                       'cause': np.nan,
                                                       'report date': np.nan,
                                                       'start date': np.nan,
                                                       'IMT Type': np.nan,
                                                       'state': np.nan,
                                                       'area': np.nan,
                                                       'percent contained': np.nan,
                                                       'expected containment': np.nan,
                                                       'LAT': float(lat),
                                                       'LON': float(lon),
                                                       'is MesoWest': False} 
        except:
            print("XLM !ERROR!, had to skip an incident. Probably a bad lat/lon??")
            continue

    if verbose:
            print('Got fire data from InciWeb: %s' % URL)   

    return return_this


def download_latest_fire_shapefile(TYPE='fire'):
    """
    Download active fire shapefiles from the web.
    Points of active fire.
    Original Script from '/uufs/chpc.utah.edu/host/gl/oper/mesowest/fire/get_fire.csh'
    Input:
        TYPE - 'fire' or 'smoke'
    """
    URL = 'http://satepsanone.nesdis.noaa.gov/pub/FIRE/HMS/GIS/'
    SAVE = '/uufs/chpc.utah.edu/common/home/u0553130/oper/HRRR_fires/fire_shapefiles/'
    NAME = 'latest_' + TYPE
    urlretrieve(URL+NAME+".dbf", SAVE+NAME+".dbf")
    urlretrieve(URL+NAME+".shp", SAVE+NAME+".shp")
    urlretrieve(URL+NAME+".shx", SAVE+NAME+".shx")


def download_fire_perimeter_shapefile(active=True):
    """
    Download active fire perimeter shapefiles.
    
    Input:
        active - True  : Download the current active fire perimeters
                 False : Download all perimeters from the current year
    """
    ## Download zip file
    URL = 'http://rmgsc.cr.usgs.gov/outgoing/GeoMAC/current_year_fire_data/current_year_all_states/'
    if active:
        NAME = 'active_perimeters_dd83.zip'
    else:
        NAME = 'perimeters_dd83.zip'
    SAVE = '/uufs/chpc.utah.edu/common/home/u0553130/oper/HRRR_fires/fire_shapefiles/'
    urlretrieve(URL+NAME, SAVE+NAME)
    ## Unzip the file
    zip_ref = zipfile.ZipFile(SAVE+NAME, 'r')
    zip_ref.extractall(SAVE)
    zip_ref.close()
    ## Remove the zip file
    os.remove(SAVE+NAME)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap

    import sys
    sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
    from BB_maps.my_basemap import draw_HRRR_map

    AFMP = get_fires()
    InciWeb = get_incidents(limit_num=100)

    # Plot fires from AFMP and InciWeb
    m = draw_HRRR_map()

    plt.figure(figsize=[10,6])

    plt.title('Fires', loc='left', fontweight='semibold')
    plt.title('InciWeb Fires (Black)\nActive Fire MapPing Program (Orange)', loc='right')
    for k, v in AFMP['FIRES'].items():
        m.scatter(v['LON'], v['LAT'],
                s=25, c='orangered', edgecolors='none', latlon=True)

    for k, v in InciWeb['FIRES'].items():
        m.scatter(v['LON'], v['LAT'],
                s=25, edgecolors=[.2,.2,.2], facecolor='none', latlon=True)

    m.drawstates()
    m.drawcountries()
    m.drawcoastlines()

    plt.show()
