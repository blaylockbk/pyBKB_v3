"""
Code abbridged from xarray plotting methods for pcolormesh
github/pydata/xarray/plot/utils: _infer_interval_breaks is used in the wrapper for pcolormesh
github/pydata/xarray/plot/plot: pcolormesh

If you use pcolormesh to make a figure and the x, y, and z coordinates are the
same size, pcolormesh will not plot the last row or column becuase it 
uses the values as the edges of the box. That isn't always the best way to 
display environmental data. These functions help plot the full data array
with pcolormesh by centering the colored grid box of the data point
on the vertice, rather than begining the edge of the box on the vertice.
"""

# abbridged function from xarray...
def _infer_interval_breaks(coord, axis=0):
    """
    Code from xarray: (github/pydata/xarray/plot/utils)
    Usage: if x is a 2d array of longitudes...
    x = _infer_interval_breaks(x, axis=1)
    x = _infer_interval_breaks(x, axis=0) # repeat for second axis
    """
    deltas = 0.5 * np.diff(coord, axis=axis)
    first = np.take(coord, [0], axis=axis) - np.take(deltas, [0], axis=axis)
    last = np.take(coord, [-1], axis=axis) + np.take(deltas, [-1], axis=axis)
    trim_last = tuple(
        slice(None, -1) if n == axis else slice(None) for n in range(coord.ndim)
    )

    coord = np.concatenate([first, coord[trim_last] + deltas, last], axis=axis)

    return coord


# function modified to apply to both coordinates before returning the value...
def _infer_interval_breaks(coord):
    """
    Code from xarray: (github/pydata/xarray/plot/utils)

    If you want to plot with pcolormesh, it will chop off the last row/column becuase
    pcolormesh uses the box edges as the verticies, and not the center of the box.
    This function infers the gridpoints to position the points in the center of the box.

    This is slightly different from the xarray code, in that this one performs the
    infering on both axes before returning the final product.

    Usage: if x is a 2d array of longitudes...
    x = _infer_interval_breaks(x)

    this will increase the size of x in both axes by 1
    """

    axis = 0
    deltas = 0.5 * np.diff(coord, axis=axis)
    first = np.take(coord, [0], axis=axis) - np.take(deltas, [0], axis=axis)
    last = np.take(coord, [-1], axis=axis) + np.take(deltas, [-1], axis=axis)
    trim_last = tuple(
        slice(None, -1) if n == axis else slice(None) for n in range(coord.ndim)
    )

    coord = np.concatenate([first, coord[trim_last] + deltas, last], axis=axis)

    axis = 1
    deltas = 0.5 * np.diff(coord, axis=axis)
    first = np.take(coord, [0], axis=axis) - np.take(deltas, [0], axis=axis)
    last = np.take(coord, [-1], axis=axis) + np.take(deltas, [-1], axis=axis)
    trim_last = tuple(
        slice(None, -1) if n == axis else slice(None) for n in range(coord.ndim)
    )

    coord = np.concatenate([first, coord[trim_last] + deltas, last], axis=axis)

    return coord
