## Brian Blaylock
## August 13, 2020   COVID-19 Era

"""
============
Synotpic API
============

Get mesonet data from the Synoptic API and return as Pandas.DataFrame.

    https://developers.synopticdata.com/

Requires a Synoptic API token. You can get your own token here:
    
    https://synopticlabs.org/api/guides/?getstarted

Synoptic API Documentation
--------------------------
https://developers.synopticdata.com/mesonet/v2/


Station Selector Parameters
---------------------------
Queried station data can be refined with "Station Selector" arguments.
Below are some more common ones. Read the API docs to  see others.
https://developers.synopticdata.com/mesonet/v2/station-selectors/

stid : str or list
    Specify which stations you want to get data for by Station ID.
    May be a single ID or list of IDs.
    ``['KSLC', 'UKBKB', 'KMRY']`` *or* ``'KSLC'``
state : str or list
    String or list of abbreviated state strings, i.e. ['UT','CA']
radius : str
    Only return stations within a great-circle distance from a 
    specified lat/lon point or station (by STID). May be in form
    ``"lat,lon,miles"`` *or* ``"stid,miles"``
vars : str or list
    Filter stations by the variables they report.
    i.e., ``['air_temp', 'wind_speed', 'wind_direction', etc.]``
    https://developers.synopticdata.com/about/station-variables/
varsoperator : {'and', 'or'}
    Define how `vars` is understood.
    Default is 'or', means any station with any variable is used.
    while 'and' means a station must report every variable to be listed.
network - int
    Network ID number. (See network API service)
    https://developers.synopticdata.com/about/station-providers/
limit : int
    Specify how many of the closest stations you want to recieve.
    limit=1 will only return the nearest station.
bbox : [lonmin, latmin, lonmax, lonmin]
    Get stations within a bounding box.
    
Other Common Parameters
-----------------------
units : {'metric', 'english'}
    See documentation for more custom unit selection.
    An example of a custom unit is ``units=temp|F`` to set just
    the temperature to degrees Fahrenheit.
obtimezone : {'UTC', 'local'}
status : {'active', 'inactive'}

.. note::
    These Datetimes have timezone information. When plotting,
    I haven't had issues with Pandas 1.1.0 and matplotlib 3.3.0,
    but for earlier version, matplotlib doesn't like the DatetimeIndex
    with timezone information. In that case, you can do something like
    ... code-block::
        df.index.tz_localize(None)
    to remove the datetime information.

"""

import sys
from datetime import datetime
import numpy as np
import requests
import urllib
import pandas as pd
from datetime import datetime

from get_credentials import get_MW_token
from BB_wx_calcs.wind import spddir_to_uv

##======================================================================
## API Token
##======================================================================
## Get your own token here: https://developers.synopticdata.com/
#_token = 'YOUR_TOKEN_HERE'
_token = get_MW_token()['token']
##======================================================================

## API Services
## https://developers.synopticdata.com/mesonet/v2/
_service = {'auth', 'networks', 'networktypes', 'variables', 'qctypes'}
_stations = {'metadata', 'timeseries', 'precipitation', 'nearesttime', 'latest'}
_service.update(_stations)

## API Station Selector
_stn_selector = {'stid', 'country', 'state', 'country', 'status', 'nwszone',
                 'nwsfirezone', 'cwa', 'gacc', 'subgacc', 'vars', 'varsoperator',
                 'network', 'radius', 'limit', 'bbox', 'fields'}

def synoptic_api(service, verbose=True, **params):
    '''
    Request data from the Synoptic API. Returns a *requests* object.
        
    API References
    --------------
    - https://developers.synopticdata.com/mesonet/v2/
    - https://developers.synopticdata.com/mesonet/explorer/
    
    Parameters
    ----------
    service : str
        API service to use, including {'auth', 'latest', 'metadata',
        'nearesttime', 'networks', 'networktypes', 'precipitation',
        'qctypes', 'timeseries', 'variables'}
    **params : keyword arguments
        API request parameters (arguments).
        Lists will be converted to a comma-separated string.
        Datetimes (datetime or pandas) will be parsed by f-string to YYYYmmddHHMM.
    
    Returns
    -------
    A ``requests.models.Response`` object from ``requests.get(URL, params)``
    
    Examples
    --------
    To read the json data for metadata for a station
    
    >>> synoptic_api('metadata', stid='WBB').json()
    
    >>> synoptic_api('metadata', stid=['WBB', 'KSLC']).json()
    
    '''   
    help_url = 'https://developers.synopticdata.com/mesonet/v2/'
    assert service in _service, f"`service` must be one of {_service}. See API documentation {help_url}"
    
    ## Service URL
    ##------------
    root = 'https://api.synopticdata.com/v2/'
    
    if service in _stations:    
        URL = f"{root}/stations/{service}"
    else:
        URL = f"{root}/{service}"
        
    ## Set API token
    ##--------------
    ## Default token is set at top of this file, but you may overwrite
    ## with keyword argument.
    params.setdefault('token', _token)
    
    ## Parse parameters
    ##-----------------
    # Change some keyword parameters to the appropriate request format
    
    ## 1) Force all param keys to be lower case
    params = {k.lower(): v for k, v in params.items()}
    
    ## 2) Join lists as comma separtated strings.
    ##    For example, stid=['KSLC', 'KMRY'] --> stid='KSLC,KRMY').
    for key, value in params.items():           
        if isinstance(value, list) and key not in ['obrange']:
            params[key] = ','.join(value)
        
    ## 2) Datetimes should be string: 'YYYYmmddHHMM' (obrange is 'YYYYmmdd')
    for i in ['start', 'end', 'expire', 'attime']:
        if i in params and not isinstance(params[i], str):
            params[i] = f"{params[i]:%Y%m%d%H%M}"
    if 'obrange' in params and not isinstance(params['obrange'], str): 
        # obrange could be one date or a list of two dates.
        if not hasattr(params['obrange'], '__len__'):
            params['obrange'] = [params['obrange']]
        params['obrange'] = ','.join([f'{i:%Y%m%d}' for i in params['obrange']])    
    
    ########################
    # Make the API request #
    ########################
    f = requests.get(URL, params)
    
    if service == 'auth':
        return f
    
    # Check Returned Data
    code = f.json()['SUMMARY']['RESPONSE_CODE']
    msg = f.json()['SUMMARY']['RESPONSE_MESSAGE']
    decode_url = urllib.parse.unquote(f.url)

    assert code == 1, f"🛑 There are errors in the API request {decode_url}. {msg}"

    if verbose:
        print(f'\n 🚚💨 Speedy Delivery from Synoptic API [{service}]: {decode_url}\n')
    
    return f

def stations_metadata(verbose=True, **params):
    """
    Get station metadata for stations as a Pandas DataFrame.

    https://developers.synopticdata.com/mesonet/v2/stations/metadata/

    Parameters
    ----------
    **params : keyword arguments
        Synoptic API arguments used to specify the data request.
        e.g., sensorvars, obrange, obtimezone, etc.
        
    Others: STATION SELECTION PARAMETERS
    https://developers.synopticdata.com/mesonet/v2/station-selectors/
    """
    assert any([i in _stn_selector for i in params]), \
    f"🤔 Please assign a station selector (i.e., {_stn_selector})"

    # Get the data
    web = synoptic_api('metadata', verbose=verbose, **params)
    data = web.json()
        
    # Initialize a DataFrame
    df = pd.DataFrame(data['STATION'], index=[i['STID'] for i in data['STATION']])
    
    # Convert data to numeric values (if possible)
    df = df.apply(pd.to_numeric, errors='ignore')

    # Deal with "Period Of Record" dictionary
    df = pd.concat([df, df.PERIOD_OF_RECORD.apply(pd.Series)], axis=1)
    df[['start', 'end']] = df[['start', 'end']].apply(pd.to_datetime)

    # Rename some fields.
    # latitude and longitude are made lowercase to conform to CF standard
    df.drop(columns=['PERIOD_OF_RECORD'], inplace=True)
    df.rename(columns=dict(LATITUDE='latitude', LONGITUDE='longitude',
                           start='RECORD_START', end='RECORD_END'),
              inplace=True)
    
    df.attrs['URL'] = urllib.parse.unquote(web.url)
    df.attrs['UNITS'] = {'ELEVATION': 'ft'}
    df.attrs['SUMMARY'] = data['SUMMARY']
    return df.transpose().sort_index()

def stations_timeseries(verbose=True, **params):
    """
    Get station data for time series.

    https://developers.synopticdata.com/mesonet/v2/stations/timeseries/

    Parameters
    ----------
    **params : keyword arguments
        Synoptic API arguments used to specify the data request.
        **Must include ``start`` and ``end`` argument *or* ``recent``.**  
    start, end : datetime
        Start and end of time series
    recent : int
        Minutes for recent observations.
   
    Others: obtimezone, units, and STATION SELECTION PARAMETERS
    https://developers.synopticdata.com/mesonet/v2/station-selectors/
    
    Examples
    --------
    >>> stations_timeseries(stid='WBB', recent=100)
    >>> stations_timeseries(radius='UKBKB,10', vars='air_temp', recent=100)
    
    Plot Air Temperature
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib.dates import DateFormatter
    >>> df = stations_timeseries(stid='WBB', recent=300)
    >>> plt.plot(df['air_temp'])
    >>> plt.plot(df['dew_point_temperature'])
    >>> plt.gca().xaxis.set_major_formatter(DateFormatter('%b %d\n%H:%M'))
    >>> plt.legend()
    """
    check1 = 'start' in params and 'end' in params
    check2 = 'recent' in params
    assert check1 or check2, "🤔 `start` and `end` *or* `recent` is required"
    assert any([i in _stn_selector for i in params]), \
    f"🤔 Please assign a station selector (i.e., {_stn_selector})"

    # Get the data
    web = synoptic_api('timeseries', verbose=verbose, **params)
    data = web.json()
    
    # Build a separate pandas.DataFrame for each station.
    Z = []
    for stn in data['STATION']:
        obs = stn.pop('OBSERVATIONS')
        senvars = stn.pop('SENSOR_VARIABLES')
        
        df = pd.DataFrame(obs).set_index('date_time')
        df.index = pd.to_datetime(df.index)
        
        # Break wind into U and V components, if speed and direction are available
        if all(['wind_speed' in senvars, 'wind_direction' in senvars]):
            for i_spd, i_dir in zip(senvars['wind_speed'].keys(),
                                    senvars['wind_direction'].keys()):
                u, v = spddir_to_uv(obs[i_spd], obs[i_dir])
                this_set = '_'.join(i_spd.split('_')[-2:])
                df[f'wind_u_{this_set}'] = u
                df[f'wind_v_{this_set}'] = v
        
        # Remove 'set_1d' and 'set_1d' from column names.
        # Sets 2+ will retain the full name. The user should refer to
        # the SENSOR_VARIABLES to see which are derived variables.
        col_names = {i: i.replace('_set_1d', '').replace('_set_1', '') for i in df.columns}
        df.rename(columns=col_names, inplace=True)
              
        # Remaining data in dict will be returned as attribute
        df.attrs = stn
        
        # Convert some strings to flaot/int
        for k, v in df.attrs.items():
            if isinstance(v, str):
                try:
                    n = float(v)
                    if n.is_integer():
                        df.attrs[k] = int(n)
                    else:
                        df.attrs[k] = n
                except:
                    pass
        
        # Rename lat/lon to lowercase to match CF convenctions
        df.attrs['latitude'] = df.attrs.pop('LATITUDE')
        df.attrs['longitude'] = df.attrs.pop('LONGITUDE')
        
        # Include other info
        df.attrs['UNITS'] = data['UNITS']
        df.attrs['QC_SUMMARY'] = data['QC_SUMMARY']
        df.attrs['SUMMARY'] = data['SUMMARY']
        df.attrs['SENSOR_VARIABLES'] = senvars
        
        Z.append(df)
        
    if len(Z) == 1:
        return Z[0]
    else:
        if verbose: print(f'Returned [{len(Z)}] stations. {[i.attrs["STID"] for i in Z]}')
        return Z

def stations_nearesttime(verbose=True, **params):
    """
    Get station data nearest a datetime.

    https://developers.synopticdata.com/mesonet/v2/stations/nearesttime/

    Parameters
    ----------
    **params : keyword arguments
        Synoptic API arguments used to specify the data request.
        **Must include ``attime`` and ``within``**   
    attime : datetime
        Datetime you want to the the nearest observations for.
    within : int
        How long ago is the oldest observation you want to receive, in minutes.
        
    Other: obtimezone, units, STATION SELECTION PARAMETERS:
    https://developers.synopticdata.com/mesonet/v2/station-selectors/
    
    Examples
    --------
    >>> stations_nearesttime(attime=datetime(2020,1,1), within=60, stid='WBB')
    """
    assert 'attime' in params, "🤔 `attime` is a required parameter (datetime)."
    assert 'within' in params, "🤔 `within` is a required parameter (int, in minutes)."
    assert any([i in _stn_selector for i in params]), \
    f"🤔 Please assign a station selector (i.e., {_stn_selector})"

    # Get the data
    web = synoptic_api('nearesttime', verbose=verbose, **params)
    data = web.json()
    
    dfs = []
    for i in data['STATION']:
        obs = i.pop('OBSERVATIONS')
        df = pd.DataFrame(obs)

        for k, v in i.items():
            if k in ['LATITUDE', 'LONGITUDE']:
                # lat/lon is lowercase for CF compliant variable name
                df[k.lower()] = [None, v]
            else:
                df[k] = [None, v]

        # Remove 'set_1d' and 'set_1d' from column names.
        # Sets 2+ will retain the full name. The user should refer to
        # the SENSOR_VARIABLES to see which are derived variables.
        col_names = {i: i.replace('_value_1d', '').replace('_value_1', '') for i in df.columns}
        df.rename(columns=col_names, inplace=True)

        # Convert date_time to datetime object
        df.loc['date_time'] = pd.to_datetime(df.loc['date_time'])


        df = df.transpose().sort_index()
        rename = dict(date_time=f"{i['STID']}_date_time", value=i['STID'])
        df.rename(columns=rename, inplace=True)
        dfs.append(df)
    
    df = pd.concat(dfs, axis=1)
    df.attrs['UNITS'] = data['UNITS']
    df.attrs['SUMMARY'] = data['SUMMARY']
    df.attrs['QC_SUMMARY'] = data['QC_SUMMARY']
    
    return df

def stations_latest(verbose=True, **params):
    """
    Get the latest station data.

    https://developers.synopticdata.com/mesonet/v2/stations/latest/

    Parameters
    ----------
    **params : keyword arguments
        Synoptic API arguments used to specify the data request.
        **Must include ``within``.**
    within : int
        Number of minutes to consider.
    
    Others: obtimezone, units, STATION SELECTION PARAMETERS:
    https://developers.synopticdata.com/mesonet/v2/station-selectors/
        
    Examples
    --------
    >>> stations_nearesttime(attime=datetime(2020,1,1), within=60, stid='WBB')
    """
    assert any([i in _stn_selector for i in params]), \
    f"🤔 Please assign a station selector (i.e., {_stn_selector})"
    
    params.setdefault('within', 60)

    # Get the data
    web = synoptic_api('latest', verbose=verbose, **params)
    data = web.json()
    
    dfs = []
    for i in data['STATION']:
        obs = i.pop('OBSERVATIONS')
        df = pd.DataFrame(obs)

        for k, v in i.items():
            if k in ['LATITUDE', 'LONGITUDE']:
                # lat/lon is lowercase for CF compliant variable name
                df[k.lower()] = [None, v]
            else:
                df[k] = [None, v]

        # Remove 'set_1d' and 'set_1d' from column names.
        # Sets 2+ will retain the full name. The user should refer to
        # the SENSOR_VARIABLES to see which are derived variables.
        col_names = {i: i.replace('_value_1d', '').replace('_value_1', '') for i in df.columns}
        df.rename(columns=col_names, inplace=True)

        # Convert date_time to datetime object
        df.loc['date_time'] = pd.to_datetime(df.loc['date_time'])


        df = df.transpose().sort_index()
        rename = dict(date_time=f"{i['STID']}_date_time", value=i['STID'])
        df.rename(columns=rename, inplace=True)
        dfs.append(df)
    
    df = pd.concat(dfs, axis=1)
    
    df.attrs['UNITS'] = data['UNITS']
    df.attrs['SUMMARY'] = data['SUMMARY']
    df.attrs['QC_SUMMARY'] = data['QC_SUMMARY']
    
    return df  

def stations_precipitation(verbose=True, **params):
    """
    Get the precipitation data.

    https://developers.synopticdata.com/mesonet/v2/stations/precipitation/

    Parameters
    ----------
    **params : keyword arguments
        Synoptic API arguments used to specify the data request.
        Requires `start` and `end` *or* `recent`.    
    """
    print("🙋🏼‍♂️ HI! THIS FUNCTION IS NOT COMPLETED YET. WILL JUST RETURN JSON.")
    
    check1 = 'start' in params and 'end' in params
    check2 = 'recent' in params
    assert check1 or check2, "🤔 `start` and `end` *or* `recent` is required"
    assert any([i in _stn_selector for i in params]), \
    f"🤔 Please assign a station selector (i.e., {_stn_selector})"
    
    # Get the data
    web = synoptic_api('precipitation', verbose=verbose, **params)
    data = web.json()
    
    return data

def networks(verbose=True, **params):
    """
    Return a DataFrame of available Networks and their metadata
    
    https://developers.synopticdata.com/mesonet/v2/networks/
    https://developers.synopticdata.com/about/station-network-type/
    
    Parameters
    ----------
    **param : keyword arguments    
    id : int or list of int
        Filter by network number.
    shortname : str or list of str
        Netork shortname, i.e. 'NWS/FAA', 'RAWS', 'UTAH DOT',         
    """
    # Get the data
    web = synoptic_api('networks', verbose=verbose, **params)
    data = web.json()
    
    df = pd.DataFrame(data['MNET'])
    df.set_index('ID', inplace=True)
    df['LAST_OBSERVATION'] = pd.to_datetime(df.LAST_OBSERVATION)
    df.attrs['SUMMARY'] = data['SUMMARY']
    
    return df

def networktypes(verbose=True, **params):
    """
    Get a DataFrame of network types
    
    https://developers.synopticdata.com/mesonet/v2/networktypes/
    https://developers.synopticdata.com/about/station-network-type/
    
    Parameters
    ----------
    **params : keyword arguments
    id : int
        Select just the network type you want
    """
    
    # Get the data
    web = synoptic_api('networktypes', verbose=verbose, **params)
    data = web.json()
    
    df = pd.DataFrame(data['MNETCAT'])
    df.set_index('ID', inplace=True)
    df.attrs['SUMMARY'] = data['SUMMARY']
    
    return df

def variables(verbose=True, **params):
    """
    Return a DataFrame of available station variables
    
    https://developers.synopticdata.com/mesonet/v2/variables/
    https://developers.synopticdata.com/mesonet/v2/api-variables/
    
    Parameters
    ----------
    **param : keyword arguments
        There are none for the 'variables' service.

    """
    # Get the data
    web = synoptic_api('variables', verbose=verbose, **params)
    data = web.json()
    
    df = pd.concat([pd.DataFrame(i) for i in data['VARIABLES']], axis=1).transpose()
    #df.set_index('vid', inplace=True)
    df.attrs['SUMMARY'] = data['SUMMARY']
    
    return df

def qctypes(verbose=True, **params):
    """
    Return a DataFrame of available quality control (QC) types
    
    https://developers.synopticdata.com/mesonet/v2/qctypes/
    https://developers.synopticdata.com/about/qc/
    
    Parameters
    ----------
    **param : keyword arguments
        Available parameters include `id` and `shortname`
    """
    # Get the data
    web = synoptic_api('qctypes', verbose=verbose, **params)
    data = web.json()
        
    df = pd.DataFrame(data['QCTYPES'])
    df = df.apply(pd.to_numeric, errors='ignore')
    df.set_index('ID', inplace=True)
    df.sort_index(inplace=True)
    df.attrs['SUMMARY'] = data['SUMMARY']
    
    return df

def auth(helpme=True, verbose=True, **params):
    """
    Return a DataFrame of authentication controls.
    
    https://developers.synopticdata.com/mesonet/v2/auth/
    https://developers.synopticdata.com/settings/
    
    Parameters
    ----------
    helpme : bool
        True - It might be easier to deal with generating new tokens 
        and listing tokens on the web settings, so just return the
        URL to help you make these changes via web.
        False - Access the ``auth`` API service.
    **param : keyword arguments
       
    Some include the following
    
    disableToken : str
    list : {1, 0}
    expire : datetime
    
    Examples
    --------
    List all tokens
    >>> auth(helpme=False, apikey='YOUR_API_KEY', list=1)
    
    Create new token (tokens are disabled after 10 years)
    >>> auth(helpme=False, apikey='YOUR_API_KEY')
    
    Create new token with expiration date
    >>> auth(helpme=False, apikey='YOUR_API_KEY', expire=datetime(2021,1,1))
    
    Disable a token (not sure why this doesn't do anything)
    >>> auth(helpme=False, apikey='YOUR_API_KEY', disable='TOKEN')
    """
    if helpme:
        web = 'https://developers.synopticdata.com/settings/'
        print(f"It's easier to manage these via the web settings: {web}")
    else:
        assert 'apikey' in params, f'🛑 `apikey` is a required argument. {web}'
        web = synoptic_api('auth', verbose=verbose, **params)
        data = web.json()
        return data
    
# Other Services
#---------------
# stations_precipitation : * NOT FINISHED
# stations_latency :
# stations_qcsegments :