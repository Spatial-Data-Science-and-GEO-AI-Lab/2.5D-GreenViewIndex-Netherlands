import osmnx as ox
from typing import Union

def street_cities(cities: Union[str, list], epsg_code: str):
    """
    Downloads street data and converts them into a specified
    epsg projection

    :param cities: one or multiple cities for download
    :return: a Geodataframe of the city's streets and its types
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

        # progress
        progress = f"{i+1}/{total_cities}"
        print(f"Processing city {city} ({progress})")

    return all_gdf_edges



