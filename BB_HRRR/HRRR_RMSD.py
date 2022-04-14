# Brian Blaylock
# September 14, 2018

"""
Calculate the Root-Mean-Square Difference (RMSD) between all forecast hours for
a variable.
"""

import numpy as np
from datetime import datetime, timedelta
import multiprocessing
import os

import sys

sys.path.append("/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3")
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon


def RMSD(validDATE, variable, FORECASTS=range(19), verbose=True):
    """
    Root-mean-square-difference for a single forecast time.
    datetime(2018, 8, 12, 21) # period of convection over Coal Hollow Fire
    variable = 'CAPE:surface'
    """
    # Load all forecasts grids for this time
    if variable.split(":")[0] == "UVGRD":
        values = np.array(
            [
                get_hrrr_variable(
                    validDATE - timedelta(hours=f),
                    variable,
                    fxx=f,
                    value_only=True,
                    verbose=False,
                )["SPEED"]
                for f in FORECASTS
            ]
        )
        forecasts = np.array([i for i in values if np.shape(i) != ()])
    else:
        # We have to filter out any 'nan' values if a file does not exist
        values = [
            get_hrrr_variable(
                validDATE - timedelta(hours=f),
                variable,
                fxx=f,
                value_only=True,
                verbose=False,
            )["value"]
            for f in FORECASTS
        ]
        forecasts = np.array([i for i in values if np.shape(i) != ()])

    if verbose:
        print(np.shape(forecasts))

    # Differences of each consecutive forecast (F00-F01, F01-F02, F03-F04, etc.)
    # differences = np.array([forecasts[i-1]-forecasts[i] for i in FORECASTS[1:]])

    # RMSD between consecutive forecasts and all reference hours (differences matrix)
    # print(['F%02d-F%02d' % (i, j) for i in FORECASTS for j in FORECASTS if i-j > 0])

    # Differences between each forecasts (don't double count)
    differences_all = np.array(
        [
            forecasts[i] - forecasts[j]
            for i in range(len(forecasts))
            for j in range(len(forecasts))
            if i - j > 0
        ]
    )

    RMSD_all = np.sqrt(np.mean(differences_all ** 2, axis=0))

    ## Normalized RMSDs, normalized by range (max-min)
    # NOTE: Ranges can't be zero or will get a divide by zero error
    # Get some percentiles for max, min
    q100, q00 = np.percentile(forecasts, [100, 0], axis=0)
    maxmin_range = q100 - q00
    maxmin_range[maxmin_range == 0] = np.nan
    nRMSD_range = RMSD_all / maxmin_range

    # Grid Lat/Lon and return info
    latlon = get_hrrr_latlon()
    latlon["RMSD"] = RMSD_all
    latlon["variable"] = variable
    latlon["DATE"] = validDATE
    latlon["normalized RMSD by range"] = nRMSD_range

    return latlon


def RMSD_range_MP(inputs):
    """replace the for loop with this multiprocessing method"""
    validDATE, variable, FORECASTS = inputs
    #
    # print(validDATE)
    if variable.split(":")[0] == "UVGRD":
        values = np.array(
            [
                get_hrrr_variable(
                    validDATE - timedelta(hours=f),
                    variable,
                    fxx=f,
                    value_only=True,
                    verbose=False,
                )["SPEED"]
                for f in FORECASTS
            ]
        )
        forecasts = np.array([i for i in values if np.shape(i) != ()])
    else:
        # We have to filter out any 'nan' values if a file does not exist
        values = [
            get_hrrr_variable(
                validDATE - timedelta(hours=f),
                variable,
                fxx=f,
                value_only=True,
                verbose=False,
            )["value"]
            for f in FORECASTS
        ]
        forecasts = np.array([i for i in values if np.shape(i) != ()])
    #
    print(validDATE, "Available Grids: %s/%s" % (len(forecasts), len(values)))
    #
    # Differences between each forecasts (don't double count)
    differences_all = np.array(
        [
            forecasts[i] - forecasts[j]
            for i in range(len(forecasts))
            for j in range(len(forecasts))
            if i - j > 0
        ]
    )
    #
    #
    count = len(differences_all)
    sum_of_squares = np.sum(differences_all ** 2, axis=0)
    #
    return [count, sum_of_squares]


def RMSD_range(sDATE, eDATE, variable, HOURS=[0], FORECASTS=range(19)):
    """
    Compute the RMSD for a range of dates at a given hour.

    Inputs:
        sDATE     - Datetime start(valid Date)
        eDATE     - Datetime end (valid Date)
        variable  - HRRR variable string (i.e. 'TMP:2 m')
        HOURS     - the hour(s) you want to include in the RMSD calculation
        FORECASTS - the forecasts you want to include in the RMSD calculation
    """
    print("============ %s ============" % variable)
    print("     sDATE : %s" % sDATE)
    print("     eDATE : %s" % eDATE)
    print("     HOURS : %s" % HOURS)
    print("  FORCASTS : %s" % FORECASTS)
    print()
    days = (eDATE - sDATE).days
    DAYS = [sDATE + timedelta(days=d) for d in range(days)]
    DATES = [datetime(d.year, d.month, d.day, h) for d in DAYS for h in HOURS]

    # Load all forecast grids for each valid time using multiprocessing.
    # cpus = np.minimum(multiprocessing.cpu_count(), len(DATES))-2
    cpus = 7
    P = multiprocessing.Pool(cpus)

    inputs = [[D, variable, FORECASTS] for D in DATES]
    results = P.map(RMSD_range_MP, inputs)
    P.close()
    count = np.sum([i[0] for i in results])
    sum_squares = np.sum([i[1] for i in results], axis=0)

    # RMSD Calculation
    RMSD = np.sqrt(sum_squares / count)

    # Grid Lat/Lon and return info
    latlon = get_hrrr_latlon()
    latlon["RMSD"] = RMSD
    latlon["variable"] = variable
    latlon["DATE RANGE"] = [sDATE, eDATE]

    return latlon


if __name__ == "__main__":
    # single = RMSD(DATE, 'REFC:entire', FORECASTS=range(19))
    from BB_maps.my_basemap import draw_HRRR_map, draw_centermap
    import matplotlib.pyplot as plt
    import matplotlib as mpl

    mpl.rcParams["figure.figsize"] = [15, 15]
    mpl.rcParams["figure.titlesize"] = 15
    mpl.rcParams["figure.subplot.wspace"] = 0.05
    mpl.rcParams["figure.subplot.hspace"] = 0.05
    mpl.rcParams["xtick.labelsize"] = 10
    mpl.rcParams["ytick.labelsize"] = 10
    mpl.rcParams["lines.linewidth"] = 1.8
    mpl.rcParams["savefig.bbox"] = "tight"
    mpl.rcParams["savefig.dpi"] = 100

    m = draw_HRRR_map(area_thresh=5000)
    mU = draw_centermap(lat=40, lon=-115, size=(10, 10))

    sDATE = datetime(2018, 7, 13)
    eDATE = datetime(2018, 8, 13)
    # SAVEDIR = 'figs/hourly_RMSD/'
    SAVEDIR = (
        "/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_RMSE/RMSD_v3"
    )
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)

    for variable in [
        "TMP:2 m",
        "UGRD:10 m",
        "VGRD:10 m",
        "LTNG:entire",
        "REFC:entire",
        "WIND:10 m",
        "CAPE:surface",
        "HGT:500 mb",
        "DPT:2 m",
    ]:
        # for variable in ['TMP:2 m']:
        if variable in ["LTNG:entire", "APCP:surface", "WIND:10 m"]:
            # These variables are hourly values and don't have an analysis value
            FORECASTS = range(1, 19)
        else:
            # The other variables have an analysis
            FORECASTS = range(0, 19)

        for H in range(0, 24):
            HOURS = [H]
            S = RMSD_range(sDATE, eDATE, variable, HOURS=HOURS, FORECASTS=FORECASTS)

            m.pcolormesh(S["lon"], S["lat"], S["RMSD"], latlon=True, vmin=0)
            cb = plt.colorbar(orientation="horizontal", shrink=0.8, pad=0.01)
            cb.set_label("Root-Mean-Square-Difference")

            m.drawcoastlines(color="w", linewidth=0.15)
            m.drawcountries(color="w", linewidth=0.15)
            m.drawstates(color="w", linewidth=0.15)

            plt.title("HRRR RMSD %s" % (variable), loc="left", fontweight="semibold")
            plt.title(
                "Start: %s\n End: %s"
                % (sDATE.strftime("%d %b %Y"), eDATE.strftime("%d %b %Y")),
                loc="right",
            )
            plt.title("Hours: %s" % HOURS)

            plt.savefig(
                SAVEDIR
                + "CONUS_HRRR_RMSD-%s_hours-%s"
                % (
                    variable.replace(":", "-").replace(" ", "-"),
                    "-".join("%02d" % x for x in HOURS),
                )
            )

            plt.cla()
            plt.clf()

            mU.pcolormesh(S["lon"], S["lat"], S["RMSD"], latlon=True, vmin=0)
            cb = plt.colorbar(orientation="horizontal", shrink=0.8, pad=0.01)
            cb.set_label("Root-Mean-Square-Difference")

            mU.drawcoastlines(color="w")
            mU.drawcountries(color="w")
            mU.drawstates(color="w")

            plt.title("HRRR RMSD %s" % (variable), loc="left", fontweight="semibold")
            plt.title(
                "Start: %s\n End: %s"
                % (sDATE.strftime("%d %b %Y"), eDATE.strftime("%d %b %Y")),
                loc="right",
            )
            plt.title("Hours: %s" % HOURS)

            plt.savefig(
                SAVEDIR
                + "WEST_HRRR_RMSD-%s_hours-%s"
                % (
                    variable.replace(":", "-").replace(" ", "-"),
                    "-".join("%02d" % x for x in HOURS),
                )
            )

            plt.cla()
            plt.clf()
