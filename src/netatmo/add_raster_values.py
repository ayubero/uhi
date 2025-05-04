import os
import glob
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
from omegaconf import OmegaConf
from src.logger_setup import logger

# Load the YAML config file
config = OmegaConf.load('../config.yaml')

from src.utils.normalize import normalize
from src.utils.resample import resample

def add_raster_values(raster_folder, stations_folder):
    resolution = config.kriging.added_variables_resolution

    # Normalize and resamples rasters
    #normalize(os.path.join(raster_folder, 'mdt.tif'))
    #normalize(os.path.join(raster_folder, 'lst.tif'))
    resample(os.path.join(raster_folder, config.paths.rasters.svf), resolution)
    resample(os.path.join(raster_folder, config.paths.rasters.gli), resolution)
    #resample(os.path.join(raster_folder, 'nbai.tif'), resolution)
    #resample(os.path.join(raster_folder, 'ndti.tif'), resolution)
    #resample(os.path.join(raster_folder, 'mdt_normalized.tif'), resolution)
    #resample(os.path.join(raster_folder, 'lst_normalized.tif'), resolution)

    # Get temperature differences
    df = pd.read_csv('./stations/diff.csv', delimiter=',')
    df.head()

    # Define the CRS for the original (longitude, latitude) and target (projected coordinates)
    wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 (longitude, latitude)
    utm = pyproj.CRS('EPSG:' + config.crs)  # UTM projection (ETRS89 / UTM zone 30N)

    # Create a transformer to convert between the two coordinate systems
    transformer = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True)

    # Apply transformation to each row and modify the DataFrame
    df['x'], df['y'] = zip(*df.apply(lambda row: transformer.transform(row['lon'], row['lat']), axis=1))
    df.head()

    # List all .tif files
    list = glob.glob(raster_folder + '/*.tif')
    
    # Add values from SVF raster
    svf_raster_path = os.path.join(raster_folder, 'svf_scaled.tif')
    with rasterio.open(svf_raster_path) as src:
        svf = src.read(1)

        # Extract coordinates for each pixel
        coords = np.array([src.transform * (col, row)
                        for row in range(src.height)
                        for col in range(src.width)])

        lons, lats = coords[:, 0], coords[:, 1]

        # Get SVF values
        svfs = []
        for index, station in df.iterrows():
            # Convert the coordinates (x, y) to row and column
            row, col = src.index(station['x'], station['y'])
            
            # Ensure the indices are within bounds
            if 0 <= row < src.height and 0 <= col < src.width:
                # Read the value of the pixel
                svf_value = svf[row, col]
                svfs.append(svf_value)
            else:
                # Handle out-of-bounds cases
                logger.warning(f'Coordinates ({station['lon']}, {station['lat']}) are out of bounds.')
                svfs.append(np.nan)
        df['svf'] = svfs

    # Add values from GLI raster
    gli_raster_path = os.path.join(raster_folder, config.paths.rasters.gli)
    with rasterio.open(gli_raster_path) as src:
        gli = src.read(
            out_shape=(
                src.count,
                int(3039),
                int(3039)
            ),
            resampling = Resampling.bilinear
        )[0]

        # Get NDVI values
        glis = []
        for index, station in df.iterrows():
            # Convert the coordinates (x, y) to row and column
            row, col = src.index(station['x'], station['y'])
        
            # Ensure the indices are within bounds
            if 0 <= row < src.height and 0 <= col < src.width:
                # Read the value of the pixel
                gli_value = gli[row, col]
                glis.append(gli_value)
            else:
                # Handle out-of-bounds cases
                logger.warning(f'Coordinates ({station['lon']}, {station['lat']}) are out of bounds.')
                glis.append(np.nan)  # Append NaN for out-of-bounds
        df['gli'] = glis

    # Drop unnecessary columns
    df = df.drop(columns=['x', 'y'])
    
    # Drop NaNs
    df = df.dropna()

    df.to_csv(os.path.join(stations_folder, config.paths.stations.stations), index=False)