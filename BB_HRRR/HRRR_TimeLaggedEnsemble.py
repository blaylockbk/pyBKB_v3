# Brian Blaylock
# July 27, 2018

"""
HRRR Time Lagged Ensemble:
https://rapidrefresh.noaa.gov/internal/pdfs/alcott_HRRRTLE_8jun2016-adj.pdf
"""

import numpy as np
from datetime import datetime, timedelta
import scipy.ndimage as ndimage
import matplotlib.pyplot as plt
import multiprocessing

import sys

sys.path.append("/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3")
sys.path.append("B:\\pyBKB_v2")
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon
from BB_maps.my_basemap import draw_HRRR_map, draw_centermap
from BB_cmap.NCAR_ensemble_cmap import cm_prob

import matplotlib as mpl

mpl.rcParams["figure.figsize"] = [12, 10]
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["savefig.dpi"] = 100  # For web
mpl.rcParams["figure.titleweight"] = "bold"
mpl.rcParams["xtick.labelsize"] = 10
mpl.rcParams["ytick.labelsize"] = 10
mpl.rcParams["axes.labelsize"] = 8
mpl.rcParams["axes.titlesize"] = 12
mpl.rcParams["figure.subplot.hspace"] = 0.01


def radial_footprint(radius):
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    footprint = x ** 2 + y ** 2 <= radius ** 2
    footprint = 1 * footprint.astype(float)
    return footprint


def first_filter(values, threshold):
    """
    If the pixel is over the threshold, then set all surrounding pixels as
    above the threshold. This ensures that this pixel will receive 100%
    probability that it will be over the threshold. We do this with a filter.
    If any pixel within the radius exceeds the threshold, then that point is
    set to exceed the threshold.
    """
    return np.max(values) >= threshold


def second_filter(values):
    """
    The second filter sums up the amount of points in the radius
    """
    return np.sum(values)


def member_multipro(inputs):
    """Multiprocessing Inputs for member"""
    validDATE = inputs[0]
    f = inputs[1]
    threshold = inputs[2]
    variable = inputs[3]
    radius = inputs[4]

    runDATE = validDATE - timedelta(hours=f)
    H = get_hrrr_variable(runDATE, "REFC:entire", fxx=f)
    # Apply spatial filters
    first = ndimage.generic_filter(
        H["value"],
        first_filter,
        footprint=radial_footprint(radius),
        extra_keywords={"threshold": threshold},
    )
    second = ndimage.generic_filter(
        first, second_filter, footprint=radial_footprint(radius)
    )
    #
    return second


def TLE(
    validDATE,
    threshold=35,
    variable="REFC:entire",
    radius=9,
    fxx=range(2, 5),
    hours_span=0,
):
    """
    Compute the Time-Lagged Ensemble for a variable

    Input:
        DATE      - Datetime object representing the valid date.
        threshold - The threshold value for which you wish to compute probability.
        variable  - Variable string from the HRRR .idx file
        radius    - The number of grid points the radial spatial filter uses
        fxx       - A list of forecast hours (between 0 and 18) to use in the probability.
        day_span  - Number hours +/- the valid hour to consider as members.
                    Default 0 will only use the validDATE. If you set to 1, then
                    will use additional model runs valid for +/- 1 hour the
                    validDATE
    """
    # Generate a list of datetimes based on the validDATE and the hours_span
    sDATE = validDATE - timedelta(hours=hours_span)
    eDATE = validDATE + timedelta(hours=hours_span)
    DATES = [
        sDATE + timedelta(hours=h)
        for h in range(int((eDATE - sDATE).seconds / 60 / 60) + 1)
    ]

    print()
    print("### Time-Lagged Ensemble###")
    print("     Valid Dates:\t%s" % DATES)
    print("        Variable:\t%s" % variable)
    print(" Threshold value:\t%s" % threshold)
    print("   Radial filter:\t %s grid points (%s km)" % (radius, (3 * radius)))
    print("  Forecast hours:\t%s" % (["f%02d" % f for f in fxx]))

    # Run spatial filter for each member:
    # List of inputs used for multiprocessing for each member
    inputs_list = [[d, f, threshold, variable, radius] for d in DATES for f in fxx]

    # Multiprocessing :)
    cpus = np.minimum(multiprocessing.cpu_count(), len(inputs_list))
    p = multiprocessing.Pool(cpus)
    members = p.map(member_multipro, inputs_list)
    # The maximum number of point in the radial footprint
    max_points = np.sum(radial_footprint(radius))
    # The TLE probability is the mean of the probability of "hits" within the radius
    member_mean = np.mean(members / max_points, axis=0)
    # Return the array with zero probability masked
    masked = member_mean
    masked = np.ma.array(masked)
    masked[masked == 0] = np.ma.masked

    # Load the latitude and longitude.
    return_this = get_hrrr_latlon()

    # also return the masked probabilities
    return_this["prob"] = masked
    return_this["members"] = len(members)

    return return_this


if __name__ == "__main__":

    # validDATE = datetime(2018, 7, 17, 6) # Thunderstom Utah SL Counties
    validDATE = datetime(2018, 8, 1, 23)  # Isolated Thunderstorms
    threshold = 35
    radius = 9
    fxx = range(9, 12)
    variable = "REFC:entire"
    hours_span = 1

    tle = TLE(
        validDATE,
        threshold=threshold,
        variable="REFC:entire",
        radius=radius,
        fxx=fxx,
        hours_span=hours_span,
    )

    # Get the values at the valid time, and plus or minus an hour
    H = get_hrrr_variable(validDATE, "REFC:entire", fxx=0)  # on the hr

    m = draw_centermap(40.77, -111.96, size=(2.5, 3.5))

    plt.figure(figsize=[10, 5])
    cm = cm_prob()
    m.pcolormesh(
        tle["lon"],
        tle["lat"],
        tle["prob"],
        cmap=cm["cmap"],
        vmax=cm["vmax"],
        vmin=cm["vmin"],
        latlon=True,
    )
    cb = plt.colorbar(pad=0.02)
    # cb.set_label('Probability Reflectivity > %s dBZ' % threshold)

    m.contour(
        H["lon"],
        H["lat"],
        H["value"] >= 35,
        levels=[1],
        linewidths=0.8,
        colors="crimson",
        latlon=True,
    )

    m.drawcoastlines()
    m.drawcountries()
    m.drawstates()
    m.arcgisimage(service="World_Shaded_Relief", xpixels=1000, dpi=100)

    plt.title("HRRR-TLE", loc="left", fontweight="semibold")
    plt.title("\nValid: %s" % validDATE.strftime("%Y %b %d %H:%M UTC"), loc="right")
    plt.xlabel(
        "Probability Reflectivity > %s dBZ\nFxx: %s\nFilter Radius: %s km"
        % (threshold, ["F%02d" % f for f in fxx], radius * 3)
    )
    plt.show()

    m = draw_HRRR_map()
    plt.figure(figsize=[10, 5])
    cm = cm_prob()
    m.pcolormesh(
        tle["lon"],
        tle["lat"],
        tle["prob"],
        cmap=cm["cmap"],
        vmax=cm["vmax"],
        vmin=cm["vmin"],
        latlon=True,
    )
    cb = plt.colorbar(pad=0.02)
    # cb.set_label('Probability Reflectivity > %s dBZ' % threshold)

    m.contour(
        H["lon"],
        H["lat"],
        H["value"] >= 35,
        levels=[1],
        linewidths=0.8,
        colors="crimson",
        latlon=True,
    )

    m.drawcoastlines()
    m.drawcountries()
    m.drawstates()

    plt.title("HRRR-TLE", loc="left", fontweight="semibold")
    plt.title("\nValid: %s" % validDATE.strftime("%Y %b %d %H:%M UTC"), loc="right")
    plt.xlabel(
        "Probability Reflectivity > %s dBZ\nFxx: %s\nFilter Radius: %s km"
        % (threshold, ["F%02d" % f for f in fxx], radius * 3)
    )
    plt.show()
# Percentiles
# pValues = {}
# for p in [0,1,2,3,4,5,10,25,33,50,66,75,90,95,96,97,98,99,100]:
#    print('working on p%02d' % p)
#    asdfpValues['p%02d' % p] = ndimage.percentile_filter(H['value'], p, footprint=radial_footprint(9), mode='reflect')
