import { useEffect, useState } from "react";
import MapView from "./MapView.jsx";
import Sidebar from "./Sidebar.jsx";
import { getAmbulances, getIncidents, reportIncident, dispatchAmbulance } from "./api.js";
import { connectAmbulanceSocket } from "./socket.js";

export default function App() {
  const [ambulances, setAmbulances] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [pendingIncident, setPendingIncident] = useState(null);
  const [dispatchResult, setDispatchResult] = useState(null);
  const [dispatching, setDispatching] = useState(false);

  // Initial load
  useEffect(() => {
    (async () => {
      try {
        const [ambs, incs] = await Promise.all([getAmbulances(), getIncidents()]);
        setAmbulances(ambs);
        setIncidents(incs);
      } catch (err) {
        console.error("Initial load failed:", err);
      }
    })();
  }, []);

  // Live ambulance updates via WebSocket
  useEffect(() => {
    const disconnect = connectAmbulanceSocket((data) => {
      setAmbulances(data);
    });
    return disconnect;
  }, []);

  // Refresh incidents every 5s (coarse polling is fine for incidents)
  useEffect(() => {
    const t = setInterval(async () => {
      try {
        const incs = await getIncidents();
        setIncidents(incs);
      } catch {}
    }, 5000);
    return () => clearInterval(t);
  }, []);

  const handleMapClick = (lat, lng) => {
    if (dispatchResult) return; // don't allow new clicks while showing a route
    setPendingIncident({ lat, lng });
  };

  const handleDispatch = async () => {
    if (!pendingIncident) return;
    setDispatching(true);
    try {
      const inc = await reportIncident(pendingIncident.lat, pendingIncident.lng, 1);
      const result = await dispatchAmbulance(inc.incident_id);
      setDispatchResult(result);
      const incs = await getIncidents();
      setIncidents(incs);
    } catch (err) {
      console.error("Dispatch failed:", err);
      alert("Dispatch failed. See console.");
    } finally {
      setDispatching(false);
    }
  };

  const handleClear = () => {
    setPendingIncident(null);
    setDispatchResult(null);
  };

  return (
    <div className="app">
      <div className="map-pane">
        <MapView
          ambulances={ambulances}
          incidents={incidents}
          route={dispatchResult?.route}
          onMapClick={handleMapClick}
          pendingIncident={pendingIncident}
        />
      </div>
      <Sidebar
        ambulances={ambulances}
        incidents={incidents}
        pendingIncident={pendingIncident}
        dispatchResult={dispatchResult}
        onDispatch={handleDispatch}
        onClearPending={handleClear}
        dispatching={dispatching}
      />
    </div>
  );
}