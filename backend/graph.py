import heapq
import osmnx as ox


def dijkstra(G, source, target):
    """
    Shortest path from source to target in an osmnx MultiDiGraph.
    Returns (coords, distance_m) where coords is a list of (lat, lng) tuples.
    """
    dist = {node: float('inf') for node in G.nodes}
    dist[source] = 0
    prev = {}
    pq = [(0, source)]

    while pq:
        d, u = heapq.heappop(pq)

        # Stale-entry check.
        if d > dist[u]:
            continue

        # Early exit: target's distance is now finalized.
        if u == target:
            break

        for v, edge_data in G[u].items():
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

    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
    return coords, dist[target]


# ──────────────────────────────────────────────────────────────
# Smoke test — only runs when you execute `python graph.py` directly.
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading Chennai road network...")
    G = ox.graph_from_place("Chennai, India", network_type="drive")
    print(f"Done! Nodes: {len(G.nodes)}, Edges: {len(G.edges)}\n")

    source_lat, source_lng = 13.0827, 80.2707
    target_lat, target_lng = 13.0067, 80.2206

    source_node = ox.distance.nearest_nodes(G, source_lng, source_lat)
    target_node = ox.distance.nearest_nodes(G, target_lng, target_lat)

    print(f"Source node: {source_node}")
    print(f"Target node: {target_node}")

    coords, distance = dijkstra(G, source_node, target_node)
    print(f"\nPath has {len(coords)} points")
    print(f"Total distance: {distance:.0f} metres ({distance/1000:.2f} km)")
    print(f"First 3 coords: {coords[:3]}")
    print(f"Last 3 coords: {coords[-3:]}")