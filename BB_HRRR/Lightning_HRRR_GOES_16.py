# Brian Blaylock
# September 27, 2018

"""
Plot image of GOES ABI, GLM overlaid with HRRR RMSDs
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys

sys.path.append("/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3")

from BB_GOES.get_ABI import get_GOES_truecolor, file_nearest
from BB_GOES.get_GLM import get_GLM_files_for_ABI, accumulate_GLM
from BB_HRRR.HRRR_Pando import get_hrrr_variable
from BB_HRRR.HRRR_RMSD import RMSD
from BB_maps.my_basemap import draw_HRRR_map
from BB_cmap.NWS_standard_cmap import cm_wind, cm_temp, cm_dpt
from BB_cmap.reflectivity_cmap import reflect_ncdc

m = draw_HRRR_map()

import matplotlib as mpl

mpl.rcParams["figure.figsize"] = [15, 15]
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


DATES = [
    datetime(2018, 7, 24, 0),
    datetime(2018, 9, 10, 0),
    datetime(2018, 8, 6, 4),
    datetime(2018, 8, 26, 23),
    datetime(2018, 7, 10, 9),
    datetime(2018, 9, 27, 0),
]

sDATE = datetime(2018, 9, 30)
eDATE = datetime(2018, 10, 1)

DATES += [
    sDATE + timedelta(hours=h)
    for h in range((eDATE - sDATE).days * 24 + int((eDATE - sDATE).seconds / 60 / 60))
]


for DATE in DATES:
    SAVEDIR = (
        "/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_RMSE/RMSE_events/%s/"
        % DATE.strftime("%Y-%m-%d_%H%M")
    )
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
        # then link the photo viewer
        photo_viewer = "/uufs/chpc.utah.edu/common/home/u0553130/public_html/Brian_Blaylock/photo_viewer/photo_viewer.php"
        os.link(photo_viewer, SAVEDIR + "photo_viewer.php")

    # Get GOES16 ABI
    FILE = file_nearest(DATE)
    ABI = get_GOES_truecolor(FILE, verbose=False)

    # Get GOES16 GLM
    GLM_files = get_GLM_files_for_ABI(FILE)
    GLM = accumulate_GLM(GLM_files)

    for variable in [
        "REFC:entire",
        "TMP:2 m",
        "WIND:10 m",
        "LTNG:entire",
        "HGT:500 mb",
        "DPT:2 m",
        "CAPE:surface",
        "UGRD:10 m",
        "VGRD:10 m",
    ]:

        # Get HRRR RMSDs
        rmsd = RMSD(DATE, variable)

        if variable in ["LTNG:entire"]:
            contours = [0.75, 20]
            units = "Max Flashes/km2/5min"
            fxx = 1
            mask_below_this = 0.02
            cmap = {"cmap": "plasma", "vmax": 2, "vmin": 0}
        elif variable in ["HGT:500 mb"]:
            contours = [15, 200]
            units = "meters"
            fxx = 0
            mask_below_this = 0
            cmap = {"cmap": "viridis", "vmax": 5940, "vmin": 5400}
        elif variable in ["CAPE:surface"]:
            contours = [1000, 7000]
            units = r"J kg$\mathregular{^{-1}}$"
            fxx = 0
            mask_below_this = 0
            cmap = {"cmap": "Oranges", "vmax": 3500, "vmin": 0}
        elif variable in ["REFC:entire"]:
            contours = [20, 200]
            units = "dBZ"
            fxx = 0
            mask_below_this = 0
            cmap = reflect_ncdc()
        elif variable in ["TMP:2 m"]:
            contours = [4, 200]
            units = "C"
            fxx = 0
            mask_below_this = -100
            cmap = cm_temp()
        elif variable in ["DPT:2 m"]:
            contours = [5, 200]
            units = "C"
            fxx = 0
            mask_below_this = -100
            cmap = cm_dpt()
        elif variable in ["WIND:10 m"]:
            contours = [4, 20]
            units = r"m s$\mathregular{^{-1}}$"
            fxx = 1
            mask_below_this = -1000
            cmap = cm_wind()
        elif variable in ["UGRD:10 m", "VGRD:10 m"]:
            contours = [4, 20]
            units = r"m s$\mathregular{^{-1}}$"
            fxx = 1
            mask_below_this = -1000
            cmap = {"cmap": "PuOr", "vmax": 30, "vmin": -30}

        # Get HRRR Analysis
        runDATE = DATE - timedelta(hours=fxx)
        H = get_hrrr_variable(runDATE, variable, fxx=fxx)
        if variable.split(":")[0] == "UVGRD":
            masked = H["SPEED"]
        else:
            masked = H["value"]
        masked = np.ma.array(masked)
        masked[masked <= mask_below_this] = np.ma.masked

        if variable.split(":")[0] in ["TMP", "DPT"]:
            masked -= 273.15

        # Plot Images

        ## -------------- Figure 1: RMSD over ABI and GLM ---------------------
        # Plot ABI
        newmap = m.pcolormesh(
            ABI["lon"],
            ABI["lat"],
            ABI["TrueColor"][:, :, 0],
            color=ABI["rgb_tuple"],
            linewidth=0,
            latlon=True,
        )
        newmap.set_array(None)

        # Plot HRRR RMSD
        m.contour(
            rmsd["lon"],
            rmsd["lat"],
            rmsd["RMSD"],
            levels=contours,
            colors="magenta",
            linewidths=0.75,
            latlon=True,
        )
        m.contourf(
            rmsd["lon"],
            rmsd["lat"],
            rmsd["RMSD"],
            levels=contours,
            colors="magenta",
            latlon=True,
            alpha=0.35,
        )
        plt.xlabel("RMSD > %s %s" % (contours[0], units), color="magenta")

        # Plot GLM
        m.scatter(
            GLM["longitude"], GLM["latitude"], c="yellow", marker="+", latlon=True
        )

        m.drawcoastlines(color="grey")
        m.drawcountries(color="grey")
        m.drawstates(color="grey")

        plt.title(
            "GOES16 ABI+GLM\n%s to %s"
            % (
                ABI["sDATE"].strftime("%Y-%m-%d %H:%M"),
                ABI["eDATE"].strftime("%Y-%m-%d %H:%M"),
            ),
            loc="left",
        )
        plt.title(
            "HRRR %s RMSD\nvalid: %s"
            % (variable, H["valid"].strftime("%Y-%m-%d %H:%M")),
            loc="right",
        )

        plt.savefig(
            SAVEDIR
            + "GLM_ABI_RMSD-_%s" % (variable.replace(":", "-").replace(" ", "-"))
        )
        plt.cla()
        plt.clf()

        ## ------------- Figure 2: RMSD over HRRR analysis and GLM ------------
        # Plot HRRR value
        m.pcolormesh(
            H["lon"],
            H["lat"],
            masked,
            latlon=True,
            cmap=cmap["cmap"],
            vmax=cmap["vmax"],
            vmin=cmap["vmin"],
        )
        plt.colorbar(orientation="horizontal", shrink=0.8, pad=0.05)

        # Plot HRRR RMSD
        m.contour(
            rmsd["lon"],
            rmsd["lat"],
            rmsd["RMSD"],
            levels=contours,
            colors="magenta",
            linewidths=0.75,
            latlon=True,
        )
        plt.xlabel("RMSD > %s %s" % (contours[0], units), color="magenta")

        # Plot GLM
        # m.scatter(GLM['longitude'], GLM['latitude'], c='yellow', marker='+', latlon=True)
        m.scatter(
            GLM["longitude"],
            GLM["latitude"],
            edgecolors="k",
            s=300,
            marker="o",
            facecolors="none",
            latlon=True,
            zorder=100,
            linewidth=0.2,
        )

        m.drawcoastlines(color="grey")
        m.drawcountries(color="grey")
        m.drawstates(color="grey")

        plt.title(
            "GOES16 GLM\n%s to %s"
            % (
                ABI["sDATE"].strftime("%Y-%m-%d %H:%M"),
                ABI["eDATE"].strftime("%Y-%m-%d %H:%M"),
            ),
            loc="left",
        )
        plt.title(
            "HRRR %s RMSD and F%02d\nvalid: %s"
            % (variable, fxx, H["valid"].strftime("%Y-%m-%d %H:%M")),
            loc="right",
        )

        plt.savefig(
            SAVEDIR
            + "GLM_anlys_RMSD-_%s" % (variable.replace(":", "-").replace(" ", "-"))
        )
        plt.cla()
        plt.clf()

        print("Finished %s %s" % (variable, DATE))
