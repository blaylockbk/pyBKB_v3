from __future__ import division

import json
from math import pi, sin

__version__ = '1.1.1'
WGS84_RADIUS = 6378137


def rad(value):
    return value * pi / 180


def ring__area(coordinates):
    """
    Calculate the approximate _area of the polygon were it projected onto
        the earth.  Note that this _area will be positive if ring is oriented
        clockwise, otherwise it will be negative.

    Reference:
        Robert. G. Chamberlain and William H. Duquette, "Some Algorithms for
        Polygons on a Sphere", JPL Publication 07-03, Jet Propulsion
        Laboratory, Pasadena, CA, June 2007 http://trs-new.jpl.nasa.gov/dspace/handle/2014/40409

    @Returns

    {float} The approximate signed geodesic _area of the polygon in square meters.
    """

    assert isinstance(coordinates, (list, tuple))

    _area = 0
    coordinates_length = len(coordinates)

    if coordinates_length > 2:
        for i in range(0, coordinates_length):
            if i == (coordinates_length - 2):
                lower_index = coordinates_length - 2
                middle_index = coordinates_length - 1
                upper_index = 0
            elif i == (coordinates_length - 1):
                lower_index = coordinates_length - 1
                middle_index = 0
                upper_index = 1
            else:
                lower_index = i
                middle_index = i + 1
                upper_index = i + 2

            p1 = coordinates[lower_index]
            p2 = coordinates[middle_index]
            p3 = coordinates[upper_index]

            _area += (rad(p3[0]) - rad(p1[0])) * sin(rad(p2[1]))

        _area = _area * WGS84_RADIUS * WGS84_RADIUS / 2

    return _area


def polygon__area(coordinates):

    assert isinstance(coordinates, (list, tuple))

    _area = 0
    if len(coordinates) > 0:
        _area += abs(ring__area(coordinates[0]))

        for i in range(1, len(coordinates)):
            _area -= abs(ring__area(coordinates[i]))

    return _area


def area(geometry):

    if isinstance(geometry, str):
        geometry = json.loads(geometry)

    assert isinstance(geometry, dict)

    _area = 0

    if geometry['type'] == 'Polygon':
        return polygon__area(geometry['coordinates'])
    elif geometry['type'] == 'MultiPolygon':
        for i in range(0, len(geometry['coordinates'])):
            _area += polygon__area(geometry['coordinates'][i])

    elif geometry['type'] == 'GeometryCollection':
        for i in range(0, len(geometry['geometries'])):
            _area += area(geometry['geometries'][i])

    return _area
