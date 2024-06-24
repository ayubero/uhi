import rasterio
from rasterio.enums import Resampling
import os,glob
import fiona

# Prompt the user to enter the path to satellite images
file_path = input('Enter satellite images path: ')
os.chdir(file_path)
os.getcwd()

# List files according to Sentinel2 bands
listB10m = glob.glob('R10m/*.jp2')
listB20m = glob.glob('R20m/*.jp2')
listB60m = glob.glob('R60m/*.jp2')

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
  
# Read and resample bands 10m
B2, transform = read_resample(listB10m[1], 1.0)
B3, _ = read_resample(listB10m[2], 1.0)
B4, _ = read_resample(listB10m[3], 1.0)
B8, _ = read_resample(listB10m[4], 1.0)
B5, _ = read_resample(listB20m[4], 2.0)
B6, _ = read_resample(listB20m[5], 2.0)
B7, _ = read_resample(listB20m[6], 2.0)
B11, _ = read_resample(listB20m[7], 2.0)
B12, _ = read_resample(listB20m[8], 2.0)
B8A, _ = read_resample(listB20m[9], 2.0) # Band 8A to 20m resolution 
B1, _ = read_resample(listB60m[1], 6.0)
B9, _ = read_resample(listB60m[8], 6.0)

# Compose bands
S2_RS = [B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12]

# Configure params
param = rasterio.open(listB10m[1]).meta # Se toma la información de la primera banda
param.update(driver='GTiff',
             count=len(S2_RS), # Band number
             dtype='int16', # Datatype
             transform=transform, # Image transformation
             width=B2.shape[1], # Image width
             height=B2.shape[0]) # Image height

# Output name
name_S2 = os.path.join(os.getcwd(), listB10m[1][6:20] + 'CompleteTile.tif')

# Export compound image
with rasterio.open(name_S2, 'w', **param) as SENTINEL2:
    for num, banda in enumerate(S2_RS, start=1):
        SENTINEL2.write(banda, num)


print('TIFF file created')

# Use shapefile to mask image
os.chdir(file_path)
os.getcwd()
list_rs = glob.glob('*CompleteTile.tif')

shapefile = input('Enter shapefile to mask image: ')

nodata = -1

with fiona.open(shapefile, 'r') as shapefile:
    shapes = [feature['geometry'] for feature in shapefile]
    shapes_crs = shapefile.crs

with rasterio.open(list_rs[0]) as src:
    out_image, out_transform = rasterio.mask.mask(src, shapes, nodata=nodata, crop=True)
    out_meta = src.meta
    
out_image[out_image == src.nodata] = nodata

out_meta.update({
    'driver': 'GTiff',
    'height': out_image.shape[1],
    'width': out_image.shape[2],
    'transform': out_transform,
    'nodata': nodata
})

output_path = list_rs[0].replace('.tif', '_masked.tif')
with rasterio.open(output_path, 'w', **out_meta) as dest:
    dest.write(out_image)

print('Finished cutting')