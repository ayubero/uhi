import torch
import torch.nn as nn
import torch.nn.functional as F
from omegaconf import OmegaConf

# Load the YAML config file
config = OmegaConf.load('../config.yaml')

class UNet(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(UNet, self).__init__()
        
        # Encoder
        self.enc1 = self.conv_block(in_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)
        
        # Bottleneck
        self.bottleneck = self.conv_block(512, 1024)
        
        # Decoder
        '''self.dec4 = self.upconv_block(1024 + 512, 512) # Concatenated bottleneck and e4
        self.dec3 = self.upconv_block(512 + 256, 256) # Concatenated decoder output and e3
        self.dec2 = self.upconv_block(256 + 128, 128) # Concatenated decoder output and e2
        self.dec1 = self.upconv_block(128 + 64, 64)'''
        #self.dec4 = self.upconv_block(1536, 512) # (1024 from bottleneck, 512 from e4)
        self.dec4 = nn.Sequential(
            nn.Conv2d(1536, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
        #self.dec3 = self.upconv_block(768, 256)
        self.dec3 = nn.Sequential(
            nn.Conv2d(768, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
        #self.dec2 = self.upconv_block(384, 128)
        self.dec2 = nn.Sequential(
            nn.Conv2d(384, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
        #self.dec1 = self.upconv_block(128 + 64, 64)
        self.dec1 = nn.Sequential(
            nn.Conv2d(192, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
                
        # Final Output
        self.final_conv = nn.Conv2d(64, out_channels, kernel_size=1)
    
    def conv_block(self, in_channels, out_channels):
        '''Convolutional block: Conv2d -> ReLU -> Conv2d -> ReLU'''
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
    
    def upconv_block(self, in_channels, out_channels):
        '''Upconvolutional block: Upsample -> Conv2d'''
        return nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2),
            self.conv_block(out_channels + out_channels // 2, out_channels)  # Match concatenated channels
        )

    
    def forward(self, x):
        # Encoder
        e1 = self.enc1(x)
        e2 = self.enc2(F.max_pool2d(e1, 2))
        e3 = self.enc3(F.max_pool2d(e2, 2))
        e4 = self.enc4(F.max_pool2d(e3, 2))
        
        # Bottleneck
        b = self.bottleneck(F.max_pool2d(e4, 2))
        
        # Decoder with skip connections
        d4 = self.dec4(torch.cat([F.interpolate(b, scale_factor=2, mode='bilinear', align_corners=True), e4], dim=1))
        d3 = self.dec3(torch.cat([F.interpolate(d4, scale_factor=2, mode='bilinear', align_corners=True), e3], dim=1))
        d2 = self.dec2(torch.cat([F.interpolate(d3, scale_factor=2, mode='bilinear', align_corners=True), e2], dim=1))
        d1 = self.dec1(torch.cat([F.interpolate(d2, scale_factor=2, mode='bilinear', align_corners=True), e1], dim=1))
        
        # Final output
        return self.final_conv(d1)

class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(config.cnn.input_channels, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(32, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 1, kernel_size=3, stride=1, padding=1)
        )
    
    def forward(self, x):
        x = self.encoder(x)
        x = nn.functional.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)
        x = self.decoder(x)
        return x
