from utils.preprocessing import mask_shapefile
import rioxarray

input_path = '../madrid/subset_S3B_SL_2_LST_20230821T104131_20230821T104431_20230821T124950_0179.tif'
output_path = '../madrid/lst/LST_20230821T104131_StudyArea.tif'
shapefile_path = '../data/shapefiles/madrid_study_area.shp'

'''with rioxarray.open_rasterio(input_path) as src:
    dst = src.rio.reproject('EPSG:25830')
    dst.rio.to_raster(input_path)'''

mask_shapefile(shapefile_path, input_path, output_path)