import osmnx as ox

print("Downloading road network...")

G = ox.graph_from_place("Chennai, India", network_type="drive")

ox.save_graphml(G, filepath="../data/roads.graphml")

print("Saved to data/roads.graphml ✅")