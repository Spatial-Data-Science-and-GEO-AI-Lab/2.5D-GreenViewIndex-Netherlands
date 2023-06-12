# linestring process
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import LineString, MultiPoint
import numpy as np
import warnings
import os
os.environ['GDAL_DATA'] = r'C:\Users\Ondrej\.conda\envs\ssml\Library\share\gdal' #change according to your environment

# pbf converter
import osmium
import pandas as pd
import geopandas as gpd
import shapely.wkb as wkblib

# dsm downloaded
import os
import requests
import zipfile
import tempfile
import rasterio
from rasterio.merge import merge as merge_tiffs


def resample_raster(input_file, output_file, scale_factor):
    """downsamples a tif images based on a specified scale
    factor

    :param input_file: tif file
    :param output_file: tif file name
    :param scale_factor: scale to which it should be downsampled
    """
    with rasterio.open(input_file) as src:
        data = src.read(
            out_shape=(
                src.count,
                int(src.height * src.res[0] / scale_factor),
                int(src.width * src.res[1] / scale_factor)
            ),
            resampling=Resampling.bilinear
        )

        transform = src.transform * src.transform.scale(
            (src.width / data.shape[-1]),
            (src.height / data.shape[-2])
        )
        profile = src.profile
        profile.update(transform=transform, width=data.shape[-1], height=data.shape[-2])

        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(data)



def create_binary_tree_map(input_file, output_file, threshold):
    """creates a binary three map (tree T/F) depending on
    the specified threshold of proability (0-100)

    :param input_file: tif file of tree probability of occurance
    :param output_file: tif file of binary tree occurance
    :param threshold: probability of occurance
    """
    with rasterio.open(input_file) as src:
        data = src.read(1)

        # Create a new array with values above the threshold
        new_data = data.copy()
        new_data[new_data <= threshold] = 0
        new_data[new_data > threshold] = 1

        # Use metadata from the input
        meta = src.meta

    with rasterio.open(output_file, 'w', **meta) as dst:
        dst.write(new_data, 1)



def process_linestrings(streets_geom: GeoDataFrame, interval: int):
    """Preprocesses street linestring data
        into point street data
        Parameters:
        streets_geom (GeoDataFrame): Geodataframe containing linestring data as geometry
        interval (int): an integer of an interval to be sampled at in metres
        Returns:
        Geodataframe: sampled points at a specified interval
        """
    sampled_points = []
    length_meters = streets_geom.length
    length_numeric = length_meters.astype(float)

    def process_single_linestring(i):
        if length_numeric[i] < 50:
            point = streets_geom.geometry[i].centroid
            sampled_points.append(point)
        else:
            line = streets_geom.geometry[i]
            num_points = int(line.length / 50) + 1
            distances = np.linspace(0, line.length, num=num_points)
            points = [line.interpolate(distance) for distance in distances]
            sampled_points.extend(points)

    _ = [process_single_linestring(i) for i in range(len(streets_geom))]

    sampled_gdf = gpd.GeoSeries(sampled_points)
    # sampled_gdf = gpd.GeoDataFrame(geometry=sampled_points)

    return sampled_gdf




class StreetsHandler(osmium.SimpleHandler):
    """The class was adapted from https://www.kaggle.com/code/maxim75/osm-osmium/notebook.
    It converts a pbf file into a Geodataframe"""
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.num_nodes = 0
        self.num_relations = 0
        self.num_ways = 0
        self.street_relations = []
        self.street_relation_members = []
        self.street_ways = []
        # A global factory that creates WKB from a osmium geometry
        self.wkbfab = osmium.geom.WKBFactory()

    def way(self, w):
        if w.tags.get("highway") is not None and w.tags.get("name") is not None:
            try:
                wkb = self.wkbfab.create_linestring(w)
                geo = wkblib.loads(wkb, hex=True)
            except:
                return
            row = { "w_id": w.id, "geo": geo }

            for key, value in w.tags:
                row[key] = value

            self.street_ways.append(row)
            self.num_ways += 1




def download_tiles(input_file, working_dir):
    """downloads DSM or DTM tiles based on urls that can be
    found on https://www.pdok.nl/
    :param input_file: directory to txt file with url links to tiles
    :param working_dir: saving directory
    :return:
    """
    with open(input_file, 'r') as f:
        tile_urls = f.read().splitlines()

    os.makedirs(working_dir, exist_ok=True) # create new directory if doesn't exist
    total_tiles = len(tile_urls)
    downloaded_tiles = 0

    # loop through each url link
    for url in tile_urls:
        file_name = url.split('/')[-1]
        output_path = os.path.join(working_dir, file_name)
        response = requests.get(url)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        downloaded_tiles += 1
        print(f"Progress: {downloaded_tiles}/{total_tiles}")




def extract_files(working_dir, output_dir):
    """ unzips tiles into the output directory, while
    deleting the zip files
    :param working_dir: directory with zip files of tiles
    :param output_dir: saving directory
    :return:
    """
    os.makedirs(output_dir, exist_ok=True)

    extracted_files = []

    for file in os.listdir(working_dir):
        if zipfile.is_zipfile(os.path.join(working_dir, file)):
            with zipfile.ZipFile(os.path.join(working_dir, file)) as zf:
                zf.extractall(output_dir)
                print("Extracted files from:", file)
                extracted_files.append(zf)

    for zf in extracted_files:
        zf.close()

    print("Files extracted and saved to:", output_dir)




def merge_tif_files(extracted_dir, output_dir, filename):
    """
    merges tif tiles into one large file
    :param extracted_dir: tiles in tif format
    :param output_dir: saving directory
    :param filename: string name
    :return:
    """
    os.makedirs(output_dir, exist_ok=True)

    tif_files = []
    for root, dirs, files in os.walk(extracted_dir):
        tif_files += [os.path.join(root, file) for file in files if file.endswith('.TIF')]

    src_files = [rasterio.open(tif_file) for tif_file in tif_files]
    merged, out_trans = merge_tiffs(src_files)
    output_file = os.path.join(output_dir, f'{filename}_merged.tif')
    output_file = os.path.normpath(output_file)

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




def process_files(input_file, output_dir, filename):
    """ creates a pipeline for downlading, extracting and
    merging tif files
    :param input_file: directory to txt file with url links to tiles
    :param output_dir: saving directory
    :param filename: string name
    :return:
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        download_tiles(input_file, temp_dir)
        extract_files(temp_dir, output_dir)
        merge_tif_files(output_dir, output_dir, filename)


