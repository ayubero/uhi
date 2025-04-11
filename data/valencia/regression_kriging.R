# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(automap)
library(ggpubr)
library(spdep)
library(sp)

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

# Ensure the data is in a SpatialPointsDataFrame
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Check the structure of the spatial points data
str(points)

# STEP 1: Fit a linear regression model
regression_model <- lm(temp_diff ~ svf + gli, data = as.data.frame(points))
summary(regression_model)

# Extract the coefficients for later prediction
regression_coefficients <- coefficients(regression_model)

# Calculate residuals
points$residuals <- residuals(regression_model)

# STEP 2: Perform kriging on the residuals
# Define the variogram model for the residuals
variogram_fit <- autofitVariogram(
  residuals ~ 1, # Using only the residuals without covariates
  input_data = points,
  model = c("Sph", "Exp", "Gau", "Ste"), # Possible variogram models to test
  verbose = TRUE
)

plot(variogram_fit)
fitted_variogram <- variogram_fit$var_model

# Perform cross-validation to evaluate the model's predictive performance
cv_results <- krige.cv(
  formula = residuals ~ 1, # Only kriging the residuals
  locations = points,
  model = fitted_variogram,
  nfold = 10
)

# Calculate RMSE from cross-validation residuals
cv_residuals <- cv_results$observed - cv_results$var1.pred
rmse <- sqrt(mean(cv_residuals^2))
cat("RMSE for residual kriging:", rmse, "\n")

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

# Create a histogram of the residuals
ggplot(as.data.frame(points), aes(x = residuals)) +
  geom_histogram(binwidth = 0.5, fill = "steelblue", color = "black", alpha = 0.7) +
  labs(title = "Histogram of Residuals", x = "Residuals", y = "Frequency") +
  theme_minimal()
shapiro.test(points$residuals)

# STEP 3: Perform kriging on the residuals to get a residual surface
residual_kriging <- krige(
  formula = residuals ~ 1, # Only kriging the residuals
  locations = points,
  newdata = covariates_spdf,
  model = fitted_variogram
)

# Convert the kriging result back to a raster
residual_raster <- raster(residual_kriging)

# STEP 4: Apply the regression model to the covariates to get the trend surface
# Create trend raster using regression coefficients
trend_raster <- regression_coefficients[1] + 
  regression_coefficients[2] * covariates_stack$svf + 
  regression_coefficients[3] * covariates_stack$gli

# STEP 5: Combine the trend surface and the residual surface
final_prediction <- trend_raster + residual_raster

# Save the output as a GeoTIFF file
output_path <- "results/regression_kriging.tif"
writeRaster(final_prediction, filename = output_path, format = "GTiff", overwrite = TRUE)

# Optional: Also save the trend and residual components separately
writeRaster(trend_raster, filename = "results/regression_trend.tif", format = "GTiff", overwrite = TRUE)
writeRaster(residual_raster, filename = "results/kriging_residuals.tif", format = "GTiff", overwrite = TRUE)

# Visualize the components
par(mfrow=c(2,2))
plot(trend_raster, main="Trend Component (from Regression)")
#plot(residual_raster, main="Residual Component (from Kriging)")
plot(final_prediction, main="Final Regression Kriging Prediction")
#plot(raster(variogram_fit$exp_var$np), main="Number of Point Pairs in Variogram")
