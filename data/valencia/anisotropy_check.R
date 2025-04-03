# Load necessary libraries
library(gstat)
library(sp)
library(ggplot2)
library(automap)

# Load the dataset
data <- read_csv("data_netatmo.csv")

# Remove missing values
data <- na.omit(data)
head(data)

# Convert data frame to spatial points
coordinates(data) <- ~ lon + lat
proj4string(data) <- CRS("+proj=longlat +datum=WGS84")

# Compute directional variograms (0°, 45°, 90°, 135°)
variogram_0   <- variogram(temp_diff ~ 1, data, alpha = 0)    # East-West
variogram_45  <- variogram(temp_diff ~ 1, data, alpha = 45)   # NE-SW
variogram_90  <- variogram(temp_diff ~ 1, data, alpha = 90)   # North-South
variogram_135 <- variogram(temp_diff ~ 1, data, alpha = 135)  # NW-SE

# Plot directional variograms to check for anisotropy
ggplot() +
  geom_line(data = variogram_0, aes(dist, gamma, color = "0° (E-W)")) +
  geom_line(data = variogram_45, aes(dist, gamma, color = "45° (NE-SW)")) +
  geom_line(data = variogram_90, aes(dist, gamma, color = "90° (N-S)")) +
  geom_line(data = variogram_135, aes(dist, gamma, color = "135° (NW-SE)")) +
  labs(title = "Directional Variograms", x = "Distance", y = "Semivariance") +
  theme_minimal() +
  scale_color_manual(name = "Direction",
                     values = c("0° (E-W)" = "red",
                                "45° (NE-SW)" = "blue",
                                "90° (N-S)" = "green",
                                "135° (NW-SE)" = "purple"))

# Check if the range (distance at which variogram reaches sill) differs by direction.
# If range varies significantly, anisotropy is present.

# Fit an anisotropic variogram model
anisotropic_model <- vgm(
  psill = 1, model = "Exp",
  range = 4,  # Set a single range value (for the major axis)
  nugget = 0.1,
  anis = c(45, 0.5)  # 45° anisotropy direction, 0.5 = minor range / major range
)


# Fit the anisotropic variogram to the data
anisotropic_fit <- fit.variogram(variogram(temp_diff ~ 1, data), anisotropic_model)

# Plot the fitted anisotropic variogram
plot(variogram(temp_diff ~ 1, data), anisotropic_fit, main = "Anisotropic Variogram Fit")
