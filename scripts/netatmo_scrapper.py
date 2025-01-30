import requests
import json
import pandas as pd
import time
from datetime import date, datetime, timezone, timedelta

'''url = 'https://api.netatmo.com/api/getpublicdata'
params = {
    'lat_ne': '41.715690885740585',
    'lon_ne': '-0.7947666087344643',
    'lat_sw': '41.58243097520002',
    'lon_sw': '-0.981554438392556',
    'required_data': 'temperature',
    'filter': 'false'
}

headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer 679b955ca250de0e040eb492|58c127707faa13c689be8f9bf2b862be'
}

response = requests.get(url, headers=headers, params=params)

print(response.status_code)
#print(response.text)

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

# Export to CSV
df.to_csv('netatmo_stations.csv', index=False)

print('Netatmo stations saved')'''


url = 'https://app.netatmo.net/api/getmeasure'

headers = {
    'Host': 'app.netatmo.net',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Authorization': 'Bearer 679b955ca250de0e040eb492|822135c9633467919aae35a53d315dab',
    'Content-Type': 'application/json;charset=utf-8',
    'Origin': 'https://weathermap.netatmo.com',
    'Connection': 'keep-alive',
    'Referer': 'https://weathermap.netatmo.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-GPC': '1'
}

start_date = date(2023, 6, 1)
end_date = date(2023, 6, 7)
delta = timedelta(days=1)

device_id = '70:ee:50:7a:8d:66'
module_id = '02:00:00:7a:82:20'

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
    except:
        pass

    #print(response.status_code)
    #print(response.text)

    # Parse JSON response
    parsed_data = json.loads(response.text)

    for entry in parsed_data['body']:
        timestamp = entry['beg_time']
        temp = entry['value'][0][0]  # First temperature value
        date_time = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        date, t = date_time.split(' ')
        rows.append({'date': date, 'time': t, 'temp': temp})

# Create DataFrame
df = pd.DataFrame(rows)

# Export to CSV
df.to_csv(device_id + '.csv', index=False)