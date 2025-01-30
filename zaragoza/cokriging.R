# Install required packages if not already installed
install.packages(c("gstat", "raster", "caret", "gridExtra", "sp"))

# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)
library(gridExtra)
library(sp)

# Load the CSV file into a dataframe
data <- read_csv("~/University/uhi/zaragoza/data.csv")

# Check correlation between temp_diff and covariates
cor(data$temp_diff, data$svf, use = "complete.obs")
cor(data$temp_diff, data$imd, use = "complete.obs")
cor(data$temp_diff, data$ndvi, use = "complete.obs")

# Load raster datasets
ndvi_raster <- raster("~/University/uhi/data/rasters/Zaragoza_ETRS89_NDVI_scaled.tif")
svf_raster <- raster("~/University/uhi/data/rasters/Zaragoza_ETRS89_Sky_View_Factor_scaled.tif")
imd_raster <- raster("~/University/uhi/data/rasters/Zaragoza_ETRS89_Imperviousness_Density_normalized_scaled.tif")

# Verify rasters are loaded correctly
plot(ndvi_raster, main = "NDVI Raster")
plot(svf_raster, main = "SVF Raster")
plot(imd_raster, main = "IMD Raster")

# Prepare spatial data frame
points <- data.frame(
  lon = data$lon,
  lat = data$lat,
  svf = data$svf,
  imd = data$imd,
  ndvi = data$ndvi,
  temp_diff = data$temp_diff
)

# Convert the data frame to a spatial data frame
coordinates(points) <- ~lon + lat
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Extract raster values at point locations
points$ndvi_raster <- extract(ndvi_raster, points)
points$svf_raster <- extract(svf_raster, points)
points$imd_raster <- extract(imd_raster, points)

# Check correlations
cor(points$temp_diff, points$ndvi_raster, use = "complete.obs")
cor(points$temp_diff, points$svf_raster, use = "complete.obs")
cor(points$temp_diff, points$imd_raster, use = "complete.obs")

# Define variograms for each variable
variogram_temp <- variogram(temp_diff ~ 1, data = points, cloud=F)
model_temp <- vgm(1.5, "Exp", 1, 0.5)
model_fit_temp <- fit.variogram(variogram_temp, model_temp)

variogram_ndvi <- variogram(ndvi_raster ~ 1, data = points, cloud=F)
model_ndvi <- vgm(1.5, "Exp", 1, 0.5)
model_fit_ndvi <- fit.variogram(variogram_ndvi, model_ndvi)

variogram_svf <- variogram(svf_raster ~ 1, data = points, cloud=F)
model_svf <- vgm(1.5, "Exp", 1, 0.5)
model_fit_svf <- fit.variogram(variogram_svf, model_svf)

variogram_imd <- variogram(imd_raster ~ 1, data = points, cloud=F)
model_imd <- vgm(1.5, "Exp", 1, 0.5)
model_fit_imd <- fit.variogram(variogram_imd, model_imd)

# Display variograms
grid.arrange(plot(variogram_temp, pl=F, model=model_fit_temp, main= "Temp Diff Variogram"),
             plot(variogram_ndvi, pl=F, model=model_fit_ndvi, main="NDVI Variogram"),
             plot(variogram_svf, pl=F, model=model_fit_svf, main="SVF Variogram"),
             plot(variogram_imd, pl=F, model=model_fit_imd, main="IMD Variogram"),
             ncol=2)

# Define gstat object for cokriging
g <- gstat(NULL, id = "temp", form = temp_diff ~ 1, data=points)
g <- gstat(g, id = "ndvi_raster", form = ndvi_raster ~ 1, data=points)
g <- gstat(g, id = "svf_raster", form = svf_raster ~ 1, data=points)
g <- gstat(g, id = "imd_raster", form = imd_raster ~ 1, data=points)

# Compute cross-variogram
cross_variogram <- variogram(g)
plot(cross_variogram, pl=F)

# Fit variogram models
g <- gstat(g, id = "temp_diff", model = model_fit_temp, fill.all=T)
g <- fit.lmc(cross_variogram, g)

# Print fitted model details
print(g)

# Plot fitted variogram
plot(variogram(g), model=g$model)

# Create a regular grid covering the study area
bbox <- extent(min(data$lon), max(data$lon), min(data$lat), max(data$lat))
grid_res <- 0.001  # Adjust resolution as needed
grid <- expand.grid(
  lon = seq(bbox@xmin, bbox@xmax, by = grid_res),
  lat = seq(bbox@ymin, bbox@ymax, by = grid_res)
)

# Convert to SpatialPixelsDataFrame
coordinates(grid) <- ~lon + lat
gridded(grid) <- TRUE
proj4string(grid) <- CRS("+proj=longlat +datum=WGS84")

# Predict using co-kriging
CK <- predict(g, grid)

# Convert prediction to raster and plot
CK_raster <- raster(CK)
plot(CK_raster, main = "Cokriged Prediction (Temp Diff)")

# Save raster output
writeRaster(CK_raster, filename = "~/University/uhi/kriged_temp_diff.tif", format = "GTiff", overwrite=TRUE)
