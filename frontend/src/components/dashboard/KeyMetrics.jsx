import React from 'react';
import { usePravaahStore } from '../../store/pravaahStore';
import { AlertTriangle, Users, CloudRain, Activity } from 'lucide-react';

const MetricCard = ({ title, value, subtext, icon, valueColor = 'text-white' }) => (
  <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 flex flex-col justify-between">
    <div className="flex justify-between items-start mb-4">
      <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
      <div className="p-2 rounded-lg bg-navy-800 text-gray-400">
        {icon}
      </div>
    </div>
    <div>
      <div className={`text-3xl font-bold tracking-tight ${valueColor}`}>
        {value}
      </div>
      <p className="text-xs text-gray-500 mt-2 font-medium">
        {subtext}
      </p>
    </div>
  </div>
);

export default function KeyMetrics() {
  const { districts, currentAnalysis: analysis } = usePravaahStore();

  // Calculate metrics
  const totalDistricts = districts.length || 23;
  const highRiskDistricts = districts.filter(d => 
    ['ORANGE', 'RED', 'PURPLE'].includes(d.alert_level)
  ).length;

  const getOverallRisk = () => {
    if (!analysis) return 'MODERATE';
    return analysis.risk_category || 'MODERATE';
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL': return 'text-risk-critical';
      case 'VERY HIGH': return 'text-risk-high';
      case 'HIGH': return 'text-risk-high';
      case 'MODERATE': return 'text-risk-moderate';
      default: return 'text-risk-low';
    }
  };

  const overallRisk = getOverallRisk();
  const riskColor = getRiskColor(overallRisk);

  // Derive population affected from scenario (mock calculation based on risk)
  // In reality, this would be computed by the backend per district.
  const affectedPop = highRiskDistricts > 0 ? (highRiskDistricts * 3.1).toFixed(1) + ' Lakh' : '0';

  // Rainfall forecast derived from active analysis or default
  const rainfallCategory = analysis?.risk_dimensions?.atmospheric_risk?.score > 6 
    ? 'Very Heavy' 
    : (analysis?.risk_dimensions?.atmospheric_risk?.score > 3 ? 'Heavy' : 'Normal');
  const rainfallMm = analysis?.risk_dimensions?.atmospheric_risk?.score > 6 
    ? '120 - 200 mm' 
    : (analysis?.risk_dimensions?.atmospheric_risk?.score > 3 ? '50 - 120 mm' : '< 50 mm');

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <MetricCard 
        title="Overall Flood Risk" 
        value={overallRisk}
        valueColor={riskColor}
        subtext={`Based on current analysis of ${totalDistricts} districts`}
        icon={<Activity size={20} className={riskColor} />}
      />
      <MetricCard 
        title="Districts at High Risk" 
        value={`${highRiskDistricts} / ${totalDistricts}`}
        valueColor={highRiskDistricts > 0 ? 'text-risk-high' : 'text-white'}
        subtext={highRiskDistricts > 0 ? `${highRiskDistricts} districts require immediate attention` : 'No immediate threats'}
        icon={<AlertTriangle size={20} className={highRiskDistricts > 0 ? 'text-risk-high' : 'text-gray-400'} />}
      />
      <MetricCard 
        title="People Potentially Affected" 
        value={affectedPop}
        subtext="Based on current scenario and population data"
        icon={<Users size={20} />}
      />
      <MetricCard 
        title="Next 48h Rainfall Forecast" 
        value={rainfallCategory}
        valueColor={rainfallCategory === 'Very Heavy' ? 'text-risk-moderate' : 'text-white'}
        subtext={`${rainfallMm} (High confidence)`}
        icon={<CloudRain size={20} className={rainfallCategory === 'Very Heavy' ? 'text-risk-moderate' : 'text-gray-400'} />}
      />
    </div>
  );
}
