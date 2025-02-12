import os
import rasterio

# Go to directory with study area rasters
raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
os.chdir(raster_path)

# Process raster
raster_name = '20230403T105629_StudyArea.tif'
with rasterio.open(raster_name) as src:
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
    dest_name = raster_name.replace('StudyArea.tif', 'rgb.tif')
    with rasterio.open(dest_name, 'w', **param) as dest:
        for num, band in enumerate(composition, start=1):
            dest.write(band, num)