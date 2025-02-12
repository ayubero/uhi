from owslib.wcs import WebCoverageService

# Connect to the WCS service
wcs_url = "https://servicios.idee.es/wcs-inspire/mdt?service=WCS&version=2.0.1"
wcs = WebCoverageService(wcs_url)

# Get coverage details
coverage_id = "Elevacion4258_5"
coverage = wcs.contents[coverage_id]

# Define the bounding box and format
bbox = (-19.00, 27.00, 5.00, 44.00)
format = "image/tiff"

# Download the coverage
response = wcs.getCoverage(
    identifier=coverage_id,
    bbox=bbox,
    format=format,
    crs="urn:ogc:def:crs:EPSG::4258"  # ETRS89-geo
)

# Save the TIFF file
with open("output.tiff", "wb") as f:
    f.write(response.read())
