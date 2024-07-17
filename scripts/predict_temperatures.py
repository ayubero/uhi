import os, glob
import numpy as np
import rasterio
import joblib
from rasterio.plot import show
import matplotlib.pyplot as plt

# Change to data directory and load the model
os.chdir(os.path.abspath(os.path.join(os.getcwd(), '../data')))
model = joblib.load('model.joblib')

# Go to directory with study area rasters
raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
os.chdir(raster_path)

# List all .tif files
raster_list = glob.glob('*.tif')

# Read and stack all bands
#for raster_name in raster_list:
with rasterio.open(raster_list[0]) as src:
    no_data_value = src.nodata

    # Read bands
    nir = src.read(8)
    swir1 = src.read(11)

    nir = np.where(nir == no_data_value, np.nan, nir)
    swir1 = np.where(swir1 == no_data_value, np.nan, swir1)
    
    # Stack the bands along a new axis
    X = np.stack([nir, swir1], axis=-1)

    # Reshape the data to 2D
    num_samples = X.shape[0] * X.shape[1]
    X_reshaped = X.reshape((num_samples, 2))

    # Handle NaN values if necessary
    nan_mask = np.isnan(X_reshaped).any(axis=1)
    X_reshaped = X_reshaped[~nan_mask]

    # Predict temperatures
    temperatures = model.predict(X_reshaped)

    # Clip the predicted temperatures to the range [0, 50]
    temperatures = np.clip(temperatures, 10, 40)

    # Reshape the temperatures back to the original 2D shape
    temperatures_2d = np.full((X.shape[0], X.shape[1]), np.nan)
    temperatures_2d[~nan_mask.reshape((X.shape[0], X.shape[1]))] = temperatures

    plt.figure(figsize=(10, 10))
    plt.imshow(temperatures_2d, cmap='plasma')
    plt.colorbar(label='ºC')
    plt.title(f'Temperatures')
    plt.show()

    #print(temperatures_2d)