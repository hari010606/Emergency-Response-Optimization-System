import redis
import json

# Connect to Redis/Memurai running on localhost.
# decode_responses=True makes get() return str instead of bytes — easier to work with.
r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def get_route(source_node, target_node):
    """
    Try to fetch a cached route between two graph nodes.
    Returns the list of [lat, lng] pairs, or None if not cached.
    """
    key = f"route:{source_node}:{target_node}"
    cached = r.get(key)
    if cached is None:
        return None
    return json.loads(cached)


def set_route(source_node, target_node, coords, ttl=600):
    """
    Store a route in the cache with a 10-minute TTL (default).
    coords is a list of (lat, lng) pairs.
    """
    key = f"route:{source_node}:{target_node}"
    r.setex(key, ttl, json.dumps(coords))


def clear_all_routes():
    """Delete every route key — useful during development."""
    for key in r.scan_iter("route:*"):
        r.delete(key)


# Self-test — runs only when you execute `python cache.py` directly.
if __name__ == "__main__":
    print("Testing cache.py...\n")

    # Test 1: miss on an empty cache
    result = get_route(111, 222)
    print(f"Fetch before set: {result}  (should be None)")

    # Test 2: store and retrieve
    fake_coords = [(13.0827, 80.2707), (13.0828, 80.2708), (13.0830, 80.2710)]
    set_route(111, 222, fake_coords)
    print(f"Stored route of {len(fake_coords)} points.")

    retrieved = get_route(111, 222)
    print(f"Fetched after set: {retrieved}")
    print(f"Round-trip matches: {retrieved == [list(c) for c in fake_coords]}")

    # Test 3: check the key exists and has a TTL
    ttl = r.ttl("route:111:222")
    print(f"TTL on the key: {ttl} seconds  (should be ~600)")

    # Cleanup
    clear_all_routes()
    print("\nCleaned up test keys.")