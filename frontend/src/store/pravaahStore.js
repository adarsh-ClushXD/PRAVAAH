/**
 * Zustand global state store for PRAVAAH.
 * Manages district data, selected district, analysis results, and UI state.
 */
import { create } from 'zustand'
import { pravaahAPI } from '../api/pravaahClient'

export const usePravaahStore = create((set, get) => ({
  // ── District State ─────────────────────────────────────────────────────
  districts: [],
  selectedDistrictId: null,
  isLoadingDistricts: false,
  districtsError: null,

  // ── Analysis State ─────────────────────────────────────────────────────
  analyses: {},          // district_id → AnalysisResponse
  isRunningAnalysis: false,
  analysisError: null,
  currentAnalysis: null,

  // ── River State ────────────────────────────────────────────────────────
  riverStations: [],
  isLoadingRivers: false,

  // ── UI State ───────────────────────────────────────────────────────────
  activePanel: 'dashboard',   // 'dashboard' | 'analysis' | 'history'
  mapZoomDistrict: null,
  systemHealth: null,
  lastUpdated: null,

  // ── Sync State ──────────────────────────────────────────────────────────
  isSyncing: false,
  syncProgress: null,   // { current: 3, total: 23, districtName: 'Howrah' }

  // ── Actions ────────────────────────────────────────────────────────────

  fetchDistricts: async () => {
    set({ isLoadingDistricts: true, districtsError: null })
    try {
      const data = await pravaahAPI.getDistricts()
      set({ districts: data, isLoadingDistricts: false, lastUpdated: new Date() })
    } catch (err) {
      set({ districtsError: err.message, isLoadingDistricts: false })
    }
  },

  selectDistrict: (districtId) => {
    set({ selectedDistrictId: districtId, mapZoomDistrict: districtId })
    // Auto-load latest analysis if not already loaded
    const { analyses } = get()
    if (districtId && !analyses[districtId]) {
      get().loadLatestAnalysis(districtId)
    }
  },

  loadLatestAnalysis: async (districtId) => {
    try {
      const data = await pravaahAPI.getLatestAnalysis(districtId)
      if (data) {
        set((state) => ({
          analyses: { ...state.analyses, [districtId]: data },
          currentAnalysis: data,
        }))
      }
    } catch {
      // Silently fail — user can trigger analysis manually
    }
  },

  runAnalysis: async (districtId, forceRefresh = false) => {
    set({ isRunningAnalysis: true, analysisError: null })
    try {
      const data = await pravaahAPI.runAnalysis(districtId, forceRefresh)
      set((state) => ({
        analyses: { ...state.analyses, [districtId]: data },
        currentAnalysis: data,
        isRunningAnalysis: false,
        lastUpdated: new Date(),
      }))
      // Refresh district list to pick up new risk scores
      await get().fetchDistricts()
      return data
    } catch (err) {
      set({ analysisError: err.message, isRunningAnalysis: false })
      throw err
    }
  },

  syncAllDistricts: async (forceRefresh = false) => {
    const { districts } = get()
    if (!districts.length) return
    
    set({ isSyncing: true, analysisError: null, syncProgress: { current: 0, total: districts.length, districtName: '' } })
    
    for (let i = 0; i < districts.length; i++) {
      const d = districts[i]
      set({ syncProgress: { current: i + 1, total: districts.length, districtName: d.name || d.district_id } })
      
      try {
        const data = await pravaahAPI.runAnalysis(d.district_id, forceRefresh)
        const { selectedDistrictId } = get()
        set((state) => ({
          analyses: { ...state.analyses, [d.district_id]: data },
          // Live-update currentAnalysis if this is the selected district
          ...(d.district_id === selectedDistrictId ? { currentAnalysis: data } : {}),
        }))
      } catch {
        // Skip failed districts silently — don't abort the whole sync
      }
    }
    
    // After sync: refresh district list for updated risk scores
    await get().fetchDistricts()
    
    // Reload the currently selected district's analysis from server to ensure freshness
    const { selectedDistrictId } = get()
    if (selectedDistrictId) {
      await get().loadLatestAnalysis(selectedDistrictId)
    }
    
    set({ isSyncing: false, syncProgress: null, lastUpdated: new Date() })
  },

  fetchRiverStations: async () => {
    set({ isLoadingRivers: true })
    try {
      const data = await pravaahAPI.getAllStations()
      set({ riverStations: data, isLoadingRivers: false })
    } catch {
      set({ isLoadingRivers: false })
    }
  },

  checkHealth: async () => {
    try {
      const health = await pravaahAPI.getHealth()
      set({ systemHealth: health })
    } catch {
      set({ systemHealth: { status: 'unreachable' } })
    }
  },

  setActivePanel: (panel) => set({ activePanel: panel }),

  getCurrentAnalysis: () => {
    const { selectedDistrictId, analyses } = get()
    return selectedDistrictId ? analyses[selectedDistrictId] : null
  },
}))
