import os, glob
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Go to directory with study area rasters
raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
os.chdir(raster_path)

# List all .tif files
list = glob.glob('*.tif')

# Read and stack all bands
dataset = []
no_data_value = -1
band: np.ndarray
for raster_name in list:
    with rasterio.open(raster_name) as src:
        no_data_value = src.nodata
        band = src.read(8)
        dataset.append(src.read(8))


# Stack all bands along a new third axis to create a 3D array
stacked_data = np.stack(dataset, axis=-1)

# Create a mask for valid data points
valid_data_mask = stacked_data != no_data_value

# Compute the sum and the count of valid data points along the third axis
valid_sum = np.where(valid_data_mask, stacked_data, 0).sum(axis=-1)
valid_count = valid_data_mask.sum(axis=-1)

# Compute the average, avoiding division by zero
average_band = np.where(valid_count > 0, valid_sum / valid_count, no_data_value)

# Keep no_data_value areas with the original no_data_value
average_band[valid_count == 0] = no_data_value

plt.figure(figsize=(10, 10))
plt.imshow(average_band, cmap='plasma')
plt.title(f'Average NIR')
plt.show()
