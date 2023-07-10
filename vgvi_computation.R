
# install relevant packages if missing
suppressWarnings({
  install.packages("remotes")
  remotes::install_git("https://github.com/STBrinkmann/GVI")
  install.packages("terra", repos = "http://cran.us.r-project.org")
  install.packages("rasterVis", repos = "http://cran.us.r-project.org")
  install.packages("leaflet")
  install.packages("sf")
  install.packages("sfheaders")
  install.packages("raster")
  install.packages("tidyverse")
  install.packages("ggplot2")
})

suppressWarnings({
  library(leaflet)
  library(leaflet.extras)
  library(terra)
  library(sf)
  library(sfheaders)
  library(GVI)
  library(raster)
  library(tidyverse)
  library(rasterVis)
  library(ggplot2)
  library(dplyr)
})



compute_vgvi <- function(sampled_points_file, dsm_cropped_directory, dtm_cropped_directory, grn_cropped_directory, output_file, parameters) {
  
  library(sf)
  library(raster)
  
  # Read sampled points file
  sampled_points <- st_read(sampled_points_file)
  
  # Extract XY-coordinates of street vertices
  xy_coords <- st_coordinates(sampled_points) %>% as_tibble()
  colnames(xy_coords) <- c("x", "y")
  
  # Convert tibble to an sf object
  ned_5m_sf <- st_as_sf(xy_coords, coords = c("x", "y"), crs = 28992)
  
  # Set cores
  cores <- 10
  
  # List of files in the directory
  cropped_files_dsm <- list.files(dsm_cropped_directory, pattern = "^cropped_tile_\\d+\\.tif$", full.names = TRUE)
  cropped_files_dtm <- list.files(dtm_cropped_directory, pattern = "^cropped_tile_\\d+\\.tif$", full.names = TRUE)
  cropped_files_grn <- list.files(grn_cropped_directory, pattern = "^cropped_tile_\\d+\\.tif$", full.names = TRUE)
  
  # Empty list to store gvi data after iterations
  gvi_results <- list()
  
  # Loop through each cropped raster file
  for (i in 1:length(cropped_files_dsm)) {
    # cropped_dsm <- raster(cropped_files_dsm[i])
    # cropped_dtm <- raster(cropped_files_dtm[i])
    # cropped_grn <- raster(cropped_files_grn[i])
    
    # Convert raster objects to SpatRaster objects
    cropped_dsm <- raster(cropped_files_dsm[i])
    cropped_dtm <- raster(cropped_files_dtm[i])
    cropped_grn <- raster(cropped_files_grn[i])
    
    # Set the CRS 
    crs(cropped_dsm) <- "EPSG:28992"
    crs(cropped_dtm) <- "EPSG:28992"
    crs(cropped_grn) <- "EPSG:28992"
    
    # Compute VGVI using the cropped rasters with custom parameters
    vgvi_result <- vgvi_from_sf(observer = ned_5m_sf,
                                dsm_rast = cropped_dsm,
                                dtm_rast = cropped_dtm,
                                greenspace_rast = cropped_grn,
                                max_distance = parameters$max_distance,
                                observer_height = parameters$observer_height,
                                raster_res = parameters$raster_res,
                                m = parameters$m, b = parameters$b,
                                mode = parameters$mode,
                                cores = cores,
                                progress = TRUE)
    
    # Store the VGVI result in the list
    gvi_results[[i]] <- vgvi_result
  }
  
  # Combine the results from all tiles
  ned_vgvi <- do.call(rbind, gvi_results)
  
  # Write the results to a CSV file
  write.csv(ned_vgvi, output_file, row.names = FALSE)
}


parameters <- list(
  max_distance = 300,
  observer_height = 1.7,
  raster_res = 5,
  m = 1,
  b = 3,
  mode = "exponential"
)

compute_vgvi("data_collection/street_data/sampled_points_ned_indexed.gpkg",
                    "data_collection/tiles/DSM_10_tiles",
                    "data_collection/tiles/DTM_10_tiles",
                    "data_collection/tiles/Greeness_10_tiles",
                    "data_collection/tiles/ned_vgvi.csv",
                    parameters)