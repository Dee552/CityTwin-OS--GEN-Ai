import networkx as nx

def load_graph():
    G = nx.Graph()

    G.add_edge("A", "B", traffic=50, capacity=100)
    G.add_edge("B", "C", traffic=60, capacity=100)
    G.add_edge("C", "D", traffic=70, capacity=100)
    G.add_edge("A", "D", traffic=40, capacity=100)

    return G


def simulate_closure(G):
    G_sim = G.copy()
    edges = list(G_sim.edges())

    if edges:
        edge = edges[0]
        G_sim.remove_edge(edge[0], edge[1])

    for u, v, data in G_sim.edges(data=True):
        data['traffic'] += 20

    return G_sim


def increase_traffic(G):
    G_sim = G.copy()
    for u, v, data in G_sim.edges(data=True):
        data['traffic'] += 30
    return G_sim


def total_traffic(G):
    return sum([data['traffic'] for _, _, data in G.edges(data=True)])