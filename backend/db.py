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

def reset_active_dispatches():
    """
    Full reset to seed state:
    - All ambulances: status='available' + restored to original seed coordinates
    - All incidents: status='resolved'
    """
    conn = get_connection()
    cur = conn.cursor()

    # Reset statuses
    cur.execute("UPDATE ambulances SET status = 'available'")
    cur.execute("UPDATE incidents SET status = 'resolved'")

    conn.commit()
    cur.close()
    conn.close()

# Original seed coordinates (keep in sync with your SQL seed data)
SEED_POSITIONS = [
    (1, 13.0827, 80.2707), (2, 13.0604, 80.2496), (3, 13.0418, 80.2341),
    (4, 13.0732, 80.2609), (5, 13.0878, 80.2785), (6, 13.1143, 80.2899),
    (7, 13.1231, 80.2156), (8, 13.1067, 80.2847), (9, 13.1389, 80.2619),
    (10, 13.1604, 80.3012), (11, 13.0067, 80.2206), (12, 13.0012, 80.2565),
    (13, 12.9801, 80.2209), (14, 12.9516, 80.1434), (15, 12.9249, 80.1000),
    (16, 12.9010, 80.2279), (17, 13.0499, 80.2824), (18, 13.0878, 80.2925),
    (19, 13.0389, 80.2619), (20, 12.9698, 80.2494), (21, 13.0732, 80.1895),
    (22, 13.0495, 80.1821), (23, 13.0846, 80.1765), (24, 13.0379, 80.1565),
    (25, 13.0923, 80.1715), (26, 13.0850, 80.2101), (27, 13.0948, 80.2294),
    (28, 13.1185, 80.2043), (29, 12.8996, 80.2209), (30, 13.1982, 80.3192),
    (31, 12.8340, 80.0437), (32, 13.0098, 80.0585), (33, 13.1760, 80.1370),
    (34, 13.0143, 80.1761), (35, 12.9467, 80.1879),
]


def reset_ambulance_positions():
    """Restore all ambulances to their original seed coordinates."""
    conn = get_connection()
    cur = conn.cursor()
    for amb_id, lat, lng in SEED_POSITIONS:
        cur.execute(
            "UPDATE ambulances SET lat = %s, lng = %s WHERE id = %s",
            (lat, lng, amb_id),
        )
    conn.commit()
    cur.close()
    conn.close()


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