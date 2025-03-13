import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
import os

def resample(input_path: str, output_resolution: float):
    '''
    Opens a .tif file, rescales it using bilinear interpolation to the given resolution,
    and saves the resulting raster with a suffix _scaled.tif.

    :param input_path: Path to the input .tif file
    :param output_resolution: Desired resolution (pixel size in units of the raster CRS)
    '''
    with rasterio.open(input_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, src.crs, src.width, src.height, 
            src.bounds.left, src.bounds.bottom, 
            src.bounds.right, src.bounds.top, 
            resolution=output_resolution
        )
        
        profile = src.profile.copy()
        profile.update({
            'transform': transform,
            'width': width,
            'height': height,
            'compress': 'lzw'
        })
        
        output_path = os.path.splitext(input_path)[0] + '_scaled.tif'
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=src.crs,
                    resampling=Resampling.bilinear
                )
    
    print(f'Rescaled raster saved to {output_path}')
    return output_path
