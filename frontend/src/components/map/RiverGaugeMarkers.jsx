/**
 * River Gauge Markers — Leaflet markers for monitoring stations.
 */
import { CircleMarker, Popup } from 'react-leaflet'

const STATUS_COLORS = {
  critical: '#FF2D55',
  warning: '#FFB800',
  normal: '#00E676',
}

export default function RiverGaugeMarkers({ stations = [] }) {
  return stations.map(station => (
    <CircleMarker
      key={station.station_id}
      center={[station.lat, station.lon]}
      radius={station.status === 'critical' ? 8 : 6}
      pathOptions={{
        fillColor: STATUS_COLORS[station.status] || '#00E676',
        fillOpacity: 0.9,
        color: '#fff',
        weight: 1.5,
      }}
    >
      <Popup className="pravaah-popup" maxWidth={280}>
        <div className="bg-navy-900 rounded-lg p-3 text-sm text-white min-w-[220px]">
          <div className="font-semibold text-cyan-glow mb-2">{station.station_name}</div>
          <div className="text-slate-400 text-xs mb-2">{station.river} River</div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400 text-xs">Current Level</span>
              <span className="font-mono text-xs font-medium">{station.current_level_m}m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 text-xs">Danger Level</span>
              <span className="font-mono text-xs text-risk-critical">{station.danger_level_m}m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 text-xs">Risk Ratio</span>
              <span className="font-mono text-xs">{(station.overflow_risk_ratio * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400 text-xs">Trend</span>
              <span className={`text-xs font-medium ${station.trend === 'rising' ? 'text-risk-critical' : station.trend === 'falling' ? 'text-risk-low' : 'text-risk-moderate'}`}>
                {station.trend === 'rising' ? '↑ Rising' : station.trend === 'falling' ? '↓ Falling' : '→ Steady'}
              </span>
            </div>
          </div>
          <div
            className={`mt-2 text-center text-xs font-bold py-1 rounded ${
              station.status === 'critical' ? 'bg-risk-critical/20 text-risk-critical' :
              station.status === 'warning' ? 'bg-risk-moderate/20 text-risk-moderate' :
              'bg-risk-low/20 text-risk-low'
            }`}
          >
            {station.status.toUpperCase()}
          </div>
        </div>
      </Popup>
    </CircleMarker>
  ))
}
