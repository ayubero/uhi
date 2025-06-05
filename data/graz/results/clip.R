# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)

# Load raster
gli_path <- "kriging_result_5m_without_clipping.tif"
gli_raster <- raster(gli_path)

# Manual clip
gli_raster[gli_raster > 2.781503] <- 2.781503
gli_raster[gli_raster < -1.764738] <- -1.764738

output_path <- "kriging_result_5m.tif"
writeRaster(gli_raster, filename = output_path, format = "GTiff", overwrite = TRUE)
