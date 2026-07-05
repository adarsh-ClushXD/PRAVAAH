import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { usePravaahStore } from '../../store/pravaahStore';

export default function AlertTicker() {
  const { districts, currentAnalysis: analysis } = usePravaahStore();
  
  // Aggregate real alerts or use mock ones if none exist
  const highRiskDistricts = districts.filter(d => 
    ['ORANGE', 'RED', 'PURPLE'].includes(d.alert_level)
  );

  let alerts = [];
  if (highRiskDistricts.length > 0) {
    alerts = highRiskDistricts.map(d => 
      `${d.alert_level} ALERT: ${d.district_name} - ${d.primary_threat || 'High flood risk detected'}`
    );
  }

  if (analysis?.sms_alert_text) {
    alerts.push(`SYSTEM BROADCAST: ${analysis.sms_alert_text}`);
  }

  // Fallback defaults if empty
  if (alerts.length === 0) {
    alerts = [
      "No critical alerts currently active.",
      "System monitoring all 23 districts in real-time.",
      "River gauges operating at nominal levels."
    ];
  }

  return (
    <div className="h-8 bg-risk-critical text-white flex items-center overflow-hidden flex-shrink-0 z-50">
      <div className="bg-red-900/40 h-full px-4 flex items-center gap-2 font-bold text-xs whitespace-nowrap z-10 shadow-[4px_0_10px_rgba(0,0,0,0.5)]">
        <AlertTriangle size={14} className="animate-pulse" />
        LIVE ALERTS
      </div>
      
      <div className="flex-1 overflow-hidden relative h-full flex items-center">
        <div className="animate-ticker whitespace-nowrap flex gap-16 absolute left-full">
          {alerts.map((alert, idx) => (
            <span key={idx} className="text-xs font-semibold tracking-wide">
              {alert}
            </span>
          ))}
          {/* Duplicate for seamless scrolling */}
          {alerts.map((alert, idx) => (
            <span key={`dup-${idx}`} className="text-xs font-semibold tracking-wide">
              {alert}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
