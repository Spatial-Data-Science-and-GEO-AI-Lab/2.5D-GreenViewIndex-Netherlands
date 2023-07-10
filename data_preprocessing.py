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

def resample_raster(input_file, output_file, scale_factor):
    """downsamples/upsample a tif images based on a specified scale
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



def split_raster(min_x, max_x, min_y, max_y):
    # splits raster into 10 tiles

    # calculate the x and y range for each tile
    x_range = (max_x - min_x) / 5
    y_range = (max_y - min_y) / 2

    tiles = []
    for i in range(2):
        for j in range(5):
            tile = {
                "min_x": min_x + (j * x_range),
                "max_x": min_x + ((j + 1) * x_range),
                "min_y": min_y + (i * y_range),
                "max_y": min_y + ((i + 1) * y_range)
            }
            tiles.append(tile)

    return tiles

import os
from rasterio import features
from rasterio.enums import Resampling

def split_and_crop_raster(raster, tiles, output_folder):
    # Create the folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cropped_tiles = []

    for i, tile in enumerate(tiles):
        extent = [tile['min_x'], tile['min_y'], tile['max_x'], tile['max_y']]
        out_transform, out_width, out_height = rasterio.warp.calculate_default_transform(raster.crs, raster.crs,
                                                                                         raster.width, raster.height,
                                                                                         *extent)
        kwargs = raster.meta.copy()
        kwargs.update({
            'crs': raster.crs,
            'transform': out_transform,
            'width': out_width,
            'height': out_height
        })
        cropped_raster = raster.read(window=rasterio.windows.from_bounds(*extent, transform=raster.transform))
        output_file = os.path.join(output_folder, f'cropped_tile_{i+1}.tif')
        with rasterio.open(output_file, 'w', **kwargs) as dst:
            dst.write(cropped_raster)

        cropped_tiles.append(cropped_raster)

    return cropped_tiles



# Example usage
min_x = 11852.3000565225
max_x = 276473.901609599
min_y = 308697.286021537
max_y = 639284.464773071

netherlands_tiles = split_raster(min_x, max_x, min_y, max_y)
print(netherlands_tiles)
