import osmnx as ox
from typing import Union
import os
import zipfile
import requests
import rasterio
from rasterio.merge import merge as merge_tiffs
import tempfile
import sys

# FUNCTION to download street data
# Note: limited to small spatial extents (cities, small regions), for country-level extraction use pyrosm package

def street_cities(cities: Union[str, list], epsg_code: str):
    """
    Downloads street data and converts them into a specified
    epsg projection

    :param cities: one or multiple cities for download
    :param epsg_code: EPSG code for projection
    :return: a list of Geodataframes containing the city's streets and their types
    """
    if isinstance(cities, str):
        cities = [cities]

    all_gdf_edges = []

    # Iterate over cities with progress tracking
    total_cities = len(cities)
    for i, city in enumerate(cities):
        G = ox.graph_from_place(city, network_type="all")
        gdf_edges, _ = ox.graph_to_gdfs(G)
        gdf_edges = gdf_edges.to_crs(f'EPSG:{epsg_code}')
        all_gdf_edges.append(gdf_edges)

        # Progress update
        progress = f"Processing city {city} ({i + 1}/{total_cities})"
        sys.stdout.write('\r' + progress)
        sys.stdout.flush()

    return all_gdf_edges


# PIPELINE to download dsm/dtm data

def download_tiles(input_file, working_dir):
    """Downloads DSM or DTM tiles based on urls that can be
    found on https://www.pdok.nl/

    :param input_file: path to a text file with URL links to tiles
    :param working_dir: directory for saving the downloaded tiles
    """
    with open(input_file, 'r') as f:
        tile_urls = f.read().splitlines()

    os.makedirs(working_dir, exist_ok=True)  # Create the directory if it doesn't exist
    total_tiles = len(tile_urls)
    downloaded_tiles = 0

    # Loop through each URL link
    for url in tile_urls[:5]:
        file_name = url.split('/')[-1]
        output_path = os.path.join(working_dir, file_name)
        response = requests.get(url)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        downloaded_tiles += 1

        # Progress update
        progress = f"Progress tiles downloaded: {downloaded_tiles}/{total_tiles}"
        sys.stdout.write('\r' + progress)
        sys.stdout.flush()

    # Print a newline after the loop is finished
    print()

def extract_files(working_dir, output_dir):
    """Unzips tiles into a new folder 'extracted_tiles
    within the defined output directory

    :param working_dir: directory with zip files of tiles
    :param output_dir: directory for saving the extracted files
    """
    os.makedirs(output_dir, exist_ok=True)
    extract_dir = os.path.join(output_dir, "extracted_tiles")
    os.makedirs(extract_dir, exist_ok=True)

    extracted_files = []

    for file in os.listdir(working_dir):
        if zipfile.is_zipfile(os.path.join(working_dir, file)):
            with zipfile.ZipFile(os.path.join(working_dir, file)) as zf:
                zf.extractall(extract_dir)
                print("Extracted files from:", file)
                extracted_files.append(zf)

    for zf in extracted_files:
        zf.close()

    print("Files extracted and saved to:", extract_dir)


def merge_tif_files(extracted_dir, output_dir, filename):
    """
    Merges extracted tiles of dsm or dtm
    :param extracted_dir:
    :param output_dir:
    :param filename:
    :return:
    """
    os.makedirs(output_dir, exist_ok=True)

    tif_files = []
    for root, dirs, files in os.walk(extracted_dir):
        tif_files += [os.path.join(root, file) for file in files if file.endswith('.tif') or file.endswith('.TIF')]

    if not tif_files:
        print("No valid TIF files found in the extracted directory.")
        return

    src_files = [rasterio.open(tif_file) for tif_file in tif_files]

    merged, out_trans = rasterio.merge.merge(src_files)
    output_file = os.path.join(output_dir, f'{filename}_merged.tif')

    meta = src_files[0].meta
    meta.update({
        "driver": "GTiff",
        "height": merged.shape[1],
        "width": merged.shape[2],
        "transform": out_trans
    })

    with rasterio.open(output_file, "w", **meta) as dst:
        dst.write(merged)

    for src_file in src_files:
        src_file.close()

    print("Merged TIFF file saved to:", output_file)



def download_lidar_data(input_file, output_dir, filename):
    """A that downloads, extracts and merges lidar dsm,
    dtm data from ahn.

    :param input_file: path to a text file with URL links to tiles
    :param output_dir: directory for saving the final merged file
    :param filename: name for the final merged file, must be string and no ending, e.g. 'dtm'
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        download_tiles(input_file, temp_dir)
        extract_files(temp_dir, output_dir)
        merge_tif_files(output_dir, output_dir, filename)




# # Run pipeline
# tiles_dsm = "C:/Users/Ondrej/Archive/2.5D-GreenViewIndex-Netherlands/AHN3/tiles_list_dtm.txt"
# output_dir = "C:/Users/Ondrej/Archive/2.5D-GreenViewIndex-Netherlands/AHN3/"
# download_lidar_data(tiles_dsm, output_dir, 'dtm')
