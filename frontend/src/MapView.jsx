import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { useEffect, useRef, useState } from "react";

const ambIcon = (status) =>
  L.divIcon({
    className: "",
    html: `<div class="amb-marker ${status}"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

const incidentIcon = L.divIcon({
  className: "",
  html: `<div class="incident-marker"></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

function ClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => onMapClick(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

function SizeInvalidator() {
  const map = useMap();
  useEffect(() => {
    // Invalidate once immediately, then again after a short delay
    map.invalidateSize();
    const t = setTimeout(() => map.invalidateSize(), 200);
    const onResize = () => map.invalidateSize();
    window.addEventListener("resize", onResize);
    return () => {
      clearTimeout(t);
      window.removeEventListener("resize", onResize);
    };
  }, [map]);
  return null;
}

function RouteFitter({ route }) {
  const map = useMap();
  useEffect(() => {
    if (route && route.length > 1) {
      const bounds = L.latLngBounds(route);
      map.fitBounds(bounds, { padding: [60, 60] });
    }
  }, [route, map]);
  return null;
}

export default function MapView({ ambulances, incidents, route, onMapClick, pendingIncident }) {
  const containerRef = useRef(null);
  // Don't render the map until the container has a real measured size
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setReady(true);
          observer.disconnect(); // only need to fire once
        }
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} style={{ height: "100%", width: "100%", position: "relative" }}>
      {ready && (
        <MapContainer
          center={[13.06, 80.24]}
          zoom={12}
          style={{ height: "100%", width: "100%", position: "absolute", inset: 0 }}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap"
          />
          <SizeInvalidator />
          <RouteFitter route={route} />
          <ClickHandler onMapClick={onMapClick} />

          {ambulances.map((a) => (
            <Marker key={a.id} position={[a.lat, a.lng]} icon={ambIcon(a.status)} />
          ))}

          {incidents.map((i) => (
            <Marker key={i.id} position={[i.lat, i.lng]} icon={incidentIcon} />
          ))}

          {pendingIncident && (
            <Marker position={[pendingIncident.lat, pendingIncident.lng]} icon={incidentIcon} />
          )}

          {route && route.length > 1 && (
            <Polyline
              positions={route}
              pathOptions={{ color: "#4f8cff", weight: 4, opacity: 0.9 }}
            />
          )}
        </MapContainer>
      )}
    </div>
  );
}
