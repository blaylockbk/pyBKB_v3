# Brian Blaylock
# Version 3.0 update
# June 21, 2018

"""
Quickly get data from the MesoWest/SynopticLabs API.
    https://synopticlabs.org/api/mesonet/

Requires a MesoWest/SynopticLabs API token. You can get your own token here:
    https://synopticlabs.org/api/guides/?getstarted

    load_json                - Basic function to load json 
    get_network_ids          - Return ID numbers for list of network shortnames.
    get_mesowest_ts          - Get a time series of data for a single station. 
    get_mesowest_radius      - Get lists of data from stations within a radius.
    get_mesowest_stninfo     - Get a dictionary of each station's metadata
    get_mesowest_percentiles - Get a series of observed percentiles for a
                               station OR get an Empirical Cumulative
                               Distribution for a series of hours.
"""

from datetime import datetime
import numpy as np
import requests
import pandas as pd

import sys
from .get_credentials import get_MW_token

from BB_wx_calcs.wind import spddir_to_uv

# Review MesoWest API documentation for the available variable names:
#   https://synopticlabs.org/api/mesonet/variables/
default_vars = 'altimeter,' \
             + 'pressure,' \
             + 'sea_level_pressure,' \
             + 'wind_direction,' \
             + 'wind_speed,' \
             + 'wind_gust,' \
             + 'air_temp,' \
             + 'relative_humidity,' \
             + 'dew_point_temperature'


def load_json(URL, verbose=True):
    '''Return json data as a dictionary from a URL'''
    if verbose:
        print('\nRetrieving from MesoWest API: %s\n' % URL)
    
    f = requests.get(URL)
    return f.json()

def get_network_ids(network_names='nws/faa,raws', verbose=True):
    """
    Return the network ID numbers for a list of network shortnames.
    
    Input:
        network_shortname - A comma separated list of network short names. 
                            Default is 'nws,raws'
    """
    URL = 'https://api.synopticlabs.org/v2/networks?' \
        + '&token=' + get_MW_token() \
        + '&shortname=' + network_names

    data = load_json(URL, verbose=verbose)

    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        return ','.join([i['ID'] for i in data['MNET']])

    else:
        # There were errors in the API request
        if verbose:
            print('  !! Errors: %s' % URL)
            print('  !! Reason: %s\n' % data['SUMMARY']['RESPONSE_MESSAGE'])
        return 'ERROR'
    

def get_mesowest_ts(stationID, sDATE, eDATE,
                    variables=default_vars, tz='UTC', set_num=0, verbose=True):
    """
    Get MesoWest Time Series

    Makes a time series query from the MesoWest API for a single station.

    Input:
        stationID  - String of the station ID (a single station)
        sDATE      - datetime object of the start time in UTC
        eDATE      - datetime object of the end time in UTC
        variables  - String of variables you want to request from the MesoWest
                     API, separated by commas. See a list of available variables
                     here: https://synopticlabs.org/api/mesonet/variables/
        tz         - Time stamp option, either 'UTC' or 'LOCAL'
        set_num    - Some stations have multiple sensors and are stored in 
                     a different 'set'. By default, grab the first set. You 
                     can change this integer if you know your staion has more
                     than one set for a particular variable. Best if used if
                     only requesting a single variable. Knowing what each set
                     is requires knowledge of the station and how the sensor 
                     variables are stored in the MesoWest database.
        verbose    - True: Print some diagnostics
                     False: Don't print anything

    Output:
        The time series data for the requested station as a dictionary.
    """

    ## Some basic checks
    assert isinstance(stationID, str), 'stationID must be a string'
    assert isinstance(sDATE, datetime) and isinstance(eDATE, datetime), 'sDATE and eDATE must be a datetime'
    assert tz.upper() in ['UTC', 'LOCAL'], "tz must be either 'UTC' or 'LOCAL'"
    assert set_num >=0 and isinstance(set_num, int), "set_num must be a positive integer"

    ## Build the MesoWest API request URL
    URL = 'http://api.mesowest.net/v2/stations/timeseries?' \
        + '&token=' + get_MW_token() \
        + '&stid=' + stationID \
        + '&start=' + sDATE.strftime("%Y%m%d%H%M") \
        + '&end=' + eDATE.strftime("%Y%m%d%H%M") \
        + '&vars=' + variables \
        + '&obtimezone=' + tz \
        + '&output=json'

    ## Open URL, and convert JSON to some python-readable format.
    data = load_json(URL, verbose=verbose)

    assert data['SUMMARY']['RESPONSE_CODE'] == 1, f"There were errors in the API request {URL}. {data['SUMMARY']['RESPONSE_MESSAGE']}"
    
    ## Grab the content we are interested in
    df = pd.DataFrame()

    # Station metadata
    stn = data['STATION'][0]
    df.attrs['URL'] = URL
    df.attrs['NAME'] = str(stn['NAME'])
    df.attrs['STID'] = str(stn['STID'])
    df.attrs['LAT'] = float(stn['LATITUDE'])
    df.attrs['LON'] = float(stn['LONGITUDE'])
    df.attrs['ELEVATION'] = float(stn['ELEVATION'])
                               # Note: Elevation is in feet, NOT METERS!

    # Dynamically create keys in the dictionary for each requested variable
    for v in stn['SENSOR_VARIABLES']:
        if verbose: print('v is: %s' % v)
        if v == 'date_time':
            # Convert date strings to a datetime object
            dates = data["STATION"][0]["OBSERVATIONS"]["date_time"]
            if tz == 'UTC':
                DATES = [datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ') for i in dates]
            else:
                DATES = [datetime.strptime(i[:-5], '%Y-%m-%dT%H:%M:%S') for i in dates]
                df.attrs['UTC-offset'] = [i[-5:] for i in dates]
            df['DATETIME'] = DATES
        else:
            # Each variable may have more than one "set", like if a station 
            # has more than one sensor. Deafult, set_num=0, will grab the
            # first (either _set_1 or _set_1d).
            key_name = str(v)
            grab_this_set = np.sort(list(stn['SENSOR_VARIABLES'][key_name]))[set_num]
            if verbose:
                print('    Used %s' % grab_this_set)
            variable_data = stn['OBSERVATIONS'][grab_this_set]
            df[key_name] = np.array(variable_data, dtype=np.float)

    if all(['wind_speed' in df, 'wind_direction' in df]):
        # Break wind into U and V components
        u, v = spddir_to_uv(df['wind_speed'], df['wind_direction'])
        df['wind_u'] = u
        df['wind_v'] = v
            
    return df.set_index('DATETIME')


def get_mesowest_radius(DATE, location,
                        radius=30, within=30,
                        variables=default_vars,
                        extra = '',
                        set_num=0,
                        verbose=True):
    """
    Get MesoWest stations within a radius

    Get data from all stations within a radius around a station ID or a 
    latitude,longitude point from the MesoWest API.

    Input:
        DATE      - datetime object of the time of interest in UTC
        location  - String of a MW station ID or string of a comma-separated
                    lat,lon as the center (i.e. 'WBB' or '40.0,-111.5')
                    HACK: If [location=None] then the radius limit is
                          disregarded and returns all stations. Therefore, it
                          is best used in congunction with the [extra=&...]
                          argument.
        radius    - Distance from center location in *MILES*.
                    Default is 30 miles.
        within    - *MINUTES*, plus or minus, the DATE to get for.
                    Default returns all observations made 30 minutes before and
                    30 minutes after the requested DATE.
        variables - String of variables you want to request from the MesoWest
                    API, separated by commas. See a list of available variables
                    here: https://synopticlabs.org/api/mesonet/variables/
        extra     - Any extra conditions or filters. Refer to the synoptic API
                    documentation for more info. String should be proceeded by
                    a "&". For example, to get stations within a specific 
                    set of networks, use [extra='&network=1,2']
        set_num   - Some stations have multiple sensors and are stored in 
                    a different 'set'. By default, grab the first set. You 
                    can change this integer if you know your staion has more
                    than one set for a particular variable. Best if used if
                    only requesting a single variable. Knowing what each set
                    is requires knowledge of the station and how the sensor 
                    variables are stored in the MesoWest database.
        verbose   - True: Print some diagnostics
                    False: Don't print anything

    Output:
        A dictionary of data at each available station.
    """
    ## Some basic checks
    assert isinstance(location, (str,type(None))), 'location must be a string or None'
    assert isinstance(DATE, datetime), 'DATE must be a datetime'
    assert set_num >=0 and isinstance(set_num, int), "set_num must be a positive integer"

    ## Build the MesoWest API request URL
    if location is None:
        if extra == '':
            if verbose:
                    print('  !! Errors:')
                    print("  !! Reason: I don't think you really want to return everything.")
                    print("             Refine your request using the 'extra=&...' argument")
            return 'ERROR'
        URL = 'http://api.mesowest.net/v2/stations/nearesttime?' \
            + '&token=' + get_MW_token() \
            + '&attime=' + DATE.strftime("%Y%m%d%H%M") \
            + '&within=' + str(within) \
            + '&obtimezone=' + 'UTC' \
            + '&vars=' + variables \
            + extra
    else:
        URL = 'http://api.mesowest.net/v2/stations/nearesttime?' \
            + '&token=' + get_MW_token() \
            + '&attime=' + DATE.strftime("%Y%m%d%H%M") \
            + '&within=' + str(within) \
            + '&radius=' + '%s,%s' % (location, radius) \
            + '&obtimezone=' + 'UTC' \
            + '&vars=' + variables \
            + extra

    ## Open URL, and convert JSON to some python-readable format.
    data = load_json(URL, verbose=verbose)
    
    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        # Initiate a dictionary of the data we want to keep
        return_this = {'URL': URL,
                       'NAME': np.array([]),
                       'STID': np.array([]),
                       'LAT': np.array([]),
                       'LON': np.array([]),
                       'ELEVATION': np.array([]),  # Elevation is in feet.
                       'DATETIME': DATE
                      }
        #
        # Create a new key for each possible variable
        for v in data['UNITS']:
            return_this[str(v)] = np.array([])
            # Since some observation times for each variables at the same station
            # *could* be different, I will store the datetimes from each variable
            # with a similar name as the variable.
            return_this[str(v) + '_DATETIME'] = np.array([])
        #
        for stn in data['STATION']:
            # Store basic metadata for each station in the dictionary.
            return_this['NAME'] = np.append(return_this['NAME'], str(stn['NAME']))
            return_this['STID'] = np.append(return_this['STID'], str(stn['STID']))
            return_this['LAT'] = np.append(return_this['LAT'], float(stn['LATITUDE']))
            return_this['LON'] = np.append(return_this['LON'], float(stn['LONGITUDE']))
            try:
                return_this['ELEVATION'] = np.append(return_this['ELEVATION'],
                                                     int(stn['ELEVATION']))
            except:
                return_this['ELEVATION'] = np.append(return_this['ELEVATION'], np.nan)
            #
            # Dynamically store data for all possible variable. If a station does
            # not have a variable, then a np.nan will be it's value.
            for v in data['UNITS']:
                if v in list(stn['SENSOR_VARIABLES']) and len(stn['OBSERVATIONS']) > 0:
                    # If value exists, then append with the data
                    grab_this_set = np.sort(list(stn['SENSOR_VARIABLES'][v]))[set_num]
                    variable_data = float(stn['OBSERVATIONS'][grab_this_set]['value'])
                    date_date = datetime.strptime(stn['OBSERVATIONS'][grab_this_set]['date_time'], '%Y-%m-%dT%H:%M:%SZ')
                    #
                    return_this[v] = \
                        np.append(return_this[v], variable_data)
                    return_this[v + '_DATETIME'] = \
                        np.append(return_this[v + '_DATETIME'], date_date)
                else:
                    if verbose:
                        print('%s is not available for %s' % (v, stn['STID']))
                    # If value doesn't exist, then append with np.nan
                    return_this[v] = \
                        np.append(return_this[v], np.nan)
                    return_this[v + '_DATETIME'] = \
                        np.append(return_this[v + '_DATETIME'], np.nan)

        return return_this

    else:
        # There were errors in the API request
        if verbose:
            print('  !! Errors: %s' % URL)
            print('  !! Reason: %s\n' % data['SUMMARY']['RESPONSE_MESSAGE'])
        return 'ERROR'


def get_mesowest_stninfo(STIDs, extra='', verbose=True):
    """
    Creates a Location Dictionary, where each key is a unique station id that 
    contains a dictionary including latitude, longitude, elevation, and other
    metadata.

    Input:
        STIDs    - A list of station IDs or a string of stations separated by
                   a comma.
        extra    - Any extra API arguments you want to attach to the URL.
        verbose  - True: Print some diagnostics
                   False: Don't print anything
    
    Returns a dictionary of dictionaries containing metadata for each station.
    """
    # API call requires list of stations to be comma separated. If a list is
    # the input, then convert it to a comma separted list.
    if isinstance(STIDs, list):
        STIDs = ','.join(STIDs)

    # Build the URL
    URL = 'http://api.mesowest.net/v2/stations/metadata?' \
        + '&token=' + get_MW_token() \
        + '&stid=' + STIDs \
        + extra

    ## Open URL, and convert JSON to some python-readable format.
    data = load_json(URL, verbose=verbose)

    assert data['SUMMARY']['RESPONSE_CODE'] == 1, f"There were errors in the API request {URL}. {data['SUMMARY']['RESPONSE_MESSAGE']}"
    
    ## Store the relevant information in a location dictionary.
    location_dict = {}

    for stn in data['STATION']:
        location_dict[stn['STID']] = {'latitude':float(stn['LATITUDE']),
                                    'longitude':float(stn['LONGITUDE']),
                                    'NAME':stn['NAME'],
                                    'ELEVATION':int(stn['ELEVATION']),
                                    'TIMEZONE': stn['TIMEZONE'],
                                    'STATUS': stn['STATUS'],
                                    'PERIOD_OF_RECORD': (datetime.strptime(stn['PERIOD_OF_RECORD']['start'], '%Y-%m-%dT%H:%M:%SZ'),
                                                         datetime.strptime(stn['PERIOD_OF_RECORD']['end'], '%Y-%m-%dT%H:%M:%SZ'))
                                    }
        
    df = pd.DataFrame(location_dict)
    df.attrs['URL'] = URL
    return df
    


def get_mesowest_percentiles(stn, variable='air_temp',
                             percentiles=[0,5,25,50,75,95,100],
                             sDATE = datetime(2016, 1, 1, 0),
                             eDATE = datetime(2016, 12, 31, 23),
                             psource='PERCENTILES2',
                             ECD = False, 
                             verbose=True):
    """
    Station history percentiles for a single station and single variable:
    Uses a 30 day window centered on the hour.
    Data at top of each hour of the year, including leap year.
    DATETIME returned is set to year 2016 to include leap year, but the data is
    is not limited to that year.
    
    Input:
        stn         - A single mesowest station ID.
        variables   - A single variable to request from the MesoWest
                      API. See a list of available variables here:
                      https://synopticlabs.org/api/mesonet/variables/
        percentiles - A list of percentiles to retrieve. Set to 'ALL' if you
                      want to retrieve all available percentiles.
        start       - Datetime object. Year is 2016 so it includes leap year,
                      but is otherwise arbitrary. Default is first day of year.
        end         - Datetime object. Year is 2016 so it includes leap year,
                      but is otherwise arbitrary. Default is last day of year.
        psource     - 'PERCENTILES2' or 'PERCENTILES_HRRR'
        ECD         - False: Returns percentiles as separate arrays for each
                             percentile. i.e. 'p00' is an array of all the 0th
                             percentiles for the range of dates,
                             'p50' is the 50th percentile, etc.
                      True : Returns percentiles as list that contains all
                             requested percentiles so you can easily plot the
                             Empirical Cumulative Distribution (ECD). This
                             makes most sense if you set percentiles='ALL'

    Output:
        A dictionary of station metadata and percentile information
    """

    if percentiles == 'ALL':
        get_percentiles = ''
    else:
        get_percentiles = '&percentiles=' + ','.join([str(p) for p in percentiles])

    URL = 'http://api.synopticlabs.org/v2/percentiles?' \
          + '&token=' + get_MW_token() \
          + '&start=' + sDATE.strftime('%m%d%H') \
          + '&end=' + eDATE.strftime('%m%d%H') \
          + '&vars=' + variable \
          + '&stid=' + stn \
          + '&psource=' + psource \
          + get_percentiles

    ## Open URL, and convert JSON to some python-readable format.
    data = load_json(URL, verbose=verbose) 
    
    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        stn = data['STATION'][0]

        return_this = {'URL': URL,
                       'STID': stn['STID'],
                       'NAME': stn['NAME'],
                       'ELEVATION': float(stn['ELEVATION']),
                       'LAT': float(stn['LATITUDE']),
                       'LON': float(stn['LONGITUDE']),
                       'variable': variable,
                       'counts': np.array(stn['PERCENTILES'][variable+'_counts_1'], dtype='int'),
                       'DATETIME': np.array([datetime(2016, int(DATE[0:2]), int(DATE[2:4]), int(DATE[4:6])) for DATE in stn['PERCENTILES']['date_time']],),
                       'PERCENTILES_LIST': np.array(data['PERCENTILE_LIST'])
                      }
        if psource == 'PERCENTILES2':
            return_this['years'] = np.array(stn['PERCENTILES'][variable+'_years_1'], dtype='int')

        if ECD:
            # Return the Empirical Cumulative Distribution for each DATETIME
            # Remove the last item from each array, which is the total count 
            # of observations, which we already returned.
            return_this['PERCENTILES'] = np.array([i[:-1] for i in stn['PERCENTILES'][variable+'_set_1']])
        else:
            # Return arrays of each percentile in the key 'p00', 'p25', etc.
            all_per = np.array(stn['PERCENTILES'][variable+'_set_1'])
            for i, p in enumerate(data['PERCENTILE_LIST']):
                return_this['p%02d' % p] = all_per[:,i]
                
        return return_this
    else:
        # There were errors in the API request
        if verbose:
            print('  !! Errors: %s' % URL)
            print('  !! Reason: %s\n' % data['SUMMARY']['RESPONSE_MESSAGE'])
        return 'ERROR'


def get_mesowest_network(network='1,2'):
    """Get list of station locations by network"""
    URL = 'http://api.mesowest.net/v2/stations/metadata?' \
        + '&token=' + get_MW_token() \
        + '&network=%s' % network
    NWS = load_json(URL)

    return {'LON': np.array([stn['LONGITUDE'] for stn in NWS['STATION']], dtype=float),        
            'LAT': np.array([stn['LATITUDE'] for stn in NWS['STATION']], dtype=float),
            'NAME': np.array([stn['NAME'] for stn in NWS['STATION']]),
            'STID': np.array([stn['STID'] for stn in NWS['STATION']])}


if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    # Get MesoWest data from functin above
    station = 'WBB'
    start = datetime(2016, 9, 25)
    end = datetime(2016, 9, 26)

    demo_timeseries = True
    demo_radius_basemap = True
    demo_radius_cartopy = True
    demo_stn_info = True
    demo_percentiles = True

    if demo_timeseries:
        a = get_mesowest_ts(station, start, end)

        temp = a['air_temp']
        RH = a['relative_humidity']
        dates = a['DATETIME']

        # Make a quick temperature and relative humidity plot
        fig, ax1 = plt.subplots(figsize=(8, 4))
        plt.title(station.upper())
        plt.xticks(rotation=30)
        
        ax1.plot(dates, temp, 'r-')
        ax1.set_xlabel('Date Time UTC')
        ax1.set_ylabel('Temperature (c)', color='r')
        ax1.tick_params('y', colors='r')

        ax2 = ax1.twinx()
        ax2.plot(dates, RH, 'g')
        ax2.set_ylabel('Relative Humidity', color='g')
        ax2.tick_params('y', colors='g')

        fig.tight_layout()
        
    
    if demo_radius_basemap or demo_radius_cartopy:
        a = get_mesowest_radius(start, 'wbb', radius=30, within=30)
        
        if demo_radius_basemap:
            from mpl_toolkits.basemap import Basemap      
            
            plt.figure(figsize=[7, 7])
            center_lat  = np.nanmean(a['LAT'])
            center_lon  = np.nanmean(a['LON'])
            box = 0.5 # degrees latitude to represent map half-box size 

            m = Basemap(projection='cyl',
                        llcrnrlon=center_lon-box, llcrnrlat=center_lat-box,
                        urcrnrlon=center_lon+box, urcrnrlat=center_lat+box)

            m.drawstates()
            m.drawcounties()
            m.arcgisimage(service='World_Shaded_Relief')
            sc = m.scatter(a['LON'], a['LAT'], c=a['air_temp'], cmap='Spectral_r', latlon=True)
            plt.colorbar(sc, pad=.01, shrink=.8)
        
        if demo_radius_cartopy:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            
            import sys
            sys.path.append('C:\\Users\\blaylockbk\\OneDrive\\Documents\\pyBKB_v3') # When on my PC
            sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')    # When on CHPC
            from BB_maps.my_cartopy import load_states, load_counties

            projection = ccrs.PlateCarree()

            states = load_states(projection)
            counties = load_counties(projection)

            fig = plt.figure(figsize=[7, 7])
            ax = fig.add_subplot(111, projection=projection)
            ax.add_feature(counties, edgecolor='k', linewidth=.3)
            ax.add_feature(states, edgecolor='k', linewidth=1)
            ax.set_extent([a['LON'].min(), a['LON'].max(), a['LAT'].min(), a['LAT'].max()], projection)
            sc = ax.scatter(a['LON'], a['LAT'], c=a['air_temp'], cmap='Spectral_r')
            plt.colorbar(sc, pad=.01, shrink=.5)


    if demo_stn_info:
        c = get_mesowest_stninfo(['wbb','ukbkb'])
        print(c)
    

    if demo_percentiles:
        d = get_mesowest_percentiles('WBB', variable='air_temp')

        # Plot max and min range for every hour (plot everything)
        fig, ax1 = plt.subplots(figsize=(8, 4))
        plt.title(d['NAME'], loc='left', fontweight='semibold')
        plt.title('Hourly Range', loc='right')
        plt.fill_between(d['DATETIME'],d['p00'],d['p100'])
        plt.ylabel('Air Temperature (C)')

        # Plot a "box and whisker" for a single hour
        hour = 18
        fig, ax1 = plt.subplots(figsize=(8, 4))
        plt.title(d['NAME'], loc='left', fontweight='semibold')
        plt.title('Hour %02d:00 UTC' % hour, loc='right')

        plt.grid(linestyle='--', alpha=.5)        
        plt.fill_between(d['DATETIME'][hour::24],d['p05'][hour::24],d['p95'][hour::24],
                         color=[.6,.6,.6], zorder=5)
        plt.fill_between(d['DATETIME'][hour::24],d['p25'][hour::24],d['p75'][hour::24],
                         color=[.3,.3,.3], zorder=5)
        plt.plot(d['DATETIME'][hour::24],d['p50'][hour::24],
                 linestyle='--', color=[.6,.6,.6], zorder=5)
        plt.plot(d['DATETIME'][hour::24],d['p100'][hour::24],
                 linestyle='--', color=[.6,.6,.6], zorder=5)
        plt.plot(d['DATETIME'][hour::24],d['p00'][hour::24],
                 linestyle='--', color=[.6,.6,.6], zorder=5)
        
        plt.ylabel('Air Temperature (C)')
        plt.xlim(d['DATETIME'][0], d['DATETIME'][-1])
        formatter = DateFormatter('%b-%d')
        plt.gcf().axes[0].xaxis.set_major_formatter(formatter)

        # Plot an Empirical Cumulative Distribution for a single time
        e = get_mesowest_percentiles('WBB',
                                     percentiles='ALL',
                                     sDATE=datetime(2018, 7, 4, 18),
                                     eDATE=datetime(2018, 7, 4, 18),
                                     variable='air_temp',
                                     ECD=True)        
        fig, ax1 = plt.subplots(figsize=(6, 4))
        idx = 0
        plt.plot(e['PERCENTILES_LIST'], e['PERCENTILES'][idx])
        plt.title(e['STID'], loc='left', fontweight='semibold')
        plt.title(e['DATETIME'][idx].strftime('%d %B %H:%M UTC'), loc='right')
        plt.xticks(e['PERCENTILES_LIST'], [0,'','','','','', 10, 25, 33, 50, 66, 75, 90, '', '', '', '','',100])
        plt.grid(linestyle='--', alpha=.5)
        plt.xlim([0,100])
        plt.xlabel('Percentile')
        plt.ylabel('Air Temperature')

    plt.show()
