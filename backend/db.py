import psycopg2
from psycopg2.extras import RealDictCursor

# Connection config — hardcoded for now; we'll move to env vars before deploying.
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "emergency_response",
    "user": "postgres",
    "password": "admin",
}


def get_connection():
    """Open a new connection to Postgres. Returns a connection object."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def get_all_ambulances():
    """Return every ambulance as a list of dicts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, lat, lng, status FROM ambulances")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_available_ambulances():
    """Return only ambulances with status='available'."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, lat, lng, status FROM ambulances WHERE status = %s",
        ("available",),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def update_ambulance_status(amb_id, new_status):
    """Change an ambulance's status (e.g. 'available' -> 'en_route')."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE ambulances SET status = %s WHERE id = %s",
        (new_status, amb_id),
    )
    conn.commit()            # writes must be committed; reads don't need this
    cur.close()
    conn.close()


def update_ambulance_location(amb_id, lat, lng):
    """Move an ambulance to new coordinates."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE ambulances SET lat = %s, lng = %s WHERE id = %s",
        (lat, lng, amb_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def create_incident(lat, lng, priority=1):
    """Insert a new incident. Returns the new incident's id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO incidents (lat, lng, priority) VALUES (%s, %s, %s) RETURNING id",
        (lat, lng, priority),
    )
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return new_id


def assign_ambulance_to_incident(incident_id, amb_id):
    """Link an ambulance to an incident and mark both as dispatched/en_route."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE incidents SET dispatched_amb_id = %s, status = %s WHERE id = %s",
        (amb_id, "dispatched", incident_id),
    )
    cur.execute(
        "UPDATE ambulances SET status = %s WHERE id = %s",
        ("en_route", amb_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_active_incidents():
    """Return all incidents that aren't resolved yet."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, lat, lng, priority, status, dispatched_amb_id, reported_at "
        "FROM incidents WHERE status != %s",
        ("resolved",),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# Quick self-test — runs only if you execute `python db.py` directly.
if __name__ == "__main__":
    print("Testing db.py...\n")

    ambs = get_all_ambulances()
    print(f"Total ambulances: {len(ambs)}")
    print(f"First ambulance: {ambs[0]}\n")

    available = get_available_ambulances()
    print(f"Available ambulances: {len(available)}\n")

    print("Creating a test incident at (13.0827, 80.2707)...")
    inc_id = create_incident(13.0827, 80.2707, priority=2)
    print(f"Created incident id={inc_id}\n")

    active = get_active_incidents()
    print(f"Active incidents: {len(active)}")
    print(f"Latest incident: {active[-1]}")