# Brian Blaylock
# September 21, 2018

"""
Stitch together two images side by side

os.system('convert img1.png img2.png +append new.png')
"""

import os
from datetime import datetime, timedelta

"""
HEAD = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_RMSE/'
for v in ['TMP:2 m', 'DPT:2 m', 'CAPE:surface', 'HGT:500 mb', 'WIND:10 m', 'UGRD:10 m', 'VGRD:10 m', 'REFC:entire', 'LTNG:entire']:
    for h in range(24):
        DIR = v.split(':')[0]
        NAM = v.replace(':', '-').replace(' ', '-')
        if v == 'HGT:500 mb':
            DIR = 'HGT500'

        img1 = HEAD+'RMSD_v2/%s/CONUS_HRRR_RMSD-%s_hours-%02d.png' % (DIR, NAM, h)
        img2 = HEAD+'RMSD_v3/%s/CONUS_HRRR_RMSD-%s_hours-%02d.png' % (DIR, NAM, h)
        new  = HEAD+'RMSD_v2v3/%s/%02d.png' % (DIR, h)
        try:
            os.system('convert %s %s +append %s' % (img1, img2, new))
        except:
            pass
"""

"""
HEAD_left = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/HRRR_Spread/Hourly_May2018-Oct2018/'
HEAD_right = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/GOES16_GLM/Hourly_May2018-Oct2018/'
DIRS = os.listdir(HEAD_left)
#for v in DIRS:
for v in ['UVGRD']:
    for h in range(24):
        img1 = HEAD_left+'%s/CONUS/*h%02d.png' % (v, h)
        img2 = HEAD_right+'CONUS/*h%02d.png' % (h)
        SAVEDIR  = HEAD_left+'%s/HRRR_and_GLM/' % (v)
        if not os.path.exists(SAVEDIR):
            os.makedirs(SAVEDIR)
        new = SAVEDIR+'h%02d.png' % (h)
        try:
            print('convert -quality 50 %s %s +append %s' % (img1, img2, new))
            os.system('convert %s %s +append %s' % (img1, img2, new))
            os.system('convert %s -resize 50%% %s' % (new, new))
        except:
            pass
"""

"""
HEAD_left = '/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/grid_resilience/'
HEAD_right = '/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/grid_resilience/'

for f in range(19):
    img1 = HEAD_left+'20181108_0600_f%02d.png' % (f)
    img2 = HEAD_left+'OSG_95th_20181108_0600_f%02d.png' % (f)
    SAVEDIR  = '/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/grid_resilience/camp_fire/'
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
    new = SAVEDIR+'20181108_0600_f%02d.png' % (f)
    try:
        print('convert -quality 50 %s %s +append %s' % (img1, img2, new))
        os.system('convert %s %s +append %s' % (img1, img2, new))
        os.system('convert %s -resize 85%% %s' % (new, new))
    except:
        pass
"""

HEAD_top = "/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/publications/GLM_HRRR/figs/May2019/cases-Scores_"
HEAD_bottom = "/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3/publications/GLM_HRRR/figs/May2019/not_shown_Cases-Map_"

sDATE = datetime(2019, 5, 8, 10)
eDATE = datetime(2019, 5, 8, 13)
hours = int((eDATE - sDATE).days * 24 + (eDATE - sDATE).seconds / 60 / 60)
DATES = [sDATE + timedelta(hours=h) for h in range(hours)]

for DATE in DATES:
    img1 = HEAD_top + DATE.strftime("%Y%m%d_%H%M.png")
    img2 = HEAD_bottom + DATE.strftime("%Y%m%d_%H%M.png")
    SAVEDIR = "/uufs/chpc.utah.edu/common/home/u0553130/public_html/PhD/GLM_and_HRRR/CaseEvents/May2019_storm/"
    if not os.path.exists(SAVEDIR):
        os.makedirs(SAVEDIR)
    new = SAVEDIR + DATE.strftime("%Y%m%d_%H%M.png")
    try:
        os.system("convert %s %s -append %s" % (img1, img2, new))
        print("Saved:", DATE)
    except:
        pass
