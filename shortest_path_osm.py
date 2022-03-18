import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from shapely import wkt


# Nanyang Polytechnic
origin = gpd.GeoDataFrame(
    columns=['name', 'geometry'], crs=4326, geometry='geometry')
origin.at[0, 'geometry'] = Point(103.8490994, 1.3800986)
origin.at[0, 'name'] = 'Nanyang Polytechnic'

origin


# Ang Mo Kio Interchange

destination = gpd.GeoDataFrame(
    columns=['name', 'geometry'], crs=4326, geometry='geometry')
destination.at[0, 'geometry'] = Point(103.7856, 1.4429)
destination.at[0, 'name'] = 'Republic Polytechnic'
destination


def shortest_path_map(origin, destination, network='drive'):
    '''origin and destination <geodataframe> crs 4326, network <str> drive, bike, walk
    return map including origins, destinations, shortest path and network
    '''

    # creating a frame for fetching OSM data
    combined = origin.append(destination)

    convex = combined.unary_union.convex_hull

    graph_extent = convex.buffer(0.02)

    # fetching graph
    graph = ox.graph_from_polygon(graph_extent, network_type=network)

    # Reproject the graph
    graph_proj = ox.project_graph(graph)

    # Get the GeoDataFrame
    edges = ox.graph_to_gdfs(graph_proj, nodes=False)

    # Get CRS info UTM
    CRS = edges.crs

    # Reproject all data
    origin_proj = origin.to_crs(crs=CRS)
    destination_proj = destination.to_crs(crs=CRS)

    # routes of shortest path
    routes = gpd.GeoDataFrame()

    # Get nodes from the graph
    nodes = ox.graph_to_gdfs(graph_proj, edges=False)

    # Iterate over origins and destinations
    for oidx, orig in origin_proj.iterrows():

        # Find closest node from the graph --> point = (latitude, longitude)
        closest_origin_node = ox.get_nearest_node(G=graph_proj, point=(
            orig.geometry.y, orig.geometry.x), method='euclidean')

        # Iterate over targets
        for tidx, target in destination_proj.iterrows():
            # Find closest node from the graph --> point = (latitude, longitude)
            closest_target_node = ox.get_nearest_node(graph_proj, point=(
                target.geometry.y, target.geometry.x), method='euclidean')

            # Check if origin and target nodes are the same --> if they are --> skip
            if closest_origin_node == closest_target_node:
                print("Same origin and destination node. Skipping ..")
                continue

            # Find the shortest path between the points
            route = nx.shortest_path(graph_proj,
                                     source=closest_origin_node,
                                     target=closest_target_node, weight='length')

            # Extract the nodes of the route
            route_nodes = nodes.loc[route]

            # Create a LineString out of the route
            path = LineString(list(route_nodes.geometry.values))

            # Append the result into the GeoDataFrame
            routes = routes.append([[path]], ignore_index=True)

    # Add a column name
    routes.columns = ['geometry']

    # Set geometry
    routes = routes.set_geometry('geometry')

    # Set coordinate reference system
    routes.crs = nodes.crs

    plt.style.use('seaborn')

    # Plot
    ax = edges.plot(figsize=(16, 10), color='gray', linewidth=0.5, alpha=0.7)
    ax = origin_proj.plot(ax=ax, color='red')
    ax = destination_proj.plot(ax=ax, color='blue')
    ax = routes.plot(ax=ax, linewidth=3, alpha=0.8, color='magenta')

    plt.axis('off')

    return ax


shortest_path_map(origin, destination)
plt.savefig('shortest_path.png')
