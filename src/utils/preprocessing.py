import rasterio
from rasterio.enums import Resampling
from rasterio.mask import mask
import os,glob
import fiona

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
        out_image, out_transform = mask(src, shapes, nodata=nodata, crop=True)
        out_meta = src.meta
        
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

# Remove buildings from study area
def mask_buildings(gpkg_path, raster_path, output_path, nodata=-1):
    # Load the geometries from the GeoPackage file
    with fiona.open(gpkg_path) as src:
        geometries = [feature['geometry'] for feature in src]

    # Open the raster file
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, geometries, invert=True)
        out_meta = src.meta

    # Update metadata
    out_meta.update({
        'driver': 'GTiff',
        'height': out_image.shape[1],
        'width': out_image.shape[2],
        'transform': out_transform,
        'nodata': nodata
    })

    with rasterio.open(output_path, 'w', **out_meta) as dest:
        dest.write(out_image)

def mask_shapefile(shapefile, raster_path, output_path, nodata=-1):
    with fiona.open(shapefile, 'r') as shapefile:
        shapes = [feature['geometry'] for feature in shapefile]
        print('Shapefile CRS:', shapefile.crs)

    with rasterio.open(raster_path) as src:
        print('Input CRS', src.crs)
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

    with rasterio.open(output_path, 'w', **out_meta) as dest:
        dest.write(out_image)