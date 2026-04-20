from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import osmnx as ox

from graph import dijkstra
from dispatch import find_nearest_ambulance, rank_ambulances
from cache import get_route as cache_get, set_route as cache_set
from db import (
    get_all_ambulances,
    get_available_ambulances,
    create_incident,
    assign_ambulance_to_incident,
    get_active_incidents,
    update_ambulance_status,
)


# ──────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────

app = FastAPI(title="Emergency Response API")

# CORS — allow your React frontend (running on a different port) to call this API.
# In production you'd restrict to specific origins; for dev, allow all.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Load the Chennai graph once at startup
# ──────────────────────────────────────────────────────────────

print("Loading Chennai road network (one-time)...")
G = ox.graph_from_place("Chennai, India", network_type="drive")
print(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")


# ──────────────────────────────────────────────────────────────
# Pydantic models — the shape of request/response bodies
# ──────────────────────────────────────────────────────────────

class IncidentRequest(BaseModel):
    lat: float
    lng: float
    priority: int = 1


class DispatchResponse(BaseModel):
    incident_id: int
    ambulance_id: int
    ambulance_name: str
    route: list          # list of [lat, lng] pairs
    distance_m: float
    num_waypoints: int


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Emergency Response API is running"}


@app.get("/ambulances")
async def list_ambulances():
    """Return all ambulances and their current status."""
    return get_all_ambulances()


@app.get("/incidents")
async def list_incidents():
    """Return all active (non-resolved) incidents."""
    return get_active_incidents()


@app.post("/incident")
async def report_incident(incident: IncidentRequest):
    """Create a new incident. Returns the new incident's id."""
    new_id = create_incident(incident.lat, incident.lng, incident.priority)
    return {"incident_id": new_id, "lat": incident.lat, "lng": incident.lng}


@app.post("/dispatch/{incident_id}", response_model=DispatchResponse)
async def dispatch(incident_id: int):
    """
    Dispatch the nearest available ambulance to the given incident.
    Runs: find-nearest → cache check → Dijkstra → DB update → return route.
    """
    # 1. Find the incident in the DB
    active = get_active_incidents()
    incident = next((i for i in active if i["id"] == incident_id), None)
    if incident is None:
        raise HTTPException(404, f"Incident {incident_id} not found or already resolved")

    # 2. Find the nearest available ambulance
    amb = find_nearest_ambulance(incident["lat"], incident["lng"])
    if amb is None:
        raise HTTPException(503, "No ambulances available")

    # 3. Map ambulance and incident coordinates to graph nodes
    source_node = ox.distance.nearest_nodes(G, amb["lng"], amb["lat"])
    target_node = ox.distance.nearest_nodes(G, incident["lng"], incident["lat"])

    # 4. Check Redis cache first
    cached = cache_get(source_node, target_node)
    if cached is not None:
        route = cached
        # Approximate distance from cached route — we lose the exact meters
        # unless we also cache the distance. For now, recompute on miss only.
        distance_m = 0.0  # placeholder; fine for now
    else:
        # 5. Cache miss — run Dijkstra
        route, distance_m = dijkstra(G, source_node, target_node)
        # Convert tuples to lists for JSON
        route = [[lat, lng] for (lat, lng) in route]
        cache_set(source_node, target_node, route)

    # 6. Update DB — link ambulance to incident, flip statuses
    assign_ambulance_to_incident(incident_id, amb["id"])

    return DispatchResponse(
        incident_id=incident_id,
        ambulance_id=amb["id"],
        ambulance_name=amb["name"],
        route=route,
        distance_m=distance_m,
        num_waypoints=len(route),
    )


@app.post("/ambulance/{amb_id}/available")
async def mark_available(amb_id: int):
    """Mark an ambulance back as available (e.g. after dropoff)."""
    update_ambulance_status(amb_id, "available")
    return {"ambulance_id": amb_id, "status": "available"}