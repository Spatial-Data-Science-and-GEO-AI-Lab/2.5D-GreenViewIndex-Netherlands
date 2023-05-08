remotes::install_git("https://github.com/STBrinkmann/GVI")
install.packages("terra")


library(terra)
library(sf)
library(sfheaders)
library(GVI)
library(raster)
library(tidyverse)
install.packages('rasterVis')
library(rasterVis)

DEM_tmp <- raster("DTM_sample.tif")
DSM_tmp <- raster("DSM_merged_sample.tif")
GS_tmp <- raster("20200629_gm_Bomenkaart_v2_resampled_sample.tif")

# Load raster objects
DEM <- rast(DEM_tmp)
DSM <- rast(DSM_tmp)
GreenSpace <- rast(GS_tmp)

# check if greenspace is 0,1 
unique(GreenSpace[])

# assign crs
terra::crs(DSM) <- "EPSG:28992"
terra::crs(DEM) <- "EPSG:28992"
terra::crs(GreenSpace) <- "EPSG:28992"


# Get XY-coordinates
xy_coords <- xyFromCell(GreenSpace, which(values(GreenSpace) >= 0)) %>% 
  as_tibble()

# Convert to shapefile
greenspace_sf <- st_as_sf(xy_coords, coords = c("x", "y"), crs = crs(GreenSpace))


# Set cores 
cores <- 22
utrecht_vgvi <- vgvi_from_sf(observer = greenspace_sf,
                               dsm_rast = DSM, 
                               dtm_rast = DEM, 
                               greenspace_rast = GreenSpace,
                               max_distance = 550, observer_height = 1.7,
                               raster_res = 5,
                               m = 1, b = 3, mode = "exponential",
                               cores = cores, 
                               progress = TRUE)


# Create AOI shapefile
aoi <- GreenSpace >= 0
aoi <- sf::st_as_sf(terra::as.polygons(aoi))

# Convert VGVI to raster format
vgvi_idw <- GVI::sf_to_rast(observer = utrecht_vgvi, v = "VGVI",
                            aoi = aoi,
                            max_distance = 400, n = 10,
                            raster_res = 5, beta = 2,
                            cores = 22, progress = TRUE)


# Plot the VGVI raster
levelplot(vgvi_idw, margin = FALSE,
          at = seq(0, 1, length.out = 101),
          col.regions = colorRampPalette(c("darkgreen", "yellow", "red")),
          main = "VGVI", xlab = "Longitude", ylab = "Latitude")



