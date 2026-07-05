import React from 'react';
import { usePravaahStore } from '../../store/pravaahStore';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function RiskMatrix() {
  const { districts, selectedDistrictId, selectDistrict } = usePravaahStore();
  const [showAll, setShowAll] = React.useState(false);

  const analyzed = [...districts].filter(d => d.composite_flood_risk_index !== null)
    .sort((a, b) => b.composite_flood_risk_index - a.composite_flood_risk_index);

  const displayDistricts = showAll ? analyzed : analyzed.slice(0, 5);

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-3 border-b border-navy-800 bg-navy-900/50 flex justify-between items-center z-10">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">3. Top Risk Districts</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-navy-700">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-navy-900 z-10">
            <tr className="border-b border-navy-800 text-xs font-semibold text-gray-500 uppercase">
              <th className="pb-3 font-medium w-12 text-center">Rank</th>
              <th className="pb-3 font-medium">District</th>
              <th className="pb-3 font-medium text-right">Risk Score</th>
              <th className="pb-3 font-medium text-center">Trend</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {displayDistricts.map((district, idx) => (
              <DistrictRow
                key={district.district_id}
                district={district}
                rank={idx + 1}
                isSelected={selectedDistrictId === district.district_id}
                onClick={() => selectDistrict(district.district_id)}
              />
            ))}
            {analyzed.length === 0 && (
              <tr>
                <td colSpan="4" className="text-center py-6 text-gray-500">
                  Run analysis to populate table
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {analyzed.length > 5 && (
        <div className="p-4 border-t border-navy-800 flex justify-center flex-shrink-0">
          <button 
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-1.5 text-xs font-medium text-gray-300 border border-navy-700 rounded-md hover:bg-navy-800 transition-colors"
          >
            {showAll ? 'Show Top 5 Only' : 'View All Districts'}
          </button>
        </div>
      )}
    </div>
  );
}

function DistrictRow({ district, rank, isSelected, onClick }) {
  const riskScore = district.composite_flood_risk_index;

  const getTrendIcon = () => {
    // Mock trend based on risk score for UI purposes
    if (riskScore > 75) return <TrendingUp size={16} className="text-risk-critical" />;
    if (riskScore > 50) return <TrendingUp size={16} className="text-risk-moderate" />;
    return <Minus size={16} className="text-gray-500" />;
  };

  return (
    <tr 
      onClick={onClick}
      className={`border-b border-navy-800/50 cursor-pointer transition-colors ${
        isSelected ? 'bg-navy-800' : 'hover:bg-navy-800/30'
      }`}
    >
      <td className="py-3 text-center text-gray-400 font-mono">{rank}</td>
      <td className={`py-3 font-medium ${isSelected ? 'text-white' : 'text-gray-300'}`}>
        {district.district_name}
      </td>
      <td className="py-3 text-right">
        <span className="font-mono text-white">{Math.round(riskScore)}%</span>
      </td>
      <td className="py-3 flex justify-center items-center">
        {getTrendIcon()}
      </td>
    </tr>
  );
}
