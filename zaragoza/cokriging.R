# Load necessary packages
library(tidyverse)
library(sp)
library(raster)
library(gstat)
library(automap)

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")

# Convert longitude and latitude columns to numeric
data$lon <- as.numeric(data$lon)
data$lat <- as.numeric(data$lat)

# Remove NA values from data
data <- na.omit(data)

# Set coordinates for spatial data
coordinates(data) <- ~ lon + lat

# Define the CRS for the data (WGS84)
proj4string(data) <- CRS("+proj=longlat +datum=WGS84 +no_defs")

# Transform the data CRS to match the rasters (ETRS89)
data <- spTransform(data, CRS(proj4string(gli_raster)))

# Remove outliers (values above the 95th percentile)
data <- data[data$svf < quantile(data$svf, 0.95), ]
data <- data[data$nbai < quantile(data$nbai, 0.95), ]
data <- data[data$gli < quantile(data$gli, 0.95), ]

# Fit variograms for each variable using automap
v_temp_diff <- autofitVariogram(temp_diff ~ 1, data)
v_svf <- autofitVariogram(svf ~ 1, data)
v_nbai <- autofitVariogram(nbai ~ 1, data)
v_gli <- autofitVariogram(gli ~ 1, data)

# Define a gstat object
#g <- gstat(NULL, id = "temp_diff", formula = temp_diff ~ 1, data = data, model = v_temp_diff$var_model)
#g <- gstat(g, id = "svf", formula = svf ~ 1, data = data, model = v_svf$var_model)
#g <- gstat(g, id = "nbai", formula = nbai ~ 1, data = data, model = v_nbai$var_model)
#g <- gstat(g, id = "gli", formula = gli ~ 1, data = data, model = v_gli$var_model)

g <- gstat(NULL, id = "temp_diff", formula = temp_diff ~ 1, data = data, model = v_temp_diff$var_model)
g <- gstat(g, id = "svf", formula = svf ~ 1, data = data, model = v_svf$var_model)
g <- fit.lmc(variogram(g), g, model = vgm(psill = 1, model = "Sph", range = 1000, nugget = 0.5))
# Create a prediction grid based on raster extent
grids <- rasterToPoints(svf_raster, spatial = TRUE)

# Ensure grids are in the same CRS as the data (ETRS89)
grids <- spTransform(grids, CRS(proj4string(gli_raster)))

# Extract raster values
grids$svf <- raster::extract(svf_raster, grids)
grids$nbai <- raster::extract(nbai_raster, grids)
grids$gli <- raster::extract(gli_raster, grids)

# Remove NA values in the grid
grids <- grids[!is.na(grids$svf) & !is.na(grids$nbai) & !is.na(grids$gli), ]

# Perform cokriging prediction
ck_result <- predict(g, grids)

# Convert results into a raster
ck_raster <- rasterFromXYZ(as.data.frame(ck_result)[, c("x", "y", "temp_diff.pred")])

# Plot the cokriging prediction
plot(ck_raster, main = "Cokriging Prediction of Temperature Difference")

