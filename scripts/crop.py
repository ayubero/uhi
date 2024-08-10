from utils.preprocessing import mask_shapefile
import rioxarray

input_path = '../madrid/subset_S3A_SL_2_LST_20230824T212144_20230824T212444_20230826T063732.tif'
output_path = '../madrid/LST_StudyArea.tif'
shapefile_path = '../data/shapefiles/madrid_study_area.shp'

'''with rioxarray.open_rasterio(input_path) as src:
    dst = src.rio.reproject('EPSG:25830')
    dst.rio.to_raster(input_path)'''

mask_shapefile(shapefile_path, input_path, output_path)