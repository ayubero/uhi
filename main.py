import os
import geopandas as gpd
from pyproj import CRS, Transformer
import datetime
import argparse
from omegaconf import OmegaConf
import shutil
import docker

from src.logger_setup import logger
from src.utils.dem_to_svf import dem_to_svf
from src.download.sentinel import download
from src.netatmo.netatmo_scrapper import get_stations, get_station_data
from src.netatmo.temperature_qc import perform_qc
from src.netatmo.compute_temperature_differences import compute_differences
from src.netatmo.add_raster_values import add_raster_values
from src.indices.gli import gli
from src.indices.nbai import nbai
from src.indices.ndti import ndti
from src.indices.ndvi import ndvi
from src.utils.average_values import average_values
from src.cnn.generate_patches import extract_patches
from src.cnn.train import train
from src.cnn.predict import predict

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

def main():
    # Load the YAML config file
    config = OmegaConf.load('config.yaml')

    # Get arguments
    parser = argparse.ArgumentParser(description="Process some input.")
    parser.add_argument('-c', '--city', required=True, help='Name of the city')
    parser.add_argument('-s', '--step', required=True, help='Step name')

    args = parser.parse_args()

    logger.info('Starting script...')
    logger.info(f'Selected city: {args.city}')
    logger.info(f'Selected step: {args.step}')

    working_folder = os.path.join('data', args.city)
    raster_folder = os.path.join(working_folder, config.paths.rasters.folder_name)
    stations_folder = os.path.join(working_folder, config.paths.stations.folder_name)

    match args.step:
        case 'download-sentinel':
            # Get extents                          
            study_area_shapefile_path = os.path.join(working_folder, 'shapefiles/study_area.shp')
            print(f'Study area shapefile: {study_area_shapefile_path}')
            extent_wgs84, _ = get_extent(study_area_shapefile_path)

            download(raster_folder, config.study_period.start, config.study_period.end, extent_wgs84['lon_ne'], extent_wgs84['lat_ne'], 10.00, study_area_shapefile_path)
        case 'download-netatmo':
            # Get extents                          
            study_area_shapefile_path = os.path.join(working_folder, 'shapefiles/study_area.shp')
            print(f'Study area shapefile: {study_area_shapefile_path}')
            extent_wgs84, _ = get_extent(study_area_shapefile_path)

            # Download Netatmo data
            token = config.download.netatmo.token
            start_date = datetime.strptime(config.study_period.start, "%d-%m-%Y").date()
            end_date = datetime.strptime(config.study_period.end, "%d-%m-%Y").date()
            get_stations(token, extent_wgs84['lat_ne'], extent_wgs84['lon_ne'], extent_wgs84['lat_sw'], extent_wgs84['lon_sw'], stations_folder)
            get_station_data(token, stations_folder, start_date, end_date)
        case 'average-bands':
            # Process sentinel variables
            sentinel_folder = os.path.join(
                raster_folder,
                config.paths.rasters.sentinel_folder_name
            )
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
                logger.info('Processing', band_name)
                output_path = os.path.join(
                    raster_folder, 
                    config.paths.rasters.average_prefix + config.paths.rasters[band_name]
                )
                average_values(sentinel_folder, output_path, band_index)
        case 'compute-gli':
            gli(
                os.path.join(raster_folder, config.paths.rasters.average_red),
                os.path.join(raster_folder, config.paths.rasters.gli),
                os.path.join(raster_folder, config.paths.rasters.blue),
                os.path.join(raster_folder, config.paths.rasters.gli)
            )
        case 'compute-nbai':
            nbai(
                os.path.join(raster_folder, config.paths.rasters.average_swir1),
                os.path.join(raster_folder, config.paths.rasters.average_swir2),
                os.path.join(raster_folder, config.paths.rasters.average_green),
                os.path.join(raster_folder, config.paths.rasters.nbai)
            )
        case 'compute-ndti':
            ndti(
                os.path.join(raster_folder, config.paths.rasters.average_red),
                os.path.join(raster_folder, config.paths.rasters.average_green),
                os.path.join(raster_folder, config.paths.rasters.ndti)
            )
        case 'compute-ndvi':
            ndvi(
                os.path.join(raster_folder, config.paths.rasters.average_red),
                os.path.join(raster_folder, config.paths.rasters.average_nir),
                os.path.join(raster_folder, config.paths.rasters.ndvi)
            )
        case 'compute-svf':
            # Convert DSM to SVF
            dem_path = os.path.join(raster_folder, config.paths.rasters.dsm)
            dem_to_svf(dem_path, raster_folder)
        case 'perform-temperature-qc':
            perform_qc(stations_folder)
        case 'compute-differences':
            compute_differences(stations_folder)
        case 'add-raster-values':
            add_raster_values(raster_folder, stations_folder)
        case 'predict-with-kriging':
            client = docker.from_env()
            docker_folder = os.path.join(working_folder, config.paths.kriging.folder_name)

            # Copy necessary files into the docker folder
            source_files = [
                os.path.join(raster_folder, config.paths.rasters.svf),
                os.path.join(raster_folder, config.paths.rasters.gli),
                os.path.join(stations_folder, config.paths.stations.stations)
            ]
            destination_files = [
                os.path.join(docker_folder, config.paths.rasters.svf),
                os.path.join(docker_folder, config.paths.rasters.gli),
                os.path.join(docker_folder, config.paths.stations.stations)
            ]
            for source, destination in zip(source_files, destination_files):
                shutil.copy2(source, destination)

            # Build the image
            image, logs = client.images.build(path=docker_folder, tag='kriging-image')

            '''# Print the build logs
            for chunk in logs:
                if 'stream' in chunk:
                    print(chunk['stream'].strip())'''
            
            # Run the container
            container = client.containers.run(
                image='kriging-image',
                name='kriging-container',
                detach=True,
                remove=True # Automatically remove container when done
            )

            # Wait for it to finish
            result = container.wait()

            # Print output
            print('Exit code:', result['StatusCode'])
            print('Logs:')
            print(container.logs().decode())
            
            # Remove input files
            for file_path in destination_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
        case 'predict-with-cnn':
            predict(
                os.path.join(raster_folder, config.paths.rasters.stacked_variables), 
                os.path.join(raster_folder, config.paths.rasters.cnn_result)
            )
        case 'train-cnn':
            patch_folder = os.path.join(working_folder, config.paths.cnn.patch_folder_name)
            explanatory_variables_path = os.path.join(raster_folder, config.paths.rasters.stacked_variables)
            target_variable_path = os.path.join(raster_folder, config.rasters.kriging_result)
            extract_patches(explanatory_variables_path, target_variable_path, config.cnn.patch_size, patch_folder)
            train(patch_folder)
        case _:
            logger.info('No step found')

if __name__ == '__main__':
    main()