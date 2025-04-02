# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(automap)
library(ggpubr)
library(spdep)

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
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Check the structure of the spatial points data
str(points)

# Define the variogram model
variogram_fit <- autofitVariogram(
  temp_diff ~ svf + gli,
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

# Ensure all rasters have the same CRS, extent, and resolution
template <- svf_raster # Use one raster as the template
gli_raster <- resample(gli_raster, template, method = "bilinear")

# Stack the covariate rasters
covariates_stack <- stack(svf_raster, gli_raster)
names(covariates_stack) <- c("svf", "gli") # Set layer names

# Convert the raster stack to a SpatialPixelsDataFrame
covariates_spdf <- as(covariates_stack, "SpatialPixelsDataFrame")

# Ensure your spatial points have the same CRS
proj4string(points) <- proj4string(template)

# Perform kriging interpolation
kriging_result <- krige(
  formula = temp_diff ~ svf + gli,  # Interpolation formula
  locations = points,                     # Spatial data points
  newdata = covariates_spdf,              # Raster stack as spatial grid
  model = fitted_variogram                 # Variogram model
)

# Convert the kriging result back to a raster
raster_output <- raster(kriging_result)

# Save the output as a GeoTIFF file
output_path <- "results/svf_gli.tif"
writeRaster(raster_output, filename = output_path, format = "GTiff", overwrite = TRUE)


