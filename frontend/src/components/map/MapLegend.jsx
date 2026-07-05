/** Map legend component */
export default function MapLegend() {
  const levels = [
    { label: 'Low', color: '#00E676', range: '0–20' },
    { label: 'Moderate', color: '#FFB800', range: '20–40' },
    { label: 'High', color: '#FF6B00', range: '40–60' },
    { label: 'Very High', color: '#FF2D55', range: '60–80' },
    { label: 'Critical', color: '#9C27B0', range: '80–100' },
  ]

  return (
    <div className="absolute bottom-4 left-4 glass-panel px-3 py-2.5 z-[1000] pointer-events-none">
      <p className="section-heading mb-2">Risk Index</p>
      <div className="space-y-1">
        {levels.map(({ label, color, range }) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: color, opacity: 0.85 }}
            />
            <span className="text-xs text-slate-300">{label}</span>
            <span className="text-xs text-slate-500 font-mono ml-auto pl-2">{range}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 pt-2 border-t border-white/5 space-y-1">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-risk-critical flex-shrink-0" />
          <span className="text-xs text-slate-400">Critical Station</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-risk-moderate flex-shrink-0" />
          <span className="text-xs text-slate-400">Warning Station</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-risk-low flex-shrink-0" />
          <span className="text-xs text-slate-400">Normal Station</span>
        </div>
      </div>
    </div>
  )
}
