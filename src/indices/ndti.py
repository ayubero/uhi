import rasterio
import matplotlib.pyplot as plt
import os

def ndti(red_path: str, green_path: str, output_path: str, show_result=False) -> None:
    '''
    Computes the Normalized Difference Turbidity Index (NDTI) as proposed by Lacaux et al., 2007
    NDTI = (Red - Green) / (Red + Green)
    '''

    # Open rasters
    with rasterio.open(red_path) as src:
        red = src.read(1)
    with rasterio.open(green_path) as src:
        green = src.read(1)

    # Compute NDTI
    ndti = (red - green) / (red + green)

    if show_result:
        plt.figure(figsize=(10, 10))
        plt.imshow(ndti, cmap='RdYlGn')
        plt.colorbar(label='NDTI values')
        plt.title(f'NDTI')
        plt.show()

    # Save result
    params = src.meta
    params.update(count = 1, dtype='float32')

    with rasterio.open(output_path, 'w', **params) as dest:
            dest.write_band(1, ndti)

if __name__ == '__main__':
    red_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/red_average_madrid.tif'))
    green_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/green_average_madrid.tif'))
    output_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/rasters/Madrid_ETRS89_NDTI.tif'))

    ndti(red_path, green_path, output_path)
