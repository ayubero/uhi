library(automap)
library(gstat)
library(sp)
library(raster)
library(caret)
library(readr)
library(combinat) # For combinations

# Function to generate raster for each combination
interpolate_combination <- function(vars, points, covariates_spdf, fitted_variogram, output_dir) {
  formula <- as.formula(paste("temp_diff ~", paste(vars, collapse = " + ")))
  print(paste("Interpolating with:", formula))
  
  # Check original temp_diff stats
  cat("Original temp_diff range:", range(data$temp_diff), "\n")
  cat("Original temp_diff mean:", mean(data$temp_diff, na.rm = TRUE), "\n")
  cat("Original temp_diff sd:", sd(data$temp_diff, na.rm = TRUE), "\n")
  
  # Scale temp_diff and store mean & sd for inverse transformation
  temp_diff_mean <- mean(data$temp_diff, na.rm = TRUE)
  temp_diff_sd <- sd(data$temp_diff, na.rm = TRUE)
  #data$temp_diff <- scale(data$temp_diff)
  data$temp_diff <- (data$temp_diff - temp_diff_mean) / temp_diff_sd
  
  # Check scaled temp_diff stats
  cat("Scaled temp_diff range:", range(data$temp_diff), "\n")
  cat("Scaled temp_diff mean:", mean(data$temp_diff, na.rm = TRUE), "\n")
  cat("Scaled temp_diff sd:", sd(data$temp_diff, na.rm = TRUE), "\n")
  
  # Fit variogram
  variogram_fit <- autofitVariogram(
    formula,
    input_data = points,
    model = c("Sph", "Exp", "Gau", "Ste"), # Possible variogram models to test
    verbose = TRUE
  )
  fitted_variogram <- variogram_fit$var_model
  #fitted_variogram <- fit.variogram(
  #  variogram(formula, data = points),
  #  vgm(psill = 0.5, model = "Exp", range = 100, nugget = 0.1)
  #)
  #plot(fitted_variogram)
  
  # Cross-validation
  cv_results <- krige.cv(
    formula = formula,
    locations = points,
    model = fitted_variogram,
    nfold = 10
  )
  
  residuals <- cv_results$observed - cv_results$var1.pred
  rmse <- sqrt(mean(residuals^2))
  cat("RMSE:", rmse, "\n")

  # Kriging interpolation
  kriging_result <- krige(
    formula = formula,
    locations = points,
    newdata = covariates_spdf,
    model = fitted_variogram
  )
  
  # Convert back to original scale
  #kriging_result$var1.pred <- kriging_result$var1.pred * temp_diff_sd + temp_diff_mean
  
  # Ensure inverse-transformed range
  cat("Inverse transformed temp_diff range:", range(kriging_result$var1.pred), "\n")
  
  # Convert to raster
  raster_output <- raster(kriging_result)
  
  # Save raster
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }
  filename <- file.path(output_dir, paste(vars, collapse = "_"))
  filename <- paste0(filename, ".tif") # Add the .tif extension
  writeRaster(raster_output, filename = filename, format = "GTiff", overwrite = TRUE)
  cat("Saved:", filename, "\n")
}

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
data$nbai <- scale(data$nbai)
data$ndti <- scale(data$ndti)
data$mdt <- scale(data$mdt)
data$lst <- scale(data$lst)

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

# Paths to the .tif files
svf_path <- "rasters/SVF_scaled.tif"
gli_path <- "rasters/GLI.tif"
nbai_path <- "rasters/NBAI.tif"
ndti_path <- "rasters/NDTI.tif"
mdt_path <- "rasters/MDT_normalized.tif"
lst_path <- "rasters/LST_normalized.tif"

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

# Define covariates
covariates <- c("svf", "gli", "nbai", "ndti", "mdt", "lst")
output_dir <- "results"

# Create all possible combinations (from 1 to all variables)
for (k in 1:length(covariates)) {
  combs <- combn(covariates, k, simplify = FALSE)
  for (comb in combs) {
    print(comb)
    if (identical(comb, c("svf", "gli"))) {
      interpolate_combination(comb, points, covariates_spdf, fitted_variogram, output_dir)
    }
  }
}

#interpolate_combination(c("svf", "gli"), covariates_spdf, fitted_variogram, output_dir)
