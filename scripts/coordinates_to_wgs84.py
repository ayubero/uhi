from pyproj import Transformer

# Define transformer from EPSG:25830 to EPSG:4326
transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)

# Convert the bounding box
lon_min, lat_min = transformer.transform(668255.4696, 4605383.1353)
lon_max, lat_max = transformer.transform(683448.1474, 4620560.3155)

# Print results
print(f"Longitude, Latitude (min): ({lon_min}, {lat_min})")
print(f"Longitude, Latitude (max): ({lon_max}, {lat_max})")
