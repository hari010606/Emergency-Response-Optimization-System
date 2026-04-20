from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
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
active_dispatches = {}


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
    print(f"DEBUG: source_node={source_node}, target_node={target_node}")

    # Trivial case: ambulance and incident map to the same graph node
    if source_node == target_node:
        route = [[amb["lat"], amb["lng"]], [incident["lat"], incident["lng"]]]
        distance_m = 0.0
    else:
        cached = cache_get(source_node, target_node)
        if cached is not None:
            route = cached["coords"]
            distance_m = cached["distance_m"]
        else:
            route, distance_m = dijkstra(G, source_node, target_node)
            route = [[lat, lng] for (lat, lng) in route]
            cache_set(source_node, target_node, route, distance_m)
    # 6. Update DB — link ambulance to incident, flip statuses
    # Register for simulation — the background task will walk the ambulance along this route
    active_dispatches[amb["id"]] = {
        "route": route,
        "progress": 0,          # index into route
        "incident_id": incident_id,
    }
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

# ──────────────────────────────────────────────────────────────
# Ambulance movement simulation
# ──────────────────────────────────────────────────────────────

async def simulate_ambulance_movement():
    """
    Background task: every 2 seconds, advance each active ambulance
    one step along its route in the database.
    """
    from db import update_ambulance_location  # import here to avoid circular issues

    while True:
        await asyncio.sleep(2)

        # Iterate over a copy because we may mutate the dict during the loop
        for amb_id, info in list(active_dispatches.items()):
            route = info["route"]
            progress = info["progress"]

            # Done — reached the incident
            if progress >= len(route) - 1:
                # Mark ambulance available again and clear the dispatch
                update_ambulance_status(amb_id, "available")
                del active_dispatches[amb_id]
                continue

            # Advance one waypoint along the route
            progress += 1
            lat, lng = route[progress]
            update_ambulance_location(amb_id, lat, lng)
            active_dispatches[amb_id]["progress"] = progress


@app.on_event("startup")
async def start_simulation():
    """Kick off the simulation loop when the server starts."""
    asyncio.create_task(simulate_ambulance_movement())


# ──────────────────────────────────────────────────────────────
# WebSocket endpoint — pushes ambulance positions every 2 seconds
# ──────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            ambulances = get_all_ambulances()
            # Convert to plain list of dicts for JSON — RealDictRow is already dict-like
            payload = json.dumps([dict(a) for a in ambulances])
            await websocket.send_text(payload)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        # Browser closed the connection — nothing to clean up, just exit
        pass