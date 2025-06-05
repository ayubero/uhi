import rasterio
import numpy as np

# Input and output file paths
input_tif = 'gli.tif'
output_tif = input_tif

# Open the raster file
with rasterio.open(input_tif) as src:
    data = src.read(1) # Read the first band
    current_nodata = src.nodata
    profile = src.profile

    # Replace NoData values with -1
    if current_nodata is not None:
        data[data == current_nodata] = -1
    else:
        print('Warning: No NoData value found. Proceeding without replacement.')

    # Update the profile to reflect new NoData value
    profile.update(nodata=-1)

# Write the updated data to a new file
with rasterio.open(output_tif, 'w', **profile) as dst:
    dst.write(data, 1)
