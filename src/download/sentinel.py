from dotenv import load_dotenv
from rasterio.enums import Resampling
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.vrt import WarpedVRT
import fiona
from fiona.transform import transform_geom
import requests
import shutil
import boto3
import os, glob, sys
import rasterio

def reproject_raster(input_file, output_file, target_crs='EPSG:25830', nodata=-1):
    with rasterio.open(input_file) as src:
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update({
            'crs': target_crs,
            'transform': transform,
            'width': width,
            'height': height,
            'nodata': nodata
        })

        with rasterio.open(output_file, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear  # You can use nearest or cubic depending on your data
                )

    print(f'Reprojected raster saved to: {output_file}')

# Read and resample raster
def read_resample(path, scale):
    with rasterio.open(path) as dataset:
        # Resample image to 10m where given scale is used
        data = dataset.read(
            out_shape=(
                dataset.count,
                int(dataset.height * scale),
                int(dataset.width * scale)
            ),
            resampling = Resampling.bilinear
        )
        transform = dataset.transform * dataset.transform.scale(
            (dataset.width / data.shape[-1]),
            (dataset.height / data.shape[-2])
        )
        return data[0], transform

# Crop to study area
def crop(file_path, output_path, shapefile):
    os.chdir(file_path)

    # List files according to Sentinel2 bands
    listB10m = sorted(glob.glob('R10m/*.jp2'))
    listB20m = sorted(glob.glob('R20m/*.jp2'))
    listB60m = sorted(glob.glob('R60m/*.jp2'))

    # Check all bands match
    print('B2', listB10m[1])
    print('B3', listB10m[2])
    print('B4', listB10m[3])
    print('B8', listB10m[4])
    print('B1', listB20m[1])
    print('B5', listB20m[5])
    print('B6', listB20m[6])
    print('B7', listB20m[7])
    print('B8A', listB20m[10])
    print('B11', listB20m[8])
    print('B12', listB20m[9])
    print('B9', listB60m[8])
    
    # Read and resample bands 10m
    B2, transform = read_resample(listB10m[1], 1.0)
    B3, _ = read_resample(listB10m[2], 1.0)
    B4, _ = read_resample(listB10m[3], 1.0)
    B8, _ = read_resample(listB10m[4], 1.0)
    B1, _ = read_resample(listB20m[1], 2.0)
    B5, _ = read_resample(listB20m[5], 2.0)
    B6, _ = read_resample(listB20m[6], 2.0)
    B7, _ = read_resample(listB20m[7], 2.0)
    B8A, _ = read_resample(listB20m[10], 2.0) # Band 8A to 20m resolution 
    B11, _ = read_resample(listB20m[8], 2.0)
    B12, _ = read_resample(listB20m[9], 2.0)
    B9, _ = read_resample(listB60m[8], 6.0)

    # Compose bands
    S2_RS = [B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12]
    #S2_RS = [B8, B11, B12]

    # Configure params
    param = rasterio.open(listB10m[1]).meta # Take info from first band
    param.update(driver='GTiff',
                count=len(S2_RS), # Band number
                dtype='int16', # Datatype
                transform=transform, # Image transformation
                width=B2.shape[1], # Image width
                height=B2.shape[0]) # Image height

    # Output name
    os.chdir(output_path)
    name_S2 = os.path.join(os.getcwd(), listB10m[1][12:27] + '_CompleteTile.tif')

    # Export compound image
    with rasterio.open(name_S2, 'w', **param) as SENTINEL2:
        for num, band in enumerate(S2_RS, start=1):
            SENTINEL2.write(band, num)

    # Mask using shapefile
    nodata = -1

    with fiona.open(shapefile, 'r') as shapefile:
        shapes = [feature['geometry'] for feature in shapefile]
        shapes_crs = shapefile.crs

    with rasterio.open(name_S2) as src:
        print('Raster CRS:', src.crs)
        print('Shapefile CRS:', shapes_crs)
        '''if shapes_crs != src.crs:
            print('Reprojecting shapefile to match raster CRS...')
            shapes = [transform_geom(shapes_crs, src.crs, geom) for geom in shapes]
        else:
            print('CRS match!')
        out_image, out_transform = mask(src, shapes, nodata=nodata, crop=True)
        out_meta = src.meta'''
        if shapes_crs != src.crs:
            print('Reprojecting raster to match shapefile CRS...')

            # Set up the in-memory reprojected raster
            with WarpedVRT(
                src,
                crs=shapes_crs,
                resampling=Resampling.nearest
            ) as vrt:
                out_image, out_transform = mask(vrt, shapes, nodata=nodata, crop=True)
                out_meta = vrt.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "nodata": nodata
                })
        else:
            print('CRS match!')
            out_image, out_transform = mask(src, shapes, nodata=nodata, crop=True)
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": nodata
            })
        
    out_image[out_image == src.nodata] = nodata

    out_meta.update({
        'driver': 'GTiff',
        'height': out_image.shape[1],
        'width': out_image.shape[2],
        'transform': out_transform,
        'nodata': nodata
    })

    output_file = name_S2.replace('CompleteTile.tif', 'StudyArea.tif')
    with rasterio.open(output_file, 'w', **out_meta) as dest:
        dest.write(out_image)

    # Reproject to EPSG:25830
    #reproject_raster(output_file, output_file)

    # Remove the file, leaving just the study area
    try:
        os.remove(name_S2)
    except FileNotFoundError:
        print(f"File '{name_S2}' not found.")
    except PermissionError:
        print(f"Permission denied: unable to remove '{name_S2}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

    print('Finished cutting')

# Load environment variables
load_dotenv()

def download_product(bucket, product: str, target: str = '') -> None:
    '''
    Downloads every file in bucket with provided product as prefix

    Raises FileNotFoundError if the product was not found

    Args:
        bucket: boto3 Resource bucket object
        product: Path to product
        target: Local catalog for downloaded files. Should end with an `/`. Default current directory.
    '''
    files = bucket.objects.filter(Prefix=product)
    if not list(files):
        raise FileNotFoundError(f'Could not find any files for {product}')
    for file in files:
        os.makedirs(os.path.dirname(file.key), exist_ok=True)
        if not os.path.isdir(file.key):
            bucket.download_file(file.key, f'{target}{file.key}')

def remove_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' and all its contents have been removed.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

def download(download_folder, start_date, end_date, longitude, latitude, clouds: float, study_area_shapefile):
    # Establish connection to S3 resource
    s3 = boto3.resource(
        's3',
        endpoint_url='https://eodata.dataspace.copernicus.eu',
        aws_access_key_id=os.getenv('ACCESS_KEY'),
        aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
        region_name='default'
    ) # Generated secrets

    # Get info about products
    # Sentinel-2
    #start_date = '2023-08-01'
    #end_date = '2023-08-31'
    # Zaragoza
    #latitude = '41.648336063076243'
    #longitude = '-0.88482371152898'
    # Madrid
    #latitude = '40.416775'
    #longitude = '-3.703790'
    clouds = str(clouds) # Cloud percentage
    product_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name%20eq%20%27SENTINEL-2%27%20and%20Attributes/OData.CSC.DoubleAttribute/any(att:att/Name%20eq%20%27cloudCover%27%20and%20att/OData.CSC.DoubleAttribute/Value%20le%20' + clouds + ')%20and%20OData.CSC.Intersects(area=geography%27SRID=4326;POINT(' + longitude + '%20' + latitude + ')%27)%20and%20ContentDate/Start%20gt%20' + start_date + 'T00:00:00.000Z%20and%20ContentDate/Start%20lt%20' + end_date + 'T00:00:00.000Z&$orderby=ContentDate/Start%20desc'

    # Sentinel-3
    #product_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name%20eq%20%27SENTINEL-3%27%20and%20Attributes/OData.CSC.DoubleAttribute/any(att:att/Name%20eq%20%27cloudCover%27%20and%20att/OData.CSC.DoubleAttribute/Value%20le%2030.00)%20and%20OData.CSC.Intersects(area=geography%27SRID=4326;POINT(-0.88482371152898%2041.648336063076243)%27)%20and%20ContentDate/Start%20gt%202023-08-01T00:00:00.000Z%20and%20ContentDate/Start%20lt%202023-08-31T00:00:00.000Z&$orderby=ContentDate/Start%20desc'

    # Fetch the JSON data from the URL
    response = requests.get(product_url)

    if response.status_code != 200:
        print('Failed to retrieve data')
        sys.exit(1)

    data = response.json()

    # Path where data will be downloaded
    target_path = os.path.abspath(os.path.join(os.getcwd(), download_folder))

    # Output path after preprocessing
    output_path = os.path.join(target_path, 'sentinel')
    print('Output path', output_path)
    os.makedirs(output_path, exist_ok=True)

    # Shapefile mask
    mask = os.path.join(target_path, study_area_shapefile)

    for product in response.json()['value']:
        # Get S3 path
        s3_path = product['S3Path'].lstrip('/eodata')
        if 'L2A' in s3_path:
            print('Date', product['OriginDate'])
            print('Downloading data from', s3_path)

            # Move to "data" folder
            os.chdir(target_path)

            # Start download
            download_product(s3.Bucket('eodata'), s3_path)

            for root, dirs, files in os.walk(os.path.join(target_path, s3_path)):
                # Check if 'IMG_DATA' is among the directories
                if 'IMG_DATA' in dirs:
                    img_path = os.path.join(root, 'IMG_DATA')
                    print('Preprocessing', img_path)
                    # Crop file to study area
                    try:
                        crop(img_path, output_path, mask)
                    except Exception as e:
                        
                        print(f'An error occurred: {e}')
                    #remove_folder(img_path)
            print('---')

    # Remove download folder
    # Current directory is "data" folder
    os.chdir(target_path)
    #remove_folder(os.path.join(os.getcwd(), 'Sentinel-2'))

#https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-2' and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le 30.00) and OData.CSC.Intersects(area=geography'SRID=4326;POINT(-0.88482371152898 41.648336063076243)') and ContentDate/Start gt 2023-04-01T00:00:00.000Z and ContentDate/Start lt 2023-04-30T00:00:00.000Z&$orderby=ContentDate/Start desc

if __name__ == '__main__':
    download('../../data/oviedo_winter/rasters', '2023-12-01', '2023-12-31', '-5.84476', '43.36029', 10.00, '../shapefiles/study_area.shp'), 
    #download('../../data/valencia/rasters', '2023-11-01', '2023-11-30', '-0.375000', '39.466667', 10.00, '../shapefiles/study_area.shp')