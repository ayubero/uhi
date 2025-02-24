# Install packages
install.packages("gstat")
install.packages("raster")
install.packages("caret")

# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)

# Load the CSV file into a dataframe
data <- read_csv("~/University/uhi/zaragoza/data_netatmo.csv")
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
#data$imd <- scale(data$imd)
#data$svf <- scale(data$svf)
#data$ndvi <- scale(data$ndvi)

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
fitted_variogram <- fit.variogram(
  variogram(temp_diff ~ svf + gli + nbai + ndti + mdt + lst, data = points),
  model = vgm("Sph")
)
print(fitted_variogram)
plot(variogram(temp_diff ~ svf + gli + nbai + ndti + mdt + lst, data = points), fitted_variogram)

# Perform cross-validation to evaluate the model's predictive performance
cv_results <- krige.cv(
  formula = temp_diff ~ svf + gli + nbai + ndti + mdt + lst, # Specify the response variable and covariates
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
gli_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_GLI.tif"
nbai_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_NBAI.tif"
ndti_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_NDTI.tif"
mdt_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_MDT05_normalized.tif"
lst_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_LST_LC09_20230815_normalized.tif"
#imd_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_Imperviousness_Density_normalized_scaled.tif"
#ndvi_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_NDVI_scaled.tif"
#swir2_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_SWIR2_normalized_scaled.tif"

# Load the .tif files as raster layers
svf_raster <- raster(svf_path)
gli_raster <- raster(gli_path)
nbai_raster <- raster(nbai_path)
ndti_raster <- raster(ndti_path)
mdt_raster <- raster(mdt_path)
lst_raster <- raster(lst_path)

# Ensure all rasters have the same CRS, extent, and resolution
template <- svf_raster # Use one raster as the template

gli_raster <- resample(gli_raster, template, method = "bilinear")
nbai_raster <- resample(nbai_raster, template, method = "bilinear")
ndti_raster <- resample(ndti_raster, template, method = "bilinear")
mdt_raster <- resample(mdt_raster, template, method = "bilinear")
lst_raster <- resample(lst_raster, template, method = "bilinear")

# Stack the covariate rasters
covariates_stack <- stack(svf_raster, gli_raster, nbai_raster, ndti_raster, mdt_raster, lst_raster)
names(covariates_stack) <- c("svf", "gli", "nbai", "ndti", "mdt", "lst") # Set layer names

# Convert the raster stack to a SpatialPixelsDataFrame
covariates_spdf <- as(covariates_stack, "SpatialPixelsDataFrame")

# Ensure your spatial points have the same CRS
proj4string(points) <- proj4string(template)

# Define the variogram model
#variogram_model <- vgm(psill = 1, model = "Sph", range = 1000, nugget = 0.1)

# Perform kriging interpolation
kriging_result <- krige(
  formula = temp_diff ~ svf + gli + nbai + ndti + mdt + lst,  # Interpolation formula
  locations = points,                     # Spatial data points
  newdata = covariates_spdf,              # Raster stack as spatial grid
  model = fitted_variogram                 # Variogram model
)

# Convert the kriging result back to a raster
raster_output <- raster(kriging_result)

# Save the output as a GeoTIFF file
output_path <- "~/University/uhi/zaragoza/interpolation_netatmo_new_variables.tif"
writeRaster(raster_output, filename = output_path, format = "GTiff", overwrite = TRUE)

#cat("Interpolated raster saved at:", output_path, "\n")

