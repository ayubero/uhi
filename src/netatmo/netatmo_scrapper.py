import requests
import json
import pandas as pd
import time
from datetime import date, datetime, timezone, timedelta
import os

def get_stations(token, lat_ne, lon_ne, lat_sw, lon_sw, output_folder):
    url = 'https://api.netatmo.com/api/getpublicdata'
    # Coordinates in WGS84
    # Zaragoza
    '''params = {
        'lat_ne': '41.715690885740585',
        'lon_ne': '-0.7947666087344643',
        'lat_sw': '41.58243097520002',
        'lon_sw': '-0.981554438392556',
        'required_data': 'temperature',
        'filter': 'false'
    }'''
    # Madrid
    '''params = {
        'lat_ne': '40.5388896',
        'lon_ne': '-3.5650026',
        'lat_sw': '40.3320266',
        'lon_sw': '-3.8313769',
        'required_data': 'temperature',
        'filter': 'false'
    }'''
    params = {
        'lat_ne': lat_ne,
        'lon_ne': lon_ne,
        'lat_sw': lat_sw,
        'lon_sw': lon_sw,
        'required_data': 'temperature',
        'filter': 'false'
    }

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers, params=params)

    print(response.status_code)
    print(response.text)

    # Parse JSON response
    parsed_data = json.loads(response.text)

    # Extract device_id, module_id, lon and lat based on temperature in the measures
    rows = []
    for item in parsed_data['body']:
        device_id = item['_id']
        lon = item['place']['location'][0]
        lat = item['place']['location'][1]
        
        # Find the module_id where the type contains 'temperature'
        module_id = None
        for measure_key, measure_data in item['measures'].items():
            if 'temperature' in measure_data['type']:
                module_id = measure_key
                break  # Stop once we find the first match
        
        rows.append({'device_id': device_id, 'module_id': module_id, 'lon': lon, 'lat': lat})

    # Create a DataFrame
    df = pd.DataFrame(rows)

    # Make sure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Export to CSV
    output_path = os.path.join(output_folder, 'netatmo_stations.csv')
    df.to_csv(output_path, index=False)

    print('Netatmo stations saved')

def get_station_data(
        token, 
        station_folder = 'stations', 
        start_date = date(2023, 6, 1), 
        end_date = date(2023, 9, 1)
    ):
    # Make sure the output folder exists
    os.makedirs(station_folder, exist_ok=True)

    # Get the list of CSV files (without the .csv extension)
    existing_files = [f.replace('.csv', '') for f in os.listdir(station_folder) if f.endswith('.csv')]

    url = 'https://app.netatmo.net/api/getmeasure'

    headers = {
        'Host': 'app.netatmo.net',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
        'Origin': 'https://weathermap.netatmo.com',
        'Connection': 'keep-alive',
        'Referer': 'https://weathermap.netatmo.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1'
    }

    delta = timedelta(days=1)

    station_csv_path = os.path.join(station_folder, 'netatmo_stations.csv')
    stations = pd.read_csv(station_csv_path, delimiter=',')
    for index, station in stations.iterrows():
        print('Processing station', index)

        device_id = station['device_id']
        module_id = station['module_id']

        if device_id in existing_files:
            print('Station', index, 'already processed')
        else:
            current_date = start_date
            rows = []
            while current_date <= end_date:
                print('Processing:', current_date.strftime('%d/%m/%Y'))
                date_begin = time.mktime(datetime.strptime(f'{current_date} 00:00:00', '%Y-%m-%d %H:%M:%S').timetuple())
                date_end = time.mktime(datetime.strptime(f'{current_date} 23:59:00', '%Y-%m-%d %H:%M:%S').timetuple())
                current_date += delta

                payload = {
                    'date_begin': str(date_begin),
                    'date_end': str(date_end),
                    'scale': 'max',
                    'device_id': device_id,
                    'module_id': module_id,
                    'type': 'temperature'
                }

                try:
                    response = requests.post(url, headers=headers, json=payload)

                    # Parse JSON response
                    #print(response.text)
                    parsed_data = json.loads(response.text)

                    for entry in parsed_data['body']:
                        timestamp = entry['beg_time']
                        temp = entry['value'][0][0] # First temperature value
                        date_time = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                        date, t = date_time.split(' ')
                        rows.append({'date': date, 'time': t, 'temp': temp})
                except:
                    pass

            # Create DataFrame
            df = pd.DataFrame(rows)

            # Check if the DataFrame is not empty before saving
            if not df.empty:
                output_csv_path = os.path.join(station_folder, device_id + '.csv')
                df.to_csv(output_csv_path, index=False)
            else:
                print('Station', index, 'has no data for the selected period')
