import pandas as pd
import glob
import os
import seaborn as sns
import matplotlib.pyplot as plt
import re
from omegaconf import OmegaConf
from src.logger_setup import logger

# Load the YAML config file
config = OmegaConf.load('./config.yaml')

def compute_differences(station_folder_path):
    ref_stations = config.temperature.reference_stations
    temperatures = pd.read_csv(os.path.join(station_folder_path, config.paths.stations.temperatures))

    # Merge the dataframe with itself to compute the difference with the reference station
    df_ref = (
        temperatures[temperatures['station'].isin(ref_stations)]
        .groupby(['date', 'time'])['temp']
        .mean()
        .reset_index()
        .rename(columns={'temp': 'temp_ref'})
    )
    df_merged = pd.merge(temperatures, df_ref, on=['date', 'time'])
    
    # Compute the daily temperature difference from reference station for each station
    df_merged['temp_diff'] = df_merged['temp'] - df_merged['temp_ref']

    df_filtered = df_merged

    # Remove rows where 'station' is in the list
    #df_filtered = df_filtered[~df_filtered['station'].isin(ref_stations)]

    # Compute temperature difference mean for each station
    df_filtered = df_filtered.groupby('station')['temp_diff'].mean().reset_index()
    
    # Remove rows with stations in the list
    df_filtered = df_filtered[~df_filtered['station'].isin(config.temperature.stations_to_remove)]
    df_filtered

    # Add coordinates
    stations = pd.read_csv(os.path.join(station_folder_path, config.paths.stations.stations))
    stations = stations.drop(columns=['module_id'])
    data = pd.merge(df_filtered, stations, left_on='station', right_on='device_id')
    data = data.drop(columns=['device_id'])
    data.to_csv(os.path.join(station_folder_path, config.paths.stations.differences), index=False)
    