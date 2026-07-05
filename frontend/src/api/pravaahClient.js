/**
 * PRAVAAH API Client
 * Axios instance with base URL, interceptors, and typed helpers.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 300000, // 5 minutes for AI analysis endpoints
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Request interceptor — log outgoing requests in dev
apiClient.interceptors.request.use((config) => {
  if (import.meta.env.DEV) {
    console.debug(`[PRAVAAH] → ${config.method?.toUpperCase()} ${config.url}`)
  }
  return config
})

// Response interceptor — normalize errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Unknown error'
    console.error(`[PRAVAAH] API Error: ${message}`)
    return Promise.reject(new Error(message))
  }
)

// ── Typed API methods ──────────────────────────────────────────────────────

export const pravaahAPI = {
  // Health
  getHealth: () => apiClient.get('/health').then(r => r.data),

  // Districts
  getDistricts: () => apiClient.get('/districts').then(r => r.data),
  getDistrict: (id) => apiClient.get(`/districts/${id}`).then(r => r.data),

  // Weather
  getWeather: (districtId) => apiClient.get(`/weather/${districtId}`).then(r => r.data),

  // Rivers
  getAllStations: () => apiClient.get('/rivers').then(r => r.data),
  getDistrictRivers: (districtId) => apiClient.get(`/rivers/district/${districtId}`).then(r => r.data),
  getStation: (stationId) => apiClient.get(`/rivers/station/${stationId}`).then(r => r.data),

  // Analysis
  runAnalysis: (districtId, forceRefresh = false) =>
    apiClient.post('/analysis/run', { district_id: districtId, force_refresh: forceRefresh }).then(r => r.data),
  getLatestAnalysis: (districtId) =>
    apiClient.get(`/analysis/${districtId}/latest`).then(r => r.data),

  // Reports
  getReportJSON: (analysisId) => `${BASE_URL}/api/v1/reports/${analysisId}/json`,
  getReportPDF: (analysisId) => `${BASE_URL}/api/v1/reports/${analysisId}/pdf`,
}
