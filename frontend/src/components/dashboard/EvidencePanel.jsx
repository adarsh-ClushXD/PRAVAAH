import React from 'react';
import { usePravaahStore } from '../../store/pravaahStore';
import { CloudRain, Droplets, Map, Navigation, Activity } from 'lucide-react';

const EvidenceRow = ({ icon, title, value, subtext, statusColor }) => (
  <div className="flex items-center space-x-3 p-3 hover:bg-navy-800/50 rounded-lg transition-colors">
    <div className={`p-2 rounded-full bg-navy-800 ${statusColor}`}>
      {icon}
    </div>
    <div className="flex-1">
      <div className="text-sm font-medium text-gray-300">{title}</div>
      <div className="flex items-baseline space-x-2">
        <span className="text-lg font-bold text-white">{value}</span>
        <span className={`text-xs ${statusColor}`}>{subtext}</span>
      </div>
    </div>
  </div>
);

export default function EvidencePanel() {
  const { currentAnalysis: analysis } = usePravaahStore();
  
  if (!analysis) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-gray-500">
        <Map size={32} className="mb-2 opacity-50" />
        <p>Select a district to view current evidence</p>
      </div>
    );
  }

  // Derive mock values based on analysis, as the prompt specifies layout based on reference image.
  // In a full implementation, these would map directly to specific fields in the fact_sheet.
  const rainfallScore = analysis.risk_dimensions?.atmospheric_risk?.score || 0;
  const riverScore = analysis.risk_dimensions?.river_overflow_risk?.score || 0;
  const soilScore = analysis.risk_dimensions?.saturation_risk?.score || 0;
  
  const rainfallSubtext = rainfallScore > 5 ? '(↑ 38% above normal)' : '(Normal)';
  const rainfallColor = rainfallScore > 5 ? 'text-risk-high' : 'text-cyan-glow';
  const rainfallValue = rainfallScore > 5 ? '145 mm' : '12 mm';

  const riverSubtext = riverScore > 6 ? '(↑ Rising Fast)' : '(Stable)';
  const riverColor = riverScore > 6 ? 'text-risk-critical' : 'text-risk-low';
  const riverValue = riverScore > 6 ? '24.6 m' : '18.2 m';

  const soilSubtext = soilScore > 6 ? 'High (Saturated)' : 'Normal';
  const soilColor = soilScore > 6 ? 'text-risk-high' : 'text-risk-moderate';

  return (
    <>
      <div className="px-5 py-3 border-b border-navy-800 bg-navy-900/50 flex justify-between items-center z-10">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">4. Current Evidence Snapshot</h3>
      </div>
      <div className="flex-1 p-2 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-navy-700">
        <EvidenceRow 
          icon={<CloudRain size={18} />} 
          title="Rainfall (Past 24h)" 
          value={rainfallValue} 
          subtext={rainfallSubtext} 
          statusColor={rainfallColor} 
        />
        <EvidenceRow 
          icon={<Navigation size={18} />} 
          title="River Level (Ganga at Farakka)" 
          value={riverValue} 
          subtext={riverSubtext} 
          statusColor={riverColor} 
        />
        <EvidenceRow 
          icon={<Map size={18} />} 
          title="Satellite Water Spread" 
          value="+18%" 
          subtext="compared to yesterday" 
          statusColor="text-risk-low" 
        />
        <EvidenceRow 
          icon={<Droplets size={18} />} 
          title="Soil Moisture" 
          value={soilSubtext} 
          subtext="" 
          statusColor={soilColor} 
        />
        <EvidenceRow 
          icon={<Activity size={18} />} 
          title="Historical Similarity" 
          value="82%" 
          subtext="match with 2021 flood event" 
          statusColor="text-purple-400" 
        />
      </div>
    </>
  );
}
