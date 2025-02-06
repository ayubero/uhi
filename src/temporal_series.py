import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import rasterio
import glob
import os

# Import temperatures
temperatures_path = os.path.abspath(os.path.join(os.getcwd(), '../data')) + '/temperatures.csv'
df = pd.read_csv(temperatures_path)

# Go to directory with study area rasters
raster_path = os.path.abspath(os.path.join(os.getcwd(), '../data/sentinel'))
os.chdir(raster_path)

# Multitemporal series
series = []
dates = []

# List and iterate over all .tif files
list = sorted(glob.glob('*.tif'))
for raster_name in list:
    year = raster_name[0:4]
    month = raster_name[4:6]
    day = raster_name[6:8]
    with rasterio.open(raster_name) as src:
        # Read band 8 (NIR)
        band = src.read(8) 
        no_data_value = src.nodata  # Get the no-data value for the band
        # Mask the no-data values
        band = np.ma.masked_equal(band, no_data_value)
        # Append band
        series.append(band)
        # Add date
        dates.append(year + '-' + month + '-' + day)

# Filter temperatures to the ones of the satellite images
df = df[df['date'].isin(dates)]

# Draw plot
'''while True:
    # Ask for coordinates
    height, width = series[0].shape
    selected_height = -1
    selected_width = -1
    while selected_height >= 0 and selected_height < height:
        selected_height = input('Select height value between 0 and', height-1)
    while selected_width >= 0 and selected_height < width:
        selected_width = input('Select height value between 0 and', width-1)'''

selected_height = 725
selected_width = 410

plt.figure(figsize=(10, 10))
plt.imshow(series[0], cmap='plasma')
plt.scatter(selected_width, selected_height, color='lime', marker='o', label='Point of Interest')
plt.show()

# Get values
values = []
for raster in series:
    values.append(raster[selected_width][selected_height])

# Get temperatures
temperatures = df['avgt'].tolist()

# Create a figure and axis
fig, ax1 = plt.subplots()

# Plot temperatures on primary y-axis
ax1.plot(dates, temperatures, marker='o', linestyle='-', color='b', label='Temperatures')
ax1.set_xlabel('Date')
plt.xticks(rotation=90)
ax1.set_ylabel('Temperature (°C)', color='b')
ax1.tick_params(axis='y', labelcolor='b')

# Create a secondary y-axis for NIR values
ax2 = ax1.twinx()
scaled_values = [x / 1000 for x in values]  # Scale other_data for better comparison
ax2.plot(dates, scaled_values, marker='s', linestyle='-', color='r', label='NIR values (scaled)')
ax2.set_ylabel('NIR values (thousands)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# Set title and legend
ax1.set_title('Temperature and NIR values')
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

# Ensure tight layout
plt.tight_layout()

# Show plot
plt.show()