from pyproj import Transformer

# Define transformer from EPSG:25830 to EPSG:4326
transformer = Transformer.from_crs('EPSG:25830', 'EPSG:4326', always_xy=True)

# Convert the bounding box
lon_min, lat_min = transformer.transform(4464931.5732000004500151, 429371.0001000000047497)
lon_max, lat_max = transformer.transform(4487726.2416000002995133, 452155.7534999999916181)

# Print results
print(f'Longitude, Latitude (min): ({lon_min}, {lat_min})')
print(f'Longitude, Latitude (max): ({lon_max}, {lat_max})')
