## Brian Blaylock
## March 21, 2019

"""
Paths for HRRR domain and for other subsets
"""

import numpy as np
from matplotlib.path import Path
import json

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon

def get_domains():
    # Get HRRR latitude and longitude grids
    Hlat, Hlon = get_hrrr_latlon(DICT=False)
    #
    ## Create Path boundaries of HRRR domain and subdomains of interest:
    # HRRR: All points counter-clockwise around the model domain.
    # West, Central, East: A 16 degree wide and 26 degree tall boundary region.
    GeoJSON_Path = '/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/geojson_area/'
    #
    domains = {
        'HRRR':
            {'lon': np.concatenate([Hlon[0], Hlon[:,-1], Hlon[-1][::-1], Hlon[:,0][::-1]]),
            'lat': np.concatenate([Hlat[0], Hlat[:,-1], Hlat[-1][::-1], Hlat[:,0][::-1]])},
        'West':{
            'lon':[-120, -104, -104, -120, -120],
            'lat':[24.4, 24.4, 50.2, 50.2, 24.2]},
        'Central':{
            'lon':[-104, -88, -88, -104, -104],
            'lat':[24.4, 24.4, 50.2, 50.2, 24.2]},
        'East':{
            'lon':[-88, -72, -72, -88, -88],
            'lat':[24.4, 24.4, 50.2, 50.2, 24.2]},
        'Utah':{
            'lon':np.array(json.loads(open(GeoJSON_Path+'UT.geo.json', 'r').read())['features'][0]['geometry']['coordinates'][0])[:,0],
            'lat':np.array(json.loads(open(GeoJSON_Path+'UT.geo.json', 'r').read())['features'][0]['geometry']['coordinates'][0])[:,1],},
    }
    #
    ## Generate Path objects from the vertices.
    for i in domains:
        domains[i]['path'] = Path(list(zip(domains[i]['lon'], domains[i]['lat'])))
        if i == 'HRRR':
            domains[i]['mask'] = np.zeros_like(Hlon)==1
        else:
            in_path = domains[i]['path'].contains_points(list(zip(Hlon.flatten(), Hlat.flatten())))
            not_in_path = np.invert(in_path)
            not_in_path = not_in_path.reshape(np.shape(Hlat))
            domains[i]['mask'] = not_in_path
    #
    return domains
