from smooth_tiled_predictions import predict_img_with_smooth_windowing
import rasterio
from rasterio.transform import from_origin
import torch
import numpy as np
from model import CNN

input_path = './data/raw/predictors_skf_imd_ndvi_small.tif'
output_path = './data/result.tif'
model_path = 'checkpoint.pth.tar'

with rasterio.open(input_path) as src:
    # Read all bands from input and target rasters
    input_img = src.read() # Shape: (3, H, W)

# Get size and origin
pixel_size_x, pixel_size_y = src.transform.a, -src.transform.e
origin_x, origin_y = src.transform.c, src.transform.f

# Smooth blending parameters
window_size = 160
nb_classes = 10

# Load the checkpoint
model = CNN()
model.load_state_dict(torch.load(model_path, weights_only=True))
model.eval()

'''predictions_smooth = predict_img_with_smooth_windowing(
    input_img,
    window_size=window_size,
    subdivisions=2, # Minimal amount of overlap for windowing. Must be an even number.
    nb_classes=nb_classes,
    pred_func=(
        lambda img_batch_subdiv: model.predict(img_batch_subdiv)
    )
)'''

patch_size = 64
stride = patch_size
_, height, width = input_img.shape
result = np.zeros((height, width))

for i in range(0, height - patch_size + 1, stride):
    for j in range(0, width - patch_size + 1, stride):
        patch = torch.from_numpy(input_img[:, i:i+patch_size, j:j+patch_size])
        patch = patch.unsqueeze(0) # Adds a batch dimension
        print(patch.shape)
        with torch.no_grad():
            prediction = model(patch)

        # Update metadata
        params = src.meta.copy()
        params.update({
            'width': patch_size,
            'height': patch_size,
            'transform': from_origin(
                origin_x + j * pixel_size_x,
                origin_y - i * pixel_size_y,
                pixel_size_x,
                -pixel_size_y
            ),
            'count': 1,  # Output has a single band
            'dtype': 'float32'
        })

        output_path = f'./data/results/patch_{i}_{j}.tif'
        with rasterio.open(output_path, 'w', **params) as dest:
            dest.write(prediction.squeeze().numpy(), 1)
        #result[i:i+patch_size, j:j+patch_size] = prediction

# Export result
'''params = src.meta
params.update(count = 1, dtype='float32')
with rasterio.open(output_path, 'w', **params) as dest:
    dest.write_band(1, result)'''