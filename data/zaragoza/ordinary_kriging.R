# Load libraries
library(gstat)
library(raster)
library(sp)
library(sf)
library(automap)
library(readr)

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")
data <- na.omit(data)  # Remove missing values

# Convert to SpatialPointsDataFrame
coordinates(data) <- ~lon + lat
proj4string(data) <- CRS("+proj=longlat +datum=WGS84")

# Define an ordinary kriging model
g_ok <- gstat(id = "temp_diff", formula = temp_diff ~ 1, data = data)

# Compute empirical variogram
vgm_ok <- variogram(g_ok)

# Fit the variogram model
vgm_model_ok <- fit.variogram(vgm_ok, vgm(psill = 1, model = "Sph", range = 5000, nugget = 0.1))

# Perform ordinary kriging interpolation
ok_result <- predict(g_ok, covariates_spdf, model = vgm_model_ok)

# Convert result to raster and save
raster_output <- raster(ok_result["temp_diff.pred"])
writeRaster(raster_output, filename = "results/kriging_output.tif", format = "GTiff", overwrite = TRUE)

