import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge

# Input TIF file paths
'''tif_files = [
    'Zaragoza_ETRS89_Sky_View_Factor.tif', 
    'Zaragoza_ETRS89_GLI.tif'
]
data_dir = '../data/rasters/'''
'''tif_files = [
    'Madrid_ETR89_SVF.tif', 
    'Madrid_ETR89_IMD_normalized.tif', 
    'Madrid_ETRS89_NDVI.tif'
]
data_dir = '../madrid/rasters/'''
tif_files = [
    'SVF.tif', 
    'GLI.tif'
]
data_dir = '../cities/oviedo/rasters/'

# Open the reference raster (high resolution)
with rasterio.open(data_dir + tif_files[0]) as ref_raster:
    ref_transform = ref_raster.transform
    ref_crs = ref_raster.crs
    ref_width = ref_raster.width
    ref_height = ref_raster.height
    ref_resolution = (ref_transform[0], -ref_transform[4])
    ref_profile = ref_raster.profile

# Resample rasters to match the reference raster
resampled_bands = []

for tif in tif_files:
    with rasterio.open(data_dir + tif) as src:
        if (
            src.width != ref_width or 
            src.height != ref_height or 
            src.transform != ref_transform
        ):
            # Resample to match the reference raster
            data = src.read(
                1, 
                out_shape=(ref_height, ref_width),
                resampling=Resampling.bilinear,  # You can use other methods, e.g., nearest
            )
            # Update transform for resampled data
            transform = ref_transform
        else:
            # No resampling needed
            data = src.read(1)
            transform = src.transform

        resampled_bands.append(data)

output_file = data_dir + 'predictors_svf_gli.tif'
ref_profile.update(count=2) # Set N bands

with rasterio.open(output_file, 'w', **ref_profile) as dst:
    for i, band in enumerate(resampled_bands, start=1):
        dst.write(band, i)

print(f'Multi-band raster saved to {output_file}')
