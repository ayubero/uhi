library(gstat)
library(raster)
library(caret)
library(readr)
library(sp)
library(combinat) # For combinations

# Function to generate raster for each combination
interpolate_combination <- function(vars, points, covariates_spdf, fitted_variogram, output_dir) {
  formula <- as.formula(paste("temp_diff ~", paste(vars, collapse = " + ")))
  print(paste("Interpolating with:", formula))
  
  # Fit variogram
  fitted_variogram <- fit.variogram(
    variogram(formula, data = points),
    model <- vgm(psill = 0.1, model = "Sph", range = 100, nugget = 0.05)
  )
  
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

# Paths to the .tif files
svf_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_Sky_View_Factor_scaled.tif"
gli_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_GLI_scaled.tif"
nbai_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_NBAI_scaled.tif"
ndti_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_NDTI_scaled.tif"
mdt_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_MDT05_normalized_scaled.tif"
lst_path <- "~/University/uhi/data/rasters/Zaragoza_ETRS89_LST_LC09_20230815_normalized_scaled.tif"
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

# Define covariates
covariates <- c("svf", "gli", "nbai", "ndti", "mdt", "lst")
output_dir <- "~/University/uhi/zaragoza/rasters_combinations"

# Create all possible combinations (from 1 to all variables)
for (k in 1:length(covariates)) {
  combs <- combn(covariates, k, simplify = FALSE)
  for (comb in combs) {
    interpolate_combination(comb, points, covariates_spdf, fitted_variogram, output_dir)
  }
}

