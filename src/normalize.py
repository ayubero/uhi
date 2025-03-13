import rasterio
import numpy as np

def normalize(input_path):
    output_path = input_path.replace('.tif', '_normalized.tif')
    
    with rasterio.open(input_path) as src:
        raster = src.read(1)
        
        # Ignore nodata values (if they exist)
        nodata = src.nodata
        mask = raster != nodata if nodata is not None else np.ones_like(raster, dtype=bool)
        
        # Calculate min and max (ignoring nodata values)
        valid_data = raster[mask]
        min_val = valid_data.min()
        max_val = valid_data.max()
        
        # Normalize raster values
        normalized_raster = np.zeros_like(raster, dtype=np.float32)
        normalized_raster[mask] = (valid_data - min_val) / (max_val - min_val)
        
        # Prepare output metadata
        meta = src.meta.copy()
        meta.update(dtype='float32', compress='lzw')
        
    # Write the normalized raster to a new file
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(normalized_raster, 1)
    
    print(f'Normalized raster saved to {output_path}')