# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(automap)

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")
#View(data)

# Check the first few rows of the dataset
head(data)

# Check correlation
cor(data$temp_diff, data$svf, use = "complete.obs")
cor(data$temp_diff, data$gli, use = "complete.obs")
cor(data$temp_diff, data$nbai, use = "complete.obs")
cor(data$temp_diff, data$ndti, use = "complete.obs")
cor(data$temp_diff, data$mdt, use = "complete.obs")
cor(data$temp_diff, data$lst, use = "complete.obs")

# Standardize covariates to have mean 0 and standard deviation 1
data$svf <- scale(data$svf)
data$gli <- scale(data$gli)
#data$temp_diff <- scale(data$temp_diff)
temp_diff_mean <- mean(data$temp_diff)
temp_diff_sd <- sd(data$temp_diff)
#data$temp_diff <- (data$temp_diff - temp_diff_mean) / temp_diff_sd
# Min-Max Normalization
#temp_diff_min <- min(data$temp_diff)
#temp_diff_max <- max(data$temp_diff)
#data$temp_diff <- (data$temp_diff - temp_diff_min) / (temp_diff_max - temp_diff_min)

points <- data.frame(
  lon = data$lon,
  lat = data$lat,
  svf = data$svf,
  gli = data$gli,
  nbai = data$nbai,
  ndti = data$ndti,
  mdt = data$mdt,
  lst = data$lst,
  temp_diff = data$temp_diff
)

# Convert the data frame to a spatial data frame
coordinates(points) <- ~lon + lat

# Ensure the data is in a SpatialPointsDataFrame (this will automatically include the coordinates as spatial information)
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Check the structure of the spatial points data
str(points)

# Define the variogram model
#variogram_model <- vgm(psill = 1, model = "Sph", range = 1000, nugget = 0.1)
# svf + gli + nbai + ndti + mdt + lst
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

# Plot observed vs. predicted
#plot(cv_results$observed, kriging_result$var1.pred, 
#     xlab = "Observed", ylab = "Predicted",
#     main = paste("Observed vs Predicted (RMSE:", round(rmse, 2), ")"))
#abline(0, 1, col = "red")

# --- INTERPOLATION ---
# Paths to the .tif files
svf_path <- "rasters/SVF.tif"
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

#kriging_result$var1.pred <- kriging_result$var1.pred * temp_diff_sd + temp_diff_mean
#kriging_result$var1.pred <- kriging_result$var1.pred * (temp_diff_max - temp_diff_min) + temp_diff_min

# Convert the kriging result back to a raster
raster_output <- raster(kriging_result)

# Save the output as a GeoTIFF file
output_path <- "results/svf_gli.tif"
writeRaster(raster_output, filename = output_path, format = "GTiff", overwrite = TRUE)

#cat("Interpolated raster saved at:", output_path, "\n")

