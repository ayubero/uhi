import numpy as np
import rasterio
from rasterio.enums import Resampling
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Function to read TIFF file and resample to match another TIFF file's dimensions
def read_and_resample_tiff(file_path, reference_tiff):
    with rasterio.open(reference_tiff) as ref:
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_shape = (ref.height, ref.width)

    with rasterio.open(file_path) as src:
        data = src.read(
            1, 
            out_shape=ref_shape, 
            resampling=Resampling.nearest
        )
        nodata_value = src.nodata
    return data, nodata_value

actual_file = '/home/andres/University/uhi_madrid/data/EsAytMadridOt2022ICU.tif'
predicted_file = '/home/andres/University/uhi_madrid/data/FullYear_StudyArea_Kmeans.tif'

# Read and resample predicted file to match the actual file's dimensions
actual_data, actual_nodata = read_and_resample_tiff(actual_file, actual_file)  # Use actual file as reference
predicted_data, predicted_nodata = read_and_resample_tiff(predicted_file, actual_file)

# Flatten arrays and remove no data values
actual_flat = actual_data.flatten()
predicted_flat = predicted_data.flatten()

# Filter out no data values
mask = (actual_flat != actual_nodata) & (predicted_flat != predicted_nodata)
actual_filtered = actual_flat[mask]
predicted_filtered = predicted_flat[mask]

# Compute the confusion matrix
cm = confusion_matrix(actual_filtered, predicted_filtered, labels=[1, 2, 3, 4, 5, 6, 7, 8])

# Plot confusion matrix
plt.figure(figsize=(10, 7))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=range(1, 9), yticklabels=range(1, 9))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()