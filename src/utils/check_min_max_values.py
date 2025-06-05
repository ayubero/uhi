import rasterio
import numpy as np

# Path to your raster file
raster_path = '../../data/graz/rasters/gli.tif'

# Open the raster file
with rasterio.open(raster_path) as src:
    # Read the first band into a NumPy array
    band1 = src.read(1)

    ''''# Calculate min and max while ignoring NoData values
    nodata = src.nodata
    if nodata is not None:
        band1 = band1[band1 != nodata]'''

    min_val = np.min(band1)
    max_val = np.max(band1)

    print(f'Minimum value: {min_val}')
    print(f'Maximum value: {max_val}')
