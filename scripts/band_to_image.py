import os, glob
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# Normalize the bands data to the range 0-1
def normalize(band):
    return (band - band.min()) / (band.max() - band.min())

# Go to directory with study area rasters
raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
os.chdir(raster_path)

# List all .tif files
list = glob.glob('*.tif')
for raster_name in list:
    with rasterio.open(raster_name) as src:
        # Read band 8 (NIR)
        band = src.read(8) 

        # Normalize for better visualization
        #band = normalize(band)

        # Export
        img_name = raster_name.replace('.tif', '_nir.png')
        plt.imsave(img_name, band, cmap='plasma')

        # Read RGB bands
        red = src.read(4)
        green = src.read(3)
        blue = src.read(2)
        
        # Normalize bands
        red = normalize(red)
        green = normalize(green)
        blue = normalize(blue)
        
        # Stack the bands into an RGB image

        # Export
        rgb = np.dstack((red, green, blue))
        img_name = raster_name.replace('.tif', '_rgb.png')
        plt.imsave(img_name, rgb)

'''# Remove all images
images = glob.glob('*.png')
for image in images:
    os.remove(image)'''