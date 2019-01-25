# Brian Blaylock
# January 23, 2019

from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os
import multiprocessing

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
from BB_HRRR.HRRR_Pando import get_hrrr_latlon, pluck_hrrr_point, get_hrrr_variable
from BB_HRRR.HRRR_Spread import spread, get_HRRR_value, mean_spread_MP
from BB_maps.my_basemap import draw_centermap, draw_HRRR_map


def get_all_variances(DATES_LIST, variable, fxx=range(0,19,6), verbose=False):
    args = [[(i, len(DATES_LIST)), D, variable, fxx, verbose] for i, D in enumerate(DATES_LIST)]
    reduce_CPUs = 2 # don't eat all computer resources
    cpus = np.minimum(multiprocessing.cpu_count() - reduce_CPUs, len(args))
    P = multiprocessing.Pool(cpus)
    all_variances = P.map(mean_spread_MP, args)
    P.close()
    mean_spread = np.sqrt(np.mean(all_variances, axis=0))
    return all_variances
# ================================================================
# ================================================================


m = draw_HRRR_map()

LAND = get_hrrr_variable(datetime(2019, 1, 1), 'LAND:surface')

VARS = ['GUST:surface', 'UVGRD:10 m', 'REFC:entire', 'LTNG:entire', 'CAPE:surface', 'TMP:2 m', 'DPT:2 m', 'HGT:500']

seasons = {'DJF': {'sDATE':datetime(2017, 12, 1),
                   'eDATE':datetime(2018, 3, 1)},
           'MAM': {'sDATE':datetime(2018, 3, 1),
                   'eDATE':datetime(2018, 6, 1)},
           'JJA': {'sDATE':datetime(2018, 6, 1),
                   'eDATE':datetime(2018, 9, 1)},
           'SON': {'sDATE':datetime(2018, 9, 1),
                   'eDATE':datetime(2018, 12, 1)},}

for variable in VARS:
    for season in seasons.keys():
        plt.clf()
        plt.cla()
        sDATE = seasons[season]['sDATE']
        eDATE = seasons[season]['eDATE']
        # List of all days for the requested season
        hours = (eDATE-sDATE).days*24
        DATES = [sDATE+timedelta(hours=h) for h in range(hours)]
        print(variable, season)
        
        # Dates for each set of hours
        DATES_0309 = list(filter(lambda x: x.hour in range(3,9), DATES))
        DATES_0915 = list(filter(lambda x: x.hour in range(9,15), DATES))
        DATES_1521 = list(filter(lambda x: x.hour in range(15,21), DATES))
        DATES_2103 = list(filter(lambda x: x.hour in list(range(21,24))+list(range(0,3)), DATES))
        
        var_0309 = get_all_variances(DATES_0309, variable)
        var_0915 = get_all_variances(DATES_0915, variable)
        var_1521 = get_all_variances(DATES_1521, variable)
        var_2103 = get_all_variances(DATES_2103, variable)
        print('got data for', variable, season)
        
        print('making plot for', variable, season)
        labels = ['0300-0900 UTC', '0900-1500 UTC', '1500-2100 UTC', '2100-0300 UTC']
        fig, axes = plt.subplots(2,2, figsize=(10,6))
        axes = axes.flatten()
        for ax, v, label in zip(axes, [var_0309, var_0915, var_1521, var_2103], labels):
            plt.sca(ax)
            mesh = m.pcolormesh(LAND['lon'], LAND['lat'], np.sqrt(np.mean(v, axis=0)),
                                vmin=0, vmax=3,
                                latlon=True)
            m.drawcoastlines()
            plt.title(label)

        cbar_ax = fig.add_axes([0.25, 0.05, 0.5, 0.02]) # [left, bottom, width, height]
        cb = fig.colorbar(mesh, cax=cbar_ax, ticks=np.arange(0,3.1,.5), orientation='horizontal')
        cb.ax.set_xlabel(r'Mean Model Spread');
        
        plt.savefig('./%s_%s' % (season, variable.replace(":", "_").replace(" ", "_")), bbox_inches='tight')
        
        
        # Save mean spread statistics for area
        #mean_spread = np.sqrt(np.mean(all_variances, axis=0))
        seasons[season]['mean domain spread'] = [np.mean(np.sqrt(np.mean(i, axis=0))) for i in [var_0309, var_0915, var_1521, var_2103]]
        
        seasons[season]['mean domain spread LAND'] = [np.mean(np.ma.array(np.sqrt(np.mean(i, axis=0)), mask=LAND['value']==0)) for i in [var_0309, var_0915, var_1521, var_2103]]
        
        seasons[season]['mean domain spread WATER'] = [np.mean(np.ma.array(np.sqrt(np.mean(i, axis=0)), mask=LAND['value']==1)) for i in [var_0309, var_0915, var_1521, var_2103]]
        
        plt.figure(2)
        labels = ['0300-0900 UTC', '0900-1500 UTC', '1500-2100 UTC', '2100-0300 UTC']
        for i in seasons.keys():
            plt.plot(seasons[i]['mean domain spread'], label=i)
        plt.xticks(range(len(labels)), labels)
        plt.legend()
        plt.grid()
        plt.ylabel('Average Mean Spread')
        plt.savefig('./%s_domain_average_spread' % variable.replace(":", "_").replace(" ", "_"))
        
        plt.figure(3)
        labels = ['0300-0900 UTC', '0900-1500 UTC', '1500-2100 UTC', '2100-0300 UTC']
        for i in seasons.keys():
            plt.plot(seasons[i]['mean domain spread LAND'], label=i)
        plt.xticks(range(len(labels)), labels)
        plt.legend()
        plt.grid()
        plt.ylabel('Average Mean Spread')
        plt.savefig('./%s_domain_average_spread_LAND' % variable.replace(":", "_").replace(" ", "_"))
        
        plt.figure(4)
        labels = ['0300-0900 UTC', '0900-1500 UTC', '1500-2100 UTC', '2100-0300 UTC']
        for i in seasons.keys():
            plt.plot(seasons[i]['mean domain spread WATER'], label=i)
        plt.xticks(range(len(labels)), labels)
        plt.legend()
        plt.grid()
        plt.ylabel('Average Mean Spread')
        plt.savefig('./%s_domain_average_spread_WATER' % variable.replace(":", "_").replace(" ", "_"))
        
        
        
        
        
        
    