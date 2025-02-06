import os, glob
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

N_COMPONENTS = 3

# Go to directory with study area rasters
raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
os.chdir(raster_path)

# List all .tif files
list = glob.glob('*.tif')

# Read and stack all bands
dataset = []
no_data_value = -1
band: np.ndarray
for raster_name in list:
    with rasterio.open(raster_name) as src:
        no_data_value = src.nodata
        band = src.read(8)
        dataset.append(src.read(8))


dataset = np.stack(dataset, axis=0)

# Reshape dataset so that each raster becomes one row in the matrix
n_samples, height, width = dataset.shape
reshaped_dataset = dataset.reshape(n_samples, height * width).T

# Apply PCA
pca = PCA(n_components=N_COMPONENTS)
pca_result = pca.fit_transform(reshaped_dataset)

# Remodelar de nuevo al formato de imagen
pca_images = pca_result.T.reshape(N_COMPONENTS, height, width)

for index, image in enumerate(pca_images):
    # Mask clusters where original band had no-data
    image = np.ma.masked_where(band == no_data_value, image)
    # Plot the result
    plt.figure(figsize=(10, 10))
    plt.imshow(image, cmap='plasma')
    plt.title(f'PCA - Component {index} explains {round(pca.explained_variance_ratio_[index]*100, 2)}% of the variance')
    plt.show()