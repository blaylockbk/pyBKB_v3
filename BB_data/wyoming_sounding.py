# Brian Blaylock
# Version 3.0 update
# July 3, 2018

"""
Download sounding data from University of Wyoming text product.
"""

from datetime import datetime
import requests

def get_wyoming_sounding(DATE, location='slc'):
    """
    Download a sounding file from University of Wyoming Site and
    return a dictionary of the values

    Input:
        DATE     - A datetime object in UTC. Hour must be either 0 or 12
        location - Defaults to slc, the Salt Lake City. Alternatively use a
                   number for the station identifer.
    """

    assert DATE.hour in [0,12], 'DATE.hour must be either 0 or 12'

    if location == 'slc':
        location = '72572'  # this is the id number for KSLC
    else:
        location = str(location)


    # Wyoming URL to download sounding
    URL = 'http://weather.uwyo.edu/cgi-bin/sounding?' \
        + 'region=naconf&TYPE=TEXT%3ALIST' \
        + '&YEAR=%s' % DATE.strftime('%Y') \
        + '&MONTH=%s' % DATE.strftime('%m') \
        + '&FROM=%s' % DATE.strftime('%d%H') \
        + '&TO=%s' % DATE.strftime('%d%H') \
        + '&STNM=' + location
    
    # Get text and split by new line character
    content = requests.get(URL).text.split('\n')

    # Find begining and ending line number that contains data
    begin = 0
    end = 0
    for i, c in enumerate(content):
        if c[:5] == ' 1000':
            begin = i
        if c == '</PRE><H3>Station information and sounding indices</H3><PRE>':
            end = i


    return_this = {'URL': URL,
                   'DATE': DATE,
                   'LOCATION': location,
                   'press': [],
                   'height': [],
                   'temp': [],
                   'dwpt': [],
                   'rh': [],
                   'mixing ratio': [],
                   'wdir': [],
                   'wspd': [],
                   'theta': []}

    for c in content[begin:end]:
        if len(c.split()) == 11:
            prs, hgt, tmp, dpt, rh, mx, wd, ws, theta, thetaE, thetaV = c.split() 
            return_this['press'].append(float(prs))             # hPa
            return_this['height'].append(int(hgt))              # m
            return_this['temp'].append(float(tmp))              # C 
            return_this['dwpt'].append(float(dpt))              # C
            return_this['rh'].append(int(rh))                   # %
            return_this['mixing ratio'].append(float(mx)/1000.) # kg/kg
            return_this['wdir'].append(int(wd))                 # degrees
            return_this['wspd'].append(float(ws)*0.5144)        # m/s
            return_this['theta'].append(float(theta))           # K

    return return_this

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    DATE = datetime(2018, 7, 1)
    w = get_wyoming_sounding(DATE)

    plt.plot(w['temp'], w['press'])
    plt.gca().invert_yaxis()
    plt.yticks(range(0,1001,100))
    plt.show()
