import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

red_path = os.path.abspath(os.path.join(os.getcwd(), '../data/red_average.tif'))
with rasterio.open(red_path) as src:
    red = src.read(1)

nir_path = os.path.abspath(os.path.join(os.getcwd(), '../data/nir_average.tif'))
with rasterio.open(nir_path) as src:
    nir = src.read(1)

ndvi = (nir - red) / (nir + red)

#ndvi = np.clip(ndvi, -0.25, 1)

plt.figure(figsize=(10, 10))
plt.imshow(ndvi, cmap='RdYlGn')
plt.colorbar(label='NDVI values')
plt.title(f'NDVI')
plt.show()

params = src.meta
print(params)
params.update(count = 1, dtype='float32')

output_path = os.path.abspath(os.path.join(os.getcwd(), '../data/rasters/Madrid_ETRS89_NDVI.tif'))
with rasterio.open(output_path, 'w', **params) as dest:
        dest.write_band(1, ndvi)
