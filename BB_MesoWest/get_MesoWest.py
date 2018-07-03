# Brian Blaylock
# Version 3.0 update
# June 21, 2018

"""
Quickly get data from the MesoWest API.
    https://synopticlabs.org/api/mesonet/

Get your own MesoWest API key and token from https://mesowest.org/api/signup/

    get_mesowest_ts         - get a time series of data for a single station 
    get_mesowest_radius     - get data from stations within a radius
    get_mesowest_stninfo    - get a dictionary of each station's metadata
    get_mesowest_perceniles - get a series of observed percentiles for a station
"""

from datetime import datetime
import numpy as np
import json
import urllib3

from get_credentials import get_MW_token


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
    
    http = urllib3.PoolManager()
    f = http.request('GET', URL)
    return json.loads(f.data)


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

    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        # There are no errors in the API Request

        ## Grab the content we are interested in
        return_this = {}

        # Station metadata
        return_this['URL'] = URL
        return_this['NAME'] = str(data['STATION'][0]['NAME'])
        return_this['STID'] = str(data['STATION'][0]['STID'])
        return_this['LATITUDE'] = float(data['STATION'][0]['LATITUDE'])
        return_this['LONGITUDE'] = float(data['STATION'][0]['LONGITUDE'])
        return_this['ELEVATION'] = float(data['STATION'][0]['ELEVATION'])
                                   # Note: Elevation is in feet, NOT METERS!

        # Dynamically create keys in the dictionary for each requested variable
        for v in data['STATION'][0]['SENSOR_VARIABLES']:
            if v == 'date_time':
                # Convert date strings to a datetime object
                dates = data["STATION"][0]["OBSERVATIONS"]["date_time"]
                if tz == 'UTC':
                    DATES = [datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ') for i in dates]
                else:
                    DATES = [datetime.strptime(i[:-5], '%Y-%m-%dT%H:%M:%S') for i in dates]
                    return_this['UTC-offset'] = [i[-5:] for i in dates]
                return_this['DATETIME'] = DATES
            else:
                # Each variable may have more than one "set", like if a station 
                # has more than one sensor. Deafult, set_num=0, will grab the
                # first (either _set_1 or _set_1d).
                key_name = str(v)
                grab_this_set = np.sort(list(data['STATION'][0]['SENSOR_VARIABLES'][key_name]))[set_num]                
                if verbose: 
                    print('    Used %s' % grab_this_set)
                variable_data = data['STATION'][0]['OBSERVATIONS'][grab_this_set]
                return_this[key_name] = np.array(variable_data, dtype=np.float)
        
        return return_this

    else:
        # There were errors in the API request
        if verbose:
            print('  !! Errors: %s' % URL)
            print('  !! Reason: %s\n' % data['SUMMARY']['RESPONSE_MESSAGE'])
        return 'ERROR'


def get_mesowest_radius(DATE, location,
                        radius=30, within=30,
                        variables=default_vars, set_num=0,
                        verbose=True):
    """
    Get MesoWest stations within a radius

    Get data from all stations within a radius around a station ID or a 
    latitude,longitude point from the MesoWest API.

    Input:
        DATE      - datetime object of the time of interest in UTC
        location  - String of a MW station ID or string of a comma-separated
                    lat,lon as the center (i.e. 'WBB' or '40.0,-111.5')
        radius    - Distance from center location in MILES. Default is 30 miles.
        within    - Minutes, plus or minus, the DATE to get for. Deafult 
                    will get all observations made 30 minutes before and
                    30 minutes after the requested DATE.
        variables - String of variables you want to request from the MesoWest
                    API, separated by commas. See a list of available variables
                    here: https://synopticlabs.org/api/mesonet/variables/
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
    assert isinstance(location, str), 'location must be a string'
    assert isinstance(DATE, datetime), 'DATE must be a datetime'
    assert set_num >=0 and isinstance(set_num, int), "set_num must be a positive integer"

    ## Build the MesoWest API request URL
    URL = 'http://api.mesowest.net/v2/stations/nearesttime?' \
        + '&token=' + get_MW_token() \
        + '&attime=' + DATE.strftime("%Y%m%d%H%M") \
        + '&within=' + str(within) \
        + '&radius=' + '%s,%s' % (location, radius) \
        + '&obtimezone=' + 'UTC' \
        + '&vars=' + variables

    ## Open URL, and convert JSON to some python-readable format.
    data = load_json(URL, verbose=verbose)
    
    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        # Initiate a dictionary of the data we want to keep
        return_this = {'URL': URL,
                       'NAME': np.array([]),
                       'STID': np.array([]),
                       'LATITUDE': np.array([]),
                       'LONGITUDE': np.array([]),
                       'ELEVATION': np.array([]),  # Elevation is in feet.
                       'DATETIME': np.array([])
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
            return_this['LATITUDE'] = np.append(return_this['LATITUDE'], float(stn['LATITUDE']))
            return_this['LONGITUDE'] = np.append(return_this['LONGITUDE'], float(stn['LONGITUDE']))
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

    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        ## Store the relevant information in a location dictionary.
        location_dict = {}

        for i in data['STATION']:
            location_dict[i['STID']] = {'LATITUDE':float(i['LATITUDE']),
                                        'LONGITUDE':float(i['LONGITUDE']),
                                        'NAME':i['NAME'],
                                        'ELEVATION':int(i['ELEVATION']),
                                        'TIMEZONE': i['TIMEZONE'],
                                        'STATUS': i['STATUS'],
                                        'PERIOD_OF_RECORD': (datetime.strptime(i['PERIOD_OF_RECORD']['start'], '%Y-%m-%dT%H:%M:%SZ'),
                                                             datetime.strptime(i['PERIOD_OF_RECORD']['end'], '%Y-%m-%dT%H:%M:%SZ'))
                                        }
        return location_dict
    else:
        # There were errors in the API request
        if verbose:
            print('  !! Errors: %s' % URL)
            print('  !! Reason: %s\n' % data['SUMMARY']['RESPONSE_MESSAGE'])
        return 'ERROR'


def get_mesowest_percentiles(stn, variable='air_temp',
                             percentiles=[0,5,25,50,75,95,100],
                             start = '010100',
                             end = '123123',
                             psource='PERCENTILES2', 
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
        percentiles - A list of percentiles to retrieve. Set to 'ALL' if you want to
                      retrieve all available percentiles.
        start       - '010100' MMDDHH. Default is begining of the year.
        end         - '123123' MMDDHH. Default is the end of the year. 
        psource     - 'PERCENTILES2' or 'PERCENTILES_HRRR'

    Output:
        A dictionary of station metadata and percentile information
    """

    if percentiles == 'ALL':
        get_percentiles = ''
    else:
        get_percentiles = '&percentiles=' + ','.join([str(p) for p in percentiles])

    URL = 'http://api.synopticlabs.org/v2/percentiles?' \
          + '&token=' + get_MW_token() \
          + '&start=' + start \
          + '&end=' + end \
          + '&vars=' + variable \
          + '&stid=' + stn \
          + '&psource=' + psource \
          + get_percentiles

    ## Open URL, and convert JSON to some python-readable format.
    data = load_json(URL, verbose=verbose) 
    
    if data['SUMMARY']['RESPONSE_CODE'] == 1:
        d = data['STATION'][0]

        return_this = {'URL': URL,
                       'STID': d['STID'],
                       'NAME': d['NAME'],
                       'ELEVATION': float(d['ELEVATION']),
                       'LATITUDE': float(d['LATITUDE']),
                       'LONGITUDE': float(d['LONGITUDE']),
                       'variable': variable,
                       'counts': np.array(d['PERCENTILES'][variable+'_counts_1'], dtype='int'),
                       'DATETIME': np.array([datetime(2016, int(DATE[0:2]), int(DATE[2:4]), int(DATE[4:6])) for DATE in d['PERCENTILES']['date_time']])
                      }
        if psource == 'PERCENTILES2':
            return_this['years'] = np.array(d['PERCENTILES'][variable+'_years_1'], dtype='int')

        all_per = np.array(d['PERCENTILES'][variable+'_set_1'])
        for i, p in enumerate(data['PERCENTILE_LIST']):
            return_this['p%02d' % p] = all_per[:,i]
                
        return return_this
    else:
        # There were errors in the API request
        if verbose:
            print('  !! Errors: %s' % URL)
            print('  !! Reason: %s\n' % data['SUMMARY']['RESPONSE_MESSAGE'])
        return 'ERROR'


if __name__ == "__main__":

    import matplotlib.pyplot as plt

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
        
    
    if demo_radius_basemap:
        from mpl_toolkits.basemap import Basemap
        
        a = get_mesowest_radius(start, 'wbb', radius=30, within=30)
        
        plt.figure(figsize=[10,10])
        center_lat  = np.nanmean(a['LATITUDE'])
        center_lon  = np.nanmean(a['LONGITUDE'])
        box = 0.5 # degrees latitude to represent map half-box size 

        m = Basemap(projection='cyl',
                    llcrnrlon=center_lon-box, llcrnrlat=center_lat-box,
                    urcrnrlon=center_lon+box, urcrnrlat=center_lat+box)

        m.drawstates()
        m.drawcounties()
        m.arcgisimage(service='World_Shaded_Relief')
        m.scatter(a['LONGITUDE'], a['LATITUDE'], c=a['air_temp'], cmap='Spectral_r', latlon=True)
        

    if demo_radius_cartopy:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        
        import sys
        sys.path.append('C:\\Users\\blaylockbk\\OneDrive\\Documents\\pyBKB_v3') # When on my PC
        sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')    # When on CHPC
        from BB_maps.my_cartopy import load_states, load_counties


        a = get_mesowest_radius(start, 'wbb', radius=30, within=30)

        projection = ccrs.PlateCarree()

        states = load_states(projection)
        counties = load_counties(projection)

        fig = plt.figure(figsize=[10,10])
        ax = fig.add_subplot(111, projection=projection)
        #ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
        #ax.add_feature(cfeature.BORDERS.with_scale('50m'))
        #ax.add_feature(cfeature.STATES.with_scale('50m'))
        #ax.add_feature(cfeature.LAKES.with_scale('50m'), linewidth=2)

        ax.add_feature(counties, edgecolor='k', linewidth=.3)
        ax.add_feature(states, edgecolor='k', linewidth=1)

        ax.set_extent([a['LONGITUDE'].min(), a['LONGITUDE'].max(), a['LATITUDE'].min(), a['LATITUDE'].max()], projection)

        ax.scatter(a['LONGITUDE'], a['LATITUDE'], c=a['air_temp'], cmap='Spectral_r')


    if demo_stn_info:
        c = get_mesowest_stninfo(['wbb','ukbkb'])
        print(c)
    

    if demo_percentiles:
        d = get_mesowest_percentiles('WBB')
        plt.fill_between(d['DATETIME'],d['p00'],d['p100'])

    plt.show()
