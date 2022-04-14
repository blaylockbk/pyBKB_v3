# Brian Blaylock
# 29 January 2018

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import multiprocessing
import os

import sys

sys.path.append("/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/")
from BB_HRRR.HRRR_Pando import get_hrrr_variable
from BB_GOES.get_GLM import get_GLM_file_nearesttime, accumulate_GLM
from BB_datetimes.range import range_dates
from BB_maps.my_basemap import draw_centermap
from BB_cmap.reflectivity_cmap import reflect_ncdc
from fires_list import get_fire

import matplotlib as mpl

mpl.rcParams["figure.titlesize"] = 15
mpl.rcParams["figure.titleweight"] = "bold"
mpl.rcParams["xtick.labelsize"] = 10
mpl.rcParams["ytick.labelsize"] = 10
mpl.rcParams["axes.labelsize"] = 12
mpl.rcParams["axes.titlesize"] = 15
mpl.rcParams["lines.linewidth"] = 1.8
mpl.rcParams["grid.linewidth"] = 0.25
mpl.rcParams["figure.subplot.wspace"] = 0.05
mpl.rcParams["figure.subplot.hspace"] = 0.05
mpl.rcParams["legend.fontsize"] = 10
mpl.rcParams["legend.framealpha"] = 0.75
mpl.rcParams["legend.loc"] = "best"
mpl.rcParams["savefig.bbox"] = "tight"
mpl.rcParams["savefig.dpi"] = 100

c = reflect_ncdc()


def make_plot(inputs):
    fire, m, d = inputs

    plt.cla()
    plt.clf()

    Hrefc = get_hrrr_variable(d, "REFC:entire", verbose=False)
    Hltng_f01 = get_hrrr_variable(
        d - timedelta(hours=1), "LTNG:entire", fxx=1, value_only=True, verbose=False
    )
    Hltng_f03 = get_hrrr_variable(
        d - timedelta(hours=3), "LTNG:entire", fxx=3, value_only=True, verbose=False
    )
    Hltng_f06 = get_hrrr_variable(
        d - timedelta(hours=6), "LTNG:entire", fxx=6, value_only=True, verbose=False
    )
    Hltng_f09 = get_hrrr_variable(
        d - timedelta(hours=9), "LTNG:entire", fxx=9, value_only=True, verbose=False
    )
    Hltng_f12 = get_hrrr_variable(
        d - timedelta(hours=12), "LTNG:entire", fxx=12, value_only=True, verbose=False
    )
    Hltng_f15 = get_hrrr_variable(
        d - timedelta(hours=15), "LTNG:entire", fxx=15, value_only=True, verbose=False
    )
    Hltng_f18 = get_hrrr_variable(
        d - timedelta(hours=18), "LTNG:entire", fxx=18, value_only=True, verbose=False
    )

    if d > datetime(2018, 1, 1):
        glm_files = get_GLM_file_nearesttime(
            d - timedelta(minutes=30), window=90, verbose=False
        )
        GLM = accumulate_GLM(glm_files)

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 10))
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 10))

    plt.sca(ax1)
    plt.title(
        "%s\nValid Date: %s"
        % (fire["name"], Hrefc["valid"].strftime("%d %b %Y %H:%M UTC"))
    )
    m.pcolormesh(
        Hrefc["lon"],
        Hrefc["lat"],
        Hrefc["value"],
        cmap=c["cmap"],
        vmin=c["vmin"],
        vmax=c["vmax"],
    )
    m.drawstates()
    m.drawcounties()
    m.arcgisimage()
    m.scatter(
        fire["longitude"],
        fire["latitude"],
        latlon=True,
        facecolors="none",
        edgecolors="w",
        s=100,
    )

    plt.sca(ax2)
    # Since contours are made ever 0.05, this represents approx. 1/2 flash in the hour per km^2 (becuase 0.05flashes*60min/5min/km^2= 1.2 flashes/km^2)
    c_interval = 0.05
    plt.title(
        "Lightning Threat: F01, F03, F06, F09, F12, F15, F18\n(white, blue, green, coral, orange, purple, pink)"
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f18["value"],
        latlon=True,
        colors="deeppink",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f15["value"],
        latlon=True,
        colors="purple",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f12["value"],
        latlon=True,
        colors="darkorange",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f09["value"],
        latlon=True,
        colors="coral",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f06["value"],
        latlon=True,
        colors="lawngreen",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f03["value"],
        latlon=True,
        colors="dodgerblue",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.contour(
        Hrefc["lon"],
        Hrefc["lat"],
        Hltng_f01["value"],
        latlon=True,
        colors="white",
        linewidths=1,
        levels=np.arange(0, 20, c_interval),
    )
    m.drawstates()
    m.drawcounties()
    m.arcgisimage()
    m.scatter(
        fire["longitude"],
        fire["latitude"],
        latlon=True,
        facecolors="none",
        edgecolors="w",
        s=100,
    )

    if d > datetime(2018, 1, 1):
        plt.sca(ax3)
        plt.title("GLM flashes for previous hour")
        m.scatter(GLM["longitude"], GLM["latitude"], marker="+", c="yellow")
        m.drawstates()
        m.drawcounties()
        m.arcgisimage()
        m.scatter(
            fire["longitude"],
            fire["latitude"],
            latlon=True,
            facecolors="none",
            edgecolors="w",
            s=100,
        )

    if d > datetime(2018, 1, 1):
        fig.set_size_inches(20, 10)
    else:
        fig.set_size_inches(15, 10)

    SAVEDIR = (
        "/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/JFSP/%s/"
        % fire["name"].replace(" ", "_")
    )
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
    plt.savefig(SAVEDIR + "%s" % Hrefc["valid"].strftime("valid_%Y%m%d-%H%M"))

    # plt.close()


# =============================================================================

if __name__ == "__main__":

    # Define the fire or event of interest
    fire = get_fire("Mallard")

    # Make map
    m = draw_centermap(fire["latitude"], fire["longitude"])

    # Date info
    sDATE = fire["sDATE"]
    eDATE = sDATE + timedelta(days=2)
    DATES = range_dates(sDATE, eDATE, HOURS=True)

    # Generate plots with multiprocessing
    timer = datetime.now()

    inputs = [(fire, m, d) for d in DATES]

    cpus = multiprocessing.cpu_count()
    p = multiprocessing.Pool(np.minimum(12, cpus))
    p.map(make_plot, inputs)
    p.close()

    print("-------- Finished -----------")
    print(datetime.now() - timer)
