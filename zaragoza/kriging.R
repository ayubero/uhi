# Install packages
install.packages("gstat")
install.packages("raster")
install.packages("caret")

# Load libraries
library(gstat)
library(raster)
library(caret)
library(readr)

# Load the CSV file into a dataframe
data <- read_csv("~/University/uhi/zaragoza/data.csv")
#View(data)

# Check the first few rows of the dataset
head(data)

points <- data.frame(
  lon = data$lon,
  lat = data$lat,
  svf = data$svf,
  imd = data$imd,
  ndvi = data$ndvi,
  swir2 = data$swir2,
  temp_diff = data$temp_diff
)

# Convert the data frame to a spatial data frame
coordinates(points) <- ~lon + lat

# Ensure the data is in a SpatialPointsDataFrame (this will automatically include the coordinates as spatial information)
proj4string(points) <- CRS("+proj=longlat +datum=WGS84")

# Check the structure of the spatial points data
str(points)

# Define the variogram model
variogram_model <- vgm(psill = 1, model = "Sph", range = 1000, nugget = 0.1)

# Perform cross-validation to evaluate the model's predictive performance
cv_results <- krige.cv(
  formula = temp_diff ~ svf + imd + ndvi,  # Specify the response variable and covariates (you can adjust this based on your problem)
  locations = points,                            # Spatial data points
  model = variogram_model,                       # Variogram model
  nfold = 10                                     # Number of folds for cross-validation
)
print(cv_results)

# Calculate RMSE from cross-validation residuals
residuals <- cv_results$observed - cv_results$var1.pred
rmse <- sqrt(mean(residuals^2))
cat("RMSE:", rmse, "\n")

# Plot observed vs. predicted
#plot(cv_results$observed, cv_results$var1.pred, 
#     xlab = "Observed", ylab = "Predicted",
#     main = paste("Observed vs Predicted (RMSE:", round(rmse, 2), ")"))
#abline(0, 1, col = "red")

