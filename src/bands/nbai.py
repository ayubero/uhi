import rasterio
import matplotlib.pyplot as plt
import os

def nbai(swir1_path: str, swir2_path: str, green_path: str, output_path: str, show_result=False) -> None:
    '''
    Computes the Normalized Built-up Area Index (NBAI) as proposed by Waqar et al., 2012
    NBAI = ((SWIR2 - SWIR1) / Green) / ((SWIR2 + SWIR1) / Green)
    '''

    # Open rasters
    with rasterio.open(swir1_path) as src:
        swir1 = src.read(1)
    with rasterio.open(swir2_path) as src:
        swir2 = src.read(1)
    with rasterio.open(green_path) as src:
        green = src.read(1)

    # Compute NBAI
    nbai = ((swir2 - swir1) / green) / ((swir2 + swir1) / green)

    if show_result:
        plt.figure(figsize=(10, 10))
        plt.imshow(nbai, cmap='RdYlGn')
        plt.colorbar(label='NBAI values')
        plt.title(f'NBAI')
        plt.show()

    # Save result
    params = src.meta
    params.update(count = 1, dtype='float32')

    with rasterio.open(output_path, 'w', **params) as dest:
            dest.write_band(1, nbai)

if __name__ == '__main__':
    swir1_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/red_average_zaragoza.tif'))
    swir2_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/nir_average_zaragoza.tif'))
    green_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/green_average_zaragoza.tif'))
    output_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/rasters/Zaragoza_ETRS89_NBAI.tif'))

    nbai(swir1_path, swir2_path, green_path, output_path)