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
from geojson_area.area import area

all_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', \
              'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', \
              'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', \
              'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', \
              'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

# Get HRRR latitude and longitude grids
Hlat, Hlon = get_hrrr_latlon(DICT=False)

def read_GeoJSON(state):
    '''
    Abbreviated State
    '''
    URL = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA/%s.geo.json' % state.upper()
    f = requests.get(URL)
    return f.json()

def get_domains(add_states=None, HRRR_specific=True, compute_area=True):
    '''
    Input:
        add_states    - A list of state abbreviations, i.e. add_states=['UT', 'CO', 'TX']
                        NOTE: Has some issues with some states where there are multiple objects.
        HRRR_specific - Paths for HRRR, West, Central, and East domains
        compute_area  - Return the approximate area of the path.
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
                    'lat':[24.4, 24.4, 50.2, 50.2, 24.4]}
        domains['Central'] = {
                    'lon':[-104, -88, -88, -104, -104],
                    'lat':[24.4, 24.4, 50.2, 50.2, 24.4]}
        domains['East'] = {
                    'lon':[-88, -72, -72, -88, -88],
                    'lat':[24.4, 24.4, 50.2, 50.2, 24.4]}
    
    # Add paths for each state requested
    if add_states != None:
        for i in add_states:
            i = i.upper()
            assert i in all_states, "'%s' is not an abbreviated state" % i
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
    ## Generate Path objects from the vertices and compute area if true.
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
        
        if compute_area:
            data = {'type':'Polygon',
                    'coordinates': [[tuple(i) for i in domains[i]['path'].vertices]]}
            this_area = area(data)
            print('%s Area in meters squared: %s' % (i, this_area))
            domains[i]['area'] = this_area
    #
    return domains


def get_RAP_path():
    # RAPv4 geogrid downloaded from
    # https://rapidrefresh.noaa.gov/RAP/static/RAPv4-ESRL/geo_em.d01.nc
    import xarray
    x = xarray.open_dataset('/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/RAPv4_geo_em.d01.nc')
    RAP_lons = np.concatenate([x.XLONG_M[0][0], x.XLONG_M[0][:,-1], x.XLONG_M[0][-1][::-1], x.XLONG_M[0][:,0][::-1]])
    RAP_lats = np.concatenate([x.XLAT_M[0][0], x.XLAT_M[0][:,-1], x.XLAT_M[0][-1][::-1], x.XLAT_M[0][:,0][::-1]])

    # There is an issue with crossing over the 180th meridian.
    # This is a quick fix without too much investigation on how to do it right...
    return {'part1':{'lon': RAP_lons[:-458],
                     'lat': RAP_lats[:-458]},
            'part2':{'lon': RAP_lons[-457:],
                     'lat': RAP_lats[-457:]},}

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