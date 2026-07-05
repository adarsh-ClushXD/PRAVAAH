import { useEffect, Suspense, lazy } from 'react'
import { usePravaahStore } from '../store/pravaahStore'
import Header from '../components/layout/Header'
import Sidebar from '../components/layout/Sidebar'
import KeyMetrics from '../components/dashboard/KeyMetrics'
import RiskMatrix from '../components/dashboard/RiskMatrix'
import XAIPanel from '../components/ai/XAIPanel'
import EvidencePanel from '../components/dashboard/EvidencePanel'
import ScenarioCards from '../components/ai/ScenarioCards'
import AlertTicker from '../components/layout/AlertTicker'
import { Hammer } from 'lucide-react'

// Lazy load the map to avoid SSR issues with Leaflet
const FloodMap = lazy(() => import('../components/map/FloodMap'))

export default function Dashboard() {
  const { fetchDistricts, fetchRiverStations, checkHealth, activePanel } = usePravaahStore()

  useEffect(() => {
    checkHealth()
    fetchDistricts()
    fetchRiverStations()

    // Periodic refresh every 10 minutes
    const interval = setInterval(() => {
      fetchDistricts()
      fetchRiverStations()
    }, 600_000)
    return () => clearInterval(interval)
  }, [])

  const renderContent = () => {
    if (activePanel !== 'dashboard') {
      return (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
          <div className="w-20 h-20 bg-navy-800 rounded-full flex items-center justify-center mb-6">
            <Hammer size={32} className="text-cyan-glow" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Feature Under Construction</h2>
          <p className="text-gray-400 max-w-md">
            The {activePanel.charAt(0).toUpperCase() + activePanel.slice(1)} module is not available in the current Hackathon demo. Please return to the Dashboard.
          </p>
        </div>
      )
    }

    return (
      <>
        {/* Section 1: Key Metrics */}
        <KeyMetrics />

        {/* Section 2, 3, 4: Middle Row (Map, Districts, Evidence) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6 min-h-[420px]">
          {/* Map */}
          <div className="lg:col-span-6 bg-navy-900 border border-navy-800 rounded-xl overflow-hidden flex flex-col relative shadow-lg shadow-black/20">
            <div className="px-5 py-3 border-b border-navy-800 bg-navy-900/50 flex justify-between items-center z-10">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">2. District Risk Map</h3>
            </div>
            <div className="flex-1 relative">
              <Suspense fallback={
                <div className="absolute inset-0 flex items-center justify-center bg-navy-950/80 backdrop-blur-sm z-50">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-cyan-glow/30 border-t-cyan-glow rounded-full animate-spin" />
                    <p className="text-xs text-slate-400">Loading map…</p>
                  </div>
                </div>
              }>
                <FloodMap />
              </Suspense>
            </div>
          </div>

          {/* Top Risk Districts Table */}
          <div className="lg:col-span-3 bg-navy-900 border border-navy-800 rounded-xl flex flex-col shadow-lg shadow-black/20 overflow-hidden">
            <RiskMatrix />
          </div>

          {/* Evidence Snapshot */}
          <div className="lg:col-span-3 bg-navy-900 border border-navy-800 rounded-xl flex flex-col shadow-lg shadow-black/20 overflow-hidden">
            <EvidencePanel />
          </div>
        </div>

        {/* Section 5, 6: Bottom Row (Scenarios & AI Insights) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 bg-navy-900 border border-navy-800 rounded-xl flex flex-col shadow-lg shadow-black/20 overflow-hidden">
            <ScenarioCards />
          </div>
          <div className="lg:col-span-5 bg-navy-900 border border-navy-800 rounded-xl flex flex-col shadow-lg shadow-black/20 overflow-hidden">
            <XAIPanel />
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="h-screen flex bg-[#050c1a] overflow-hidden text-gray-200 font-sans selection:bg-cyan-glow/30">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#050c1a]">
        <Header />

        <main className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-navy-700">
          {renderContent()}
        </main>

        {/* Section 7: Alert Footer */}
        <AlertTicker />
      </div>
    </div>
  )
}
