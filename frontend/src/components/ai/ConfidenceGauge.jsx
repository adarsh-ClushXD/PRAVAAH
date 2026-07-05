/** Confidence gauge visualization */
import { formatConfidence } from '../../utils/riskColorScale'

export default function ConfidenceGauge({ score, assessment }) {
  const pct = Math.round((score || 0) * 100)
  const color = pct >= 75 ? '#00E676' : pct >= 50 ? '#FFB800' : '#FF6B00'
  const circumference = 2 * Math.PI * 28

  return (
    <div className="glass-panel p-3 flex items-center gap-3">
      {/* SVG Arc gauge */}
      <div className="relative flex-shrink-0 w-16 h-16">
        <svg viewBox="0 0 64 64" className="w-full h-full -rotate-90">
          <circle cx="32" cy="32" r="28" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="5" />
          <circle
            cx="32" cy="32" r="28"
            fill="none"
            stroke={color}
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - (score || 0))}
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
          <span className="text-sm font-bold font-mono" style={{ color }}>{pct}%</span>
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-slate-300 mb-0.5">AI Confidence</p>
        <p className="text-[10px] text-slate-500 leading-relaxed">
          {assessment?.reliability_note || 'Confidence based on data completeness and source reliability.'}
        </p>
        {assessment?.data_completeness && (
          <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-slate-400 font-mono">
            {assessment.data_completeness}
          </span>
        )}
      </div>
    </div>
  )
}
