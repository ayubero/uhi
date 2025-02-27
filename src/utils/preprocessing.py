import rasterio
from rasterio.mask import mask
import fiona

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