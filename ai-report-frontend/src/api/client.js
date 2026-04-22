import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export async function generateReport(payload) {
  const { data } = await api.post("/reports/generate", payload);
  return data;
}

export async function sendChatQuestion(payload) {
  const { data } = await api.post("/agent/chat", payload);
  return data;
}

export async function fetchReportHistory() {
  const { data } = await api.get("/reports/history");
  return data;
}

export async function checkBackendHealth() {
  const { data } = await api.get("/health");
  return data;
}
