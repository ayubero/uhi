# Load necessary packages
library(tidyverse)
library(sp)
library(raster)
library(gstat)
library(automap)

# Load the CSV file into a dataframe
data <- read_csv("~/University/uhi/zaragoza/data.csv")

# Check correlation between temp_diff and covariates
cor(data$temp_diff, data$svf, use = "complete.obs")
cor(data$temp_diff, data$nbai, use = "complete.obs")
cor(data$temp_diff, data$gli, use = "complete.obs")

# Load raster datasets (updated variables)
gli_raster <- raster("~/University/uhi/data/rasters/Zaragoza_ETRS89_GLI.tif")
svf_raster <- raster("~/University/uhi/data/rasters/Zaragoza_ETRS89_Sky_View_Factor_scaled.tif")
nbai_raster <- raster("~/University/uhi/data/rasters/Zaragoza_ETRS89_NBAI.tif")

# Verify rasters are loaded correctly
plot(gli_raster, main = "GLI Raster")
plot(svf_raster, main = "SVF Raster")
plot(nbai_raster, main = "NBAI Raster")

# Define a formula for cokriging (temp_diff is the primary variable)
formula <- temp_diff ~ svf + nbai + gli

data$lon <- as.numeric(as.character(data$lon))
data$lat <- as.numeric(as.character(data$lat))

# Set as spatial data
coordinates(data) <- ~ lon + lat
proj4string(data) <- CRS(proj4string(gli_raster))  # Match raster CRS

# Fit variograms for each variable using automap
v_temp_diff <- autofitVariogram(temp_diff ~ 1, data)
v_svf <- autofitVariogram(svf ~ 1, data)
v_nbai <- autofitVariogram(nbai ~ 1, data)
v_gli <- autofitVariogram(gli ~ 1, data)

# Define a gstat object for cokriging
g <- gstat(NULL, id = "temp_diff", formula = temp_diff ~ 1, data = data, model = v_temp_diff$var_model)
g <- gstat(g, id = "svf", formula = svf ~ 1, data = data, model = v_svf$var_model)
g <- gstat(g, id = "nbai", formula = nbai ~ 1, data = data, model = v_nbai$var_model)
g <- gstat(g, id = "gli", formula = gli ~ 1, data = data, model = v_gli$var_model)

# Compute cross-variograms automatically
g <- gstat(g, id = "temp_diff", model = v_temp_diff$var_model, fill.all = TRUE)

# Create a prediction grid based on raster extent
grid <- spTransform(grid, CRS(proj4string(svf_raster)))

# Ensure the grid is spatial and matches the raster CRS
coordinates(grid) <- ~x + y
proj4string(grid) <- proj4string(svf_raster)

# Extract values from rasters
grid$svf <- extract(svf_raster, grid)
grid$nbai <- extract(nbai_raster, grid)
grid$gli <- extract(gli_raster, grid)

# Perform cokriging prediction
ck_result <- predict(g, grid)

# Convert results into a raster
ck_raster <- rasterFromXYZ(as.data.frame(ck_result)[, c("x", "y", "temp_diff.pred")])

# Plot the cokriging prediction
plot(ck_raster, main = "Cokriging Prediction of Temperature Difference")
