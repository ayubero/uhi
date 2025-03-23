from owslib.wcs import WebCoverageService
import rasterio
from rasterio.plot import show

# Define the WCS URL
wcs_url = 'https://servicios.idee.es/wcs-inspire/mdt?request=GetCoverage&bbox=219815.8558928584,4127174.1479494297,250214.58515687028,4157574.328919708&service=WCS&version=1.0.0&coverage=Elevacion25830_5&interpolationMethod=bilinear&crs=EPSG:25830&format=ArcGrid&width=6080&height=6080'

# Connect to the WCS service
wcs = WebCoverageService(wcs_url, version='2.0.1')

# List available coverages
print(list(wcs.contents))  

coverage_id = '15' #'Elevacion25830_5'

bbox = (
    -6.158884001205189,  # minx (lon_sw)
    37.24901003514264,   # miny (lat_sw)
    -5.826827983975654,  # maxx (lon_ne)
    37.53134457442109    # maxy (lat_ne)
)

response = wcs.getCoverage(
    identifier=coverage_id,
    bbox=bbox,
    crs="EPSG:4326",
    format="image/tiff",
    width=500,  # Adjust for resolution
    height=500
)

# Save the response as a file
output_file = "mdt_spain.tif"
with open(output_file, 'wb') as file:
    file.write(response.read())