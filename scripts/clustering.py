import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.cluster import KMeans

file_path = '/home/andres/University/uhi/data/Sentinel-2/MSI/L2A/2024/06/16/S2B_MSIL2A_20240616T105619_N0510_R094_T30TXM_20240616T123533.SAFE/GRANULE/L2A_T30TXM_A038015_20240616T105828/IMG_DATA/30TXM_20240616CompleteTile_masked_without_buildings.tif'

# Open the file
with rasterio.open(file_path) as dataset:
    '''
    matrix = np.dstack(dataset.read(1), dataset.read(2), dataset.read(3))
    rows, cols, nbands = matrix.shape
    matrix = matrix.reshape((rows*cols, nbands))
    '''
    # Read band 1
    band1 = dataset.read(1)  # Change the number to read a different band if needed
    no_data_value = dataset.nodata  # Get the no-data value for the band

    # Mask the no-data values
    band1 = np.ma.masked_equal(band1, no_data_value)

    # Plot the band using matplotlib
    plt.figure(figsize=(10, 10))
    plt.title('Band 1')
    cmap = plt.cm.plasma
    cmap.set_bad(color='none')  # Set the color for masked values to transparent
    show(band1, cmap=cmap)

    # Flatten the band to prepare for clustering
    data = band1.flatten().reshape(-1, 1)  # Reshape to a column vector

    # Perform K-means clustering
    num_clusters = 5  # One cluster is for mask
    kmeans = KMeans(n_clusters=num_clusters, random_state=0).fit(data)

    # Assign to each pixel its centroid value
    quantized_clusters = kmeans.cluster_centers_[kmeans.labels_]
    quantized_clusters = quantized_clusters.reshape(band1.shape)

    # Mask clusters where original band had no-data
    quantized_clusters = np.ma.masked_where(band1 == no_data_value, quantized_clusters)

    # Plot the clustered image
    plt.figure(figsize=(10, 10))
    plt.imshow(quantized_clusters, cmap='plasma')
    plt.colorbar(label='Cluster')
    plt.title(f'Pixel Clusters (K={num_clusters-1})')
    plt.show()

    # Export
    params = dataset.meta
    params.update(count = 1)
    '''output_band = kmeans.labels_.reshape(band1.shape)
    output_band = np.ma.masked_where(band1 == no_data_value, output_band)'''
    output_name = '/home/andres/University/uhi/data/Sentinel-2/MSI/L2A/2024/06/16/S2B_MSIL2A_20240616T105619_N0510_R094_T30TXM_20240616T123533.SAFE/GRANULE/L2A_T30TXM_A038015_20240616T105828/IMG_DATA/30TXM_20240616CompleteTile_masked_without_buildings_kmeans.tif'
    with rasterio.open(output_name, 'w', **params) as dest:
        dest.write_band(1, quantized_clusters)