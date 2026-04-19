import heapq
import osmnx as ox

print("Loading Chennai road network...")
G = ox.graph_from_place("Chennai, India", network_type="drive")
print(f"Done! Nodes: {len(G.nodes)}, Edges: {len(G.edges)}\n")


def dijkstra(G, source, target):
    # Table 1: shortest known distance to every node (∞ until we find a route).
    dist = {node: float('inf') for node in G.nodes}
    dist[source] = 0

    # Table 2: who each node came from on its best path so far.
    prev = {}

    # Min-heap of (distance, node) pairs. Smallest distance pops first.
    pq = [(0, source)]

    while pq:
        d, u = heapq.heappop(pq)

        # Stale-entry check — see note below.
        if d > dist[u]:
            continue

        # Early exit: target's distance is now finalized.
        if u == target:
            break

        # Relax every outgoing edge from u.
        for v, edge_data in G[u].items():
            # osmnx MultiDiGraph: pick the shortest of any parallel edges.
            edge_len = min(e['length'] for e in edge_data.values())

            alt = dist[u] + edge_len
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                heapq.heappush(pq, (alt, v))

    # Walk prev backwards from target to reconstruct the path.
    path, node = [], target
    while node in prev:
        path.append(node)
        node = prev[node]
    path.append(source)
    path.reverse()

    # Convert node IDs to (lat, lng) pairs for the frontend.
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
    return coords, dist[target]


# Smoke test — two points in Chennai.
source_lat, source_lng = 13.0827, 80.2707    # central Chennai
target_lat, target_lng = 13.0067, 80.2206    # further southwest

source_node = ox.distance.nearest_nodes(G, source_lng, source_lat)
target_node = ox.distance.nearest_nodes(G, target_lng, target_lat)

print(f"Source node: {source_node}")
print(f"Target node: {target_node}")

coords, distance = dijkstra(G, source_node, target_node)
print(f"\nPath has {len(coords)} points")
print(f"Total distance: {distance:.0f} metres ({distance/1000:.2f} km)")
print(f"First 3 coords: {coords[:3]}")
print(f"Last 3 coords: {coords[-3:]}")