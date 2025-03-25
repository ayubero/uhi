#from utils.preprocessing import crop
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

s3_path = '/eodata/Sentinel-3/SLSTR/SL_2_LST___/2023/08/21/S3B_SL_2_LST____20230821T104131_20230821T104431_20230821T124950_0179_083_108_2160_PS2_O_NR_004.SEN3'.lstrip('/eodata')

# Establish connection to S3 resource
s3 = boto3.resource(
    's3',
    endpoint_url='https://eodata.dataspace.copernicus.eu',
    aws_access_key_id=os.getenv('ACCESS_KEY'),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
    region_name='default'
) # Generated secrets

download(s3.Bucket('eodata'), s3_path)