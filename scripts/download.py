from utils.preprocessing import crop
from dotenv import load_dotenv
import requests
import shutil
import boto3
import os

# Load environment variables
load_dotenv()

def download(bucket, product: str, target: str = '') -> None:
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
start_date = '2023-08-01'
end_date = '2023-08-31'
latitude = '41.648336063076243'
longitude = '-0.88482371152898'
clouds = '30.00' # Cloud percentage
product_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name%20eq%20%27SENTINEL-2%27%20and%20Attributes/OData.CSC.DoubleAttribute/any(att:att/Name%20eq%20%27cloudCover%27%20and%20att/OData.CSC.DoubleAttribute/Value%20le%20' + clouds + ')%20and%20OData.CSC.Intersects(area=geography%27SRID=4326;POINT(' + longitude + '%20' + latitude + ')%27)%20and%20ContentDate/Start%20gt%20' + start_date + 'T00:00:00.000Z%20and%20ContentDate/Start%20lt%20' + end_date + 'T00:00:00.000Z&$orderby=ContentDate/Start%20desc'

# Sentinel-3
#product_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name%20eq%20%27SENTINEL-3%27%20and%20Attributes/OData.CSC.DoubleAttribute/any(att:att/Name%20eq%20%27cloudCover%27%20and%20att/OData.CSC.DoubleAttribute/Value%20le%2030.00)%20and%20OData.CSC.Intersects(area=geography%27SRID=4326;POINT(-0.88482371152898%2041.648336063076243)%27)%20and%20ContentDate/Start%20gt%202023-08-01T00:00:00.000Z%20and%20ContentDate/Start%20lt%202023-08-31T00:00:00.000Z&$orderby=ContentDate/Start%20desc'

# Fetch the JSON data from the URL
response = requests.get(product_url)

if response.status_code != 200:
    print('Failed to retrieve data')
    os.exit(1)

data = response.json()

# Path where data will be downloaded
target_path = os.path.abspath(os.path.join(os.getcwd(), '../data'))

# Output path after preprocessing
output_path = os.path.join(target_path, 'sentinel')
print('Output path', output_path)
os.makedirs(output_path, exist_ok=True)

# Shapefile mask
mask = os.path.join(target_path, 'shapefiles/mask.shp')

for product in response.json()['value']:
    # Get S3 path
    s3_path = product['S3Path'].lstrip('/eodata')
    if 'L2A' in s3_path:
        print('Date', product['OriginDate'])
        print('Downloading data from', s3_path)

        # Move to "data" folder
        os.chdir(target_path)

        # Start download
        download(s3.Bucket('eodata'), s3_path)

        for root, dirs, files in os.walk(os.path.join(target_path, s3_path)):
            # Check if 'IMG_DATA' is among the directories
            if 'IMG_DATA' in dirs:
                img_path = os.path.join(root, 'IMG_DATA')
                print('Preprocessing', img_path)
                # Crop file to study area
                crop(img_path, output_path, mask)
                remove_folder(img_path)
        print('---')

# Remove download folder
# Current directory is "data" folder
os.chdir(target_path)
remove_folder(os.path.join(os.getcwd(), 'Sentinel-2'))

#https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-2' and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le 30.00) and OData.CSC.Intersects(area=geography'SRID=4326;POINT(-0.88482371152898 41.648336063076243)') and ContentDate/Start gt 2023-04-01T00:00:00.000Z and ContentDate/Start lt 2023-04-30T00:00:00.000Z&$orderby=ContentDate/Start desc
