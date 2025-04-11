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

# Standardize covariates to have mean 0 and standard deviation 1
data$svf <- scale(data$svf)
data$gli <- scale(data$gli)

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
#proj4string(points) <- CRS("+proj=longlat +datum=WGS84")
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

proj_crs <- CRS("+proj=utm +zone=30 +datum=WGS84") # use appropriate UTM zone
points_proj <- spTransform(points, proj_crs)

# Check the structure of the spatial points data
str(points)

# Define the variogram model
variogram_fit <- autofitVariogram(
  temp_diff ~ 1, #
  input_data = points_proj,
  model = c("Sph", "Exp", "Gau", "Ste"), # Possible variogram models to test
  verbose = TRUE
)
plot(variogram_fit)
fitted_variogram <- variogram_fit$var_model
#fitted_variogram <- vgm(psill = 0.35, model = "Sph", range = 10, nugget = 0.1)

# Perform cross-validation to evaluate the model's predictive performance
cv_results <- krige.cv(
  formula = temp_diff ~ 1, # Specify the response variable and covariates
  locations = points_proj, # Spatial data points
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

# Ensure all rasters have the same CRS, extent, and resolution
template <- svf_raster # Use one raster as the template
gli_raster <- resample(gli_raster, template, method = "bilinear")

# Create a grid of spatial points (prediction locations)
grid <- rasterToPoints(template, spatial = TRUE)
proj4string(grid) <- proj_crs

# Convert SpatialPoints to SpatialPixelsDataFrame
gridded(grid) <- TRUE  # now it's a grid
grid_df <- as(grid, "SpatialPixelsDataFrame")

identical(proj4string(points), proj4string(grid_df))

kriging_result <- krige(
  formula = temp_diff ~ 1,
  locations = points_proj,
  newdata = grid_df,
  model = fitted_variogram
)

crs(kriging_result) <- proj_crs
crs(template) <- proj_crs
extent(template) <- extent(kriging_result)

# Convert the kriging result back to a raster
#raster_output <- raster(kriging_result)
raster_output <- rasterize(kriging_result, template, field = "var1.pred", fun = mean)
extent(kriging_result)
extent(raster_output)

head(kriging_result@data)


summary(raster_output)
plot(raster_output)
hist(values(raster_output), main = "Histogram of Kriging Output", breaks = 50)

# Save the output as a GeoTIFF file
output_path <- "results/universal_kriging.tif"
writeRaster(raster_output, filename = output_path, format = "GTiff", overwrite = TRUE)

