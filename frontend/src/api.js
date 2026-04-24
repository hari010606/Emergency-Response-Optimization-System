import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

export async function getAmbulances() {
  const res = await client.get("/ambulances");
  return res.data;
}

export async function getIncidents() {
  const res = await client.get("/incidents");
  return res.data;
}

export async function reportIncident(lat, lng, priority = 1) {
  const res = await client.post("/incident", { lat, lng, priority });
  return res.data;
}

export async function dispatchAmbulance(incidentId) {
  const res = await client.post(`/dispatch/${incidentId}`);
  return res.data;
}

export async function markAvailable(ambId) {
  const res = await client.post(`/ambulance/${ambId}/available`);
  return res.data;
}