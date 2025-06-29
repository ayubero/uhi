# Load libraries
library(gstat)
library(raster)
library(sp)
library(sf)
library(automap)
library(readr)
library(dplyr)

# Load the CSV file into a dataframe
data <- read_csv("data_netatmo.csv")
data <- na.omit(data)  # Remove missing values

# Standardize secondary variables
data$svf <- scale(data$svf)
data$gli <- scale(data$gli)

cor(data$temp_diff, data$svf, use = "complete.obs")
cor(data$temp_diff, data$gli, use = "complete.obs")
cor(data$svf, data$gli, use = "complete.obs")


# Convert to spatial points
coordinates(data) <- ~lon + lat
proj4string(data) <- CRS("+proj=longlat +datum=WGS84")

# Create a gstat object for co-kriging
g_co <- gstat(
  id = "temp_diff", formula = temp_diff ~ 1, data = data
)
g_co <- gstat(
  g_co, id = "svf", formula = svf ~ 1, data = data
)
g_co <- gstat(
  g_co, id = "gli", formula = gli ~ 1, data = data
)

# Compute cross-variograms
vgm_co <- variogram(g_co)
plot(vgm_co)  # Visualize the auto- and cross-variograms
print(vgm_co)
print(g_co)

# Fit a co-kriging model
#vgm_initial <- vgm(psill = 1, model = "Sph", range = 0.3, nugget = 0.1)
#vgm_model <- fit.variogram(vgm_co, vgm_initial)
vgm_model <- fit.lmc(vgm_co, g_co, model = vgm(2, "Exp", 0.3, 0.1))
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

plot(covariates_spdf, col = "lightgray")  # Prediction grid
points(data, col = "red", pch = 20)  # Observation points

print(proj4string(data))
print(proj4string(covariates_spdf))

# Perform co-kriging interpolation
ck_result <- predict(g_co, covariates_spdf) #, model = vgm_model
summary(ck_result)
print(vgm_model)
summary(covariates_spdf)

summary(ck_result)

# Convert result to raster and save
raster_output <- raster(ck_result["temp_diff.pred"])
writeRaster(raster_output, filename = "results/co_kriging_output.tif", format = "GTiff", overwrite = TRUE)
