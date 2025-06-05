import os
import shutil
import re

# Set your folder paths
folder1 = '../../data/graz/patches/test'
folder2 = '../../data/zaragoza/patches/test'
destination = '../../patches/test'

# Create destination if it doesn't exist
os.makedirs(destination, exist_ok=True)

# Helper to extract the max number in existing files
def get_max_index(folder):
    max_index = -1
    for filename in os.listdir(folder):
        match = re.match(r'input_(\d+)\.npy', filename)
        if match:
            max_index = max(max_index, int(match.group(1)))
    return max_index

# Copy files from folder1
index = 0
for filename in os.listdir(folder1):
    if filename.startswith('input_') and filename.endswith('.npy'):
        number = re.search(r'(\d+)', filename).group()
        src_input = os.path.join(folder1, f'input_{number}.npy')
        src_target = os.path.join(folder1, f'target_{number}.npy')
        dst_input = os.path.join(destination, f'input_{index}.npy')
        dst_target = os.path.join(destination, f'target_{index}.npy')
        shutil.copyfile(src_input, dst_input)
        shutil.copyfile(src_target, dst_target)
        index += 1

# Copy files from folder2
for filename in os.listdir(folder2):
    if filename.startswith('input_') and filename.endswith('.npy'):
        number = re.search(r'(\d+)', filename).group()
        src_input = os.path.join(folder2, f'input_{number}.npy')
        src_target = os.path.join(folder2, f'target_{number}.npy')
        dst_input = os.path.join(destination, f'input_{index}.npy')
        dst_target = os.path.join(destination, f'target_{index}.npy')
        shutil.copyfile(src_input, dst_input)
        shutil.copyfile(src_target, dst_target)
        index += 1
