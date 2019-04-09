## Brian Blaylock
## March 21, 2019

"""
Paths for HRRR domain and for other subsets

Source of GeoJson files:
https://github.com/johan/world.geo.json/tree/master/countries/USA
"""

import numpy as np
from matplotlib.path import Path
import json
import requests

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon

# Get HRRR latitude and longitude grids
Hlat, Hlon = get_hrrr_latlon(DICT=False)

def read_GeoJSON(state):
    '''
    Abbreviated State
    '''
    URL = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA/%s.geo.json' % state.upper()
    f = requests.get(URL)
    return f.json()

def get_domains(add_states=None, HRRR_specific=True):
    '''
    add_states is a list of state abbreviations, i.e. add_states=['UT', 'CO', 'TX']
    NOTE: Has some issues with some states where there are multiple objects.
    '''
    
    ## Create Path boundaries of HRRR domain and subdomains of interest:
    domains = {}

    if HRRR_specific:
        # HRRR: All points counter-clockwise around the model domain.
        # West, Central, East: A 16 degree wide and 26 degree tall boundary region.
        domains['HRRR'] = {'lon': np.concatenate([Hlon[0], Hlon[:,-1], Hlon[-1][::-1], Hlon[:,0][::-1]]),
                           'lat': np.concatenate([Hlat[0], Hlat[:,-1], Hlat[-1][::-1], Hlat[:,0][::-1]])}
        domains['West'] = {
                    'lon':[-120, -104, -104, -120, -120],
                    'lat':[24.4, 24.4, 50.2, 50.2, 24.2]}
        domains['Central'] = {
                    'lon':[-104, -88, -88, -104, -104],
                    'lat':[24.4, 24.4, 50.2, 50.2, 24.2]}
        domains['East'] = {
                    'lon':[-88, -72, -72, -88, -88],
                    'lat':[24.4, 24.4, 50.2, 50.2, 24.2]}
    
    # Add paths for each state requested
    if add_states != None:
        for i in add_states:
            data = read_GeoJSON(i)
            state = data['features'][0]['properties']['name']
            coords = data['features'][0]['geometry']['coordinates']
            if data['features'][0]['geometry']['type'] == 'MultiPolygon':
                print('WARNING: Multiple Polygons in %s. Only using largest polygon.' % state)
                sizes = [len(i[0]) for i in coords]
                if state == 'Michigan':
                    idx = 0 # Exception: use the "oven mitt" portion.    
                else:
                    idx = np.argmax(sizes)
                domains[state] = {'lon': np.array(coords[idx])[0][:,0],
                                  'lat': np.array(coords[idx])[0][:,1]}
            else:
                idx = 0
                domains[state] = {'lon': np.array(coords[idx])[:,0],
                                  'lat': np.array(coords[idx])[:,1]}
    ##
    ## Generate Path objects from the vertices.
    ## 
    for i in domains:
        domains[i]['path'] = Path(list(zip(domains[i]['lon'], domains[i]['lat'])))
        if i == 'HRRR':
            domains[i]['mask'] = np.zeros_like(Hlon)==1 # An array of False...Don't make anything.
        else:
            in_path = domains[i]['path'].contains_points(list(zip(Hlon.flatten(), Hlat.flatten())))
            not_in_path = np.invert(in_path)
            not_in_path = not_in_path.reshape(np.shape(Hlat))
            domains[i]['mask'] = not_in_path
    #
    return domains


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    all_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', \
                  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', \
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', \
                  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', \
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

    some_states = ['UT', 'ID', 'CA', 'MA', 'CO', 'TX', 'FL', 'OH', 'VA']
    
    DOM = get_domains(add_states=some_states)

    for i in DOM:
        dom = DOM[i]
        plt.plot(dom['lon'], dom['lat'])
    plt.show()