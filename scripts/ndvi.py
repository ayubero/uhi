import rasterio
import numpy as np
import matplotlib.pyplot as plt

input_path = '../data/sentinel/20230602T105629_StudyArea.tif'
with rasterio.open(input_path) as src:
    no_data_value = src.nodata
    green = src.read(3)
    red = src.read(4)
    nir = src.read(8)
    swir1 = src.read(11)

ndvi = (nir - red) / (nir + red)

ndvi = np.clip(ndvi, -0.25, 1)

plt.figure(figsize=(10, 10))
plt.imshow(ndvi, cmap='RdYlGn')
plt.colorbar(label='NDVI values')
plt.title(f'NDVI')
plt.show()

'''ndbi = (swir1 - nir) / (swir1 + nir)

plt.figure(figsize=(10, 10))
plt.imshow(ndbi, cmap='RdYlGn')
plt.colorbar(label='NDBI values')
plt.title(f'NDBI')
plt.show()'''

ndwi = (green - nir) / (green + nir)

plt.figure(figsize=(10, 10))
plt.imshow(ndwi, cmap='Blues')
plt.colorbar(label='NDWI values')
plt.title(f'NDWI')
plt.show()

plus = ndvi + ndwi

plt.figure(figsize=(10, 10))
plt.imshow(plus, cmap='Blues')
plt.colorbar(label='NDVI + NDWI values')
plt.title(f'NDVI + NDWI')
plt.show()