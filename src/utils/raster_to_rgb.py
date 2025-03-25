import os
import rasterio

def raster_to_rgb_image(raster_path:str):
    with rasterio.open(raster_path) as src:
        # Read bands
        red = src.read(4) 
        green = src.read(3)
        blue = src.read(2)

        composition = [red, green, blue]

        # Configure params
        param = src.meta
        param.update(driver='GTiff',
                    count=len(composition), # Band number
                    dtype='int16', # Datatype
                    width=red.shape[1], # Image width
                    height=red.shape[0])
        
        # Export compound image
        dest_name = raster_path.replace('StudyArea.tif', 'rgb.tif')
        with rasterio.open(dest_name, 'w', **param) as dest:
            for num, band in enumerate(composition, start=1):
                dest.write(band, num)

if __name__ == '__main__':
    # Go to directory with study area rasters
    raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
    os.chdir(raster_path)

    # Process raster
    raster_name = '20230403T105629_StudyArea.tif'
    raster_to_rgb_image(raster_name)