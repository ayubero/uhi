import os
import geopandas as gpd
from pyproj import CRS, Transformer

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
    print(extent_etrs89)

    # Since the coordinates are in a projected coordinate system, the dimensions can be directly computed
    width = extent_etrs89['lon_ne'] - extent_etrs89['lon_sw']
    columns = width / 5 # Resolution of 5m/px
    height = extent_etrs89['lat_ne'] - extent_etrs89['lat_sw']
    rows = height / 5 # Resolution of 5m/px
    print('Columns: ', columns)
    print('Rows', rows)

    extent_wgs84, extent_etrs89

if __name__ == '__main__':
    directory = 'cities'
    if os.path.isdir(directory):
        selected_folder = choose_folder(directory)
        if selected_folder:
            study_area_shapefile_path = os.path.join(directory, selected_folder, 'shapefiles/study_area.shp')
            print(f'Study area shapefile: {study_area_shapefile_path}')
            extent_wgs84, extent_etrs89 = get_extent(study_area_shapefile_path)

            
    else:
        print('Invalid directory path.')
