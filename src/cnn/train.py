import os
from torch.utils.data import DataLoader
from torch.utils.data import DataLoader, random_split
import torch.optim as optim
import torch.nn as nn
import torch
import logging
import matplotlib.pyplot as plt
from omegaconf import OmegaConf

from model import UNet, CNN
from dataset import RasterPatchDataset

# Load the YAML config file
config = OmegaConf.load('../config.yaml')

def save_checkpoint(state, filename='checkpoint.pth.tar'):
    torch.save(state, filename)
    logging.info('Save checkpoint to {0:}'.format(filename))

def train(patch_dir: str):
    # Configuration
    num_epochs = config.cnn.epochs
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    # Create Dataset and split into train & validation
    full_dataset = RasterPatchDataset(os.path.join(patch_dir, 'train'))
    train_size = int(0.8 * len(full_dataset))  # 80% for training
    val_size = len(full_dataset) - train_size  # 20% for validation
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=config.cnn.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.cnn.batch_size, shuffle=False)

    test_dataset = RasterPatchDataset(os.path.join(patch_dir, 'test'))
    test_loader = DataLoader(test_dataset, batch_size=config.cnn.batch_size, shuffle=False)

    # Initialize model, loss, and optimizer
    model = CNN().to(device)
    #model = UNet(in_channels=3, out_channels=1).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=config.cnn.learning_rate)

    # Lists to store loss values
    train_losses = []
    val_losses = []

    # Training loop
    for epoch in range(num_epochs):
        model.train()
        train_loss = 0
        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            targets = targets.unsqueeze(1) # Add channel dimension
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        train_loss /= len(train_loader) # Compute average loss
        train_losses.append(train_loss)
        
        # Validation phase
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                targets = targets.unsqueeze(1)
                loss = criterion(outputs, targets)
                val_loss += loss.item()
        
        val_loss /= len(val_loader) # Compute average loss
        val_losses.append(val_loss)

        print(f'Epoch {epoch+1}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')
        save_checkpoint(model.state_dict())

    # Plot learning curve
    # plt.plot(range(1, num_epochs + 1), train_losses, label='Train Loss')
    # plt.plot(range(1, num_epochs + 1), val_losses, label='Validation Loss')
    # plt.xlabel('Epochs')
    # plt.ylabel('MSE')
    # plt.title('Learning Curve')
    # plt.legend()
    # plt.show()

    # Evaluate on the test dataset
    model.eval()
    test_loss = 0
    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            targets = targets.unsqueeze(1) # Add channel dimension
            loss = criterion(outputs, targets)
            test_loss += loss.item()

    test_loss /= len(test_loader) # Compute average test loss

    print(f'Test Loss: {test_loss:.4f}')

if __name__ == '__main__':
    train('data/patches')