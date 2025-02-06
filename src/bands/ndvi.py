import rasterio
import matplotlib.pyplot as plt
import os

def ndvi(red_path: str, nir_path: str, output_path: str, show_result=False) -> None:
    '''
    Computes the Normalized Difference Vegetation Index (NDVI) as proposed by Kriegler et al., 1969
    NDVI = (NIR - Red) / (NIR + Red)
    '''

    # Open rasters
    with rasterio.open(red_path) as src:
        red = src.read(1)
    with rasterio.open(nir_path) as src:
        nir = src.read(1)

    # Compute NDVI
    ndvi = (nir - red) / (nir + red)

    if show_result:
        plt.figure(figsize=(10, 10))
        plt.imshow(ndvi, cmap='RdYlGn')
        plt.colorbar(label='NDVI values')
        plt.title(f'NDVI')
        plt.show()

    # Save result
    params = src.meta
    print(params)
    params.update(count = 1, dtype='float32')

    with rasterio.open(output_path, 'w', **params) as dest:
            dest.write_band(1, ndvi)

if __name__ == '__main__':
    red_path = os.path.abspath(os.path.join(os.getcwd(), '../data/red_average.tif'))
    nir_path = os.path.abspath(os.path.join(os.getcwd(), '../data/nir_average.tif'))
    output_path = os.path.abspath(os.path.join(os.getcwd(), '../data/rasters/Madrid_ETRS89_NDVI.tif'))

    ndvi(red_path, nir_path, output_path)