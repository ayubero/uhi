import os
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn as nn
import torch
import logging
from model import UNet, CNN
from dataset import RasterPatchDataset

def save_checkpoint(state, filename='checkpoint.pth.tar'):
    torch.save(state, filename)
    logging.info('Save checkpoint to {0:}'.format(filename))

# Configuration
num_epochs = 30
output_dir = 'data/patches'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')

# Create DataLoader
train_dataset = RasterPatchDataset(os.path.join(output_dir, 'train'))
test_dataset = RasterPatchDataset(os.path.join(output_dir, 'test'))

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

# Initialize model, loss, and optimizer
model = CNN().to(device)
#model = UNet(in_channels=3, out_channels=1).to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=1e-2)

# Training loop
for epoch in range(num_epochs):
    model.train()
    for inputs, targets in train_loader:  # Assuming dataloader provides batches of data
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        #print(inputs.shape)
        outputs = model(inputs)
        targets = targets.unsqueeze(1) # Add channel dimension
        #print(outputs.shape)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        save_checkpoint(model.state_dict())
    print(f'Epoch {epoch+1}, Loss: {loss.item()}')
