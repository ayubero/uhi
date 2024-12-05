import os
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn as nn
import torch
from model import TemperatureCNN
from dataset import RasterPatchDataset

# Configuration
num_epochs = 100
output_dir = 'patches'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')

# Create DataLoader
train_dataset = RasterPatchDataset(os.path.join(output_dir, 'train'))
#test_dataset = RasterPatchDataset(os.path.join(output_dir, 'test'))

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
#test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

# Initialize model, loss, and optimizer
model = TemperatureCNN().to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(num_epochs):
    model.train()
    for inputs, targets in train_loader:  # Assuming dataloader provides batches of data
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
    print(f'Epoch {epoch+1}, Loss: {loss.item()}')
