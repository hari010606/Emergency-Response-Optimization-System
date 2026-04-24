export default function Sidebar({
  ambulances,
  incidents,
  pendingIncident,
  dispatchResult,
  onDispatch,
  onClearPending,
  dispatching,
}) {
  const availableCount = ambulances.filter((a) => a.status === "available").length;
  const enRouteCount = ambulances.filter(
    (a) => a.status === "en_route" || a.status === "dispatched"
  ).length;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>Emergency Response</h1>
        <div className="subtitle">Chennai · {availableCount} available · {enRouteCount} en-route</div>
      </div>

      <div className="sidebar-section">
        <h2>Dispatch</h2>
        {!pendingIncident && !dispatchResult && (
          <div className="empty">Click anywhere on the map to report an incident.</div>
        )}

        {pendingIncident && !dispatchResult && (
          <div className="dispatch-card">
            <div className="label">Incident location</div>
            <div className="coord">
              {pendingIncident.lat.toFixed(5)}, {pendingIncident.lng.toFixed(5)}
            </div>
            <div className="dispatch-actions">
              <button className="primary" onClick={onDispatch} disabled={dispatching}>
                {dispatching ? "Dispatching…" : "Dispatch nearest"}
              </button>
              <button onClick={onClearPending} disabled={dispatching}>Cancel</button>
            </div>
          </div>
        )}

        {dispatchResult && (
          <div className="dispatch-card">
            <div className="row">
              <span className="label">Ambulance</span>
              <span className="value">{dispatchResult.ambulance_name}</span>
            </div>
            <div className="row">
              <span className="label">Distance</span>
              <span className="value">
                {(dispatchResult.distance_m / 1000).toFixed(2)} km
              </span>
            </div>
            <div className="row">
              <span className="label">Waypoints</span>
              <span className="value">{dispatchResult.num_waypoints}</span>
            </div>
            <div className="dispatch-actions">
              <button onClick={onClearPending}>New incident</button>
            </div>
          </div>
        )}
      </div>

      <div className="sidebar-section">
        <h2>Active incidents</h2>
        {incidents.filter((i) => i.status !== "resolved").length === 0 && (
          <div className="empty">None.</div>
        )}
        {incidents
          .filter((i) => i.status !== "resolved")
          .map((i) => (
            <div key={i.id} className="list-item">
              <div>
                <div className="name">Incident #{i.id}</div>
                <div className="meta">
                  {Number(i.lat).toFixed(4)}, {Number(i.lng).toFixed(4)}
                </div>
              </div>
              <span className={`status-pill ${i.status}`}>{i.status}</span>
            </div>
          ))}
      </div>

      <div className="sidebar-section scroll">
        <h2>Fleet</h2>
        {ambulances.map((a) => (
          <div key={a.id} className="list-item">
            <div>
              <div className="name">{a.name}</div>
              <div className="meta">
                {Number(a.lat).toFixed(4)}, {Number(a.lng).toFixed(4)}
              </div>
            </div>
            <span className={`status-pill ${a.status}`}>{a.status.replace("_", " ")}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}