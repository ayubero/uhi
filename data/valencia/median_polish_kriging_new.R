# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(automap)
library(ggpubr)
library(spdep)
library(spatstat) # For median polish
library(MASS)     # For robust regression
library(mgcv)     # For GAM

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

# Create a spatial data frame
points <- data.frame(
  lon = data$lon,
  lat = data$lat,
  svf = data$svf,
  gli = data$gli,
  temp_diff = data$temp_diff
)

# Convert the data frame to a spatial data frame
coordinates(points) <- ~lon + lat

# Set the coordinate reference system
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Consider rescaling the temperature data if values are very small
# This can help with numerical stability
scale_factor <- 1000  # Adjust based on your data
points$temp_diff_scaled <- points$temp_diff * scale_factor

# ====== APPROACH 1: IMPROVED MEDIAN POLISH ======
# Create a coarser grid for median polish to improve convergence
grid_res <- 20  # Reduced from 50 to have fewer empty cells
x_range <- range(coordinates(points)[,1])
y_range <- range(coordinates(points)[,2])

# Create grid cells
grid_x <- seq(from = x_range[1], to = x_range[2], length.out = grid_res)
grid_y <- seq(from = y_range[1], to = y_range[2], length.out = grid_res)

# Assign each point to a grid cell
points$cell_x <- findInterval(coordinates(points)[,1], grid_x)
points$cell_y <- findInterval(coordinates(points)[,2], grid_y)

# Create a matrix to hold temperature values
grid_matrix <- matrix(NA, nrow = length(grid_y), ncol = length(grid_x))

# Populate the matrix with mean values for each cell
for (i in 1:length(points)) {
  x_idx <- points$cell_x[i]
  y_idx <- points$cell_y[i]
  
  if (x_idx > 0 && y_idx > 0 && x_idx <= length(grid_x) && y_idx <= length(grid_y)) {
    if (is.na(grid_matrix[y_idx, x_idx])) {
      grid_matrix[y_idx, x_idx] <- points$temp_diff_scaled[i]
    } else {
      # If multiple points fall in the same cell, take their average
      grid_matrix[y_idx, x_idx] <- mean(c(grid_matrix[y_idx, x_idx], points$temp_diff_scaled[i]), na.rm = TRUE)
    }
  }
}

# Count non-NA cells to check grid density
non_na_count <- sum(!is.na(grid_matrix))
total_cells <- grid_res * grid_res
cat("Grid density:", non_na_count, "/", total_cells, "=", non_na_count/total_cells, "\n")

# Apply median polish with more iterations and relaxed convergence criteria
mp_result <- medpolish(grid_matrix, na.rm = TRUE, maxiter = 1000, eps = 0.1)

# Check convergence
cat("Median polish convergence:", mp_result$converged, "\n")

# Extract components of median polish
overall_median <- mp_result$overall
row_effects <- mp_result$row
col_effects <- mp_result$col
residuals_matrix <- mp_result$residuals

# Calculate trend and residuals for each observation point
points$mp_trend <- overall_median
points$mp_trend[!is.na(points$cell_y) & !is.na(points$cell_x)] <- 
  overall_median + 
  row_effects[points$cell_y[!is.na(points$cell_y) & !is.na(points$cell_x)]] + 
  col_effects[points$cell_x[!is.na(points$cell_y) & !is.na(points$cell_x)]]

# Calculate residuals
points$mp_residuals <- points$temp_diff_scaled - points$mp_trend

# ====== APPROACH 2: ROBUST REGRESSION TREND ======
# Extract coordinates for trend modeling
coords <- coordinates(points)
colnames(coords) <- c("x", "y")

# Fit robust linear model for trend surface
rlm_trend <- rlm(temp_diff_scaled ~ x + y + I(x^2) + I(y^2) + I(x*y), 
                 data = cbind(as.data.frame(points), coords))

# Calculate residuals from robust trend
points$rlm_residuals <- residuals(rlm_trend)

# ====== APPROACH 3: GAM TREND ======
# Fit a GAM model with smoothing splines
gam_trend <- gam(temp_diff_scaled ~ s(x, y) + svf + gli, 
                 data = cbind(as.data.frame(points), coords))

# Calculate residuals from GAM trend
points$gam_residuals <- residuals(gam_trend)

# ====== CHOOSE RESIDUALS TO USE ======
# Compare the variograms of different residuals and choose the best one
v_mp <- variogram(mp_residuals ~ 1, points)
v_rlm <- variogram(rlm_residuals ~ 1, points)
v_gam <- variogram(gam_residuals ~ 1, points)

# Plot comparison of variograms
par(mfrow = c(1, 3))
plot(v_mp, main = "Median Polish Residuals")
plot(v_rlm, main = "Robust Regression Residuals")
plot(v_gam, main = "GAM Residuals")
par(mfrow = c(1, 1))

# Based on visual inspection, choose which residuals to use for kriging
# For this example, let's use GAM residuals which often work best
# You can change this based on which variogram looks most promising
chosen_residuals <- "gam_residuals"
cat("Using", chosen_residuals, "for kriging\n")

# Fit variogram to chosen residuals
variogram_formula <- as.formula(paste0(chosen_residuals, " ~ 1"))
variogram_fit <- autofitVariogram(
  variogram_formula,
  input_data = points,
  model = c("Sph", "Exp", "Gau", "Ste"),
  verbose = TRUE
)

plot(variogram_fit)
fitted_variogram <- variogram_fit$var_model

# Check if the variogram shows spatial structure
cat("Nugget:", fitted_variogram$psill[1], "\n")
cat("Sill:", sum(fitted_variogram$psill), "\n")
cat("Range:", fitted_variogram$range[2], "\n")

# If nugget/sill ratio is high, spatial dependence is weak
nugget_sill_ratio <- fitted_variogram$psill[1] / sum(fitted_variogram$psill)
cat("Nugget/Sill ratio:", nugget_sill_ratio, "\n")

# Perform cross-validation
cv_results <- krige.cv(
  formula = variogram_formula,
  locations = points,
  model = fitted_variogram,
  nfold = 10
)

# Calculate RMSE from cross-validation
residuals_cv <- cv_results$observed - cv_results$var1.pred
rmse <- sqrt(mean(residuals_cv^2))
cat("RMSE:", rmse, "\n")

# --- INTERPOLATION ---
# Paths to the .tif files
svf_path <- "rasters/SVF_scaled.tif"
gli_path <- "rasters/GLI.tif"

# Load the .tif files as raster layers
svf_raster <- raster(svf_path)
gli_raster <- raster(gli_path)

# Ensure all rasters have the same CRS, extent, and resolution
template <- svf_raster
gli_raster <- resample(gli_raster, template, method = "bilinear")

# Stack the covariate rasters
covariates_stack <- stack(svf_raster, gli_raster)
names(covariates_stack) <- c("svf", "gli")

# Convert the raster stack to a SpatialPixelsDataFrame
covariates_spdf <- as(covariates_stack, "SpatialPixelsDataFrame")

# Ensure your spatial points have the same CRS
proj4string(points) <- proj4string(template)

# Kriging the residuals
kriging_result <- krige(
  formula = variogram_formula,
  locations = points,
  newdata = covariates_spdf,
  model = fitted_variogram
)

# Create prediction grid for trend surface
pred_grid <- as.data.frame(covariates_spdf)
coordinates_pred <- coordinates(covariates_spdf)
colnames(coordinates_pred) <- c("x", "y")
pred_grid <- cbind(pred_grid, coordinates_pred)

# Predict trend surface based on chosen method
if (chosen_residuals == "mp_residuals") {
  # For median polish, create a function to predict trend
  # Get cell indices for each prediction point
  pred_cell_x <- findInterval(pred_grid$x, grid_x)
  pred_cell_y <- findInterval(pred_grid$y, grid_y)
  
  # Calculate trend values
  trend_values <- rep(overall_median, nrow(pred_grid))
  for (i in 1:nrow(pred_grid)) {
    x_idx <- pred_cell_x[i]
    y_idx <- pred_cell_y[i]
    
    if (x_idx > 0 && y_idx > 0 && x_idx <= length(grid_x) && y_idx <= length(grid_y)) {
      trend_values[i] <- overall_median + row_effects[y_idx] + col_effects[x_idx]
    }
  }
  
  trend_raster <- raster(template)
  trend_raster <- setValues(trend_raster, trend_values)
  
} else if (chosen_residuals == "rlm_residuals") {
  # For robust regression trend
  pred_trend <- predict(rlm_trend, newdata = pred_grid)
  trend_raster <- raster(template)
  trend_raster <- setValues(trend_raster, pred_trend)
  
} else if (chosen_residuals == "gam_residuals") {
  # For GAM trend
  pred_trend <- predict(gam_trend, newdata = pred_grid)
  trend_raster <- raster(template)
  trend_raster <- setValues(trend_raster, pred_trend)
}

# Add trend to kriged residuals
kriged_residuals <- raster(kriging_result)
final_prediction <- kriged_residuals + trend_raster

# Scale back to original units if scaling was applied
final_prediction <- final_prediction / scale_factor

# Save the output as a GeoTIFF file
method_name <- gsub("_residuals", "", chosen_residuals)
output_path <- paste0("results/", method_name, "_kriging.tif")
writeRaster(final_prediction, filename = output_path, format = "GTiff", overwrite = TRUE)

# Also save trend and residuals separately
trend_output_path <- paste0("results/", method_name, "_trend.tif")
residuals_output_path <- paste0("results/", method_name, "_residuals.tif")
writeRaster(trend_raster / scale_factor, filename = trend_output_path, format = "GTiff", overwrite = TRUE)
writeRaster(kriged_residuals / scale_factor, filename = residuals_output_path, format = "GTiff", overwrite = TRUE)

# Create diagnostic plots
# Plot original data
spplot(points, "temp_diff", main = "Original Temperature Data")

# Plot trend surface
plot(trend_raster / scale_factor, main = paste0(method_name, " Trend Surface"))

# Plot kriged residuals
plot(kriged_residuals / scale_factor, main = paste0(method_name, " Kriged Residuals"))

# Plot final prediction
plot(final_prediction, main = paste0(method_name, " Final Prediction"))