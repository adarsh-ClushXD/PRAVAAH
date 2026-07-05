import React from 'react';
import { usePravaahStore } from '../../store/pravaahStore';
import { Activity } from 'lucide-react';

export default function ScenarioCards() {
  const { currentAnalysis: analysis } = usePravaahStore();
  const scenarios = analysis?.scenarios;

  const cards = [
    { key: 'best_case', label: 'Best Case Scenario', borderColor: 'border-risk-low', textColor: 'text-risk-low', bg: 'bg-risk-low/5' },
    { key: 'most_likely', label: 'Most Likely Outcome', borderColor: 'border-cyan-glow', textColor: 'text-cyan-glow', bg: 'bg-cyan-glow/5' },
    { key: 'worst_case', label: 'Worst Case Scenario', borderColor: 'border-risk-critical', textColor: 'text-risk-critical', bg: 'bg-risk-critical/5' },
  ];

  if (!scenarios) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-5 py-3 border-b border-navy-800 bg-navy-900/50 flex justify-between items-center z-10">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">5. Predictive Scenarios (72h)</h3>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-gray-500">
          <Activity size={32} className="mb-2 opacity-50" />
          <p>Run analysis to generate predictive scenarios</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-3 border-b border-navy-800 bg-navy-900/50 flex justify-between items-center z-10">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">5. Predictive Scenarios (72h)</h3>
      </div>
      <div className="flex-1 p-5 overflow-x-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full">
          {cards.map(({ key, label, borderColor, textColor, bg }) => {
            const scenario = scenarios?.[key];
            if (!scenario) return null;
            const pct = Math.round((scenario.probability || 0) * 100);
            const impact = scenario.projected_impact || {};

            return (
              <div
                key={key}
                className={`rounded-xl p-4 flex flex-col border-t-2 ${borderColor} ${bg} relative overflow-hidden`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className={`text-sm font-bold ${textColor}`}>{label}</span>
                  <span className="text-xs font-mono font-bold text-white bg-navy-950/50 px-2 py-1 rounded">{pct}% prob</span>
                </div>

                <div className="flex-1 space-y-3">
                  {/* Timeline */}
                  {scenario['72h_timeline']?.length > 0 && (
                    <div className="space-y-2 relative">
                      <div className="absolute left-1.5 top-2 bottom-2 w-[1px] bg-navy-700"></div>
                      {scenario['72h_timeline'].slice(0, 3).map((t, i) => (
                        <div key={i} className="flex items-start gap-3 relative">
                          <div className={`w-3 h-3 rounded-full mt-0.5 z-10 bg-navy-950 border-[2px] ${borderColor}`}></div>
                          <div>
                            <span className="text-xs font-bold text-white block">+{t.hours_from_now}h</span>
                            <span className="text-xs text-gray-400 leading-relaxed block">{t.description}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Impact metrics */}
                <div className="mt-4 pt-3 border-t border-navy-800/50">
                  <div className="flex justify-between items-end">
                    <div>
                      <p className="text-[10px] text-gray-500 uppercase tracking-wider">Est. Impact Area</p>
                      <p className="text-sm font-mono font-bold text-gray-200">
                        {impact.estimated_flood_area_km2?.toLocaleString() || '--'} km²
                      </p>
                    </div>
                    {impact.evacuation_required && (
                      <div className="flex items-center gap-1 text-[10px] text-risk-critical bg-risk-critical/10 px-2 py-1 rounded">
                        <span className="w-1.5 h-1.5 rounded-full bg-risk-critical animate-pulse" />
                        EVAC REQ
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
