#!/uufs/chpc.utah.edu/common/home/u0553130/anaconda3/envs/pyBKB_v3/bin/python

# Brian Blaylock
# May 2, 2018             # Went bowling with my friend William Rees last night

"""
Plots HRRR data on a map for the specified domain.

Note: For CGI, cannot print anything to screen when outputting a .png file

Contents:
    load_lats_lons  - Preload the latitude and longitude for the domain
    draw_map_base   - Creates the map object, draws state lines (etc), draws base image
    draw_wind       - Color fill, high winds, barbs, quivers, 95th percentile, divergence, convergence
    draw_gust       - Hatching for strong gusts
    draw_refc       - Composite reflectivity fill (masked) and contours
    draw_tmp_dpt    - Color fill TMP or DPT, freezing contours, 5th and 95th percentile
    draw_rh         - Color fill, compute relative humidity at specified levels
    draw_hgt        - Contour height at levels, 5th and 95th percentile for 500 hPa
    draw_mslp       - Color fill and contour for Mean Sea Level Pressure
    draw_redflag    - Color fill red flag conditions and red flag potential
    draw_variable   - Generic color fill for any other variable, masked option available
"""


import numpy as np
from datetime import datetime, timedelta
import h5py

import matplotlib as mpl
#mpl.use('Agg')   # uncomment for cronjob
import matplotlib.pyplot as plt
mpl.rcParams['figure.figsize'] = [12, 10]
mpl.rcParams['savefig.bbox'] = 'tight'
mpl.rcParams['savefig.dpi'] = 100     # For web
mpl.rcParams['figure.titleweight'] = 'bold'
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['axes.labelsize'] = 8
mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['figure.subplot.hspace'] = 0.01

# Colorbar
pad = 0.01
shrink = 0.7


import sys, os
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3')
# For some reason, the pyBKB_v3 version of basemap won't load correctly.
# So, we hack it an load it from the version 2.7 packages
#sys.path.append('/uufs/chpc.utah.edu/sys/pkg/python/2.7.3_rhel6/lib/python2.7/site-packages/')
#import BB_maps.my_basemap import draw_HRRR_map, draw_ALASKA_map
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon, hrrr_subset
from BB_MesoWest.get_MesoWest import get_mesowest_stninfo
from BB_wx_calcs.humidity import Tempdwpt_to_RH
from BB_wx_calcs.pressure import vapor_pressure_deficit
from BB_cmap.NWS_standard_cmap import *
from BB_cmap.reflectivity_colormap import reflect_ncdc


###############################################################################
###############################################################################

def load_lats_lons(model):
    """
    Preload the latitude and longitude grid
    """
    if model in ['hrrr', 'hrrrX']:
        lats, lons = get_hrrr_latlon(DICT=False)
    elif model == 'hrrrak':
        AK = get_hrrr_variable(datetime(2018, 2, 24, 15), 'TMP:2 m', fxx=0, model='hrrrak', verbose=False)
        lats = AK['lat']
        lons = AK['lon']
    return [lats, lons]
'''

def draw_map_base(model, dsize, background,
                  location, lat, lon,
                  RUNDATE, VALIDDATE, fxx,
                  map_res='l',
                  plot_title=True):
    """
    Create basemap with the base image (arcgis image, model terrain, model landuse)

    Inputs:
        map_res - Map resolution: 'l' for low, 'i' for intermediate, 'h' for high, 'f' for full
        title   - True: Add a title to the plot
                  False: Do not add a title

    Output:
        A list of [the map object, transparency for pcolormesh, subset half_box, barb thin amount]
    """
    if dsize == 'full':
        if model != 'hrrrak':
            barb_thin = 70
            m = draw_HRRR_map()
        else:
            barb_thin = 75
            m = draw_ALASKA_map(res=map_res, area_thresh=2500)
        alpha = 1
        half_box = None
        m.drawmapboundary(fill_color='lightblue', zorder=0)
        m.fillcontinents(color='tan',lake_color='lightblue', zorder=1)
    else:
        if dsize == 'small':
            plus_minus_latlon = .27      # +/- latlon box around center point
            barb_thin = 1               # Thin out excessive wind barbs
            arcgis_res = 1000            # ArcGIS image resolution
            half_box = 15                # Half box for subset when plotting barbs
            alpha = .75                  # Alpha (pcolormesh transparency)
            area_thresh = 1              # Area Threshold for features (island and water bodies)
            if map_res != 'f':
                map_res = 'h'                # overwrite the map res default to be high if not requesting full.
        elif dsize == 'medium':
            plus_minus_latlon = .75; barb_thin = 2;  arcgis_res = 2500; half_box = 35;  alpha = 1; area_thresh=1
            if map_res != 'f':
                map_res = 'h'
        elif dsize == 'large':
            plus_minus_latlon = 2.5; barb_thin = 6;  arcgis_res = 800;  half_box = 110; alpha = 1; area_thresh=50
            if map_res != 'f':
                map_res = 'h'
        elif dsize == 'xlarge':
            plus_minus_latlon = 5;   barb_thin = 12; arcgis_res = 700;  half_box = 210; alpha = 1; area_thresh=500
            if map_res != 'f':
                map_res = 'i'
        elif dsize == 'xxlarge':
            plus_minus_latlon = 10;  barb_thin = 25; arcgis_res = 700;  half_box = 430; alpha = 1; area_thresh=500
        elif dsize == 'xxxlarge':
            plus_minus_latlon = 15;  barb_thin = 35; arcgis_res = 1000; half_box = 700; alpha = 1;  area_thresh=1200
        
        m = Basemap(resolution=map_res,
                    projection='cyl',
                    area_thresh=area_thresh,
                    llcrnrlon=lon-plus_minus_latlon, llcrnrlat=lat-plus_minus_latlon,
                    urcrnrlon=lon+plus_minus_latlon, urcrnrlat=lat+plus_minus_latlon,)
        
        if background == 'arcgis':
            m.arcgisimage(service='World_Shaded_Relief', xpixels=arcgis_res, verbose=False)
        elif background == 'arcgisSat':
            m.arcgisimage(service='ESRI_Imagery_World_2D', xpixels=arcgis_res, verbose=False)
        elif background == 'arcgisRoad':
            m.arcgisimage(service='NatGeo_World_Map', xpixels=arcgis_res, verbose=False)
    
    m.drawcountries(zorder=1000)
    m.drawstates(zorder=1000)
    m.drawcoastlines(zorder=1000)
    if dsize in ['small', 'medium', 'large']:
        try:
            m.drawcounties(zorder=1000)
        except:
            "Will not work for [URL].cgi images"
            pass
    
    if background == 'terrain':
        # Get data
        H_ter = get_hrrr_variable(RUNDATE, 'HGT:surface',
                                  model=model, fxx=fxx,
                                  outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                  verbose=False, value_only=False)
        H_land = get_hrrr_variable(RUNDATE, 'LAND:surface',
                                   model=model, fxx=fxx,
                                   outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                   verbose=False, value_only=True)        
        # Plot the terrain
        m.contourf(H_ter['lon'], H_ter['lat'], H_ter['value'],
                   levels=range(0, 4000, 200),
                   cmap='Greys_r',
                   zorder=1,
                   latlon=True)
        # Plot Water area
        m.contour(H_ter['lon'], H_ter['lat'], H_land['value'],
                  levels=[0, 1],
                  colors='b',
                  zorder=1,
                  latlon=True)
    elif background == 'landuse':
        from BB_cmap.landuse_colormap import LU_MODIS21
        if model=='hrrr':
            VGTYP = 'VGTYP:surface'
        else:
            VGTYP = 'var discipline=2 center=59 local_table=1 parmcat=0 parm=198'
        H_LU = get_hrrr_variable(RUNDATE, VGTYP,
                                 model=model, fxx=fxx,
                                 outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                 verbose=False, value_only=False)
        # Plot the terrain
        cm, labels = LU_MODIS21()
        m.pcolormesh(H_LU['lon'], H_LU['lat'], H_LU['value'],
                     cmap=cm, vmin=1, vmax=len(labels) + 1,
                     zorder=1,
                     latlon=True)

    if plot_title:
        if dsize != 'full':
            m.scatter(lon, lat, marker='+', c='r', s=100, zorder=1000, latlon=True)
            plt.title('Center: %s\n%s' % (location, model.upper()), fontweight='bold')
        else:
            plt.title('%s' % (model.upper()), fontweight='bold')
        plt.title('Run: %s F%02d' % (RUNDATE.strftime('%Y-%m-%d %H:%M UTC'), fxx), loc='left')
        plt.title('Valid: %s' % VALIDDATE.strftime('%Y-%m-%d %H:%M UTC') , loc='right')

    return [m, alpha, half_box, barb_thin]



def draw_wind(m, lons, lats,
              model, dsize, background,
              location, lat, lon,
              RUNDATE, VALIDDATE, fxx,
              alpha, half_box, barb_thin,
              level='10 m',
              Fill=False,
              Shade=False,
              Barbs=False,
              Quiver=False,
              p95=False,
              Convergence=False,
              Vorticity=False):
    """
    wind speed, wind barbs, wind quiver, Convergence, Divergence,
    shade high wind area, wind speed 95th percentile exceedance
    """
    LEVEL = level.replace(' ', '')

    H_UV = get_hrrr_variable(RUNDATE, 'UVGRD:%s' % level,
                             model=model, fxx=fxx,
                             outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                             verbose=False, value_only=False)
    
    if Fill:
        cmap = cm_wind()
        m.pcolormesh(lons, lats, H_UV['SPEED'],
                     latlon=True,
                     cmap=cmap['cmap'],
                     vmin=cmap['cmap'], vmax=cmap['cmap'],
                     zorder=2,
                     alpha=alpha)
        cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink, extend='max')
        cb.set_label(r'%s Wind Speed (m s$\mathregular{^{-1}}$)' % level)

    if Shade:
            m.contourf(lons, lats, H_UV['SPEED'],
                       levels=[10, 15, 20, 25],
                       colors=('yellow', 'orange', 'red'),
                       alpha=alpha,
                       extend='max',
                       zorder=3,
                       latlon=True)
            cb = plt.colorbar(orientation='horizontal', shrink=shrink, pad=pad)
            cb.set_label(r'%s Wind Speed (ms$\mathregular{^{-1}}$)' % level)

    if Barbs or Quiver:
        if level == '10 m':
            color = 'k'
        elif level == '80 m':
            color = 'darkred'
        elif level == '500 mb':
            color = 'navy'
        else:
            color='k'

        # For small domain plots, trimming the edges significantly reduces barb plotting time
        if barb_thin < 20:
            subset = hrrr_subset(H_UV, half_box=half_box, lat=lat, lon=lon, verbose=False)
        else:
            subset = H_UV

        # Need to rotate vectors for map projection
        subset['UGRD'], subset['VGRD'] = m.rotate_vector(subset['UGRD'], subset['VGRD'], subset['lon'], subset['lat'])

        thin = barb_thin
        # Add to plot
        if Barbs:
            m.barbs(subset['lon'][::thin,::thin], subset['lat'][::thin,::thin],
                    subset['UGRD'][::thin,::thin], subset['VGRD'][::thin,::thin],
                    zorder=10, length=5.5, color=color,
                    barb_increments={'half':2.5, 'full':5,'flag':25},
                    latlon=True)

        if Quiver:
            Q = m.quiver(subset['lon'][::thin,::thin], subset['lat'][::thin,::thin],
                         subset['UGRD'][::thin,::thin], subset['VGRD'][::thin,::thin],
                         zorder=10,
                         units='inches',
                         scale=40, color=color,
                         latlon=True)    
            qk = plt.quiverkey(Q, .92, 0.07, 10, r'10 s$^{-1}$',
                            labelpos='S',
                            coordinates='axes',
                            color='magenta')
            qk.text.set_backgroundcolor('w')

    if p95:
        DIR = '/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/HRRR_OSG/hourly30/UVGRD_%s/' % level.replace(' ', '_')
        FILE = 'OSG_HRRR_%s_m%02d_d%02d_h%02d_f00.h5' % (('UVGRD_%s' % level.replace(' ', '_'), VALIDDATE.month, VALIDDATE.day, VALIDDATE.hour))
        with h5py.File(DIR+FILE, 'r') as f:
            spd_p95 = f["p95"][:]
        masked = H_UV['SPEED']-spd_p95
        masked = np.ma.array(masked)
        masked[masked < 0] = np.ma.masked
        
        m.pcolormesh(lons, lats, masked,
                     vmax=10, vmin=0,
                     latlon=True,
                     zorder=9,
                     cmap='viridis',
                     alpha=alpha)
        cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
        cb.set_label(r'%s Wind Speed exceeding 95th Percentile (m s$\mathregular{^{-1}}$)' % level)

    if Convergence or Vorticity:
        
        dudx, dudy = np.gradient(H_UV['UGRD'], 3, 3)
        dvdx, dvdy = np.gradient(H_UV['VGRD'], 3, 3)
        
        if Vorticity:
            vorticity = dvdx - dudy
            # Mask values
            vort = vorticity
            vort = np.ma.array(vort)
            vort[np.logical_and(vort < .05, vort > -.05) ] = np.ma.masked

            m.pcolormesh(lons, lats, vort,
                        latlon=True, cmap='bwr',
                        zorder=8,
                        vmax=np.max(vort),
                        vmin=-np.max(vort))
            cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
            cb.set_label(r'%s Vorticity (s$\mathregular{^{-1}}$)' % level)
        if Convergence:
            convergence = dudx + dvdy
            # Mask values
            conv = convergence
            conv = np.ma.array(conv)
            conv[np.logical_and(conv < .05, conv > -.05) ] = np.ma.masked

            m.pcolormesh(lons, lats, conv,
                        latlon=True, cmap='bwr',
                        zorder=8,
                        vmax=np.max(conv),
                        vmin=-np.max(conv))
            cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
            cb.set_label(r'%s Convergence (s$\mathregular{^{-1}}$)' % level)



def draw_gust(m, lons, lats,
              model, dsize, background,
              location, lat, lon,
              RUNDATE, VALIDDATE, fxx,
              alpha, half_box, barb_thin):
    """
    hatch fill for wind gust
    """
    H = get_hrrr_variable(RUNDATE, 'GUST:surface',
                          model=model, fxx=fxx,
                          outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                          verbose=False, value_only=True)
    m.contourf(lons, lats, H['value'],
               levels=[0, 10, 15, 20, 25],
               hatches=[None, '.', '\\\\', '*'],
               colors='none',
               extend='max',
               zorder=9,
               latlon=True)
    cb = plt.colorbar(orientation='horizontal', shrink=shrink, pad=pad)
    cb.set_label(r'Surface Wind Gust (m s$\mathregular{^{-1}}$)')
    m.contour(lons, lats, H['value'],
                levels=[10, 15, 20, 25],
                colors='k',
                zorder=9,
                latlon=True)



def draw_refc(m, lons, lats,
              model, dsize, background,
              location, lat, lon,
              RUNDATE, VALIDDATE, fxx,
              alpha, half_box, barb_thin,
              Fill=False,
              Contour=False, contours = range(10, 81, 10)):
    """
    Composite reflectivity
        dBZ_contours    - list of values to contour if Contour=True
    """
    if model in ['hrrr', 'hrrrak']:
        REFC = 'REFC:entire'
    else:
        REFC = 'var discipline=0 center=59 local_table=1 parmcat=16 parm=196'
    H_ref = get_hrrr_variable(RUNDATE, REFC,
                              model=model, fxx=fxx,
                              outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                              verbose=False, value_only=True)
    # Mask values
    dBZ = H_ref['value']
    dBZ = np.ma.array(dBZ)
    dBZ[dBZ == -10] = np.ma.masked
    
    # Add fill to plot
    if Fill:
        m.pcolormesh(lons, lats, dBZ,
                     cmap=reflect_ncdc(),
                     vmax=80, vmin=0,
                     alpha=alpha,
                     zorder=5,
                     latlon=True)
        cb2 = plt.colorbar(orientation='horizontal', shrink=shrink, pad=pad)
        cb2.set_label('Simulated Composite Reflectivity (dBZ)')

    # Add Contour to plot
    if Contour==True:
        cREF = m.contour(lons, lats, dBZ,
                         cmap=reflect_ncdc(),
                         levels=contours,
                         vmax=80, vmin=0,
                         latlon=True,
                         zorder=5)
        plt.clabel(cREF, cREF.levels[::2], fmt='%2.0f', colors='k', fontsize=9)



def draw_tmp_dpt(m, lons, lats,
                 model, dsize, background,
                 location, lat, lon,
                 RUNDATE, VALIDDATE, fxx,
                 alpha, half_box, barb_thin,
                 variable='TMP:2 m',
                 Fill=False,
                 Contour=False, contours = [0],
                 p05p95=False,                 
                 ):
    """
    temperature and dewpoint fill,
    freezing line, -12c line,
    95th and 5th percentile exceedance
    """
    VAR, level = variable.split(':')
    if VAR not in ['TMP', 'DPT']:
        raise ValueError("VAR must be either TMP or DPT")

    if VAR == 'TMP':
        cmap = cm_temp()
        cmapOSG = 'bwr'
        label = '%s Temperature (C)' % level
    elif VAR == 'DPT':
        cmap = cm_dpt()
        cmapOSG = 'BrBG'
        label = '%s Dew Point Temperature (C)' % level


    H = get_hrrr_variable(RUNDATE, '%s:%s' % (VAR,level),
                          model=model, fxx=fxx,
                          outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                          verbose=False, value_only=True)

    if Fill:
        m.pcolormesh(lons, lats, H['value']-273.15,
                     cmap=cmap['cmap'],
                     alpha=alpha,
                     vmin=cmap['vmin'], vmax=cmap['vmax'],
                     zorder=2, latlon=True)
        cbT = plt.colorbar(orientation='horizontal', shrink=shrink, pad=pad, extend='both')
        cbT.set_label(label)
        cbT.set_ticks(range(cmap['vmin'],cmap['vmax']+1,5))
    
    if Contour:
        m.contour(lons, lats, H['value']-273.15,
                  colors='k',
                  linewidths=.8,
                  levels=contours,
                  zorder=10,
                  latlon=True)

    if p05p95:
        DIR = '/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/HRRR_OSG/hourly30/%s_%s/' % (VAR, level.replace(' ', '_'))
        FILE = 'OSG_HRRR_%s_%s_m%02d_d%02d_h%02d_f00.h5' % (VAR, level.replace(' ', '_'), VALIDDATE.month, VALIDDATE.day, VALIDDATE.hour)

        ### Plot Depression
        with h5py.File(DIR+FILE, 'r') as f:
            p05 = f["p05"][:]
        masked = H['value']-p05 # both these datasets are in Kelvin, but when we take the difference it is in Celsius
        masked = np.ma.array(masked)
        masked[masked > 0] = np.ma.masked
        
        mesh_depression = m.pcolormesh(lons, lats, masked,
                                    vmax=10, vmin=-10,
                                    latlon=True,
                                    zorder=3,
                                    cmap=cmapOSG)
        
        ### Plot Exceedance
        with h5py.File(DIR+FILE, 'r') as f:
            p95 = f["p95"][:]
        masked = H['value']-p95 # both these datasets are in Kelvin, but when we take the difference it is in Celsius
        masked = np.ma.array(masked)
        masked[masked < 0] = np.ma.masked

        mesh_exceedance = m.pcolormesh(lons, lats, masked,
                                    vmax=10, vmin=-10,
                                    latlon=True,
                                    zorder=3,
                                    cmap=cmapOSG)
        
        cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink, extend='both')
        cb.set_label(r'5$\mathregular{^{th}}$/95$\mathregular{^{th}}$ percentile Depression/Exceedance %s' % label)


def draw_pot(m, lons, lats,
             model, dsize, background,
             location, lat, lon,
             RUNDATE, VALIDDATE, fxx,
             alpha, half_box, barb_thin,
             level='2 m'):
    """
    2 m Potential Temperature
    """
    # Only 2 m Potential temperature is in the HRRR file
    level = '2 m'
    H = get_hrrr_variable(RUNDATE, 'POT:%s' % level,
                          model=model, fxx=fxx,
                          outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                          verbose=False, value_only=True)
    m.pcolormesh(lons, lats, H['value'], cmap="coolwarm",
                 zorder=2,
                 latlon=True)
    cbT = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
    cbT.set_label('%s Potential Temperature (K)' % level)


def draw_rh(m, lons, lats,
            model, dsize, background,
            location, lat, lon,
            RUNDATE, VALIDDATE, fxx,
            alpha, half_box, barb_thin,
            level='2 m'):
    """
    Relative Humidity, calculated for levels != '2 m'
    """
    if level == '2 m':
        H = get_hrrr_variable(RUNDATE, 'RH:%s' % level,
                              model=model, fxx=fxx,
                              outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                              verbose=False, value_only=True)
    else:
        # Must compute the RH from TMP and DPT
        H_DPT = get_hrrr_variable(RUNDATE, 'DPT:%s' % level,
                              model=model, fxx=fxx,
                              outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                              verbose=False, value_only=True)
        H_TMP = get_hrrr_variable(RUNDATE, 'TMP:%s' % level,
                                model=model, fxx=fxx,
                                outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                verbose=False, value_only=True)
        H = {'value':Tempdwpt_to_RH(H_TMP['value']-273.15, H_DPT['value']-273.15)}

    m.pcolormesh(lons, lats, H['value'], cmap="RdYlGn",
                    vmin=0, vmax=100,
                    zorder=2,
                    latlon=True)
    cbT = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
    cbT.set_label('%s Relative Humidity (%%)' % level)



def draw_vpd(m, lons, lats,
             model, dsize, background,
             location, lat, lon,
             RUNDATE, VALIDDATE, fxx,
             alpha, half_box, barb_thin,
             level='2 m',
             Fill=False,
             Crossover=False):
    """
    Vapor Pressure Deficit: calculated from Temperature and Relative Humidity
    """
    if level == '2 m':
        H_RH = get_hrrr_variable(RUNDATE, 'RH:%s' % level,
                                 model=model, fxx=fxx,
                                 outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                 verbose=False, value_only=True)
        H_TMP = get_hrrr_variable(RUNDATE, 'TMP:%s' % level,
                                  model=model, fxx=fxx,
                                  outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                  verbose=False, value_only=True)
    else:
        # Must compute the RH from TMP and DPT
        H_DPT = get_hrrr_variable(RUNDATE, 'DPT:%s' % level,
                              model=model, fxx=fxx,
                              outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                              verbose=False, value_only=True)
        H_TMP = get_hrrr_variable(RUNDATE, 'TMP:%s' % level,
                                model=model, fxx=fxx,
                                outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                                verbose=False, value_only=True)
        H_RH = {'value':Tempdwpt_to_RH(H_TMP['value']-273.15, H_DPT['value']-273.15)}

    if Fill:
        H_VPD = {'value': vapor_pressure_deficit(H_TMP['value']-273.15, H_RH['value'])}
        m.pcolormesh(lons, lats, H_VPD['value'], cmap="magma_r",
                        vmin=0, vmax=70,
                        zorder=2,
                        latlon=True)
        cbT = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
        cbT.set_label('%s Vapor Pressure Deficit (hPa)' % level)
    if Crossover:
        difference = H_RH['value']-(H_TMP['value']-273.15)
        m.contour(lons, lats, difference,
                  colors='white',
                  linewidths=1.2,
                  levels=[0],
                  zorder=10,
                  latlon=True)



def draw_hgt(m, lons, lats,
             model, dsize, background,
             location, lat, lon,
             RUNDATE, VALIDDATE, fxx,
             alpha, half_box, barb_thin,
             level='500 mb',
             Contour=False,
             p05p95=False
             ):
    VAR = 'HGT'
    cmap = 'RdGy'
    cmapOSG = 'RdGy'
    label = '%s Height (m)' % level
    vmax=50
    vmin=-50
        
    H = get_hrrr_variable(RUNDATE, 'HGT:%s' % level,
                          model=model, fxx=fxx,
                          outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                          verbose=False, value_only=True)

    if Contour:
        CS = m.contour(lons, lats, H['value'], 
                        levels=range(3000, 8000, 60),
                        linewidths=1.7,
                        colors='k', 
                        latlon=True,
                        zorder=100)
        plt.clabel(CS, inline=1, fmt='%2.f')

    if p05p95:
        DIR = '/uufs/chpc.utah.edu/common/home/horel-group8/blaylock/HRRR_OSG/hourly30/%s_%s/' % (VAR, level.split(' ')[0])
        FILE = 'OSG_HRRR_%s_%s_m%02d_d%02d_h%02d_f00.h5' % (VAR, level.split(' ')[0], VALIDDATE.month, VALIDDATE.day, VALIDDATE.hour)

        ### Plot Depression
        with h5py.File(DIR+FILE, 'r') as f:
            p05 = f["p05"][:]
        masked = H['value']-p05
        masked = np.ma.array(masked)
        masked[masked > 0] = np.ma.masked
        
        mesh_depression = m.pcolormesh(lons, lats, masked,
                                       vmax=vmax, vmin=vmin,
                                       latlon=True,
                                       zorder=3,
                                       cmap=cmapOSG)
        
        ### Plot Exceedance
        with h5py.File(DIR+FILE, 'r') as f:
            p95 = f["p95"][:]
        masked = H['value']-p95
        masked = np.ma.array(masked)
        masked[masked < 0] = np.ma.masked

        mesh_exceedance = m.pcolormesh(lons, lats, masked,
                                       vmax=vmax, vmin=vmin,
                                       latlon=True,
                                       zorder=3,
                                       cmap=cmapOSG)
        
        cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink, extend='both')
        cb.set_label(r'5$\mathregular{^{th}}$/95$\mathregular{^{th}}$ percentile Depression/Exceedance %s' % label)


def draw_mslp(m, lons, lats,
              model, dsize, background,
              location, lat, lon,
              RUNDATE, VALIDDATE, fxx,
              alpha, half_box, barb_thin,
              Fill=False,
              Contour=False):
    H = get_hrrr_variable(RUNDATE, 'MSLMA:mean sea level',
                          model=model, fxx=fxx,
                          outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                          verbose=False, value_only=True)

    if Fill:
        m.pcolormesh(lons, lats, H['value']/100., 
                     latlon=True,
                     cmap='viridis',
                     zorder=2)
        cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
        cb.set_label('Mean Sea Level Pressure (hPa)')
    
    if Contour:
            CS = m.contour(lons, lats, H['value']/100., 
                           latlon=True,
                           levels=range(952, 1200, 4),
                           colors='k',
                           zorder=9)
            CS.clabel(inline=1, fmt='%2.f',
                    zorder=400)


def draw_redflag(m, lons, lats,
                 model, dsize, background,
                 location, lat, lon,
                 RUNDATE, VALIDDATE, fxx,
                 alpha, half_box, barb_thin,
                 RH=25, SPEED=6.7,
                 Fill=False,
                 Contour=False,
                 Fill_Potential=False):
    # Generalized criteria for red flag warning
    # Winds (gusts) greater than 6.7 m/s and RH < 25%
    rf_RH = RH
    rf_WIND = SPEED

    # Get Data
    H_gust = get_hrrr_variable(RUNDATE, 'GUST:surface',
                               model=model, fxx=fxx,
                               outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                               verbose=False, value_only=True)
    H_rh = get_hrrr_variable(RUNDATE, 'RH:2 m',
                             model=model, fxx=fxx,
                             outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                             verbose=False, value_only=True)
    
    RedFlag = np.logical_and(H_gust['value'] >rf_WIND, H_rh['value'] < rf_RH)

    if Fill:
        masked = np.ma.array(RedFlag)
        masked[masked == 0] = np.ma.masked 
        m.pcolormesh(lons, lats, masked,
                     cmap="YlOrRd_r",
                     alpha=alpha,
                     zorder=5, latlon=True)

    if Contour:
        try:
            CS = m.contour(lons, lats, RedFlag, 
                            latlon=True,
                            colors='darkred',
                            linewidths=.75,
                            levels=[0],
                            zorder=10)
        except:
            # maybe there isn't any contours in this domain
            pass

    if Fill_Potential:
        cdict3 = {'red':  ((0.0,  1.0, 1.0),
                           (0.5,  0.5, 0.5),
                           (0.5,  1.0, 1.0),
                           (1.0,  0.4, 0.4)),
                  'green': ((0.0,  1.0, 1.0),
                            (0.5,  0.5, 0.5),
                            (0.5,  0.4, 0.4),
                            (1.0,  0.0, 0.0)),
                  'blue':  ((0.0,  1.0, 1.0),
                            (0.5,  0.5, 0.5),
                            (0.5,  0.0, 0.0),
                            (1.0,  0.0, 0.0))
                }
        plt.register_cmap(name='FirePot', data=cdict3)
        
        # Definate Red Flag Area:
        RED_FLAG = np.logical_and(H_rh['value'] < rf_RH,
                                  H_gust['value'] > rf_WIND)
        # Linear Equation
        b = (rf_RH-rf_WIND)*(rf_RH/rf_WIND)
        z = -(rf_RH/rf_WIND)*(H_rh['value']-H_gust['value'])+b
        
        m.pcolormesh(lons, lats, z,
                     cmap="FirePot",
                     alpha=alpha,
                     vmax=200, vmin=-200,
                     zorder=3,
                     latlon=True)
        cb = plt.colorbar(orientation='horizontal', pad=pad, shrink=shrink)
        cb.set_label(r'Red Flag Potential')
        
    plt.xlabel(r'Red Flag Criteria: Winds > %s m s$\mathregular{^{-1}}$ and RH < %s%%' % (SPEED,RH))



def draw_variable(m, lons, lats,
                  model, dsize, background,
                  location, lat, lon,
                  RUNDATE, VALIDDATE, fxx,
                  alpha, half_box, barb_thin,
                  variable='APCP:surface:0',
                  masked=False):
    """
    Uses pcolormesh to plot a variableiable for the domain.

    Input:
        variable - The desired variable string from a line in the .idx file.
        masked   - False: Do not mask any values
                   True:  Mask values == 0
    """
    split = variable.split(":")
    VAR = split[0]
    level = split[1]
    H = get_hrrr_variable(RUNDATE, variable,
                          model=model, fxx=fxx,
                          outDIR='/uufs/chpc.utah.edu/common/home/u0553130/temp/',
                          verbose=False, value_only=False)
    
    if variable == 'APCP:surface:0':
        label = 'Total Precipitation since F00 (mm)'
        cmap = cm_precip()
        vmin = 0
        vmax = 762
    elif variable == 'APCP:surface':
        label = '1 hour Total Precipitation (mm)'
        cmap = cm_precip()
        vmin = 0
        vmax = 762
    elif variable == 'TCDC:entire':
        label = 'Total Cloud Cover'
        cmap = cm_sky()
        vmin = 0
        vmax = 90
    elif variable == 'SNOWC':
        label = 'Snow Cover (%)'
        cmap = 'Blues'
        vmin = 0
        vmax = 100
    elif variable == 'CAPE:surface':
        label = r'Surface CAPE (J kg$\mathregular{^{-1}}$)'
        cmap = 'Oranges'
        vmin = 0
        vmax = 3500
    elif variable == 'CIN:surface':
        label = r'Surface CIN (J kg$\mathregular{^{-1}}$)'
        cmap = 'BuPu_r'
        vmin = -1000
        vmax = 0
    #elif variable == 'POT:2 m':
    #    cmap = 'Oranges'
    #    label = '2 m Potential Temperature (C)'
    #    vmax = H['value'].max()
    #    vmin = H['value'].min()
    elif variable == 'PWAT':
        cmap = 'RdYlGn'
        label = r'Vertically Integrated Liquid Water (kg m$\mathregular{^{-2}}$)'
        vmax = H['value'].max()
        vmin = 0
    else:
        cmap = 'viridis'
        label = '%s (%s)' % (variable, H['units'])
        vmax = H['value'].max()
        vmin = H['value'].min()

    values = H['value']
    
    if H['units'] == 'K':
        values -= 273.15

    if masked:
        values = np.ma.array(values)
        if VAR == 'APCP':        
            values[values < .25] = np.ma.masked
        elif VAR == 'LTNG':
            values[values < .01] = np.ma.masked
        else:
            values[values == 0] = np.ma.masked

    m.pcolormesh(lons, lats, values,
                 cmap=cmap,
                 alpha=alpha,
                 vmax=vmax, vmin=vmin,
                 zorder=3, latlon=True)
    cbS = plt.colorbar(orientation='horizontal', shrink=shrink, pad=pad)
    cbS.set_label(label)

###############################################################################
###############################################################################

if __name__ == '__main__':

    model = 'hrrr'
    dsize = 'full'
    
    if model == 'hrrrak':
        location = 'PATK'
    else:
        location = 'WBB'
    background = 'arcgis'
    fxx = 0
    
    # DATES
    sDATE = datetime(2019, 1, 28, 0)
    eDATE = datetime(2019, 1, 29, 1)
    
    EVENT = 'Polar_Vortex_%s' % sDATE.strftime('%Y-%m-%d')

    hours = int((eDATE-sDATE).seconds/60/60 + (eDATE-sDATE).days*24)
    DATES = [sDATE + timedelta(hours=h) for h in range(0,hours+1)]
    

    for VALIDDATE in DATES[0:1]:
        RUNDATE = VALIDDATE - timedelta(hours=fxx)

        if ',' in location:
            # User put inputted a lat/lon point request
            lat, lon = location.split(',')
            lat = float(lat)
            lon = float(lon)
        else:
            # User requested a MesoWest station
            location = location.upper()
            stninfo = get_mesowest_stninfo([location])
            lat = stninfo[location]['latitude']
            lon = stninfo[location]['longitude']

        lats, lons = load_lats_lons(model)

        
        m, alpha, half_box, barb_thin = draw_map_base(model, dsize, background,
                                                      location, lat, lon,
                                                      RUNDATE, VALIDDATE, fxx)
        
        draw_pot(m, lons, lats,
                 model, dsize, background,
                 location, lat, lon,
                 RUNDATE, VALIDDATE, fxx,
                 alpha, half_box, barb_thin        
                )
        
        """
        draw_tmp_dpt(m, lons, lats,
                    model, dsize, background,
                    location, lat, lon,
                    RUNDATE, VALIDDATE, fxx,
                    alpha, half_box, barb_thin,
                    variable='TMP:2 m',
                    Fill=False,
                    Contour=False, contours = [0],
                    p05p95=True,                 
                    )

        draw_hgt(m, lons, lats,
                model, dsize, background,
                location, lat, lon,
                RUNDATE, VALIDDATE, fxx,
                alpha, half_box, barb_thin,
                level='500 mb',
                Contour=True,
                p05p95=False
                )
        """

        #plt.show()
        SAVEDIR = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR/Events_Day/%s/' % EVENT
        if not os.path.exists(SAVEDIR):
            os.makedirs(SAVEDIR)
        SAVEFIG = SAVEDIR + '%s_f%02d' % (VALIDDATE.strftime('%Y-%m-%d_h%H'), fxx)
        plt.savefig(SAVEFIG)
        print('SAVED:', SAVEFIG)
        plt.close()
        plt.clf()
        plt.cla()
'''