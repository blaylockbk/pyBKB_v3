# Brian Blaylock
# Version 3 update
# June 21, 2018

"""
KEEP THESE PRIVATE

In an effort to protect my tokens from the public, these function will return
my MesoWest token as a string, to be used in other functions to make API calls.

A user could still get the token by looking at the URL string returned
by the querey, but this really isn't a concern.

This function is not uploaded to github by the .gitignore file
"""

def get_MW_token():
    '''
    Return Brian Blaylock's MesoWest API token
    
    https://developers.synopticdata.com/settings/
    https://developers.synopticdata.com/about/tokens/
    
    '''
    return dict(token='2562b729557f45f5958516081f06c9eb',
                key='e599f8236cf64277961b50fb329ef11a')


def get_ESRL_credentials():
    ''''
    Return credentials required for logging onto the ESRL FTP server
    gsdftp.fsl.noaa.gov for downloading the eXperimental HRRR
    '''
    return ['anonymous', 'brian.blaylock@utah.edu']


def get_LIS_credentials():
    '''
    These are for logging into NASA's Land Information System Data Portal
    https://portal.nccs.nasa.gov/lisdata
    Contact: Kristi.R.Arsenault@nasa.gov
    Returns [Username, Password]
    '''
    return ['bblaylo', 'nccsBB!999999']


def get_RDA_credentials():
    """
    For logging into the Research Data Archive system.
    https://rda.ucar.edu/
    """
    return ['brian.blaylock.ctr@nrlmry.navy.mil', 'g0ut3$']
