import os
import geopandas as gpd
from pyproj import CRS, Transformer
from datetime import date

from src.dem_to_svf import dem_to_svf
from src.netatmo_scrapper import get_stations, get_station_data
from src.average_values import average_values
from src.bands.gli import gli
from src.bands.nbai import nbai
from src.bands.ndti import ndti

def list_folders(directory):
    '''List all folders in the given directory.'''
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

def choose_folder(directory):
    '''Display a menu of folders for the user to choose from.'''
    folders = list_folders(directory)
    if not folders:
        print('No folders found in the specified directory.')
        return None

    print('Select a folder:')
    for i, folder in enumerate(folders, start=1):
        print(f'{i}. {folder}')

    while True:
        try:
            choice = int(input('Enter the number of your choice: '))
            if 1 <= choice <= len(folders):
                return folders[choice - 1]
            else:
                print('Invalid choice. Please enter a number from the list.')
        except ValueError:
            print('Invalid input. Please enter a number.')

def get_extent(shapefile_path):
    gdf = gpd.read_file(shapefile_path)

    # Get the bounding box (minx, miny, maxx, maxy)
    minx, miny, maxx, maxy = gdf.total_bounds

    # Get the CRS of the shapefile
    shapefile_crs = gdf.crs

    # Define transformer to WGS84 if the CRS is different
    if shapefile_crs != CRS.from_epsg(4326):
        transformer = Transformer.from_crs(shapefile_crs, CRS.from_epsg(4326), always_xy=True)
        minx, miny = transformer.transform(minx, miny)
        maxx, maxy = transformer.transform(maxx, maxy)

    # Store extent in the required format
    extent_wgs84 = {
        'lat_ne': maxy, # Northeast latitude (max latitude)
        'lon_ne': maxx, # Northeast longitude (max longitude)
        'lat_sw': miny, # Southwest latitude (min latitude)
        'lon_sw': minx, # Southwest longitude (min longitude)
    }

    # Transform into ETRS89
    transformer = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(25830), always_xy=True)
    minx, miny = transformer.transform(minx, miny)
    maxx, maxy = transformer.transform(maxx, maxy)

    # Store extent in the required format
    extent_etrs89 = {
        'lat_ne': maxy, # Northeast latitude (max latitude)
        'lon_ne': maxx, # Northeast longitude (max longitude)
        'lat_sw': miny, # Southwest latitude (min latitude)
        'lon_sw': minx, # Southwest longitude (min longitude)
    }

    # Print the extent
    #print(extent_etrs89)

    # Since the coordinates are in a projected coordinate system, the dimensions can be directly computed
    width = extent_etrs89['lon_ne'] - extent_etrs89['lon_sw']
    columns = width / 5 # Resolution of 5m/px
    height = extent_etrs89['lat_ne'] - extent_etrs89['lat_sw']
    rows = height / 5 # Resolution of 5m/px
    print('Columns: ', columns)
    print('Rows', rows)

    return extent_wgs84, extent_etrs89

def get_variable_path(raster_folder, band_name):
    return os.path.join(raster_folder, f'average_{band_name}.tif')

if __name__ == '__main__':
    directory = 'cities'
    if os.path.isdir(directory):
        selected_folder = choose_folder(directory)
        if selected_folder:
            working_folder = os.path.join(directory, selected_folder)
            raster_folder = os.path.join(working_folder, 'rasters')
            stations_folder = os.path.join(working_folder, 'stations')

            # Get extents                          
            study_area_shapefile_path = os.path.join(working_folder, 'shapefiles/study_area.shp')
            print(f'Study area shapefile: {study_area_shapefile_path}')
            extent_wgs84, extent_etrs89 = get_extent(study_area_shapefile_path)

            # Convert DEM to SVF
            #dem_path = os.path.join(raster_folder, 'MDS.tif')
            #dem_to_svf(dem_path, raster_folder)

            # Download Netatmo data
            #token = '679b955ca250de0e040eb492|af139a78741792c9320be1292af57786'
            #get_stations(token, extent_wgs84['lat_ne'], extent_wgs84['lon_ne'], extent_wgs84['lat_sw'], extent_wgs84['lon_sw'], stations_folder)
            #get_station_data(token, stations_folder, date(2023, 6, 1), date(2023, 9, 1))

            # Process sentinel variables
            '''sentinel_folder = os.path.join(raster_folder, 'sentinel')
            sentinel_bands = [
                ('blue', 2),
                ('green', 3),
                ('red', 4),
                ('nir', 8),
                ('swir1', 11),
                ('swir2', 12),
            ]
            # Create average rasters for each band
            for band in sentinel_bands:
                band_name, band_index = band
                print('Processing', band_name)
                output_path = get_variable_path(raster_folder, band_name)
                average_values(sentinel_folder, output_path, band_index)
            # Generate variables
            gli(
                get_variable_path(raster_folder, 'red'),
                get_variable_path(raster_folder, 'green'),
                get_variable_path(raster_folder, 'blue'),
                os.path.join(raster_folder, 'GLI.tif')
            )'''
            nbai(
                get_variable_path(raster_folder, 'swir1'),
                get_variable_path(raster_folder, 'swir2'),
                get_variable_path(raster_folder, 'green'),
                os.path.join(raster_folder, 'NBAI.tif'),
                True
            )
            '''ndti(
                get_variable_path(raster_folder, 'red'),
                get_variable_path(raster_folder, 'green'),
                os.path.join(raster_folder, 'NDTI.tif')
            )'''

    else:
        print('Invalid directory path.')