import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples

N_CLUSTERS = 4 # One cluster is for mask

file_path = '/home/andres/University/uhi/data/sentinel/20230403T105629_StudyArea.tif'

# Open the file
with rasterio.open(file_path) as dataset:
    '''
    matrix = np.dstack(dataset.read(1), dataset.read(2), dataset.read(3))
    rows, cols, nbands = matrix.shape
    matrix = matrix.reshape((rows*cols, nbands))
    '''
    # Read band
    band = dataset.read(8) # Change the number to read a different band if needed
    no_data_value = dataset.nodata  # Get the no-data value for the band

    # Mask the no-data values
    band = np.ma.masked_equal(band, no_data_value)

    # Plot the band using matplotlib
    plt.figure(figsize=(10, 10))
    plt.title('Band 8 - NIR')
    cmap = plt.cm.plasma
    cmap.set_bad(color='none')  # Set the color for masked values to transparent
    show(band, cmap=cmap)

    # Flatten the band to prepare for clustering
    data = band.flatten().reshape(-1, 1)  # Reshape to a column vector

    # Perform K-means clustering
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(data)

    # Assign to each pixel its centroid value
    quantized_clusters = kmeans.cluster_centers_[kmeans.labels_]
    quantized_clusters = quantized_clusters.reshape(band.shape)

    # Mask clusters where original band had no-data
    quantized_clusters = np.ma.masked_where(band == no_data_value, quantized_clusters)

    # Plot the clustered image
    plt.figure(figsize=(10, 10))
    plt.imshow(quantized_clusters, cmap='plasma')
    plt.colorbar(label='Cluster')
    plt.title(f'Pixel Clusters (K={N_CLUSTERS})')
    plt.show()

    # Sampling a subset of the data for silhouette score calculation
    sample_size = 10000  # Set the sample size
    sample_indices = np.random.choice(np.arange(data.shape[0]), size=sample_size, replace=False)
    data_sample = data[sample_indices]
    labels_sample = kmeans.labels_[sample_indices]

    # Calculate the silhouette score on the sample
    silhouette_avg = silhouette_score(data_sample, labels_sample)
    print(f'Silhouette Score (sample of {sample_size}): {silhouette_avg:.2f}')

    # Calculate silhouette scores for each sample in the subset
    sample_silhouette_values = silhouette_samples(data_sample, labels_sample)

    # Plotting silhouette scores for each cluster
    fig, ax1 = plt.subplots(1, 1)
    fig.set_size_inches(8, 6)

    # Initialize the y-axis position
    y_lower = 10
    for i in range(N_CLUSTERS):
        ith_cluster_silhouette_values = sample_silhouette_values[labels_sample == i]
        ith_cluster_silhouette_values.sort()
        size_cluster_i = ith_cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster_i

        color = plt.cm.nipy_spectral(float(i) / N_CLUSTERS)
        ax1.fill_betweenx(np.arange(y_lower, y_upper),
                        0, ith_cluster_silhouette_values,
                        facecolor=color, edgecolor=color, alpha=0.7)
        ax1.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))

        y_lower = y_upper + 10  # 10 for the 0 samples gap

    ax1.set_title("The silhouette plot for the various clusters.")
    ax1.set_xlabel("The silhouette coefficient values")
    ax1.set_ylabel("Cluster label")

    ax1.axvline(x=silhouette_avg, color="red", linestyle="--")
    ax1.set_yticks([])  # Clear the yaxis labels / ticks
    ax1.set_xticks(np.arange(-0.1, 1.1, 0.2))

    plt.show()

    # Export
    params = dataset.meta
    params.update(count = 1)
    '''output_band = kmeans.labels_.reshape(band.shape)
    output_band = np.ma.masked_where(band == no_data_value, output_band)
    output_name = '/home/andres/University/uhi/data/Sentinel-2/MSI/L2A/2024/06/16/S2B_MSIL2A_20240616T105619_N0510_R094_T30TXM_20240616T123533.SAFE/GRANULE/L2A_T30TXM_A038015_20240616T105828/IMG_DATA/30TXM_20240616CompleteTile_masked_without_buildings_kmeans.tif'
    with rasterio.open(output_name, 'w', **params) as dest:
        dest.write_band(1, quantized_clusters)'''