import os
import rasterio
import numpy as np
from sklearn.model_selection import train_test_split
from omegaconf import OmegaConf

# Load the YAML config file
config = OmegaConf.load('../config.yaml')

def extract_patches(input_tif, target_tif, patch_size, output_dir, stride=None):
    if stride is None:
        stride = patch_size # Non-overlapping patches by default

    with rasterio.open(input_tif) as src_input, rasterio.open(target_tif) as src_target:
        # Read all bands from input and target rasters
        input_data = src_input.read() # Shape: (N, H, W)
        target_data = src_target.read(1) # Shape: (H, W) - single band
        
        height, width = target_data.shape
        patches = []

        print('Predictors shape:', input_data.shape)
        print('Target shape:', target_data.shape)
        
        # Extract patches using a sliding window
        for i in range(0, height - patch_size + 1, stride):
            for j in range(0, width - patch_size + 1, stride):
                input_patch = input_data[:, i:i+patch_size, j:j+patch_size]
                target_patch = target_data[i:i+patch_size, j:j+patch_size]
                patches.append((input_patch, target_patch))
        
        # Split into train/test
        train_patches, test_patches = train_test_split(patches, test_size=0.2, random_state=42)
        
        # Save patches to folders
        def save_patches(patches, folder):
            os.makedirs(folder, exist_ok=True)
            for idx, (input_patch, target_patch) in enumerate(patches):
                np.save(os.path.join(folder, f'input_{idx}.npy'), input_patch)
                np.save(os.path.join(folder, f'target_{idx}.npy'), target_patch)
        
        save_patches(train_patches, os.path.join(output_dir, 'train'))
        save_patches(test_patches, os.path.join(output_dir, 'test'))
        
        print(f'Saved {len(train_patches)} training patches and {len(test_patches)} testing patches.')

if __name__ == '__main__':
    # Parameters
    input_tif = './data/raw/predictors_svf_gli.tif' # Predictor variables
    target_tif = './data/raw/interpolation_svf_gli.tif' # Target variable
    patch_size = config.cnn.patch_size
    output_dir = 'data/patches'

    # Extract patches and save them
    extract_patches(input_tif, target_tif, patch_size, output_dir)