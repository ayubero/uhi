from smooth_tiled_predictions import predict_img_with_smooth_windowing
import rasterio
from rasterio.transform import from_origin
import torch
import numpy as np
from scipy.signal.windows import triang
import matplotlib.pyplot as plt
from omegaconf import OmegaConf

from model import CNN

# Load the YAML config file
config = OmegaConf.load('../config.yaml')

input_path = './data/raw/oviedo_predictors_svf_gli.tif'
output_path = './data/oviedo_cnn_result.tif'
model_path = 'checkpoint.pth.tar'

with rasterio.open(input_path) as src:
    # Read all bands from input and target rasters
    input_img = src.read() # Shape: (3, H, W)

# Get size and origin
pixel_size_x, pixel_size_y = src.transform.a, -src.transform.e
origin_x, origin_y = src.transform.c, src.transform.f

# Patch and overlap parameters
patch_size = config.cnn.patch_size
overlap = patch_size // 4 # 25% overlap
stride = patch_size - overlap
_, height, width = input_img.shape

# Initialize result and weights arrays
result = np.zeros((height, width), dtype=np.float32)
weights = np.zeros((height, width), dtype=np.float32)

def _spline_window(window_size, power=2):
    '''
    Squared spline (power=2) window function:
    Creates a 1D weighting window for blending patches.
    '''
    intersection = int(window_size / 4)
    
    # Outer part of the window
    wind_outer = (abs(2 * triang(window_size)) ** power) / 2
    wind_outer[intersection:-intersection] = 0

    # Inner part of the window
    wind_inner = 1 - (abs(2 * (triang(window_size) - 1)) ** power) / 2
    wind_inner[:intersection] = 0
    wind_inner[-intersection:] = 0

    # Combine inner and outer parts
    wind = wind_inner + wind_outer
    wind = wind / np.average(wind)  # Normalize to maintain consistent blending
    return wind

def create_weight_mask(window_size, power=2):
    '''
    Creates a 2D weight mask using the spline window function.
    '''
    # Generate 1D spline window
    spline_1d = _spline_window(window_size, power)

    # Create 2D weight mask by taking the outer product
    weight_mask = np.outer(spline_1d, spline_1d)
    return weight_mask

weight_mask = create_weight_mask(patch_size)

# Load the checkpoint
model = CNN()
model.load_state_dict(torch.load(model_path, weights_only=True))
model.eval()

for i in range(0, height - patch_size + 1, stride):
    for j in range(0, width - patch_size + 1, stride):
        patch = torch.from_numpy(input_img[:, i:i+patch_size, j:j+patch_size])
        patch = patch.unsqueeze(0) # Adds a batch dimension
        #print(patch.shape)
        with torch.no_grad():
            prediction = model(patch)

        # Convert prediction to numpy and squeeze extra dimensions
        prediction_np = prediction.squeeze().numpy()
        
        # Apply weight mask and add to result
        result[i:i + patch_size, j:j + patch_size] += prediction_np * weight_mask
        weights[i:i + patch_size, j:j + patch_size] += weight_mask

# Export result
params = src.meta
params.update(count = 1, dtype='float32')

# Normalize result by weights to handle overlap
result /= np.maximum(weights, 1e-6)  # Avoid division by zero

with rasterio.open(output_path, 'w', **params) as dest:
    dest.write(result, 1)
