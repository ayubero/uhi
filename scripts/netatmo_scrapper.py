import requests
import numpy

import requests

url = "https://api.netatmo.com/api/getpublicdata"
params = {
    "lat_ne": "41.6422",
    "lon_ne": "-0.8423",
    "lat_sw": "41.6334",
    "lon_sw": "-0.8540",
    "required_data": "temperature",
    "filter": "false"
}

headers = {
    "Accept": "application/json",
    "Authorization": "Bearer 679b955ca250de0e040eb492|04f60a16c049ce6536b4b815624fb78b"
}

response = requests.get(url, headers=headers, params=params)

print(response.status_code)
print(response.text)


'''url = "https://app.netatmo.net/api/getmeasure"

headers = {
    "Host": "app.netatmo.net",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Authorization": "Bearer 679b955ca250de0e040eb492|04f60a16c049ce6536b4b815624fb78b",
    "Content-Type": "application/json;charset=utf-8",
    "Origin": "https://weathermap.netatmo.com",
    "Connection": "keep-alive",
    "Referer": "https://weathermap.netatmo.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1"
}

payload = {
    "date_begin": "1738188000",
    "date_end": "1738249944",
    "scale": "max",
    "device_id": "70:ee:50:17:e6:22",
    "module_id": "70:ee:50:17:e6:22",
    "type": "Pressure"
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.text)'''
