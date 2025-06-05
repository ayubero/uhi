# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)

# Load raster
gli_path <- "gli.tif"
gli_raster <- raster(gli_path)

# Manual clip
gli_raster[gli_raster > 0.306613] <- 0.306613
gli_raster[gli_raster < -0.217631] <- -0.217631

output_path <- "gli_clipped.tif"
writeRaster(gli_raster, filename = output_path, format = "GTiff", overwrite = TRUE)