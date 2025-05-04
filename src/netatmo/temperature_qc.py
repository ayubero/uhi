import pandas as pd
import glob
import os
import seaborn as sns
import matplotlib.pyplot as plt
import re
from omegaconf import OmegaConf
from src.logger_setup import logger

# Load the YAML config file
config = OmegaConf.load('../config.yaml')

# For each hour, find the closest timestamp (either before or after)
def get_closest_hour(row, df):
    # Find all rows for the target hour and the next hour (or previous if needed)
    target_hour = row['hour']
    closest_row = df.iloc[(df['time'] - row['time']).abs().argmin()]
    return closest_row

def perform_qc(station_folder_path):
    # Remove all empty files
    for file_name in os.listdir(station_folder_path):
        file_path = os.path.join(station_folder_path, file_name)
        if os.path.isfile(file_path) and os.path.getsize(file_path) < 5: # Less than 5 bytes
            os.remove(file_path)
            print(f'Deleted: {file_path}')

    # Get CSV files with station temperatures
    station_files = sorted(glob.glob('*.csv'))
    station_files.remove('netatmo_stations.csv')
    try:
        station_files.remove('temperatures.csv')
    except:
        pass
    try:
        station_files.remove('diff.csv')
    except:
        pass

    # Preprocess all stations
    all_dataframes = []
    for csv_file in station_files:
        logger.info(f'Processing {csv_file}')
        df = pd.read_csv(csv_file, delimiter=',')
        df['time'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y-%m-%d %H:%M:%S')
        df['hour'] = df['time'].dt.hour
        
        # Apply the function to each row in the dataframe
        closest_temps = df.groupby(['date', 'hour'], group_keys=False).apply(lambda group: get_closest_hour(group.iloc[0], group))

        # Convert the result back into a dataframe
        result = closest_temps.reset_index(drop=True)[['date', 'time', 'temp']]

        # Get just the time
        result['time'] = result['time'].dt.hour
        
        # Filter by date interval
        start_date = '2023-06-01'
        end_date = '2023-08-31'
        result = result[(result['date'] >= start_date) & (result['date'] <= end_date)]
        #result['station'] = re.search(r"/([^/]+)\.csv$", csv_file).group(1)
        result['station'] = re.search(r"(.+)\.csv$", csv_file).group(1)

        all_dataframes.append(result)

    # Concatenate all dataframes into one
    temperatures = pd.concat(all_dataframes, ignore_index=True)

    # Quality control
    # Remove values below -20ºC and above 45ºC
    temperatures = temperatures[(temperatures['temp'] >= config.temperature.quality_control.min_temperature) & (temperatures['temp'] <= config.temperature.quality_control.max_temperature)]

    # Keep only rows where the temperature difference is within ±thresholdºC
    threshold = config.temperature.quality_control.temperature_variation_threshold
    # Define a function to filter each station's data
    def filter_station_data(station_df):
        station_df = station_df.copy()  # Avoid modifying the original dataframe
        station_df['temp_diff_prev'] = station_df['temp'].diff()
        station_df['temp_diff_next'] = station_df['temp'].diff(-1)
        
        # Keep only rows where the temperature difference is within ±thresholdºC
        filtered = station_df[(station_df['temp_diff_prev'].abs() <= threshold) & (station_df['temp_diff_next'].abs() <= threshold)]
        
        return filtered.drop(columns=['temp_diff_prev', 'temp_diff_next'])

    # Apply filtering per station
    temperatures = temperatures.groupby('station', group_keys=False).apply(filter_station_data)

    # Detect outliers checking the data distribution using z-score
    # Group by date and time, then compute the mean and standard deviation of temp
    grouped = temperatures.groupby(['date', 'time'])['temp'].agg(['mean', 'std'])

    # Merge the mean and std back to the original dataframe
    temperatures = temperatures.merge(grouped, on=['date', 'time'])

    # Compute the Z-score
    temperatures['z_score'] = (temperatures['temp'] - temperatures['mean']) / temperatures['std']

    # Remove rows where the z-score value is outside the range between -2.32 and 1.64
    temperatures = temperatures[(temperatures['z_score'].abs() >= config.temperature.quality_control.lower_tail) & ((temperatures['z_score'].abs() <= config.temperature.quality_control.upper_tail))]

    # Remove unnecessary columns
    temperatures = temperatures.drop(columns=['z_score', 'mean', 'std'])
    temperatures.to_csv(os.path.join(station_folder_path, config.paths.stations.temperatures), index=False)
