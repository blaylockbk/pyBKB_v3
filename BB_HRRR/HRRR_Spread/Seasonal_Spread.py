# Brian Blaylock
# January 23, 2019

from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os
import multiprocessing

import sys

sys.path.append("/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3")
from BB_HRRR.HRRR_Pando import get_hrrr_latlon, pluck_hrrr_point, get_hrrr_variable
from BB_HRRR.HRRR_Spread import spread, get_HRRR_value, mean_spread_MP
from BB_maps.my_basemap import draw_centermap, draw_HRRR_map


def get_all_variances(DATES_LIST, variable, fxx=range(0, 19, 6), verbose=False):
    args = [
        [(i, len(DATES_LIST)), D, variable, fxx, verbose]
        for i, D in enumerate(DATES_LIST)
    ]
    reduce_CPUs = 2  # don't eat all computer resources
    cpus = np.minimum(multiprocessing.cpu_count() - reduce_CPUs, len(args))
    P = multiprocessing.Pool(cpus)
    all_variances = P.map(mean_spread_MP, args)
    P.close()
    mean_spread = np.sqrt(np.mean(all_variances, axis=0))
    return all_variances


# ================================================================
# ================================================================


m = draw_HRRR_map()

LAND = get_hrrr_variable(datetime(2019, 1, 1), "LAND:surface")

VARS = [
    "GUST:surface",
    "UVGRD:10 m",
    "REFC:entire",
    "LTNG:entire",
    "CAPE:surface",
    "TMP:2 m",
    "DPT:2 m",
    "HGT:500",
]

VARS = {
    "TMP:2 m": {
        "cmap": "magma",
        "vmax": 2.5,
        "vmin": 0,
        "label": "2 m Temperature",
        "units": "C",
    },
    "DPT:2 m": {
        "cmap": "magma",
        "vmax": 5,
        "vmin": 0,
        "label": "2 m Dew Point",
        "units": "C",
    },
    "GUST:surface": {
        "cmap": "magma",
        "vmax": 3.5,
        "vmin": 0,
        "label": "Surface Wind Gust",
        "units": r"m s$\mathregular{^{-1}}$",
    },
    "UGRD:10 m": {
        "cmap": "magma",
        "vmax": 3.25,
        "vmin": 0,
        "label": "10 m U Wind Component",
        "units": r"m s$\mathregular{^{-1}}$",
    },
    "VGRD:10 m": {
        "cmap": "magma",
        "vmax": 3.25,
        "vmin": 0,
        "label": "10 m V Wind Component",
        "units": r"m s$\mathregular{^{-1}}$",
    },
    "REFC:entire": {
        "cmap": "magma",
        "vmax": 15,
        "vmin": 0,
        "label": "Simulated Composite Reflectivity",
        "units": "dBZ",
    },
    "LTNG:entire": {
        "cmap": "magma",
        "vmax": 0.6,
        "vmin": 0,
        "label": "Hourly Max Lightning Threat",
        "units": r"Flashes km$\mathregular{^{-2}}$ 5min$\mathregular{^{-1}}$",
    },
    "HGT:500 mb": {
        "cmap": "magma",
        "vmax": 8,
        "vmin": 0,
        "label": "500 hPa Geopotential Height",
        "units": "m",
    },
    "CAPE:surface": {
        "cmap": "magma",
        "vmax": 1000,
        "vmin": 0,
        "label": "Convective Available Potential Energy",
        "units": "J kg",
    },
    "APCP:surface": {
        "cmap": "magma",
        "vmax": 5,
        "vmin": 0,
        "label": "1 hr Accumulated Precipitation",
        "units": "mm",
    },
    "WIND:10 m": {
        "cmap": "magma",
        "vmax": 3,
        "vmin": 0,
        "label": "10 m Hourly Max Wind Speed",
        "units": r"m s$\mathregular{^{-1}}$",
    },
    "UVGRD:10 m": {
        "cmap": "magma",
        "vmax": 2.5,
        "vmin": 0,
        "label": "10 m Wind Speed",
        "units": r"m s$\mathregular{^{-1}}$",
    },
}

seasons = {  #'DJF': {'sDATE':datetime(2017, 12, 1),
    #        'eDATE':datetime(2018, 3, 1)},
    #'MAM': {'sDATE':datetime(2018, 3, 1),
    #        'eDATE':datetime(2018, 6, 1)},
    "JJA": {"sDATE": datetime(2018, 6, 1), "eDATE": datetime(2018, 9, 1)},
    #'SON': {'sDATE':datetime(2018, 9, 1),
    #        'eDATE':datetime(2018, 12, 1)}
}

select_VARS = {}
select_VARS["LTNG:entire"] = VARS["LTNG:entire"]

for variable in select_VARS:
    for season in seasons.keys():
        plt.clf()
        plt.cla()
        sDATE = seasons[season]["sDATE"]
        eDATE = seasons[season]["eDATE"]
        # List of all days for the requested season
        hours = (eDATE - sDATE).days * 24
        DATES = [sDATE + timedelta(hours=h) for h in range(hours)]
        print(variable, season)

        # Dates for each set of hours
        DATES_0309 = list(filter(lambda x: x.hour in range(3, 9), DATES))
        DATES_0915 = list(filter(lambda x: x.hour in range(9, 15), DATES))
        DATES_1521 = list(filter(lambda x: x.hour in range(15, 21), DATES))
        DATES_2103 = list(
            filter(lambda x: x.hour in list(range(21, 24)) + list(range(0, 3)), DATES)
        )

        timer = datetime.now()
        var_0309 = get_all_variances(DATES_0309, variable)
        print("finished 1 of 4. Timer:", datetime.now() - timer)
        var_0915 = get_all_variances(DATES_0915, variable)
        print("finished 2 of 4. Timer:", datetime.now() - timer)
        var_1521 = get_all_variances(DATES_1521, variable)
        print("finished 3 of 4. Timer:", datetime.now() - timer)
        var_2103 = get_all_variances(DATES_2103, variable)
        print("finished 4 of 4. Timer:", datetime.now() - timer)
        print("got data for", variable, season)

        print("making plot for", variable, season)
        labels = ["0300-0900 UTC", "0900-1500 UTC", "1500-2100 UTC", "2100-0300 UTC"]
        fig, axes = plt.subplots(2, 2, figsize=(10, 6))
        axes = axes.flatten()
        for ax, v, label in zip(axes, [var_0309, var_0915, var_1521, var_2103], labels):
            plt.sca(ax)
            mesh = m.pcolormesh(
                LAND["lon"],
                LAND["lat"],
                np.sqrt(np.mean(v, axis=0)),
                vmin=VARS[variable]["vmin"],
                vmax=VARS[variable]["vmax"],
                latlon=True,
            )
            m.drawcoastlines()
            plt.title(label)

        cbar_ax = fig.add_axes([0.25, 0.05, 0.5, 0.02])  # [left, bottom, width, height]
        cb = fig.colorbar(mesh, cax=cbar_ax, orientation="horizontal")
        cb.ax.set_xlabel(
            r"%s Mean Model Spread \n %s (%s)"
            % (season, VARS[variable]["label"], VARS[variable]["units"])
        )

        plt.savefig(
            "./%s_%s" % (season, variable.replace(":", "_").replace(" ", "_")),
            bbox_inches="tight",
        )

        # Save mean spread statistics for area
        # mean_spread = np.sqrt(np.mean(all_variances, axis=0))
        seasons[season]["%s mean domain spread" % variable] = [
            np.mean(np.sqrt(np.mean(i, axis=0)))
            for i in [var_0309, var_0915, var_1521, var_2103]
        ]

        seasons[season]["%s mean domain spread LAND" % variable] = [
            np.mean(np.ma.array(np.sqrt(np.mean(i, axis=0)), mask=LAND["value"] == 0))
            for i in [var_0309, var_0915, var_1521, var_2103]
        ]

        seasons[season]["%s mean domain spread WATER" % variable] = [
            np.mean(np.ma.array(np.sqrt(np.mean(i, axis=0)), mask=LAND["value"] == 1))
            for i in [var_0309, var_0915, var_1521, var_2103]
        ]

    plt.figure(2)
    plt.cla()
    plt.clf()
    for i in seasons.keys():
        plt.plot(seasons[i]["%s mean domain spread" % variable], label=i)
    plt.xticks(range(len(labels)), labels)
    plt.legend()
    plt.grid()
    plt.ylabel("Average Mean Spread")
    plt.savefig(
        "./%s_domain_average_spread" % variable.replace(":", "_").replace(" ", "_")
    )

    plt.figure(3)
    plt.cla()
    plt.clf()
    for i in seasons.keys():
        plt.plot(seasons[i]["%s mean domain spread LAND" % variable], label=i)
    plt.xticks(range(len(labels)), labels)
    plt.legend()
    plt.grid()
    plt.ylabel("Average Mean Spread")
    plt.savefig(
        "./%s_domain_average_spread_LAND" % variable.replace(":", "_").replace(" ", "_")
    )

    plt.figure(4)
    plt.cla()
    plt.clf()
    for i in seasons.keys():
        plt.plot(seasons[i]["%s mean domain spread WATER" % variable], label=i)
    plt.xticks(range(len(labels)), labels)
    plt.legend()
    plt.grid()
    plt.ylabel("Average Mean Spread")
    plt.savefig(
        "./%s_domain_average_spread_WATER"
        % variable.replace(":", "_").replace(" ", "_")
    )
