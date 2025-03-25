import os, glob
import numpy as np
import rasterio
import matplotlib.pyplot as plt

def average_values(input_folder: str, output_path: str, band_index: int, show_result=False):
    '''
    Compute average of all the files contained in `input_folder`, the result is exported as `output_path`.
    '''

    # Go to directory with study area rasters
    #os.chdir(input_folder)

    # List all .tif files
    list = glob.glob(input_folder + '/*.tif')

    # Read and stack all bands
    dataset = []
    no_data_value = -1
    band: np.ndarray
    source: rasterio.io.DatasetReader
    for raster_name in list:
        with rasterio.open(raster_name) as src:
            no_data_value = src.nodata if src.nodata is not None else -9999
            band = src.read(band_index)
            dataset.append(band)
            source = src


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

    # Mask clusters where original band had no-data
    average_band = np.ma.masked_where(band == no_data_value, average_band)

    if show_result:
        plt.figure(figsize=(10, 10))
        plt.imshow(average_band, cmap='plasma')
        plt.colorbar(label='Band values')
        plt.title(f'Band average')
        plt.show()

    # Export
    params = source.meta
    params.update(count = 1)
    with rasterio.open(output_path, 'w', **params) as dest:
        dest.write_band(1, average_band)

if __name__ == '__main__':
    rasters_folder = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel/madrid'))
    output_name = os.path.abspath(os.path.join(os.getcwd(), '../data/swir2_average_madrid.tif'))
    average_values(rasters_folder, output_name, 12)
