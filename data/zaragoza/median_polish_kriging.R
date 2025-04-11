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

# Print summary of temperature differences to check variation
cat("Summary of temperature differences:\n")
print(summary(data$temp_diff))

# Standardize covariates to have mean 0 and standard deviation 1
data$svf <- scale(data$svf)
data$gli <- scale(data$gli)

# ---- APPLY MEDIAN POLISH ----
# Check if we have enough unique locations for a good grid
cat("Number of unique longitude values:", length(unique(data$lon)), "\n")
cat("Number of unique latitude values:", length(unique(data$lat)), "\n")

# Create matrix for median polish - force as.numeric to avoid factors causing issues
temp_matrix <- matrix(NA, 
                      nrow=length(unique(data$lon)), 
                      ncol=length(unique(data$lat)))
unique_lons <- sort(unique(data$lon))
unique_lats <- sort(unique(data$lat))

# Fill the matrix with temperature values
for(i in 1:nrow(data)) {
  lon_idx <- which(unique_lons == data$lon[i])
  lat_idx <- which(unique_lats == data$lat[i])
  
  # Check if we have valid indices
  if(length(lon_idx) > 0 && length(lat_idx) > 0) {
    # Average if multiple points fall in same cell
    if(is.na(temp_matrix[lon_idx, lat_idx])) {
      temp_matrix[lon_idx, lat_idx] <- data$temp_diff[i]
    } else {
      temp_matrix[lon_idx, lat_idx] <- mean(c(temp_matrix[lon_idx, lat_idx], data$temp_diff[i]), na.rm=TRUE)
    }
  }
}

# Check matrix filling
cat("Number of NA cells in temperature matrix:", sum(is.na(temp_matrix)), "\n")
cat("Percentage of filled cells:", 100 * (1 - sum(is.na(temp_matrix))/(nrow(temp_matrix)*ncol(temp_matrix))), "%\n")

# If matrix is too sparse (>90% empty), we might need a different approach
if(sum(is.na(temp_matrix))/(nrow(temp_matrix)*ncol(temp_matrix)) > 0.9) {
  cat("WARNING: Matrix is very sparse. Consider using a coarser grid.\n")
  
  # Alternative: Use a coarser grid with larger cells
  grid_res_factor <- 2  # Adjust as needed
  n_lon_bins <- max(3, length(unique_lons) %/% grid_res_factor)
  n_lat_bins <- max(3, length(unique_lats) %/% grid_res_factor)
  
  lon_breaks <- seq(min(data$lon), max(data$lon), length.out = n_lon_bins + 1)
  lat_breaks <- seq(min(data$lat), max(data$lat), length.out = n_lat_bins + 1)
  
  # Create bin indicators
  data$lon_bin <- cut(data$lon, breaks = lon_breaks, labels = FALSE, include.lowest = TRUE)
  data$lat_bin <- cut(data$lat, breaks = lat_breaks, labels = FALSE, include.lowest = TRUE)
  
  # Aggregate to bins
  agg_data <- aggregate(temp_diff ~ lon_bin + lat_bin, data = data, FUN = mean)
  
  # Create new matrix
  temp_matrix <- matrix(NA, nrow = n_lon_bins, ncol = n_lat_bins)
  for(i in 1:nrow(agg_data)) {
    temp_matrix[agg_data$lon_bin[i], agg_data$lat_bin[i]] <- agg_data$temp_diff[i]
  }
  
  # Update unique coordinates to match bins
  unique_lons <- (lon_breaks[-1] + lon_breaks[-length(lon_breaks)]) / 2
  unique_lats <- (lat_breaks[-1] + lat_breaks[-length(lat_breaks)]) / 2
  
  cat("Created coarser grid with dimensions:", dim(temp_matrix), "\n")
  cat("New fill percentage:", 100 * (1 - sum(is.na(temp_matrix))/(nrow(temp_matrix)*ncol(temp_matrix))), "%\n")
}

# Replace remaining NAs with median
if(sum(is.na(temp_matrix)) > 0) {
  med_val <- median(temp_matrix, na.rm = TRUE)
  temp_matrix[is.na(temp_matrix)] <- med_val
}

# Check matrix variation
cat("Range of values in temperature matrix:", range(temp_matrix), "\n")
cat("Standard deviation of matrix:", sd(as.vector(temp_matrix)), "\n")

# Apply median polish - only if we have sufficient variation
mp_result <- medpolish(temp_matrix, trace.iter = TRUE, maxiter = 20)

# Check median polish results
cat("Median Polish Overall Effect:", mp_result$overall, "\n")
cat("Range of Row Effects:", range(mp_result$row), "\n")
cat("Range of Column Effects:", range(mp_result$col), "\n")
cat("Range of Residuals:", range(mp_result$residuals, na.rm=TRUE), "\n")

# If no spatial trend was detected (flat row/column effects)
if(all(mp_result$row == 0) && all(mp_result$col == 0)) {
  cat("WARNING: No spatial trend detected in median polish. Proceeding with ordinary kriging of original values.\n")
  
  # Skip median polish and use original values
  data$residual <- data$temp_diff
} else {
  # Create a mapping from original points to residuals
  data$residual <- NA
  for(i in 1:nrow(data)) {
    lon_idx <- which(unique_lons == data$lon[i])
    lat_idx <- which(unique_lats == data$lat[i])
    
    if(length(lon_idx) > 0 && length(lat_idx) > 0) {
      data$residual[i] <- mp_result$residuals[lon_idx, lat_idx]
      
      # Also store row and column effects for validation
      data$row_effect[i] <- mp_result$row[lon_idx]
      data$col_effect[i] <- mp_result$col[lat_idx]
    }
  }
  
  # Handle any missing residuals
  if(sum(is.na(data$residual)) > 0) {
    cat("WARNING: Some points couldn't be matched to residuals. Using median.\n")
    data$residual[is.na(data$residual)] <- median(mp_result$residuals, na.rm=TRUE)
  }
  
  # Validate: reconstructed value should equal original
  data$reconstructed <- data$residual + data$row_effect + data$col_effect + mp_result$overall
  cat("Mean absolute error of reconstruction:", mean(abs(data$temp_diff - data$reconstructed), na.rm=TRUE), "\n")
}

# Convert to spatial format for kriging
sp_data <- data
coordinates(sp_data) <- ~lon + lat
proj4string(sp_data) <- CRS("+proj=longlat +datum=WGS84")

# Fit the variogram
variogram_fit <- autofitVariogram(
  residual ~ 1,  
  input_data = sp_data,
  model = c("Sph", "Exp", "Gau", "Ste"),
  verbose = TRUE
)

# Print variogram parameters
print("Variogram model parameters:")
print(variogram_fit$var_model)

# ---- HANDLE RASTERS ----
# Load raster layers
svf_raster <- raster("rasters/SVF_scaled.tif")
gli_raster <- raster("rasters/GLI.tif")

# Check raster dimensions
cat("SVF raster dimensions:", nrow(svf_raster), "x", ncol(svf_raster), "\n")
cat("GLI raster dimensions:", nrow(gli_raster), "x", ncol(gli_raster), "\n")

# Fix the different dimensions issue
# Option 1: Resample GLI to match SVF exactly
gli_raster <- resample(gli_raster, svf_raster, method = "bilinear")
cat("After resampling - GLI dimensions:", nrow(gli_raster), "x", ncol(gli_raster), "\n")

# Create interpolation raster grid directly from SVF
# (skip stacking if not needed for model)
prediction_grid <- rasterToPoints(svf_raster, spatial = TRUE)
cat("Number of prediction points:", nrow(prediction_grid), "\n")

# Make sure CRS is properly set
if(is.na(proj4string(prediction_grid))) {
  cat("WARNING: Prediction grid has no CRS, setting to UTM 30N\n")
  proj4string(prediction_grid) <- CRS("+proj=utm +zone=30 +ellps=GRS80 +units=m +no_defs")
}

# Transform data to match prediction grid's CRS
sp_data_transformed <- spTransform(sp_data, CRS(proj4string(prediction_grid)))

# Perform kriging on residuals
cat("Performing kriging...\n")
kriging_result <- krige(
  formula = residual ~ 1,
  locations = sp_data_transformed,
  newdata = prediction_grid,
  model = variogram_fit$var_model
)

# Check kriging output
cat("Range of kriged values:", range(kriging_result$var1.pred), "\n")
cat("Standard deviation of kriged values:", sd(kriging_result$var1.pred), "\n")

# Add trend components if median polish detected spatial trends
if(!all(mp_result$row == 0) && !all(mp_result$col == 0)) {
  # Transform prediction points back to WGS84 for matching with median polish grid
  prediction_points_wgs84 <- spTransform(prediction_grid, CRS("+proj=longlat +datum=WGS84"))
  prediction_coords <- coordinates(prediction_points_wgs84)
  
  # Assign row and column effects
  row_effect_pred <- numeric(nrow(prediction_coords))
  col_effect_pred <- numeric(nrow(prediction_coords))
  
  for(i in 1:nrow(prediction_coords)) {
    # Find closest lon/lat in original grid
    lon_idx <- which.min(abs(unique_lons - prediction_coords[i,1]))
    lat_idx <- which.min(abs(unique_lats - prediction_coords[i,2]))
    
    row_effect_pred[i] <- mp_result$row[lon_idx]
    col_effect_pred[i] <- mp_result$col[lat_idx]
  }
  
  # Check range of trend components
  cat("Range of interpolated row effects:", range(row_effect_pred), "\n")
  cat("Range of interpolated column effects:", range(col_effect_pred), "\n")
  
  # Add trend components to kriged residuals
  kriging_result$prediction <- kriging_result$var1.pred + 
    row_effect_pred + 
    col_effect_pred + 
    mp_result$overall
} else {
  # If no trends detected, prediction is just the kriged value
  kriging_result$prediction <- kriging_result$var1.pred
}

# Check final prediction
cat("Range of final predictions:", range(kriging_result$prediction), "\n")
cat("Standard deviation of final predictions:", sd(kriging_result$prediction), "\n")

# Create raster from kriging result
prediction_raster <- raster(svf_raster)  # Use SVF as template
prediction_raster <- setValues(prediction_raster, NA)  # Clear values

# Assign kriged values to raster
prediction_pts <- data.frame(
  coordinates(kriging_result),
  prediction = kriging_result$prediction
)
coordinates(prediction_pts) <- ~x+y
proj4string(prediction_pts) <- proj4string(prediction_grid)

# Rasterize points
prediction_raster <- rasterize(prediction_pts, prediction_raster, field="prediction")

# Check raster
cat("Final raster min value:", minValue(prediction_raster), "\n")
cat("Final raster max value:", maxValue(prediction_raster), "\n")
cat("Number of unique values in raster:", length(unique(values(prediction_raster)[!is.na(values(prediction_raster))])), "\n")

# Save the raster
writeRaster(prediction_raster, filename = "results/median_polish_kriging_fixed.tif", 
            format = "GTiff", overwrite = TRUE)

# Also save just the kriged residuals for comparison
residuals_raster <- raster(svf_raster)  # Use SVF as template
residuals_pts <- data.frame(
  coordinates(kriging_result),
  residual = kriging_result$var1.pred
)
coordinates(residuals_pts) <- ~x+y
proj4string(residuals_pts) <- proj4string(prediction_grid)
residuals_raster <- rasterize(residuals_pts, residuals_raster, field="residual")

writeRaster(residuals_raster, filename = "results/kriged_residuals_only.tif", 
            format = "GTiff", overwrite = TRUE)

cat("Analysis complete. Check the output rasters.\n")

