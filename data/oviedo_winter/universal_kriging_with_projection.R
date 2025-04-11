# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(automap)
library(ggpubr)
library(spdep)
library(scales)
library(leaflet)

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")

# Check the first few rows of the dataset
head(data)

# Remove rows with missing values
data <- na.omit(data)

# Check correlation
cor(data$temp_diff, data$svf, use = "complete.obs")
cor(data$temp_diff, data$gli, use = "complete.obs")

points <- data.frame(
  lon = data$lon,
  lat = data$lat,
  svf = data$svf,
  gli = data$gli,
  temp_diff = data$temp_diff
)

# Convert the data frame to a spatial data frame
coordinates(points) <- ~lon + lat

# Ensure the data is in a SpatialPointsDataFrame (this will automatically include the coordinates as spatial information)
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Create interactive map
#leaflet(points) %>%
#  addTiles() %>%  # Add OpenStreetMap tiles
#  addCircleMarkers(
#    radius = 5,
#    color = "red",
#    fillOpacity = 0.7,
#    popup = ~paste("ID:", row.names(points@data), 
#                   "<br>Temp Diff:", points$temp_diff)
#  ) %>%
#  addScaleBar()

proj_crs <- CRS("+proj=utm +zone=30 +datum=WGS84") # Use appropriate UTM zone
points <- spTransform(points, proj_crs)

# Check the structure of the spatial points data
str(points)

# Define the variogram model
variogram_fit <- autofitVariogram(
  temp_diff ~ svf + gli, #
  input_data = points,
  model = c("Sph", "Exp", "Gau", "Ste"), # Possible variogram models to test
  verbose = TRUE
)
plot(variogram_fit)
fitted_variogram <- variogram_fit$var_model

# Perform cross-validation to evaluate the model's predictive performance
cv_results <- krige.cv(
  formula = temp_diff ~ svf + gli, # Specify the response variable and covariates
  locations = points, # Spatial data points
  model = fitted_variogram, # Variogram model
  nfold = 10 # Number of folds for cross-validation
)
print(cv_results)

# Calculate RMSE from cross-validation residuals
residuals <- cv_results$observed - cv_results$var1.pred
rmse <- sqrt(mean(residuals^2))
cat("RMSE:", rmse, "\n")

# --- INTERPOLATION ---
# Paths to the .tif files
svf_path <- "rasters/SVF_scaled.tif"
gli_path <- "rasters/GLI.tif"

# Load the .tif files as raster layers
svf_raster <- raster(svf_path)
gli_raster <- raster(gli_path)

range(values(svf_raster), na.rm = TRUE)
range(values(gli_raster), na.rm = TRUE)

# Ensure all rasters have the same CRS, extent, and resolution
template <- svf_raster
gli_raster <- resample(gli_raster, template, method = "bilinear")

# Stack the covariate rasters
cov_stack <- stack(svf_raster, gli_raster)
names(cov_stack) <- c("svf", "gli")

# Create a grid of prediction points with covariates
grid <- rasterToPoints(cov_stack, spatial = TRUE)
grid <- spTransform(grid, proj_crs)

# Make sure grid is a SpatialPixelsDataFrame for kriging
gridded(grid) <- TRUE
grid_df <- as(grid, "SpatialPixelsDataFrame")

# Confirm covariates are properly included in the grid
head(grid_df@data)

identical(proj4string(points), proj4string(grid_df))

kriging_result <- krige(
  formula = temp_diff ~ svf + gli,
  locations = points,
  newdata = grid_df,
  model = fitted_variogram
)

crs(kriging_result) <- proj_crs

# Convert the kriging result back to a raster
raster_output <- raster(kriging_result)

summary(raster_output)
plot(raster_output)
hist(values(raster_output), main = "Histogram of Kriging Output", breaks = 50)

# Save the output as a GeoTIFF file
output_path <- "results/universal_kriging_with_projection.tif"
writeRaster(raster_output, filename = output_path, format = "GTiff", overwrite = TRUE)

# Export variances
kriging_uncertainty <- sqrt(kriging_result$var1.var)

# Create a raster with the same extent, resolution, and CRS as the original covariates stack (or kriging result)
raster_uncertainty <- raster(grid_df)  # This creates a raster object with the same spatial properties

# Assign the uncertainty values to the raster
values(raster_uncertainty) <- kriging_uncertainty

# Save the uncertainty raster as a GeoTIFF file
uncertainty_output_path <- "results/variances_with_projection.tif"
writeRaster(raster_uncertainty, filename = uncertainty_output_path, format = "GTiff", overwrite = TRUE)
