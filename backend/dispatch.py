import heapq
from db import get_available_ambulances


def find_nearest_ambulance(incident_lat, incident_lng):
    """
    Pick the nearest available ambulance to the incident.
    Returns the ambulance dict (id, name, lat, lng, status), or None if no
    ambulances are available.
    """
    available = get_available_ambulances()
    if not available:
        return None

    heap = []
    for amb in available:
        # Squared straight-line distance. No sqrt — we only need ranking.
        dist_sq = (amb["lat"] - incident_lat) ** 2 + (amb["lng"] - incident_lng) ** 2
        heapq.heappush(heap, (dist_sq, amb["id"], amb))
        #                      ↑ primary sort key (distance)
        #                                ↑ tie-breaker (unique id, avoids dict comparison)
        #                                        ↑ the actual payload we want back

    _, _, nearest = heapq.heappop(heap)
    return nearest


def rank_ambulances(incident_lat, incident_lng, k=None):
    """
    Return all available ambulances ranked by straight-line distance.
    If k is given, return only the top-k. Useful for showing 'nearest 3' in the UI.
    """
    available = get_available_ambulances()
    if not available:
        return []

    heap = []
    for amb in available:
        dist_sq = (amb["lat"] - incident_lat) ** 2 + (amb["lng"] - incident_lng) ** 2
        heapq.heappush(heap, (dist_sq, amb["id"], amb))

    n = k if k is not None else len(heap)
    result = []
    for _ in range(min(n, len(heap))):
        _, _, amb = heapq.heappop(heap)
        result.append(amb)
    return result


# Self-test
if __name__ == "__main__":
    print("Testing dispatch.py...\n")

    # Incident at Egmore (13.0827, 80.2707) — should dispatch AMB-01 (same spot)
    inc_lat, inc_lng = 13.0827, 80.2707
    print(f"Incident at ({inc_lat}, {inc_lng}) — Egmore")
    nearest = find_nearest_ambulance(inc_lat, inc_lng)
    print(f"Nearest: {nearest['name']} at ({nearest['lat']}, {nearest['lng']})\n")

    # Incident at Velachery (12.9801, 80.2209) — should dispatch AMB-13 (same spot)
    inc_lat, inc_lng = 12.9801, 80.2209
    print(f"Incident at ({inc_lat}, {inc_lng}) — Velachery")
    nearest = find_nearest_ambulance(inc_lat, inc_lng)
    print(f"Nearest: {nearest['name']} at ({nearest['lat']}, {nearest['lng']})\n")

    # Incident at Tambaram (12.95, 80.15) — should dispatch AMB-14 or AMB-15
    inc_lat, inc_lng = 12.9500, 80.1500
    print(f"Incident at ({inc_lat}, {inc_lng}) — Tambaram")
    top3 = rank_ambulances(inc_lat, inc_lng, k=3)
    print(f"Top 3 nearest:")
    for i, amb in enumerate(top3, 1):
        print(f"  {i}. {amb['name']} at ({amb['lat']}, {amb['lng']})")