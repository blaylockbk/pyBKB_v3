# Brian Blaylock
# July 3, 2018

"""
Return Basemaps for domains I regularly use.

Can define the resolution of the map with resolution argument:
    'c' - crude
    'l' - low
    'i' - intermediate
    'h' - high
    'f' - full

Note: Basemap is no longer supported
"""

from mpl_toolkits.basemap import Basemap

def draw_centermap(lat, lon, size=(3,3), resolution='i', area_thresh=2000):
    """
    Draw a square map given a center latitude and longitude.
    input:
        lat  - The center latitude
        lon  - The center longitude
        size - A tuple for the distance between the center location and how far
               left/right/up/down you want the map to display
    """
    return Basemap(projection='cyl', resolution=resolution, area_thresh=area_thresh,
                   llcrnrlon=lon-size[1], llcrnrlat=lat-size[0],
                   urcrnrlon=lon+size[1], urcrnrlat=lat+size[0])


def draw_HRRR_map(resolution='i', area_thresh=2000):
    """
    Draw the Continental United States HRRR Domain with lambert conformal
    projection.
    Map specifications are from the HRRR's namelist.wps file:
    https://rapidrefresh.noaa.gov/hrrr/HRRR/static/HRRRv1/namelist.wps
    """
    return Basemap(projection='lcc', resolution=resolution, area_thresh=area_thresh,
                   width=1800*3000, height=1060*3000,
                   lat_1=38.5, lat_2=38.5,
                   lat_0=38.5, lon_0=-97.5)



