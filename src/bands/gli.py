import rasterio
import matplotlib.pyplot as plt
import os

def gli(red_path: str, green_path: str, blue_path: str, output_path: str, show_result=False) -> None:
    '''
    Computes the Green Leaf Index (GLI) as proposed by Louhaichi et al., 2001
    GLI = (2*Green - Red - Blue) / (2*Green + Red + Blue)
    '''

    # Open rasters
    with rasterio.open(red_path) as src:
        red = src.read(1)
    with rasterio.open(green_path) as src:
        green = src.read(1)
    with rasterio.open(blue_path) as src:
        blue = src.read(1)

    # Compute GLI
    nbai = (2*green - red - blue) / (2*green + red + blue)

    if show_result:
        plt.figure(figsize=(10, 10))
        plt.imshow(nbai, cmap='RdYlGn')
        plt.colorbar(label='GLI values')
        plt.title(f'GLI')
        plt.show()

    # Save result
    params = src.meta
    params.update(count = 1, dtype='float32')

    with rasterio.open(output_path, 'w', **params) as dest:
            dest.write_band(1, nbai)

if __name__ == '__main__':
    red_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/red_average_zaragoza.tif'))
    green_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/green_average_zaragoza.tif'))
    blue_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/blue_average_zaragoza.tif'))
    output_path = os.path.abspath(os.path.join(os.getcwd(), '../../data/rasters/Zaragoza_ETRS89_GLI.tif'))

    gli(red_path, green_path, blue_path, output_path)
