# Load libraries
library(gstat)
library(raster)
library(sp)
library(sf)
library(automap)
library(readr)

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")
data <- na.omit(data)  # Remove missing values

# Standardize secondary variables
data$svf <- scale(data$svf)
data$gli <- scale(data$gli)

# Check correlations to understand relationships
cor_temp_svf <- cor(data$temp_diff, data$svf, use = "complete.obs")
cor_temp_gli <- cor(data$temp_diff, data$gli, use = "complete.obs")
cor_svf_gli <- cor(data$svf, data$gli, use = "complete.obs")

print(paste("Correlation temp_diff-svf:", cor_temp_svf))
print(paste("Correlation temp_diff-gli:", cor_temp_gli))
print(paste("Correlation svf-gli:", cor_svf_gli))

# Convert to spatial points
coordinates(data) <- ~lon + lat
proj4string(data) <- CRS("+proj=longlat +datum=WGS84")

# Create a gstat object for co-kriging, using formula with covariates
# This is a key change - using linear models with the secondary variables
g_co <- gstat(
  id = "temp_diff", formula = temp_diff ~ 1, data = data
)
g_co <- gstat(
  g_co, id = "svf", formula = svf ~ 1, data = data
)
g_co <- gstat(
  g_co, id = "gli", formula = gli ~ 1, data = data
)

# Compute auto- and cross-variograms
vgm_co <- variogram(g_co)
#plot(vgm_co)  # Visualize the auto- and cross-variograms
print(vgm_co)

# Try different variogram models to find a better fit
# Using a smaller range will capture more local variation
vgm_model <- fit.lmc(vgm_co, g_co, 
                     model = vgm(c("Sph", "Sph", "Sph"), 
                                 c(0.6, 0.8, 0.7),  # Different sills for different components
                                 c(2000, 2000, 2000),  # Smaller range to capture more detail
                                 c(0.05, 0.05, 0.05)))  # Small nugget for smoother transitions

# Create a proper LMC model structure
vgm_model <- vgm(psill=0.6, model="Exp", range=2000, nugget=0.05)

# Fit the LMC model
vgm_model <- fit.lmc(vgm_co, g_co, model=vgm_model)

# Plot to check the model fit
plot(vgm_co, model = vgm_model)

# Load rasters
svf_raster <- raster("rasters/SVF_scaled.tif")
gli_raster <- raster("rasters/GLI.tif")

# Ensure matching CRS and resolution
template <- svf_raster
gli_raster <- resample(gli_raster, template, method = "bilinear")

# Convert rasters to SpatialPixelsDataFrame
covariates_stack <- stack(svf_raster, gli_raster)
names(covariates_stack) <- c("svf", "gli")
covariates_spdf <- as(covariates_stack, "SpatialPixelsDataFrame")

# Reproject rasters to match WGS 84
wgs84_crs <- CRS("+proj=longlat +datum=WGS84 +no_defs")
covariates_spdf <- spTransform(covariates_spdf, wgs84_crs)

# Ensure coordinate reference systems match
proj4string(covariates_spdf) <- proj4string(data)

# Verify projection matches
print(proj4string(data))
print(proj4string(covariates_spdf))

# Plot the prediction grid and observation points
plot(covariates_spdf, col = "lightgray")  
points(data, col = "red", pch = 20)  

# Perform co-kriging interpolation
ck_result <- predict(g_co, covariates_spdf, model = vgm_model)
summary(ck_result)

# Create output raster
temp_pred_raster <- raster(template)  # Use the grid structure
temp_pred_raster[] <- ck_result$temp_diff.pred  # Assign the values

# Apply post-processing to enhance contrast and emphasize local patterns
# This helps to make the influence of secondary variables more visible
# Calculate min, max and adjust contrast
min_val <- min(ck_result$temp_diff.pred, na.rm = TRUE)
max_val <- max(ck_result$temp_diff.pred, na.rm = TRUE)
mean_val <- mean(ck_result$temp_diff.pred, na.rm = TRUE)
sd_val <- sd(ck_result$temp_diff.pred, na.rm = TRUE)

# Enhance contrast by stretching values (optional)
# You can adjust the factor to increase or decrease the enhancement
enhancement_factor <- 1.2
temp_enhanced <- (ck_result$temp_diff.pred - mean_val) * enhancement_factor + mean_val

# Create enhanced raster
temp_enhanced_raster <- raster(template)
temp_enhanced_raster[] <- temp_enhanced

# Check summaries
summary(temp_pred_raster)
summary(temp_enhanced_raster)

# Save both regular and enhanced results
writeRaster(temp_pred_raster, filename = "results/co_kriging_output.tif", format = "GTiff", overwrite = TRUE)
writeRaster(temp_enhanced_raster, filename = "results/co_kriging_enhanced.tif", format = "GTiff", overwrite = TRUE)

# Optional: Create a version with even stronger local detail
# This uses a hybrid approach where we directly incorporate the secondary variables
# Get correlation signs to ensure correct direction
sign_svf <- sign(cor_temp_svf)
sign_gli <- sign(cor_temp_gli)

# Adjust weight calculation to account for correlation direction
weight_svf <- abs(cor_temp_svf) * 0.8  # Lower weight to avoid over-emphasis
weight_gli <- abs(cor_temp_gli) * 0.8

# Create hybrid values with proper sign consideration
hybrid_values <- ck_result$temp_diff.pred + 
  (sign_svf * weight_svf * scale(covariates_spdf$svf)[,1]) + 
  (sign_gli * weight_gli * scale(covariates_spdf$gli)[,1])
hybrid_raster <- raster(template)
hybrid_raster[] <- hybrid_values

writeRaster(hybrid_raster, filename = "results/hybrid_kriging.tif", format = "GTiff", overwrite = TRUE)

# Visualize results
par(mfrow=c(2,2))
plot(temp_pred_raster, main="Standard Cokriging")
plot(temp_enhanced_raster, main="Enhanced Contrast")
plot(hybrid_raster, main="Hybrid with Direct Variable Influence")
plot(covariates_spdf$svf, main="SVF Variable")
