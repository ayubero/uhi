from dotenv import load_dotenv
import requests
import boto3
import os

# Load environment variables
load_dotenv()

# Establish connection to S3 resource
s3 = boto3.resource(
    's3',
    endpoint_url='https://eodata.dataspace.copernicus.eu',
    aws_access_key_id=os.getenv('ACCESS_KEY'),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
    region_name='default'
) # Generated secrets

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
        dirname = os.path.join(target, os.path.dirname(file.key))
        os.makedirs(dirname, exist_ok=True)
        if not os.path.isdir(file.key):
            bucket.download_file(file.key, f'{target}{file.key}')

# Get info about products
product_url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Name%20eq%20%27S2B_MSIL2A_20240616T105619_N0510_R094_T30TXM_20240616T123533.SAFE%27'

# Fetch the JSON data from the URL
response = requests.get(product_url)

if response.status_code != 200:
    print('Failed to retrieve data')
    os.exit(1)

# Get S3 path
data = response.json()
s3_path = data['value'][0]['S3Path'].lstrip('/eodata')
print('Downloading data from', s3_path)

# Path where data will be downloaded
target_path = os.path.abspath(os.path.join(os.getcwd(), '../data')) + '/'

# Path to the product to download
download(s3.Bucket('eodata'), s3_path.lstrip('/eodata'), target_path)

# https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Name%20eq%20%27S2B_MSIL2A_20240616T105619_N0510_R094_T30TXM_20240616T123533.SAFE%27
# https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=not%20(Collection/Name%20eq%20%27SENTINEL-2%27)%20and%20ContentDate/Start%20gt%202022-05-03T00:00:00.000Z%20and%20ContentDate/Start%20lt%202022-05-03T00:10:00.000Z&$orderby=ContentDate/Start&$top=100