# Install packages
install.packages("gstat")
install.packages("raster")
install.packages("caret")
install.packages("dplyr")

# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)

# Load the CSV file into a dataframe
data <- read_csv("~/University/uhi/zaragoza/data.csv")
#View(data)

# Check the first few rows of the dataset
head(data)

# Check correlation
cor(data$temp_diff, data$svf, use = "complete.obs")
cor(data$temp_diff, data$imd, use = "complete.obs")
cor(data$temp_diff, data$ndvi, use = "complete.obs")

# Standardize covariates to have mean 0 and standard deviation 1
#data$imd <- scale(data$imd)
#data$svf <- scale(data$svf)
#data$ndvi <- scale(data$ndvi)

points <- data.frame(
  lon = data$lon,
  lat = data$lat,
  svf = data$svf,
  imd = data$imd,
  ndvi = data$ndvi,
  swir2 = data$swir2,
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
fitted_variogram <- fit.variogram(
  variogram(temp_diff ~ svf + imd + ndvi, data = points),
  model = vgm("Exp")
)
print(fitted_variogram)
plot(variogram(temp_diff ~ svf + imd + ndvi, data = points), fitted_variogram)

if (FALSE) {
  # Candidate variogram models
  models <- c("Sph", "Exp", "Gau", "Mat")
  fitted_models <- lapply(models, function(model) {
    fit.variogram(variogram(temp_diff ~ svf + imd + ndvi, data = points), vgm(model))
  })
  
  names(fitted_models) <- models
  fitted_models
  
  cv_results <- krige.cv(temp_diff ~ svf + imd + ndvi, points, model = fitted_models[["Mat"]])
  residuals <- cv_results$observed - cv_results$var1.pred
  rmse <- sqrt(mean(residuals^2))
  cat("RMSE:", rmse, "\n")
}

# Perform cross-validation to evaluate the model's predictive performance
cv_results <- krige.cv(
  formula = temp_diff ~ svf + imd + ndvi, # Specify the response variable and covariates
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
svf_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_Sky_View_Factor_scaled.tif"
imd_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_Imperviousness_Density_normalized_scaled.tif"
ndvi_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_NDVI_scaled.tif"
swir2_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_SWIR2_normalized_scaled.tif"

# Load the .tif files as raster layers
svf_raster <- raster(svf_path)
imd_raster <- raster(imd_path)
ndvi_raster <- raster(ndvi_path)
swir2_raster <- raster(swir2_path)

# Ensure all rasters have the same CRS, extent, and resolution
template <- svf_raster # Use one raster as the template

imd_raster <- resample(imd_raster, template, method = "bilinear")
ndvi_raster <- resample(ndvi_raster, template, method = "bilinear")
swir2_raster <- resample(swir2_raster, template, method = "bilinear")

# Stack the covariate rasters
covariates_stack <- stack(svf_raster, imd_raster, ndvi_raster, swir2_raster)
names(covariates_stack) <- c("svf", "imd", "ndvi", "swir2") # Set layer names

# Convert the raster stack to a SpatialPixelsDataFrame
covariates_spdf <- as(covariates_stack, "SpatialPixelsDataFrame")

# Ensure your spatial points have the same CRS
proj4string(points) <- proj4string(template)

# Define the variogram model
#variogram_model <- vgm(psill = 1, model = "Sph", range = 1000, nugget = 0.1)

# Perform kriging interpolation
kriging_result <- krige(
  formula = temp_diff ~ svf + imd + ndvi,  # Interpolation formula
  locations = points,                     # Spatial data points
  newdata = covariates_spdf,              # Raster stack as spatial grid
  model = fitted_variogram                 # Variogram model
)

# Convert the kriging result back to a raster
raster_output <- raster(kriging_result)

# Save the output as a GeoTIFF file
output_path <- "~/University/uhi/zaragoza/interpolation_SVF+IMD+NDVI.tif"
writeRaster(raster_output, filename = output_path, format = "GTiff", overwrite = TRUE)

#cat("Interpolated raster saved at:", output_path, "\n")
