# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(automap)
library(ggpubr)
library(spdep)
library(stats) # For median polish

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")

# Remove rows with missing values
data <- na.omit(data)

# Standardize covariates to have mean 0 and standard deviation 1
data$svf <- scale(data$svf)
data$gli <- scale(data$gli)

# Create a copy of the data frame before conversion to spatial
data_df_original <- data

# Convert data to spatial format
coordinates(data) <- ~lon + lat
proj4string(data) <- CRS("+proj=longlat +datum=WGS84")

# ---- APPLY MEDIAN POLISH ----
# Create a grid of the temperature differences
mp_data <- with(data_df_original, tapply(temp_diff, list(lon, lat), mean, na.rm = TRUE))

# Handle missing values
mp_data[is.na(mp_data)] <- median(mp_data, na.rm = TRUE)

# Apply median polish
mp_result <- medpolish(mp_data, trace.iter = TRUE)

# Extract residuals, row effects, column effects, and overall effect
residuals_matrix <- mp_result$residuals
row_effects <- mp_result$row
col_effects <- mp_result$col
overall_effect <- mp_result$overall

# Create a dataframe to map each observation to its corresponding residual
grid_points <- expand.grid(
  lon = as.numeric(rownames(mp_data)),
  lat = as.numeric(colnames(mp_data))
)
grid_points$residual <- as.vector(residuals_matrix)

# Merge residuals with original data
data_with_residuals <- merge(
  data_df_original,
  grid_points,
  by = c("lon", "lat"),
  all.x = TRUE
)

# If any rows don't have residuals (shouldn't happen with proper grid alignment)
if(any(is.na(data_with_residuals$residual))) {
  warning("Some observations couldn't be matched to residuals")
  data_with_residuals$residual[is.na(data_with_residuals$residual)] <- 0
}

# Convert back to spatial format for kriging
sp_data <- data_with_residuals
coordinates(sp_data) <- ~lon + lat
proj4string(sp_data) <- CRS("+proj=longlat +datum=WGS84")

# Fit the variogram on residuals
variogram_fit <- autofitVariogram(
  residual ~ 1,  
  input_data = sp_data,
  model = c("Sph", "Exp", "Gau", "Ste"),
  verbose = TRUE
)

plot(variogram_fit)
fitted_variogram <- variogram_fit$var_model

# ---- CROSS-VALIDATION ----
cv_results <- krige.cv(
  formula = residual ~ 1,
  locations = sp_data,
  model = fitted_variogram,
  nfold = 10
)

# RMSE Calculation
residuals_cv <- cv_results$observed - cv_results$var1.pred
rmse <- sqrt(mean(residuals_cv^2))
cat("RMSE:", rmse, "\n")

# ---- INTERPOLATION ----
# Load raster layers
svf_raster <- raster("rasters/SVF_scaled.tif")
gli_raster <- raster("rasters/GLI.tif")

# Resample to match resolution
gli_raster <- resample(gli_raster, svf_raster, method = "bilinear")

# Create spatial grid
covariates_stack <- stack(svf_raster, gli_raster)
names(covariates_stack) <- c("svf", "gli")
covariates_spdf <- as(covariates_stack, "SpatialPixelsDataFrame")

# Ensure CRS matching between datasets
proj4string(sp_data) <- CRS("+proj=longlat +datum=WGS84")
proj4string(covariates_spdf) <- CRS("+proj=utm +zone=30 +ellps=GRS80 +units=m +no_defs")

# Reproject data to match the CRS of covariates_spdf
sp_data_transformed <- spTransform(sp_data, CRS(proj4string(covariates_spdf)))

# Perform kriging on residuals
kriging_residuals <- krige(
  formula = residual ~ 1,
  locations = sp_data_transformed,
  newdata = covariates_spdf,
  model = fitted_variogram
)

# Extract coordinates from interpolation grid to match with median polish effects
grid_coords <- coordinates(covariates_spdf)
colnames(grid_coords) <- c("x", "y")

# Transform grid coordinates back to WGS84 to match original data
grid_points_wgs84 <- spTransform(
  SpatialPoints(grid_coords, proj4string = CRS(proj4string(covariates_spdf))),
  CRS("+proj=longlat +datum=WGS84")
)
grid_coords_wgs84 <- coordinates(grid_points_wgs84)
colnames(grid_coords_wgs84) <- c("lon", "lat")

# Function to find closest row/column index in median polish matrix
find_closest <- function(value, reference_values) {
  which.min(abs(value - reference_values))
}

# Create vectors to store row and column effects for each grid point
row_indices <- apply(grid_coords_wgs84[, "lon", drop = FALSE], 1, 
                     function(x) find_closest(x, as.numeric(rownames(mp_data))))
col_indices <- apply(grid_coords_wgs84[, "lat", drop = FALSE], 1, 
                     function(x) find_closest(x, as.numeric(colnames(mp_data))))

# Assign row and column effects to each grid point
grid_row_effects <- row_effects[row_indices]
grid_col_effects <- col_effects[col_indices]

# Add combined median polish effects to kriged residuals to get final prediction
kriging_residuals$prediction <- kriging_residuals$var1.pred + grid_row_effects + 
  grid_col_effects + overall_effect

# Convert to raster and save
prediction_raster <- raster(kriging_residuals, layer="prediction")
writeRaster(prediction_raster, filename = "results/median_polish_kriging.tif", 
            format = "GTiff", overwrite = TRUE)