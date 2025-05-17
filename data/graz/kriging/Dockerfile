# Base R image with geospatial support
FROM rocker/geospatial:latest

# Set working directory
WORKDIR /app

# Copy the R script and data folder
COPY . .

# Install required R packages
RUN R -e "install.packages(c('gstat', 'raster', 'caret', 'automap', 'ggpubr', 'spdep'))"

# Run the R script
CMD ["Rscript", "kriging.R"]
