# Brian Blaylock
# September 14, 2018

"""
Dealing with HRRR lightning variable.

The HRRR Lightning Threat is the Hourly Max Lightning threat 3 based on a
combination of threats 1 and 2. It represents the entire atmosphere, and has
units flashes/km2/5min

Threat 1 is based on the vertical flux of graupel at -15C
Threat 2 is based on the vertical integrated frozen hydrometeors    
"""

import numpy as np
from datetime import datetime, timedelta
import multiprocessing
import sys

sys.path.append("/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v3")
sys.path.append("B:\pyBKB_v3")
from BB_HRRR.HRRR_Pando import get_hrrr_variable, get_hrrr_latlon


def get_HRRR_lightning(DATE, fxx=1):
    """Return the HRRR Lightning grid for a Date"""
    H = get_hrrr_variable(DATE, "LTNG:entire", fxx=fxx, value_only=True, verbose=False)
    return H["value"]


def accumulate_grid_chunks(DATES, date_idx_chunks, fxx=1):
    """Accumulate Lightning values for a chunk of DATES"""
    start, end = date_idx_chunks
    accum_chunk = np.sum(
        [get_HRRR_lightning(D, fxx=fxx) for D in DATES[start:end]], axis=0
    )
    return accum_chunk


def MP(inputs):
    """Multiprocessing Setup"""
    DATES, date_idx_chunks, fxx = inputs
    return accumulate_grid_chunks(DATES, date_idx_chunks, fxx)


def accumulate_HRRR_lightning(sDATE, eDATE, fxx=1):
    """
    Accumulate HRRR lightning threat values between two dates

    Input:
        sDATE - Datetime object of start date
        eDATE - Datetime object of end date
        fxx   - Forecast lead time. Must be greater than zero because it's an
                 hourly product.
    """
    print("Start Date :", sDATE)
    print("End Date   :", eDATE)
    print("FXX        :", fxx)

    # Create list of DATES
    hours = (eDATE - sDATE).days * 24 + int((eDATE - sDATE).seconds / 60 / 60)
    DATES = [sDATE + timedelta(hours=h) for h in range(hours)]

    # Set up multiprocessing. We are going to cut the work into as many chunks
    # as we have processors. Then each processor will work on it's own chunk.
    # Then find the indexes of DATES each job will perform.
    cpus = multiprocessing.cpu_count()
    chunk_step = int(len(DATES) / cpus)
    chunks = list(range(0, len(DATES), chunk_step)) + [-1]
    chunk_sections = [
        [DATES, (chunks[i], chunks[i + 1]), fxx] for i in range(len(chunks) - 1)
    ]

    # Accumulate the chunks
    P = multiprocessing.Pool(cpus)
    results = P.map(MP, chunk_sections)
    P.close()

    # Acuumulate the results
    accum_lightning = np.sum(results, axis=0)

    return accum_lightning


if __name__ == "__main__":
    # Accumulate Lightning Between two dates
    sDATE = datetime(2018, 5, 8)
    eDATE = datetime(2018, 9, 10)
    fxx = 18
    A = accumulate_HRRR_lightning(sDATE, eDATE, fxx=fxx)

    # Make a map
    import matplotlib.pyplot as plt
    from BB_maps.my_basemap import draw_HRRR_map

    latlon = get_hrrr_latlon()
    lat = latlon["lat"]
    lon = latlon["lon"]
    m = draw_HRRR_map()

    m.pcolormesh(lon, lat, A, cmap="magma", latlon=True)
    cb = plt.colorbar(orientation="horizontal", pad=0.01, shrink=0.8, extend="max")
    cb.set_label(r"Maximum Flashes km$\mathregular{^{-2}}$ 5min$\mathregular{^{-1}}$")

    m.drawcoastlines(color="grey")
    m.drawcountries(color="grey")
    m.drawstates(color="grey")

    plt.title(
        "Accumulated HRRR F%02d Lightning Threat3" % fxx,
        loc="left",
        fontweight="semibold",
    )
    plt.title(
        "Start: %s\n End: %s"
        % (sDATE.strftime("%d %b %Y"), eDATE.strftime("%d %b %Y")),
        loc="right",
    )

    plt.show()
