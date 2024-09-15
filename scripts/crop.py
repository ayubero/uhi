from utils.preprocessing import mask_shapefile
import rioxarray

input_path = '../data/swir2_average.tif'
output_path = '../data/swir2_average_masked.tif'
shapefile_path = '../data/shapefiles/zaragoza_outline.shp'

'''with rioxarray.open_rasterio(input_path) as src:
    dst = src.rio.reproject('EPSG:25830')
    dst.rio.to_raster(input_path)'''

mask_shapefile(shapefile_path, input_path, output_path)