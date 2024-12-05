import os
import numpy as np
import torch
from torch.utils.data import Dataset

class RasterPatchDataset(Dataset):
    def __init__(self, folder):
        self.input_files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.startswith('input')])
        self.target_files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.startswith('target')])

    def __len__(self):
        return len(self.input_files)

    def __getitem__(self, idx):
        input_patch = np.load(self.input_files[idx])  # Shape: (3, patch_size, patch_size)
        target_patch = np.load(self.target_files[idx])  # Shape: (patch_size, patch_size)
        return torch.tensor(input_patch, dtype=torch.float32), torch.tensor(target_patch, dtype=torch.float32)