import rasterio
import matplotlib.pyplot as plt
import numpy as np
import os

def nbai(swir1_path: str, swir2_path: str, green_path: str, output_path: str, show_result=False) -> None:
    '''
    Computes the Normalized Built-up Area Index (NBAI) as proposed by Waqar et al., 2012
    NBAI = (SWIR2 - (SWIR1 / Green)) / (SWIR2 + (SWIR1 / Green))
    '''

    # Open rasters
    with rasterio.open(swir1_path) as src:
        swir1 = src.read(1)
    with rasterio.open(swir2_path) as src:
        swir2 = src.read(1)
    with rasterio.open(green_path) as src:
        green = src.read(1)

    # Compute the ratio with np.divide() to avoid division by zero
    ratio = np.divide(swir1, green, where=(green != 0), out=np.zeros_like(swir1, dtype=float))

    # Compute NBAI
    denominator = swir2 + ratio
    nbai = np.divide(swir2 - ratio, denominator, where=(denominator != 0), out=np.zeros_like(swir2, dtype=float))
    
    if show_result:
        plt.figure(figsize=(10, 10))
        plt.imshow(nbai, cmap='RdYlGn')
        plt.colorbar(label='NBAI values')
        plt.title(f'NBAI')
        plt.show()

    # Save result
    params = src.meta
    params.update(nodata=np.nan)
    params.update(count = 1, dtype='float32')

    with rasterio.open(output_path, 'w', **params) as dest:
            dest.write_band(1, nbai)

if __name__ == '__main__':
    swir1_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/red_average_madrid.tif'))
    swir2_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/nir_average_madrid.tif'))
    green_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/green_average_madrid.tif'))
    output_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/rasters/Madrid_ETRS89_NBAI.tif'))

    nbai(swir1_path, swir2_path, green_path, output_path)
